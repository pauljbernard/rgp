"""Content projection service -- projects artifacts to distribution channels."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.models import ContentProjectionTable
from app.db.session import SessionLocal
from app.models.editorial import ContentProjectionRecord
from app.services.event_store_service import event_store_service


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
            row = ContentProjectionTable(
                id=proj_id,
                tenant_id=tenant_id,
                artifact_id=artifact_id,
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
                tenant_id=tenant_id,
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
            rows = (
                session.query(ContentProjectionTable)
                .filter(
                    ContentProjectionTable.artifact_id == artifact_id,
                    ContentProjectionTable.tenant_id == tenant_id,
                )
                .order_by(ContentProjectionTable.projected_at.desc())
                .all()
            )
            return [ContentProjectionRecord.model_validate(r) for r in rows]

    def get_projection_status(
        self, projection_id: str
    ) -> ContentProjectionRecord:
        with SessionLocal() as session:
            row = (
                session.query(ContentProjectionTable)
                .filter(ContentProjectionTable.id == projection_id)
                .one()
            )
            return ContentProjectionRecord.model_validate(row)


content_projection_service = ContentProjectionService()
