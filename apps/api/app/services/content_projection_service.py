"""Content projection service -- projects artifacts to distribution channels."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import ArtifactTable, ContentProjectionTable
from app.db.session import SessionLocal
from app.models.editorial import ContentProjectionRecord
from app.services.event_store_service import event_store_service
from app.services.request_state_bridge import get_request_state


class ContentProjectionService:
    """Projects knowledge artifacts to external distribution channels."""

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def project_to_channel(
        self,
        artifact_id: str,
        channel: str,
        config: dict | None,
        actor_id: str,
        tenant_id: str,
    ) -> ContentProjectionRecord:
        now = datetime.now(timezone.utc)
        proj_id = f"cp_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            artifact_row, resolved_tenant_id = self._resolve_artifact(session, artifact_id, tenant_id)
            row = ContentProjectionTable(
                id=proj_id,
                tenant_id=resolved_tenant_id,
                artifact_id=artifact_row.id,
                channel=channel,
                projection_status="pending",
                projected_at=now,
                external_ref=None,
                config=config,
            )
            session.add(row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=resolved_tenant_id,
                event_type="content_projection.created",
                aggregate_type="content_projection",
                aggregate_id=proj_id,
                actor=actor_id,
                detail=f"Artifact {artifact_id} projected to channel '{channel}'",
                artifact_id=artifact_id,
            )
            session.commit()
            session.refresh(row)
            return ContentProjectionRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_projections(
        self, artifact_id: str, tenant_id: str
    ) -> list[ContentProjectionRecord]:
        with SessionLocal() as session:
            artifact_row, resolved_tenant_id = self._resolve_artifact(session, artifact_id, tenant_id)
            rows = (
                session.query(ContentProjectionTable)
                .filter(
                    ContentProjectionTable.artifact_id == artifact_row.id,
                    ContentProjectionTable.tenant_id == resolved_tenant_id,
                )
                .order_by(ContentProjectionTable.projected_at.desc())
                .all()
            )
            return [ContentProjectionRecord.model_validate(r) for r in rows]

    def get_projection_status(
        self, projection_id: str, tenant_id: str | None = None
    ) -> ContentProjectionRecord:
        with SessionLocal() as session:
            row = (
                session.query(ContentProjectionTable)
                .filter(ContentProjectionTable.id == projection_id)
                .one()
            )
            if tenant_id is not None:
                _artifact_row, resolved_tenant_id = self._resolve_artifact(session, row.artifact_id, tenant_id)
                if row.tenant_id != resolved_tenant_id:
                    raise StopIteration(projection_id)
            return ContentProjectionRecord.model_validate(row)

    @staticmethod
    def _resolve_artifact(session, artifact_id: str, tenant_id: str | None) -> tuple[ArtifactTable, str]:
        artifact_row = (
            session.query(ArtifactTable)
            .filter(ArtifactTable.id == artifact_id)
            .one()
        )
        request = get_request_state(artifact_row.request_id, tenant_id)
        if request is None:
            raise StopIteration(artifact_id)
        return artifact_row, request.tenant_id


content_projection_service = ContentProjectionService()
