"""Editorial workflow service -- manages multi-stage editorial review processes."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import EditorialWorkflowTable
from app.db.session import SessionLocal
from app.models.editorial import (
    CreateEditorialWorkflowRequest,
    EditorialWorkflowRecord,
)
from app.services.event_store_service import event_store_service


class EditorialWorkflowService:
    """Orchestrates editorial workflow stages and role assignments."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_workflow(
        self,
        payload: CreateEditorialWorkflowRequest,
        actor_id: str,
        tenant_id: str,
    ) -> EditorialWorkflowRecord:
        now = datetime.now(timezone.utc)
        wf_id = f"ew_{uuid4().hex[:12]}"

        stages = payload.stages or []
        current_stage = stages[0]["name"] if stages else "drafting"

        with SessionLocal() as session:
            row = EditorialWorkflowTable(
                id=wf_id,
                tenant_id=tenant_id,
                request_id=payload.request_id,
                artifact_id=payload.artifact_id,
                current_stage=current_stage,
                stages=stages,
                role_assignments=payload.role_assignments,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="editorial_workflow.created",
                aggregate_type="editorial_workflow",
                aggregate_id=wf_id,
                actor=actor_id,
                detail=f"Editorial workflow created for request {payload.request_id}",
                request_id=payload.request_id,
                artifact_id=payload.artifact_id,
            )
            session.commit()
            session.refresh(row)
            return EditorialWorkflowRecord.model_validate(row)

    def get_workflow(self, workflow_id: str) -> EditorialWorkflowRecord:
        with SessionLocal() as session:
            row = (
                session.query(EditorialWorkflowTable)
                .filter(EditorialWorkflowTable.id == workflow_id)
                .one()
            )
            return EditorialWorkflowRecord.model_validate(row)

    def list_workflows(
        self, request_id: str, tenant_id: str
    ) -> list[EditorialWorkflowRecord]:
        with SessionLocal() as session:
            rows = (
                session.query(EditorialWorkflowTable)
                .filter(
                    EditorialWorkflowTable.request_id == request_id,
                    EditorialWorkflowTable.tenant_id == tenant_id,
                )
                .order_by(EditorialWorkflowTable.created_at.desc())
                .all()
            )
            return [EditorialWorkflowRecord.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Stage progression
    # ------------------------------------------------------------------

    def advance_stage(
        self, workflow_id: str, actor_id: str
    ) -> EditorialWorkflowRecord:
        """Move the workflow to its next stage.

        Marks the current stage as ``completed`` and advances
        ``current_stage`` to the next entry in the stages list.  Raises
        ``ValueError`` if the workflow is already on its final stage.
        """
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(EditorialWorkflowTable)
                .filter(EditorialWorkflowTable.id == workflow_id)
                .one()
            )

            stages: list[dict] = list(row.stages or [])
            stage_names = [s["name"] for s in stages]

            if row.current_stage not in stage_names:
                raise ValueError(
                    f"Current stage '{row.current_stage}' not found in workflow stages"
                )

            current_idx = stage_names.index(row.current_stage)
            if current_idx >= len(stages) - 1:
                raise ValueError("Workflow is already on its final stage")

            # Mark the current stage completed
            stages[current_idx]["status"] = "completed"

            # Advance
            next_stage = stages[current_idx + 1]
            next_stage["status"] = "in_progress"
            row.current_stage = next_stage["name"]
            row.stages = stages
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="editorial_workflow.stage_advanced",
                aggregate_type="editorial_workflow",
                aggregate_id=workflow_id,
                actor=actor_id,
                detail=f"Advanced to stage '{next_stage['name']}'",
                request_id=row.request_id,
                artifact_id=row.artifact_id,
            )
            session.commit()
            session.refresh(row)
            return EditorialWorkflowRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Role assignment
    # ------------------------------------------------------------------

    def assign_role(
        self,
        workflow_id: str,
        role: str,
        user_id: str,
        actor_id: str,
    ) -> EditorialWorkflowRecord:
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(EditorialWorkflowTable)
                .filter(EditorialWorkflowTable.id == workflow_id)
                .one()
            )

            assignments = dict(row.role_assignments or {})
            assignments[role] = user_id
            row.role_assignments = assignments
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="editorial_workflow.role_assigned",
                aggregate_type="editorial_workflow",
                aggregate_id=workflow_id,
                actor=actor_id,
                detail=f"Role '{role}' assigned to user {user_id}",
                request_id=row.request_id,
                artifact_id=row.artifact_id,
            )
            session.commit()
            session.refresh(row)
            return EditorialWorkflowRecord.model_validate(row)


editorial_workflow_service = EditorialWorkflowService()
