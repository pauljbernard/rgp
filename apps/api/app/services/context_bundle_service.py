"""Context bundle service — assembles governed context bundles for agent sessions.

Gathers request data, template semantics, workflow state, policy constraints,
relationships, and prior review decisions into a single governed bundle that
can be scoped and access-logged.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import (
    ContextAccessLogTable,
    ContextBundleTable,
    RequestRelationshipTable,
    RequestTable,
    ReviewQueueTable,
    RunTable,
    TemplateTable,
)
from app.db.session import SessionLocal
from app.models.context import (
    ContextAccessLogRecord,
    ContextBundleRecord,
)
from app.services.knowledge_service import knowledge_service


class ContextBundleService:
    """Assembles, scopes, and access-logs governed context bundles."""

    def _build_bundle_payload(self, request_id: str, tenant_id: str) -> tuple[dict, list[dict], str]:
        with SessionLocal() as session:
            request_row = (
                session.query(RequestTable)
                .filter(
                    RequestTable.id == request_id,
                    RequestTable.tenant_id == tenant_id,
                )
                .one()
            )

            template_data: dict = {}
            tpl = (
                session.query(TemplateTable)
                .filter(
                    TemplateTable.id == request_row.template_id,
                    TemplateTable.tenant_id == tenant_id,
                )
                .first()
            )
            if tpl:
                template_data = {
                    "template_id": tpl.id,
                    "version": tpl.version,
                    "name": tpl.name,
                    "schema": tpl.template_schema or {},
                }

            workflow_state: dict = {}
            if request_row.current_run_id:
                run = session.query(RunTable).filter(RunTable.id == request_row.current_run_id).first()
                if run:
                    workflow_state = {
                        "run_id": run.id,
                        "workflow": run.workflow,
                        "status": run.status,
                        "current_step": run.current_step,
                        "progress_percent": run.progress_percent,
                    }

            reviews = (
                session.query(ReviewQueueTable)
                .filter(ReviewQueueTable.request_id == request_id)
                .all()
            )
            prior_decisions = [
                {
                    "review_id": rv.id,
                    "scope": rv.review_scope,
                    "type": rv.type,
                    "blocking_status": rv.blocking_status,
                    "assigned_reviewer": rv.assigned_reviewer,
                }
                for rv in reviews
            ]

            rels = (
                session.query(RequestRelationshipTable)
                .filter(
                    (RequestRelationshipTable.source_request_id == request_id)
                    | (RequestRelationshipTable.target_request_id == request_id)
                )
                .all()
            )
            relationship_graph = [
                {
                    "source": rel.source_request_id,
                    "target": rel.target_request_id,
                    "type": rel.relationship_type,
                }
                for rel in rels
            ]

            knowledge_artifacts = knowledge_service.retrieve_for_context(
                request_id=request_id,
                tenant_id=tenant_id,
                max_items=5,
            )
            knowledge_context = [
                {
                    "artifact_id": artifact.id,
                    "name": artifact.name,
                    "description": artifact.description,
                    "content": artifact.content,
                    "content_type": artifact.content_type,
                    "version": artifact.version,
                    "status": artifact.status,
                    "tags": artifact.tags or [],
                    "updated_at": artifact.updated_at,
                }
                for artifact in knowledge_artifacts
            ]

            contents = {
                "request_data": {
                    "id": request_row.id,
                    "request_type": request_row.request_type,
                    "title": request_row.title,
                    "status": request_row.status,
                    "priority": request_row.priority,
                    "tags": request_row.tags or [],
                    "input_payload": request_row.input_payload or {},
                    "policy_context": request_row.policy_context or {},
                },
                "template_semantics": template_data,
                "workflow_state": workflow_state,
                "policy_constraints": [],
                "prior_decisions": prior_decisions,
                "relationship_graph": relationship_graph,
                "knowledge_context": knowledge_context,
            }
            provenance = [
                {"source": "request", "id": request_id},
                {"source": "template", "id": request_row.template_id},
                *[
                    {"source": "knowledge_artifact", "id": artifact.id}
                    for artifact in knowledge_artifacts
                ],
            ]
            return contents, provenance, request_row.template_id

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------

    def assemble_bundle(
        self,
        request_id: str,
        session_id: str | None,
        bundle_type: str,
        assembled_by: str,
        tenant_id: str,
    ) -> ContextBundleRecord:
        """Gather all governed context for a request and persist a bundle.

        The bundle contents include request data, template semantics, current
        workflow/run state, active policy constraints, related requests, and
        prior review decisions.
        """
        contents, provenance, _template_id = self._build_bundle_payload(request_id, tenant_id)
        with SessionLocal() as session:
            now = datetime.now(timezone.utc)
            bundle_id = f"cb_{uuid.uuid4().hex[:12]}"

            bundle_row = ContextBundleTable(
                id=bundle_id,
                tenant_id=tenant_id,
                request_id=request_id,
                session_id=session_id,
                version=1,
                bundle_type=bundle_type,
                contents=contents,
                policy_scope=None,
                assembled_by=assembled_by,
                assembled_at=now,
                provenance=provenance,
            )
            session.add(bundle_row)
            session.commit()
            session.refresh(bundle_row)
            return ContextBundleRecord.model_validate(bundle_row)

    def preview_bundle(
        self,
        request_id: str,
        session_id: str | None,
        bundle_type: str,
        assembled_by: str,
        tenant_id: str,
    ) -> ContextBundleRecord:
        contents, provenance, _template_id = self._build_bundle_payload(request_id, tenant_id)
        now = datetime.now(timezone.utc)
        return ContextBundleRecord(
            id=f"cb_preview_{uuid.uuid4().hex[:12]}",
            tenant_id=tenant_id,
            request_id=request_id,
            session_id=session_id,
            version=1,
            bundle_type=bundle_type,
            contents=contents,
            policy_scope=None,
            assembled_by=assembled_by,
            assembled_at=now,
            provenance=provenance,
        )

    # ------------------------------------------------------------------
    # Scoping
    # ------------------------------------------------------------------

    def scope_bundle(
        self, bundle_id: str, policy_scope: dict
    ) -> ContextBundleRecord:
        """Apply a policy scope to an existing bundle, restricting its contents."""
        with SessionLocal() as session:
            row = (
                session.query(ContextBundleTable)
                .filter(ContextBundleTable.id == bundle_id)
                .one()
            )
            row.policy_scope = policy_scope
            row.version = row.version + 1

            # Filter contents based on scope if scope specifies allowed keys.
            allowed_keys = policy_scope.get("allowed_content_keys")
            if allowed_keys and isinstance(row.contents, dict):
                row.contents = {
                    k: v for k, v in row.contents.items() if k in allowed_keys
                }

            session.commit()
            session.refresh(row)
            return ContextBundleRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Access logging
    # ------------------------------------------------------------------

    def record_access(
        self,
        bundle_id: str,
        accessor_type: str,
        accessor_id: str,
        resource: str,
        result: str,
        policy_basis: dict | None = None,
    ) -> ContextAccessLogRecord:
        """Record an access attempt against a context bundle."""
        now = datetime.now(timezone.utc)
        log_id = f"cal_{uuid.uuid4().hex[:12]}"
        row = ContextAccessLogTable(
            id=log_id,
            bundle_id=bundle_id,
            accessor_type=accessor_type,
            accessor_id=accessor_id,
            accessed_resource=resource,
            access_result=result,
            policy_basis=policy_basis,
            accessed_at=now,
        )
        with SessionLocal() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return ContextAccessLogRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_bundle(self, bundle_id: str) -> ContextBundleRecord:
        """Retrieve a context bundle by id."""
        with SessionLocal() as session:
            row = (
                session.query(ContextBundleTable)
                .filter(ContextBundleTable.id == bundle_id)
                .one()
            )
            return ContextBundleRecord.model_validate(row)


context_bundle_service = ContextBundleService()
