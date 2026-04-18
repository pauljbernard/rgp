"""Workspace service -- manages workspaces tied to governance requests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import WorkspaceTable
from app.db.session import SessionLocal
from app.models.workspace import CreateWorkspaceRequest, WorkspaceRecord
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state


class WorkspaceService:
    """Lifecycle management for request workspaces."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_workspace(
        self, payload: CreateWorkspaceRequest, actor_id: str, tenant_id: str
    ) -> WorkspaceRecord:
        now = datetime.now(timezone.utc)
        workspace_id = f"ws_{uuid4().hex[:12]}"
        request = get_request_state(payload.request_id, tenant_id)
        if request is None:
            raise StopIteration(payload.request_id)

        with SessionLocal() as session:
            row = WorkspaceTable(
                id=workspace_id,
                tenant_id=request.tenant_id,
                request_id=payload.request_id,
                name=payload.name,
                status="created",
                owner_id=payload.owner_id,
                source_ref=payload.source_ref,
                target_ref=payload.target_ref,
                protected_targets=payload.protected_targets,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=request.tenant_id,
                event_type="workspace.created",
                aggregate_type="workspace",
                aggregate_id=workspace_id,
                actor=actor_id,
                detail=f"Workspace '{payload.name}' created for request {payload.request_id}",
                request_id=payload.request_id,
            )
            session.commit()
            session.refresh(row)
            return WorkspaceRecord.model_validate(row)

    def get_workspace(self, workspace_id: str, tenant_id: str | None = None) -> WorkspaceRecord:
        with SessionLocal() as session:
            row = self._get_workspace_row(session, workspace_id, tenant_id)
            return WorkspaceRecord.model_validate(row)

    def list_workspaces(
        self, request_id: str, tenant_id: str
    ) -> list[WorkspaceRecord]:
        if get_request_state(request_id, tenant_id) is None:
            raise StopIteration(request_id)
        with SessionLocal() as session:
            rows = (
                session.query(WorkspaceTable)
                .filter(
                    WorkspaceTable.request_id == request_id,
                    WorkspaceTable.tenant_id == tenant_id,
                )
                .order_by(WorkspaceTable.created_at.desc())
                .all()
            )
            return [WorkspaceRecord.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    def merge_workspace(
        self, workspace_id: str, actor_id: str, tenant_id: str | None = None
    ) -> WorkspaceRecord:
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = self._get_workspace_row(session, workspace_id, tenant_id)
            row.status = "merged"
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="workspace.merged",
                aggregate_type="workspace",
                aggregate_id=workspace_id,
                actor=actor_id,
                detail=f"Workspace '{row.name}' merged",
                request_id=row.request_id,
            )
            session.commit()
            session.refresh(row)
            return WorkspaceRecord.model_validate(row)

    def abandon_workspace(
        self, workspace_id: str, actor_id: str, tenant_id: str | None = None
    ) -> WorkspaceRecord:
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = self._get_workspace_row(session, workspace_id, tenant_id)
            row.status = "abandoned"
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="workspace.abandoned",
                aggregate_type="workspace",
                aggregate_id=workspace_id,
                actor=actor_id,
                detail=f"Workspace '{row.name}' abandoned",
                request_id=row.request_id,
            )
            session.commit()
            session.refresh(row)
            return WorkspaceRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Protection guard
    # ------------------------------------------------------------------

    def assert_protected_target(
        self, workspace_id: str, target: str, tenant_id: str | None = None
    ) -> None:
        """Raise ValueError if *target* is on the workspace's protected list."""
        with SessionLocal() as session:
            row = self._get_workspace_row(session, workspace_id, tenant_id)
            protected = row.protected_targets or []
            if target in protected:
                raise ValueError(
                    f"Target '{target}' is protected in workspace {workspace_id}"
                )

    @staticmethod
    def _get_workspace_row(session, workspace_id: str, tenant_id: str | None = None) -> WorkspaceTable:
        row = (
            session.query(WorkspaceTable)
            .filter(WorkspaceTable.id == workspace_id)
            .one()
        )
        if tenant_id is None:
            return row
        request = get_request_state(row.request_id, tenant_id)
        if request is None or row.tenant_id != request.tenant_id:
            raise StopIteration(workspace_id)
        return row


workspace_service = WorkspaceService()
