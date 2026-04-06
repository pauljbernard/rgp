"""Knowledge service -- manages knowledge artifacts, versioning, and reuse tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import or_

from app.db.models import KnowledgeArtifactTable, KnowledgeArtifactVersionTable
from app.db.session import SessionLocal
from app.models.common import PaginatedResponse
from app.models.knowledge import (
    CreateKnowledgeArtifactRequest,
    KnowledgeArtifactRecord,
    KnowledgeVersionRecord,
)
from app.services.event_store_service import event_store_service


class KnowledgeService:
    """Manages the full lifecycle of knowledge artifacts."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_artifact(
        self,
        payload: CreateKnowledgeArtifactRequest,
        actor_id: str,
        tenant_id: str,
    ) -> KnowledgeArtifactRecord:
        now = datetime.now(timezone.utc)
        artifact_id = f"ka_{uuid4().hex[:12]}"

        with SessionLocal() as session:
            row = KnowledgeArtifactTable(
                id=artifact_id,
                tenant_id=tenant_id,
                name=payload.name,
                description=payload.description,
                content=payload.content,
                content_type=payload.content_type,
                version=1,
                status="draft",
                policy_scope=payload.policy_scope,
                provenance=[],
                tags=payload.tags,
                created_by=actor_id,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.flush()

            # Store the initial version snapshot
            version_id = f"kav_{uuid4().hex[:12]}"
            version_row = KnowledgeArtifactVersionTable(
                id=version_id,
                artifact_id=artifact_id,
                version=1,
                content=payload.content,
                summary=payload.description,
                author=actor_id,
                created_at=now,
            )
            session.add(version_row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=tenant_id,
                event_type="knowledge_artifact.created",
                aggregate_type="knowledge_artifact",
                aggregate_id=artifact_id,
                actor=actor_id,
                detail=f"Knowledge artifact '{payload.name}' created",
                artifact_id=artifact_id,
            )
            session.commit()
            session.refresh(row)
            return KnowledgeArtifactRecord.model_validate(row)

    def list_artifacts(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 25,
        query: str | None = None,
        status: str | None = None,
    ) -> PaginatedResponse[KnowledgeArtifactRecord]:
        with SessionLocal() as session:
            q = session.query(KnowledgeArtifactTable).filter(KnowledgeArtifactTable.tenant_id == tenant_id)
            if status:
                q = q.filter(KnowledgeArtifactTable.status == status)
            if query:
                like_pattern = f"%{query}%"
                q = q.filter(
                    or_(
                        KnowledgeArtifactTable.name.ilike(like_pattern),
                        KnowledgeArtifactTable.description.ilike(like_pattern),
                    )
                )
            rows = q.order_by(KnowledgeArtifactTable.updated_at.desc()).all()
        records = [KnowledgeArtifactRecord.model_validate(r) for r in rows]
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedResponse.create(items=records[start:end], page=page, page_size=page_size, total_count=len(records))

    def get_artifact(self, artifact_id: str, tenant_id: str) -> KnowledgeArtifactRecord:
        with SessionLocal() as session:
            row = (
                session.query(KnowledgeArtifactTable)
                .filter(
                    KnowledgeArtifactTable.id == artifact_id,
                    KnowledgeArtifactTable.tenant_id == tenant_id,
                )
                .one()
            )
            return KnowledgeArtifactRecord.model_validate(row)

    def list_versions(self, artifact_id: str, tenant_id: str) -> list[KnowledgeVersionRecord]:
        with SessionLocal() as session:
            artifact = (
                session.query(KnowledgeArtifactTable)
                .filter(
                    KnowledgeArtifactTable.id == artifact_id,
                    KnowledgeArtifactTable.tenant_id == tenant_id,
                )
                .one()
            )
            rows = (
                session.query(KnowledgeArtifactVersionTable)
                .filter(KnowledgeArtifactVersionTable.artifact_id == artifact.id)
                .order_by(KnowledgeArtifactVersionTable.version.desc())
                .all()
            )
            return [KnowledgeVersionRecord.model_validate(row) for row in rows]

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def publish_artifact(
        self, artifact_id: str, actor_id: str, tenant_id: str
    ) -> KnowledgeArtifactRecord:
        """Publish the artifact: set status=published and bump the version."""
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(KnowledgeArtifactTable)
                .filter(
                    KnowledgeArtifactTable.id == artifact_id,
                    KnowledgeArtifactTable.tenant_id == tenant_id,
                )
                .one()
            )
            row.status = "published"
            row.version = row.version + 1
            row.updated_at = now
            session.flush()

            # Snapshot the new version
            version_id = f"kav_{uuid4().hex[:12]}"
            version_row = KnowledgeArtifactVersionTable(
                id=version_id,
                artifact_id=artifact_id,
                version=row.version,
                content=row.content,
                summary=row.description,
                author=actor_id,
                created_at=now,
            )
            session.add(version_row)
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="knowledge_artifact.published",
                aggregate_type="knowledge_artifact",
                aggregate_id=artifact_id,
                actor=actor_id,
                detail=f"Knowledge artifact '{row.name}' published as v{row.version}",
                artifact_id=artifact_id,
            )
            session.commit()
            session.refresh(row)
            return KnowledgeArtifactRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_artifacts(
        self,
        query: str,
        tenant_id: str,
        tags: list[str] | None = None,
    ) -> list[KnowledgeArtifactRecord]:
        """Search knowledge artifacts by name, description, or tags."""
        like_pattern = f"%{query}%"

        with SessionLocal() as session:
            q = (
                session.query(KnowledgeArtifactTable)
                .filter(
                    KnowledgeArtifactTable.tenant_id == tenant_id,
                    or_(
                        KnowledgeArtifactTable.name.ilike(like_pattern),
                        KnowledgeArtifactTable.description.ilike(like_pattern),
                    ),
                )
                .order_by(KnowledgeArtifactTable.updated_at.desc())
            )
            rows = q.all()

            results = [KnowledgeArtifactRecord.model_validate(r) for r in rows]

            # Client-side tag filtering (JSON column)
            if tags:
                tag_set = set(tags)
                results = [
                    r for r in results if tag_set.intersection(set(r.tags or []))
                ]

            return results

    # ------------------------------------------------------------------
    # Context retrieval
    # ------------------------------------------------------------------

    def retrieve_for_context(
        self,
        request_id: str,
        tenant_id: str,
        max_items: int = 10,
    ) -> list[KnowledgeArtifactRecord]:
        """Retrieve published knowledge artifacts relevant to a context bundle.

        Returns the most recently updated published artifacts for the
        tenant, up to ``max_items``.  A production implementation would
        incorporate semantic similarity against the request context.
        """
        with SessionLocal() as session:
            rows = (
                session.query(KnowledgeArtifactTable)
                .filter(
                    KnowledgeArtifactTable.tenant_id == tenant_id,
                    KnowledgeArtifactTable.status == "published",
                )
                .order_by(KnowledgeArtifactTable.updated_at.desc())
                .limit(max_items)
                .all()
            )
            return [KnowledgeArtifactRecord.model_validate(r) for r in rows]

    # ------------------------------------------------------------------
    # Reuse tracking
    # ------------------------------------------------------------------

    def track_reuse(
        self, artifact_id: str, request_id: str, actor_id: str
    ) -> None:
        """Record that the artifact was reused in a request's context."""
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(KnowledgeArtifactTable)
                .filter(KnowledgeArtifactTable.id == artifact_id)
                .one()
            )

            provenance = list(row.provenance or [])
            provenance.append(
                {
                    "request_id": request_id,
                    "actor_id": actor_id,
                    "reused_at": now.isoformat(),
                }
            )
            row.provenance = provenance
            row.updated_at = now
            session.flush()

            event_store_service.append(
                session,
                tenant_id=row.tenant_id,
                event_type="knowledge_artifact.reused",
                aggregate_type="knowledge_artifact",
                aggregate_id=artifact_id,
                actor=actor_id,
                detail=f"Artifact reused in request {request_id}",
                artifact_id=artifact_id,
                request_id=request_id,
            )
            session.commit()


knowledge_service = KnowledgeService()
