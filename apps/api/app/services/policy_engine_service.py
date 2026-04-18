"""Policy engine service — evaluates policy rules against request context.

Merges the extensible policy DSL with legacy TransitionGateTable checks
to produce a unified list of triggered actions for governance transitions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import PolicyRuleTable, TransitionGateTable
from app.db.session import SessionLocal
from app.domain.policy_dsl import evaluate_rules
from app.models.policy import (
    CreatePolicyRuleRequest,
    PolicyRuleRecord,
    UpdatePolicyRuleRequest,
)
from app.models.request import RequestRecord


class PolicyEngineService:
    """Evaluates policy rules from the database against a request context dict.

    Combines the extensible ``policy_dsl`` evaluation engine with legacy
    ``TransitionGateTable`` checks so that callers receive a single, ordered
    list of triggered actions.
    """

    # ------------------------------------------------------------------
    # Core evaluation
    # ------------------------------------------------------------------

    def evaluate_for_transition(
        self,
        session,
        request_row: RequestRecord,
        target_status: str,
        tenant_id: str,
    ) -> list[dict]:
        """Evaluate all active policy rules for a proposed status transition.

        Builds a context dict from *request_row*, queries matching
        ``PolicyRuleTable`` rows for the tenant, runs them through the DSL
        evaluator, and then merges in any legacy ``TransitionGateTable``
        constraints.

        Returns an ordered list of triggered action dicts.
        """
        context = self._build_context(request_row, target_status)

        # --- extensible policy rules ---
        rule_rows = (
            session.query(PolicyRuleTable)
            .filter(
                PolicyRuleTable.tenant_id == tenant_id,
                PolicyRuleTable.active.is_(True),
            )
            .order_by(PolicyRuleTable.priority)
            .all()
        )

        rule_dicts = [
            {
                "id": r.id,
                "condition": r.condition or {},
                "actions": r.actions or [],
                "priority": r.priority,
                "active": r.active,
            }
            for r in rule_rows
        ]

        actions = evaluate_rules(rule_dicts, context)

        # --- legacy transition gate checks ---
        gate_actions = self._evaluate_transition_gates(
            session, target_status, tenant_id
        )
        actions.extend(gate_actions)

        return actions

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    def list_policy_rules(self, tenant_id: str) -> list[PolicyRuleRecord]:
        """Return all policy rules for a tenant."""
        with SessionLocal() as session:
            rows = (
                session.query(PolicyRuleTable)
                .filter(PolicyRuleTable.tenant_id == tenant_id)
                .order_by(PolicyRuleTable.priority)
                .all()
            )
            return [PolicyRuleRecord.model_validate(r) for r in rows]

    def create_policy_rule(
        self,
        tenant_id: str,
        policy_id: str,
        payload: CreatePolicyRuleRequest,
    ) -> PolicyRuleRecord:
        """Persist a new policy rule."""
        now = datetime.now(timezone.utc)
        row = PolicyRuleTable(
            id=f"pr_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            policy_id=policy_id,
            name=payload.name,
            condition=payload.condition,
            actions=payload.actions,
            priority=payload.priority,
            active=payload.active,
            created_at=now,
            updated_at=now,
        )
        with SessionLocal() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return PolicyRuleRecord.model_validate(row)

    def update_policy_rule(
        self,
        rule_id: str,
        tenant_id: str,
        payload: UpdatePolicyRuleRequest,
    ) -> PolicyRuleRecord:
        """Update an existing policy rule (partial update)."""
        with SessionLocal() as session:
            row = (
                session.query(PolicyRuleTable)
                .filter(
                    PolicyRuleTable.id == rule_id,
                    PolicyRuleTable.tenant_id == tenant_id,
                )
                .one()
            )
            update_data = payload.model_dump(exclude_none=True)
            for field, value in update_data.items():
                setattr(row, field, value)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(row)
            return PolicyRuleRecord.model_validate(row)

    def delete_policy_rule(self, rule_id: str, tenant_id: str) -> None:
        """Delete a policy rule by id."""
        with SessionLocal() as session:
            row = (
                session.query(PolicyRuleTable)
                .filter(
                    PolicyRuleTable.id == rule_id,
                    PolicyRuleTable.tenant_id == tenant_id,
                )
                .one()
            )
            session.delete(row)
            session.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context(request_row: RequestRecord, target_status: str) -> dict:
        """Build a flat context dict suitable for the policy DSL evaluator."""
        return {
            "request_id": request_row.id,
            "request_type": request_row.request_type,
            "template_id": request_row.template_id,
            "status": request_row.status.value if hasattr(request_row.status, "value") else str(request_row.status),
            "target_status": target_status,
            "priority": request_row.priority.value if hasattr(request_row.priority, "value") else str(request_row.priority),
            "owner_team_id": request_row.owner_team_id,
            "submitter_id": request_row.submitter_id,
            "tags": request_row.tags or [],
            "policy_context": request_row.policy_context or {},
        }

    @staticmethod
    def _evaluate_transition_gates(
        session, target_status: str, tenant_id: str
    ) -> list[dict]:
        """Query TransitionGateTable and emit ``require_review`` actions for
        any gates that apply to *target_status*."""
        gates = (
            session.query(TransitionGateTable)
            .filter(
                TransitionGateTable.tenant_id == tenant_id,
                TransitionGateTable.transition_target == target_status,
                TransitionGateTable.active.is_(True),
            )
            .order_by(TransitionGateTable.gate_order)
            .all()
        )
        actions: list[dict] = []
        for gate in gates:
            actions.append(
                {
                    "type": "require_review",
                    "reviewer": gate.required_check_name,
                    "reason": f"Transition gate: {gate.gate_scope}",
                    "source": "transition_gate",
                    "gate_id": gate.id,
                }
            )
        return actions


policy_engine_service = PolicyEngineService()
