"""Queue routing service -- assignment groups, skill-based routing, and escalation rules."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import AssignmentGroupTable, EscalationRuleTable
from app.db.session import SessionLocal
from app.domain.policy_dsl import evaluate_condition
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state, record_request_event, update_request_state


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

    def list_escalation_rules(self, tenant_id: str) -> list[dict]:
        with SessionLocal() as session:
            rows = (
                session.query(EscalationRuleTable)
                .filter(
                    EscalationRuleTable.tenant_id == tenant_id,
                    EscalationRuleTable.status == "active",
                )
                .order_by(EscalationRuleTable.created_at.asc())
                .all()
            )
            return [_escalation_record(r) for r in rows]

    def evaluate_escalations(
        self, request_id: str, tenant_id: str
    ) -> list[dict]:
        """Evaluate all active escalation rules against the given request.

        Builds a context from the request row and evaluates each rule's
        condition using the policy DSL. Returns the list of triggered rules.
        """
        with SessionLocal() as session:
            request = get_request_state(request_id, tenant_id)
            if not request:
                raise StopIteration(request_id)

            # Build context for condition evaluation
            now = datetime.now(timezone.utc)
            created_at = request.created_at
            age_hours = (now - created_at).total_seconds() / 3600.0 if created_at else 0

            context = {
                "request_id": request.id,
                "status": request.status,
                "priority": request.priority,
                "request_type": request.request_type,
                "owner_team_id": request.owner_team_id,
                "tags": request.tags or [],
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

    def execute_escalation(
        self,
        request_id: str,
        rule_id: str,
        tenant_id: str,
        actor: str,
    ) -> dict:
        now = datetime.now(timezone.utc)
        request = get_request_state(request_id, tenant_id)
        from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

        dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
        is_dynamo_canonical = dynamodb_adapter._get_request_item(tenant_id, request_id) is not None

        with SessionLocal() as session:
            rule_row = (
                session.query(EscalationRuleTable)
                .filter(
                    EscalationRuleTable.id == rule_id,
                    EscalationRuleTable.tenant_id == tenant_id,
                    EscalationRuleTable.status == "active",
                )
                .first()
            )
            if request is None or not rule_row:
                raise ValueError("Unknown request or escalation rule")

            outcome = f"escalated:{rule_row.escalation_type}"
            updated_request_fields: dict = {}
            if rule_row.escalation_type == "reassign":
                updated_request_fields["owner_team_id"] = rule_row.escalation_target
                outcome = f"reassigned:{rule_row.escalation_target}"
            else:
                policy_context = dict(request.policy_context or {})
                policy_context["last_escalation"] = {
                    "rule_id": rule_row.id,
                    "type": rule_row.escalation_type,
                    "target": rule_row.escalation_target,
                    "executed_at": now.isoformat(),
                    "executed_by": actor,
                }
                updated_request_fields["policy_context"] = policy_context
                outcome = f"{rule_row.escalation_type}:{rule_row.escalation_target}"

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="queue_routing.escalation_executed",
                aggregate_type="request",
                aggregate_id=request_id,
                actor=actor,
                detail=f"Escalation rule '{rule_row.name}' executed for request {request_id}",
                request_id=request_id,
                payload={
                    "rule_id": rule_row.id,
                    "escalation_type": rule_row.escalation_type,
                    "escalation_target": rule_row.escalation_target,
                    "outcome": outcome,
                },
            )
            session.commit()

            update_request_state(
                request_id,
                tenant_id,
                actor,
                **updated_request_fields,
                updated_at=now,
                updated_by=actor,
            )
            if is_dynamo_canonical:
                record_request_event(
                    request_id,
                    tenant_id,
                    actor,
                    "Escalation Executed",
                    f"Escalation rule '{rule_row.name}' executed",
                    status=RequestStatus(request.status).value if isinstance(request.status, str) else request.status.value,
                )

            return {
                "request_id": request_id,
                "rule_id": rule_row.id,
                "escalation_type": rule_row.escalation_type,
                "escalation_target": rule_row.escalation_target,
                "outcome": outcome,
                "executed_at": now.isoformat(),
            }

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

    # ------------------------------------------------------------------
    # Recommendation
    # ------------------------------------------------------------------

    def recommend_assignment(
        self,
        request_id: str,
        tenant_id: str,
    ) -> dict:
        with SessionLocal() as session:
            request = get_request_state(request_id, tenant_id)
            if not request:
                raise StopIteration(request_id)

            required_skills = sorted(
                {
                    *(request.tags or []),
                    request.request_type,
                    str(request.priority),
                }
            )
            recommended = self.route_by_skill(required_skills, tenant_id) or self.route_by_capacity(tenant_id)
            route_basis: list[str] = []
            matched_skills: list[str] = []
            if recommended:
                matched_skills = sorted(set(recommended.get("skill_tags", [])) & set(required_skills))
                if matched_skills:
                    route_basis.append(f"skill overlap: {', '.join(matched_skills)}")
                if recommended.get("max_capacity") is not None:
                    route_basis.append(f"capacity: {recommended['current_load']}/{recommended['max_capacity']}")
                else:
                    route_basis.append("capacity: unbounded")
            else:
                route_basis.append("no eligible assignment group found")

            return {
                "request_id": request_id,
                "recommended_group_id": recommended.get("id") if recommended else None,
                "recommended_group_name": recommended.get("name") if recommended else None,
                "matched_skills": matched_skills,
                "route_basis": route_basis,
                "current_load": recommended.get("current_load") if recommended else None,
                "max_capacity": recommended.get("max_capacity") if recommended else None,
            }


queue_routing_service = QueueRoutingService()
