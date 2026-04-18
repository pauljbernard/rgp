"""Change set service -- manages change sets within governance workspaces."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import ChangeSetTable
from app.db.session import SessionLocal
from app.models.workspace import ChangeSetRecord, CreateChangeSetRequest
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state


class ChangeSetService:
    """Lifecycle management for change sets attached to requests."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_change_set(
        self, payload: CreateChangeSetRequest, actor_id: str, tenant_id: str
    ) -> ChangeSetRecord:
        now = datetime.now(timezone.utc)
        cs_id = f"cs_{uuid4().hex[:12]}"
        request = get_request_state(payload.request_id, tenant_id)
        if request is None:
            raise StopIteration(payload.request_id)

        with SessionLocal() as session:
            row = ChangeSetTable(
                id=cs_id,
                tenant_id=request.tenant_id,
                request_id=payload.request_id,
                workspace_id=payload.workspace_id,
                artifact_id=payload.artifact_id,
                status="draft",
                version=1,
                diff_metadata=payload.diff_metadata,
                lineage=None,
                applicable_type=payload.applicable_type,
                description=payload.description,
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="change_set.created",
                aggregate_type="change_set",
                aggregate_id=cs_id,
                actor=actor_id,
                detail=f"Change set created for request {payload.request_id}",
                request_id=payload.request_id,
                artifact_id=payload.artifact_id,
            )
            session.commit()
            session.refresh(row)
            return ChangeSetRecord.model_validate(row)

    def get_change_set(self, change_set_id: str, tenant_id: str | None = None) -> ChangeSetRecord:
        with SessionLocal() as session:
            row = self._get_change_set_row(session, change_set_id, tenant_id)
            return ChangeSetRecord.model_validate(row)

    def list_change_sets(
        self, request_id: str, tenant_id: str
    ) -> list[ChangeSetRecord]:
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            rows = (
                session.query(ChangeSetTable)
                .filter(
                    ChangeSetTable.request_id == request_id,
                    ChangeSetTable.tenant_id == request.tenant_id,
                )
                .order_by(ChangeSetTable.created_at.desc())
                .all()
            )
            return [ChangeSetRecord.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    def submit_change_set(
        self, change_set_id: str, actor_id: str, tenant_id: str | None = None
    ) -> ChangeSetRecord:
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = self._get_change_set_row(session, change_set_id, tenant_id)
            row.status = "submitted"
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="change_set.submitted",
                aggregate_type="change_set",
                aggregate_id=change_set_id,
                actor=actor_id,
                detail=f"Change set {change_set_id} submitted",
                request_id=row.request_id,
                artifact_id=row.artifact_id,
            )
            session.commit()
            session.refresh(row)
            return ChangeSetRecord.model_validate(row)

    def apply_change_set(
        self, change_set_id: str, actor_id: str, tenant_id: str | None = None
    ) -> ChangeSetRecord:
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = self._get_change_set_row(session, change_set_id, tenant_id)
            row.status = "applied"
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="change_set.applied",
                aggregate_type="change_set",
                aggregate_id=change_set_id,
                actor=actor_id,
                detail=f"Change set {change_set_id} applied",
                request_id=row.request_id,
                artifact_id=row.artifact_id,
            )
            session.commit()
            session.refresh(row)
            return ChangeSetRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Diff
    # ------------------------------------------------------------------

    def diff_change_set(self, change_set_id: str, tenant_id: str | None = None) -> dict:
        """Return the diff_metadata stored on the change set.

        In a production implementation this would compute a live diff
        between the workspace artifact and its base version.  Here we
        surface the persisted metadata and augment it with summary
        information.
        """
        with SessionLocal() as session:
            row = self._get_change_set_row(session, change_set_id, tenant_id)
            diff = row.diff_metadata or {}
            return {
                "change_set_id": change_set_id,
                "status": row.status,
                "version": row.version,
                "applicable_type": row.applicable_type,
                "diff_metadata": diff,
            }

    @staticmethod
    def _get_change_set_row(session, change_set_id: str, tenant_id: str | None = None) -> ChangeSetTable:
        row = (
            session.query(ChangeSetTable)
            .filter(ChangeSetTable.id == change_set_id)
            .one()
        )
        if tenant_id is None:
            return row
        request = get_request_state(row.request_id, tenant_id)
        if request is None or row.tenant_id != request.tenant_id:
            raise StopIteration(change_set_id)
        return row


change_set_service = ChangeSetService()
