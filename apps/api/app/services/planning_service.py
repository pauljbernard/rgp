"""Planning service -- manages planning constructs, memberships, and roadmap views."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func

from app.db.models import PlanningConstructTable, PlanningMembershipTable
from app.db.session import SessionLocal
from app.models.planning import (
    CreatePlanningConstructRequest,
    PlanningConstructDetail,
    PlanningConstructRecord,
    PlanningMembershipRecord,
    PlanningProgressRecord,
    PlanningRoadmapEntry,
)
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state


class PlanningService:
    """Manages planning constructs (initiatives, programs, releases, etc.)."""

    _COMPLETED_STATUSES = {"completed", "closed", "promoted"}
    _IN_PROGRESS_STATUSES = {
        "submitted",
        "validated",
        "classified",
        "ownership_resolved",
        "planned",
        "queued",
        "in_execution",
        "awaiting_input",
        "awaiting_review",
        "under_review",
        "approved",
        "promotion_pending",
    }
    _BLOCKED_STATUSES = {"validation_failed", "changes_requested", "rejected", "failed"}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_construct(
        self,
        payload: CreatePlanningConstructRequest,
        actor_id: str,
        tenant_id: str,
    ) -> PlanningConstructRecord:
        now = datetime.now(timezone.utc)
        construct_id = f"pc_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = PlanningConstructTable(
                id=construct_id,
                tenant_id=tenant_id,
                type=payload.type,
                name=payload.name,
                description=payload.description,
                owner_team_id=payload.owner_team_id,
                status="active",
                priority=payload.priority,
                target_date=payload.target_date,
                capacity_budget=payload.capacity_budget,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="planning_construct.created",
                aggregate_type="planning_construct",
                aggregate_id=construct_id,
                actor=actor_id,
                detail=f"Planning construct '{payload.name}' ({payload.type}) created",
            )
            session.commit()
            session.refresh(row)
            return PlanningConstructRecord.model_validate(row)

    def get_construct(self, construct_id: str) -> PlanningConstructRecord:
        with SessionLocal() as session:
            row = (
                session.query(PlanningConstructTable)
                .filter(PlanningConstructTable.id == construct_id)
                .one()
            )
            return PlanningConstructRecord.model_validate(row)

    def list_memberships(self, construct_id: str) -> list[PlanningMembershipRecord]:
        with SessionLocal() as session:
            construct = (
                session.query(PlanningConstructTable)
                .filter(PlanningConstructTable.id == construct_id)
                .one()
            )
            rows = (
                session.query(PlanningMembershipTable)
                .filter(PlanningMembershipTable.planning_construct_id == construct_id)
                .order_by(PlanningMembershipTable.sequence.asc(), PlanningMembershipTable.priority.desc())
                .all()
            )
            return [
                PlanningMembershipRecord.model_validate(row)
                for row in rows
                if get_request_state(row.request_id, construct.tenant_id) is not None
            ]

    def list_constructs(
        self, tenant_id: str, type: str | None = None
    ) -> list[PlanningConstructRecord]:
        with SessionLocal() as session:
            q = session.query(PlanningConstructTable).filter(
                PlanningConstructTable.tenant_id == tenant_id,
            )
            if type:
                q = q.filter(PlanningConstructTable.type == type)
            rows = q.order_by(PlanningConstructTable.priority.desc(), PlanningConstructTable.created_at.desc()).all()
            return [PlanningConstructRecord.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    def add_request(
        self,
        construct_id: str,
        request_id: str,
        sequence: int = 0,
        priority: int = 0,
    ) -> PlanningMembershipRecord:
        now = datetime.now(timezone.utc)
        membership_id = f"pm_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            construct = (
                session.query(PlanningConstructTable)
                .filter(PlanningConstructTable.id == construct_id)
                .one()
            )
            if get_request_state(request_id, construct.tenant_id) is None:
                raise StopIteration(request_id)
            row = PlanningMembershipTable(
                id=membership_id,
                planning_construct_id=construct_id,
                request_id=request_id,
                sequence=sequence,
                priority=priority,
                added_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=construct.tenant_id,
                event_type="planning_construct.request_added",
                aggregate_type="planning_construct",
                aggregate_id=construct_id,
                actor="system",
                detail=f"Request {request_id} added to construct {construct_id}",
                request_id=request_id,
            )
            session.commit()
            session.refresh(row)
            return PlanningMembershipRecord.model_validate(row)

    def remove_request(
        self, construct_id: str, request_id: str
    ) -> None:
        with SessionLocal() as session:
            construct = (
                session.query(PlanningConstructTable)
                .filter(PlanningConstructTable.id == construct_id)
                .one()
            )
            if get_request_state(request_id, construct.tenant_id) is None:
                raise StopIteration(request_id)
            row = (
                session.query(PlanningMembershipTable)
                .filter(
                    PlanningMembershipTable.planning_construct_id == construct_id,
                    PlanningMembershipTable.request_id == request_id,
                )
                .one()
            )
            session.delete(row)

            event_store_service.append(
                session,
                tenant_id=construct.tenant_id,
                event_type="planning_construct.request_removed",
                aggregate_type="planning_construct",
                aggregate_id=construct_id,
                actor="system",
                detail=f"Request {request_id} removed from construct {construct_id}",
                request_id=request_id,
            )
            session.commit()

    def reorder_requests(
        self, construct_id: str, ordering: list[dict]
    ) -> list[PlanningMembershipRecord]:
        """Reorder requests within a construct.

        ``ordering`` is a list of dicts, each with ``request_id``,
        ``sequence``, and optionally ``priority``.
        """
        with SessionLocal() as session:
            construct = (
                session.query(PlanningConstructTable)
                .filter(PlanningConstructTable.id == construct_id)
                .one()
            )
            for entry in ordering:
                if get_request_state(entry["request_id"], construct.tenant_id) is None:
                    raise StopIteration(entry["request_id"])
                row = (
                    session.query(PlanningMembershipTable)
                    .filter(
                        PlanningMembershipTable.planning_construct_id == construct_id,
                        PlanningMembershipTable.request_id == entry["request_id"],
                    )
                    .one()
                )
                row.sequence = entry.get("sequence", row.sequence)
                row.priority = entry.get("priority", row.priority)

            session.commit()

            rows = (
                session.query(PlanningMembershipTable)
                .filter(PlanningMembershipTable.planning_construct_id == construct_id)
                .order_by(PlanningMembershipTable.sequence.asc())
                .all()
            )
            return [
                PlanningMembershipRecord.model_validate(row)
                for row in rows
                if get_request_state(row.request_id, construct.tenant_id) is not None
            ]

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def aggregate_progress(self, construct_id: str) -> dict:
        """Query child requests and return a status summary.

        Returns a dict with counts per request status and overall
        completion percentage.
        """
        with SessionLocal() as session:
            construct = (
                session.query(PlanningConstructTable)
                .filter(PlanningConstructTable.id == construct_id)
                .one()
            )
            memberships = (
                session.query(PlanningMembershipTable)
                .filter(PlanningMembershipTable.planning_construct_id == construct_id)
                .all()
            )
            request_ids = [m.request_id for m in memberships]

            if not request_ids:
                return {
                    "construct_id": construct_id,
                    "total": 0,
                    "status_counts": {},
                    "completion_pct": 0.0,
                }

            status_counts: dict[str, int] = {}
            total = 0
            for request_id in request_ids:
                request = get_request_state(request_id, construct.tenant_id)
                if request is None:
                    continue
                status = request.status.value if hasattr(request.status, "value") else str(request.status)
                status_counts[status] = status_counts.get(status, 0) + 1
                total += 1

            completed = sum(status_counts.get(status, 0) for status in self._COMPLETED_STATUSES)
            completion_pct = (completed / total * 100.0) if total > 0 else 0.0

            return {
                "construct_id": construct_id,
                "total": total,
                "status_counts": status_counts,
                "completion_pct": round(completion_pct, 1),
            }

    # ------------------------------------------------------------------
    # Roadmap view
    # ------------------------------------------------------------------

    @staticmethod
    def _schedule_state(target_date: datetime | None, completion_pct: float) -> str:
        if not target_date:
            return "unscheduled"
        if completion_pct >= 100.0:
            return "complete"
        now = datetime.now(timezone.utc)
        if target_date < now:
            return "overdue"
        if (target_date - now).days <= 14:
            return "due_soon"
        return "on_track"

    def get_roadmap_view(
        self, tenant_id: str, type: str | None = None
    ) -> list[PlanningRoadmapEntry]:
        """Return a timeline projection of constructs with their progress.

        Each entry includes the construct metadata plus aggregated
        membership and completion information.
        """
        with SessionLocal() as session:
            q = session.query(PlanningConstructTable).filter(
                PlanningConstructTable.tenant_id == tenant_id,
            )
            if type:
                q = q.filter(PlanningConstructTable.type == type)

            constructs = q.order_by(
                PlanningConstructTable.target_date.asc().nulls_last(),
                PlanningConstructTable.priority.desc(),
            ).all()

            roadmap: list[PlanningRoadmapEntry] = []
            for c in constructs:
                member_count = (
                    session.query(func.count(PlanningMembershipTable.id))
                    .filter(PlanningMembershipTable.planning_construct_id == c.id)
                    .scalar()
                )
                progress = self.aggregate_progress(c.id)
                completed_count = sum(progress["status_counts"].get(status, 0) for status in self._COMPLETED_STATUSES)
                in_progress_count = sum(progress["status_counts"].get(status, 0) for status in self._IN_PROGRESS_STATUSES)
                blocked_count = sum(progress["status_counts"].get(status, 0) for status in self._BLOCKED_STATUSES)
                completion_pct = progress["completion_pct"]

                roadmap.append(
                    PlanningRoadmapEntry(
                        id=c.id,
                        type=c.type,
                        name=c.name,
                        status=c.status,
                        priority=c.priority,
                        target_date=c.target_date.isoformat() if c.target_date else None,
                        capacity_budget=c.capacity_budget,
                        member_count=member_count,
                        completion_pct=completion_pct,
                        completed_count=completed_count,
                        in_progress_count=in_progress_count,
                        blocked_count=blocked_count,
                        schedule_state=self._schedule_state(c.target_date, completion_pct),
                        owner_team_id=c.owner_team_id,
                    )
                )

            return roadmap

    def get_construct_detail(self, construct_id: str) -> PlanningConstructDetail:
        construct = self.get_construct(construct_id)
        memberships = self.list_memberships(construct_id)
        progress = PlanningProgressRecord(**self.aggregate_progress(construct_id))
        return PlanningConstructDetail(
            construct=construct,
            memberships=memberships,
            progress=progress,
        )


planning_service = PlanningService()
