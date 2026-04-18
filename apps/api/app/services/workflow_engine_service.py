"""Workflow execution engine — step-level orchestration with pause/resume/cancel/retry."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.db.models import WorkflowDefinitionTable, WorkflowExecutionTable, WorkflowStepExecutionTable
from app.db.session import SessionLocal
from app.models.workflow import (
    WorkflowCommand,
    WorkflowExecutionDetail,
    WorkflowExecutionRecord,
    WorkflowExecutionStatus,
    WorkflowStepExecutionRecord,
    WorkflowStepStatus,
)
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state


class WorkflowEngineService:
    """Orchestrates workflow execution at the step level."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_workflow(
        self,
        run_id: str,
        request_id: str,
        tenant_id: str,
        workflow_definition_id: str | None = None,
        actor_id: str = "system",
    ) -> WorkflowExecutionRecord:
        """Create a new workflow execution and advance to the first step."""
        now = datetime.now(timezone.utc)
        execution_id = f"wfe_{uuid4().hex[:12]}"
        request = get_request_state(request_id, tenant_id)
        if request is None:
            raise StopIteration(request_id)

        with SessionLocal() as session:
            steps_json: list[dict] = []
            if workflow_definition_id:
                defn = session.get(WorkflowDefinitionTable, workflow_definition_id)
                if defn:
                    steps_json = defn.steps or []

            execution = WorkflowExecutionTable(
                id=execution_id,
                tenant_id=request.tenant_id,
                run_id=run_id,
                request_id=request_id,
                workflow_definition_id=workflow_definition_id,
                status=WorkflowExecutionStatus.RUNNING,
                current_step_index=0,
                step_states=[],
                started_at=now,
                created_at=now,
                updated_at=now,
            )
            session.add(execution)

            for idx, step_def in enumerate(steps_json):
                step = WorkflowStepExecutionTable(
                    id=f"{execution_id}_s{idx}",
                    workflow_execution_id=execution_id,
                    step_index=idx,
                    step_name=step_def.get("name", f"step_{idx}"),
                    status=WorkflowStepStatus.PENDING,
                    input_payload=step_def.get("config"),
                )
                session.add(step)

            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="workflow.started",
                aggregate_type="workflow_execution",
                aggregate_id=execution_id,
                actor=actor_id,
                detail=f"Workflow execution started for run {run_id}",
                request_id=request_id,
                run_id=run_id,
            )
            session.commit()
            return self._record_from_row(execution)

    def advance_step(self, execution_id: str, actor_id: str = "system", tenant_id: str | None = None) -> WorkflowExecutionRecord:
        """Complete the current step and advance to the next, or complete the workflow."""
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            execution = self._get_execution_row(session, execution_id, tenant_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            if execution.status != WorkflowExecutionStatus.RUNNING:
                raise ValueError(f"Cannot advance workflow in status {execution.status}")

            current_step = session.scalars(
                select(WorkflowStepExecutionTable).where(
                    WorkflowStepExecutionTable.workflow_execution_id == execution_id,
                    WorkflowStepExecutionTable.step_index == execution.current_step_index,
                )
            ).first()

            if current_step:
                current_step.status = WorkflowStepStatus.COMPLETED
                current_step.completed_at = now

            total_steps = session.scalars(
                select(WorkflowStepExecutionTable).where(
                    WorkflowStepExecutionTable.workflow_execution_id == execution_id
                )
            ).all()

            next_index = execution.current_step_index + 1
            if next_index >= len(total_steps):
                execution.status = WorkflowExecutionStatus.COMPLETED
                execution.completed_at = now
                event_type = "workflow.completed"
                detail = "All steps completed"
            else:
                execution.current_step_index = next_index
                next_step = [s for s in total_steps if s.step_index == next_index]
                if next_step:
                    next_step[0].status = WorkflowStepStatus.RUNNING
                    next_step[0].started_at = now
                event_type = "workflow.step_advanced"
                detail = f"Advanced to step {next_index}"

            execution.updated_at = now
            event_store_service.append(
                session,
                tenant_id=execution.tenant_id,
                event_type=event_type,
                aggregate_type="workflow_execution",
                aggregate_id=execution_id,
                actor=actor_id,
                detail=detail,
                request_id=execution.request_id,
                run_id=execution.run_id,
            )
            session.commit()
            return self._record_from_row(execution)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def pause_workflow(self, execution_id: str, reason: str = "", actor_id: str = "system", tenant_id: str | None = None) -> WorkflowExecutionRecord:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            execution = self._get_execution_row(session, execution_id, tenant_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            if execution.status != WorkflowExecutionStatus.RUNNING:
                raise ValueError(f"Cannot pause workflow in status {execution.status}")
            execution.status = WorkflowExecutionStatus.PAUSED
            execution.pause_reason = reason
            execution.paused_at = now
            execution.updated_at = now
            event_store_service.append(
                session,
                tenant_id=execution.tenant_id,
                event_type="workflow.paused",
                aggregate_type="workflow_execution",
                aggregate_id=execution_id,
                actor=actor_id,
                detail=reason or "Paused by operator",
                request_id=execution.request_id,
                run_id=execution.run_id,
            )
            session.commit()
            return self._record_from_row(execution)

    def resume_workflow(self, execution_id: str, actor_id: str = "system", tenant_id: str | None = None) -> WorkflowExecutionRecord:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            execution = self._get_execution_row(session, execution_id, tenant_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            if execution.status != WorkflowExecutionStatus.PAUSED:
                raise ValueError(f"Cannot resume workflow in status {execution.status}")
            execution.status = WorkflowExecutionStatus.RUNNING
            execution.resumed_at = now
            execution.updated_at = now
            event_store_service.append(
                session,
                tenant_id=execution.tenant_id,
                event_type="workflow.resumed",
                aggregate_type="workflow_execution",
                aggregate_id=execution_id,
                actor=actor_id,
                detail="Workflow resumed",
                request_id=execution.request_id,
                run_id=execution.run_id,
            )
            session.commit()
            return self._record_from_row(execution)

    def cancel_workflow(self, execution_id: str, reason: str = "", actor_id: str = "system", tenant_id: str | None = None) -> WorkflowExecutionRecord:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            execution = self._get_execution_row(session, execution_id, tenant_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            if execution.status in {WorkflowExecutionStatus.COMPLETED, WorkflowExecutionStatus.CANCELED}:
                raise ValueError(f"Cannot cancel workflow in status {execution.status}")
            execution.status = WorkflowExecutionStatus.CANCELED
            execution.cancel_reason = reason
            execution.completed_at = now
            execution.updated_at = now
            event_store_service.append(
                session,
                tenant_id=execution.tenant_id,
                event_type="workflow.canceled",
                aggregate_type="workflow_execution",
                aggregate_id=execution_id,
                actor=actor_id,
                detail=reason or "Workflow canceled",
                request_id=execution.request_id,
                run_id=execution.run_id,
            )
            session.commit()
            return self._record_from_row(execution)

    def retry_step(self, execution_id: str, step_index: int, actor_id: str = "system", tenant_id: str | None = None) -> WorkflowExecutionRecord:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            execution = self._get_execution_row(session, execution_id, tenant_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")

            step = session.scalars(
                select(WorkflowStepExecutionTable).where(
                    WorkflowStepExecutionTable.workflow_execution_id == execution_id,
                    WorkflowStepExecutionTable.step_index == step_index,
                )
            ).first()
            if not step:
                raise ValueError(f"Step {step_index} not found")
            if step.status != WorkflowStepStatus.FAILED:
                raise ValueError(f"Can only retry failed steps, step is {step.status}")

            step.status = WorkflowStepStatus.RUNNING
            step.error_message = None
            step.retry_count += 1
            step.started_at = now
            step.completed_at = None

            if execution.status == WorkflowExecutionStatus.FAILED:
                execution.status = WorkflowExecutionStatus.RUNNING
            execution.current_step_index = step_index
            execution.retry_count += 1
            execution.failure_reason = None
            execution.updated_at = now
            event_store_service.append(
                session,
                tenant_id=execution.tenant_id,
                event_type="workflow.step_retried",
                aggregate_type="workflow_execution",
                aggregate_id=execution_id,
                actor=actor_id,
                detail=f"Retrying step {step_index}",
                request_id=execution.request_id,
                run_id=execution.run_id,
            )
            session.commit()
            return self._record_from_row(execution)

    def skip_step(self, execution_id: str, step_index: int, actor_id: str = "system", tenant_id: str | None = None) -> WorkflowExecutionRecord:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            execution = self._get_execution_row(session, execution_id, tenant_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")

            step = session.scalars(
                select(WorkflowStepExecutionTable).where(
                    WorkflowStepExecutionTable.workflow_execution_id == execution_id,
                    WorkflowStepExecutionTable.step_index == step_index,
                )
            ).first()
            if not step:
                raise ValueError(f"Step {step_index} not found")

            step.status = WorkflowStepStatus.SKIPPED
            step.completed_at = now
            execution.updated_at = now
            event_store_service.append(
                session,
                tenant_id=execution.tenant_id,
                event_type="workflow.step_skipped",
                aggregate_type="workflow_execution",
                aggregate_id=execution_id,
                actor=actor_id,
                detail=f"Skipped step {step_index}",
                request_id=execution.request_id,
                run_id=execution.run_id,
            )
            session.commit()
            return self._record_from_row(execution)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_execution(self, execution_id: str, tenant_id: str | None = None) -> WorkflowExecutionDetail:
        with SessionLocal() as session:
            execution = self._get_execution_row(session, execution_id, tenant_id)
            if not execution:
                raise ValueError(f"Workflow execution {execution_id} not found")
            steps = session.scalars(
                select(WorkflowStepExecutionTable)
                .where(WorkflowStepExecutionTable.workflow_execution_id == execution_id)
                .order_by(WorkflowStepExecutionTable.step_index)
            ).all()
            return WorkflowExecutionDetail(
                **self._record_from_row(execution).model_dump(),
                steps=[self._step_record_from_row(s) for s in steps],
            )

    @staticmethod
    def _get_execution_row(session, execution_id: str, tenant_id: str | None = None) -> WorkflowExecutionTable | None:
        execution = session.get(WorkflowExecutionTable, execution_id)
        if execution is None or tenant_id is None:
            return execution
        request = get_request_state(execution.request_id, tenant_id)
        if request is None or execution.tenant_id != request.tenant_id:
            raise StopIteration(execution_id)
        return execution

    # ------------------------------------------------------------------
    # Row mappers
    # ------------------------------------------------------------------

    @staticmethod
    def _record_from_row(row: WorkflowExecutionTable) -> WorkflowExecutionRecord:
        return WorkflowExecutionRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            run_id=row.run_id,
            request_id=row.request_id,
            workflow_definition_id=row.workflow_definition_id,
            status=row.status,
            current_step_index=row.current_step_index,
            pause_reason=row.pause_reason,
            cancel_reason=row.cancel_reason,
            failure_reason=row.failure_reason,
            retry_count=row.retry_count,
            started_at=row.started_at,
            paused_at=row.paused_at,
            resumed_at=row.resumed_at,
            completed_at=row.completed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _step_record_from_row(row: WorkflowStepExecutionTable) -> WorkflowStepExecutionRecord:
        return WorkflowStepExecutionRecord(
            id=row.id,
            workflow_execution_id=row.workflow_execution_id,
            step_index=row.step_index,
            step_name=row.step_name,
            status=row.status,
            input_payload=row.input_payload,
            output_payload=row.output_payload,
            error_message=row.error_message,
            retry_count=row.retry_count,
            started_at=row.started_at,
            completed_at=row.completed_at,
        )


workflow_engine_service = WorkflowEngineService()
