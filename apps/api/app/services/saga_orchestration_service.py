"""Saga orchestration service — coordinates multi-request workflows with compensation.

Implements the saga pattern: each saga definition declares an ordered list
of steps, and the execution engine advances through them one at a time.
If a step fails the engine runs compensating actions in reverse order.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import SagaDefinitionTable, SagaExecutionTable
from app.db.session import SessionLocal
from app.models.saga import SagaExecutionRecord, SagaStatus


class SagaOrchestrationService:
    """Manages saga lifecycle: creation, advancement, and compensation."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_saga(
        self,
        definition_id: str,
        tenant_id: str,
        actor_id: str,
    ) -> SagaExecutionRecord:
        """Create a new saga execution from a definition.

        Initialises step states from the definition's step list and sets
        the execution status to ``running``.
        """
        now = datetime.now(timezone.utc)
        execution_id = f"sge_{uuid.uuid4().hex[:12]}"

        with SessionLocal() as session:
            definition = (
                session.query(SagaDefinitionTable)
                .filter(
                    SagaDefinitionTable.id == definition_id,
                    SagaDefinitionTable.tenant_id == tenant_id,
                )
                .one()
            )

            steps = definition.steps if isinstance(definition.steps, list) else []
            step_states = [
                {
                    "step_index": i,
                    "request_id": step.get("request_id"),
                    "status": "pending",
                    "compensation_status": None,
                    "error": None,
                }
                for i, step in enumerate(steps)
            ]

            row = SagaExecutionTable(
                id=execution_id,
                tenant_id=tenant_id,
                saga_definition_id=definition_id,
                status=SagaStatus.RUNNING,
                step_states=step_states,
                compensation_log=[],
                created_at=now,
                completed_at=None,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return SagaExecutionRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Advancement
    # ------------------------------------------------------------------

    def advance_saga(
        self, execution_id: str, actor_id: str
    ) -> SagaExecutionRecord:
        """Advance the saga to the next pending step.

        Marks the current step as ``completed`` and moves the execution
        forward.  If all steps are complete the execution status becomes
        ``completed``.
        """
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(SagaExecutionTable)
                .filter(SagaExecutionTable.id == execution_id)
                .one()
            )

            if row.status not in (SagaStatus.RUNNING, SagaStatus.PENDING):
                raise ValueError(
                    f"Cannot advance saga in status '{row.status}'"
                )

            step_states: list[dict] = list(row.step_states) if row.step_states else []
            advanced = False

            for step in step_states:
                if step.get("status") == "pending":
                    step["status"] = "completed"
                    advanced = True
                    break

            if not advanced:
                raise ValueError("No pending steps remaining to advance")

            # Check if all steps are now completed.
            all_done = all(s.get("status") == "completed" for s in step_states)
            row.step_states = step_states
            if all_done:
                row.status = SagaStatus.COMPLETED
                row.completed_at = now

            session.commit()
            session.refresh(row)
            return SagaExecutionRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Compensation
    # ------------------------------------------------------------------

    def compensate(
        self, execution_id: str, actor_id: str
    ) -> SagaExecutionRecord:
        """Run compensating actions in reverse order for all completed steps.

        Sets the execution status to ``compensating`` and then
        ``compensated`` once all compensations succeed.
        """
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(SagaExecutionTable)
                .filter(SagaExecutionTable.id == execution_id)
                .one()
            )

            row.status = SagaStatus.COMPENSATING
            step_states: list[dict] = list(row.step_states) if row.step_states else []
            compensation_log: list[dict] = list(row.compensation_log) if row.compensation_log else []

            # Walk completed steps in reverse and mark as compensated.
            for step in reversed(step_states):
                if step.get("status") == "completed":
                    step["compensation_status"] = "compensated"
                    compensation_log.append(
                        {
                            "step_index": step["step_index"],
                            "action": "compensate",
                            "actor": actor_id,
                            "timestamp": now.isoformat(),
                        }
                    )

            row.step_states = step_states
            row.compensation_log = compensation_log
            row.status = SagaStatus.COMPENSATED
            row.completed_at = now

            session.commit()
            session.refresh(row)
            return SagaExecutionRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_execution(self, execution_id: str) -> SagaExecutionRecord:
        """Retrieve a saga execution by id."""
        with SessionLocal() as session:
            row = (
                session.query(SagaExecutionTable)
                .filter(SagaExecutionTable.id == execution_id)
                .one()
            )
            return SagaExecutionRecord.model_validate(row)


saga_orchestration_service = SagaOrchestrationService()
