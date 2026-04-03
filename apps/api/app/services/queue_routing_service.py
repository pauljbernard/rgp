"""Queue routing service -- assignment groups, skill-based routing, and escalation rules."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import AssignmentGroupTable, EscalationRuleTable, RequestTable
from app.db.session import SessionLocal
from app.domain.policy_dsl import evaluate_condition
from app.services.event_store_service import event_store_service


def _group_record(row: AssignmentGroupTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "skill_tags": row.skill_tags,
        "max_capacity": row.max_capacity,
        "current_load": row.current_load,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _escalation_record(row: EscalationRuleTable) -> dict:
    return {
        "id": row.id,
        "tenant_id": row.tenant_id,
        "name": row.name,
        "condition": row.condition,
        "escalation_target": row.escalation_target,
        "escalation_type": row.escalation_type,
        "delay_minutes": row.delay_minutes,
        "status": row.status,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


class QueueRoutingService:
    """Manages assignment groups, skill-based and capacity-based routing, and escalation."""

    # ------------------------------------------------------------------
    # Assignment groups
    # ------------------------------------------------------------------

    def create_assignment_group(self, payload: dict, tenant_id: str) -> dict:
        now = datetime.now(timezone.utc)
        group_id = f"ag_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = AssignmentGroupTable(
                id=group_id,
                tenant_id=tenant_id,
                name=payload.get("name", "Unnamed group"),
                skill_tags=payload.get("skill_tags", []),
                max_capacity=payload.get("max_capacity"),
                current_load=0,
                status="active",
                created_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="queue_routing.group_created",
                aggregate_type="assignment_group",
                aggregate_id=group_id,
                actor="system",
                detail=f"Assignment group '{row.name}' created",
            )
            session.commit()
            session.refresh(row)
            return _group_record(row)

    def list_assignment_groups(self, tenant_id: str) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(AssignmentGroupTable)
                .filter(
                    AssignmentGroupTable.tenant_id == tenant_id,
                    AssignmentGroupTable.status == "active",
                )
                .order_by(AssignmentGroupTable.created_at.asc())
                .all()
            )
            return [_group_record(r) for r in rows]

    # ------------------------------------------------------------------
    # Routing strategies
    # ------------------------------------------------------------------

    def route_by_skill(
        self, required_skills: list[str], tenant_id: str
    ) -> dict | None:
        """Find the assignment group whose skill tags best overlap the required skills.

        Returns the group with the highest overlap count, or None if no
        active groups match any skill.
        """
        with SessionLocal() as session:
            groups = (
                session.query(AssignmentGroupTable)
                .filter(
                    AssignmentGroupTable.tenant_id == tenant_id,
                    AssignmentGroupTable.status == "active",
                )
                .all()
            )

            best: AssignmentGroupTable | None = None
            best_score = 0

            for group in groups:
                group_skills = set(group.skill_tags or [])
                overlap = len(group_skills & set(required_skills))
                if overlap > best_score:
                    best_score = overlap
                    best = group

            return _group_record(best) if best else None

    def route_by_capacity(self, tenant_id: str) -> dict | None:
        """Find the active assignment group with the lowest current load.

        Groups at or above their max capacity are excluded.
        """
        with SessionLocal() as session:
            groups = (
                session.query(AssignmentGroupTable)
                .filter(
                    AssignmentGroupTable.tenant_id == tenant_id,
                    AssignmentGroupTable.status == "active",
                )
                .order_by(AssignmentGroupTable.current_load.asc())
                .all()
            )

            for group in groups:
                if group.max_capacity is None or group.current_load < group.max_capacity:
                    return _group_record(group)

            return None

    # ------------------------------------------------------------------
    # Escalation rules
    # ------------------------------------------------------------------

    def create_escalation_rule(self, payload: dict, tenant_id: str) -> dict:
        now = datetime.now(timezone.utc)
        rule_id = f"er_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = EscalationRuleTable(
                id=rule_id,
                tenant_id=tenant_id,
                name=payload.get("name", "Unnamed rule"),
                condition=payload.get("condition", {}),
                escalation_target=payload.get("escalation_target", ""),
                escalation_type=payload.get("escalation_type", "reassign"),
                delay_minutes=payload.get("delay_minutes", 60),
                status="active",
                created_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="queue_routing.escalation_rule_created",
                aggregate_type="escalation_rule",
                aggregate_id=rule_id,
                actor="system",
                detail=f"Escalation rule '{row.name}' created",
            )
            session.commit()
            session.refresh(row)
            return _escalation_record(row)

    def evaluate_escalations(
        self, request_id: str, tenant_id: str
    ) -> list[dict]:
        """Evaluate all active escalation rules against the given request.

        Builds a context from the request row and evaluates each rule's
        condition using the policy DSL. Returns the list of triggered rules.
        """
        with SessionLocal() as session:
            request_row = (
                session.query(RequestTable)
                .filter(
                    RequestTable.id == request_id,
                    RequestTable.tenant_id == tenant_id,
                )
                .first()
            )
            if not request_row:
                return []

            # Build context for condition evaluation
            now = datetime.now(timezone.utc)
            created_at = request_row.created_at
            age_hours = (now - created_at).total_seconds() / 3600.0 if created_at else 0

            context = {
                "request_id": request_row.id,
                "status": request_row.status,
                "priority": request_row.priority,
                "request_type": request_row.request_type,
                "owner_team_id": request_row.owner_team_id,
                "tags": request_row.tags or [],
                "age_hours": age_hours,
            }

            rules = (
                session.query(EscalationRuleTable)
                .filter(
                    EscalationRuleTable.tenant_id == tenant_id,
                    EscalationRuleTable.status == "active",
                )
                .order_by(EscalationRuleTable.delay_minutes.asc())
                .all()
            )

            triggered: list[dict] = []
            for rule in rules:
                if evaluate_condition(rule.condition, context):
                    triggered.append(_escalation_record(rule))

            return triggered

    # ------------------------------------------------------------------
    # Load management
    # ------------------------------------------------------------------

    def increment_load(self, group_id: str) -> None:
        """Increment the current load counter for an assignment group."""
        with SessionLocal() as session:
            row = (
                session.query(AssignmentGroupTable)
                .filter(AssignmentGroupTable.id == group_id)
                .one()
            )
            row.current_load = row.current_load + 1
            session.commit()

    def decrement_load(self, group_id: str) -> None:
        """Decrement the current load counter for an assignment group (floor at 0)."""
        with SessionLocal() as session:
            row = (
                session.query(AssignmentGroupTable)
                .filter(AssignmentGroupTable.id == group_id)
                .one()
            )
            row.current_load = max(0, row.current_load - 1)
            session.commit()


queue_routing_service = QueueRoutingService()
