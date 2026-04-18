"""Projection service — projects RGP entities into external systems.

Manages bidirectional projection mappings between internal RGP entities
(requests, artifacts, etc.) and their counterparts in external systems
(Jira, GitHub, ServiceNow, etc.).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import AgentSessionTable, ArtifactTable, IntegrationTable, ProjectionMappingTable, ReconciliationLogTable
from app.db.session import SessionLocal
from app.models.federation import ProjectionMappingRecord
from app.services.projection_adapter_service import projection_adapter_service
from app.services.request_state_bridge import get_request_state


class ProjectionService:
    """Projects entities outward and syncs external state back."""

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    def project_entity(
        self,
        entity_type: str,
        entity_id: str,
        integration_id: str,
        tenant_id: str,
    ) -> ProjectionMappingRecord:
        """Create a projection mapping for an entity to an external system.

        Looks up the integration to determine the external system name,
        then persists a ``ProjectionMappingTable`` row with status
        ``pending``.
        """
        now = datetime.now(timezone.utc)
        projection_id = f"pm_{uuid.uuid4().hex[:12]}"

        with SessionLocal() as session:
            canonical_snapshot = self._canonical_snapshot_from_session(session, entity_type, entity_id, tenant_id)
            if not canonical_snapshot:
                raise StopIteration(entity_id)
            integration = (
                session.query(IntegrationTable)
                .filter(
                    IntegrationTable.id == integration_id,
                    IntegrationTable.tenant_id == tenant_id,
                )
                .one()
            )

            row = ProjectionMappingTable(
                id=projection_id,
                tenant_id=tenant_id,
                integration_id=integration_id,
                entity_type=entity_type,
                entity_id=entity_id,
                external_system=integration.name,
                external_ref=f"{integration_id}:{entity_type}:{entity_id}",
                external_state={},
                projection_status="pending",
                last_projected_at=now,
                last_synced_at=None,
            )
            adapter = projection_adapter_service.resolve_adapter(integration)
            row.external_state = {
                **adapter.project_entity(entity_type, entity_id, canonical_snapshot),
                "projected_entity_type": entity_type,
                "projected_entity_id": entity_id,
            }
            session.add(row)
            session.add(
                ReconciliationLogTable(
                    id=f"rl_{uuid.uuid4().hex[:12]}",
                    projection_id=projection_id,
                    action="projected",
                    detail=f"Projected {entity_type} {entity_id} to {integration.name}",
                    resolved_by="system",
                    created_at=now,
                )
            )
            session.commit()
            session.refresh(row)
            record = self._record_from_row(row)
            record.conflicts = self.detect_conflicts(record.id, record.tenant_id)
            return record

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def sync_external_state(
        self, projection_id: str, tenant_id: str | None = None
    ) -> ProjectionMappingRecord:
        """Refresh the projection mapping with latest external state.

        In a production implementation this would call the adapter for
        the external system.  Here we update the sync timestamp and mark
        the projection as ``synced``.
        """
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = self._get_projection_row(session, projection_id, tenant_id)
            canonical_snapshot = self._canonical_snapshot(session, row)
            integration = (
                session.query(IntegrationTable)
                .filter(
                    IntegrationTable.id == row.integration_id,
                    IntegrationTable.tenant_id == row.tenant_id,
                )
                .one()
            )
            adapter = projection_adapter_service.resolve_adapter(integration)
            snapshot = adapter.query_external_state(
                row.external_ref or f"{row.integration_id}:{row.entity_type}:{row.entity_id}",
                row.external_state or {},
                canonical_snapshot,
            )
            row.last_synced_at = now
            row.external_state = {
                **(row.external_state or {}),
                **snapshot.external_state,
                "last_synced_at": now.isoformat().replace("+00:00", "Z"),
            }
            row.projection_status = "synced"
            session.add(
                ReconciliationLogTable(
                    id=f"rl_{uuid.uuid4().hex[:12]}",
                    projection_id=projection_id,
                    action="synced",
                    detail=f"Synchronized external state for {row.entity_type} {row.entity_id}",
                    resolved_by="system",
                    created_at=now,
                )
            )
            session.commit()
            session.refresh(row)
            record = self._record_from_row(row)
            record.conflicts = self.detect_conflicts(record.id, record.tenant_id)
            return record

    def update_external_state(
        self,
        projection_id: str,
        external_status: str | None,
        external_title: str | None,
        external_ref: str | None,
        tenant_id: str | None = None,
    ) -> ProjectionMappingRecord:
        now = datetime.now(timezone.utc)
        with SessionLocal() as session:
            row = self._get_projection_row(session, projection_id, tenant_id)
            row.external_state = {
                **(row.external_state or {}),
                **({"status": external_status} if external_status else {}),
                **({"title": external_title} if external_title else {}),
            }
            shadow = dict((row.external_state or {}).get("_adapter_shadow") or {})
            if external_status:
                shadow["status"] = external_status
            if external_title:
                shadow["title"] = external_title
            if shadow:
                row.external_state["_adapter_shadow"] = shadow
            if external_ref:
                row.external_ref = external_ref
            session.add(
                ReconciliationLogTable(
                    id=f"rl_{uuid.uuid4().hex[:12]}",
                    projection_id=projection_id,
                    action="observed_external_state",
                    detail=f"Observed external state for {row.entity_type} {row.entity_id}",
                    resolved_by="system",
                    created_at=now,
                )
            )
            session.commit()
            session.refresh(row)
            record = self._record_from_row(row)
            record.conflicts = self.detect_conflicts(record.id, record.tenant_id)
            return record

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, projection_id: str, tenant_id: str | None = None) -> list[dict]:
        """Detect conflicts between internal and external state.

        Returns a list of conflict dicts, each describing a field-level
        divergence.  If the external state has not been synced yet an
        empty list is returned.
        """
        with SessionLocal() as session:
            row = self._get_projection_row(session, projection_id, tenant_id)

            if row.external_state is None:
                return []

            conflicts: list[dict] = []
            external = row.external_state or {}
            if external.get("resolution_basis") == "accept_external":
                return conflicts

            canonical_state = self._canonical_snapshot(session, row)
            ext_status = external.get("status")
            canonical_status = canonical_state.get("status")
            if ext_status and canonical_status and ext_status != canonical_status:
                conflicts.append(
                    {
                        "field": "status",
                        "internal": canonical_status,
                        "external": ext_status,
                        "projection_id": projection_id,
                    }
                )
            ext_title = external.get("title")
            canonical_title = canonical_state.get("title")
            if ext_title and canonical_title and ext_title != canonical_title:
                conflicts.append(
                    {
                        "field": "title",
                        "internal": canonical_title,
                        "external": ext_title,
                        "projection_id": projection_id,
                    }
                )

            return conflicts

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_projections(
        self,
        tenant_id: str,
        integration_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[ProjectionMappingRecord]:
        """List projection mappings, optionally filtered by integration."""
        with SessionLocal() as session:
            query = session.query(ProjectionMappingTable).filter(
                ProjectionMappingTable.tenant_id == tenant_id,
            )
            if integration_id:
                query = query.filter(
                    ProjectionMappingTable.integration_id == integration_id
                )
            if entity_type:
                query = query.filter(ProjectionMappingTable.entity_type == entity_type)
            if entity_id:
                query = query.filter(ProjectionMappingTable.entity_id == entity_id)
            rows = query.all()
            records: list[ProjectionMappingRecord] = []
            for row in rows:
                record = self._record_from_row(row)
                record.conflicts = self.detect_conflicts(record.id, record.tenant_id)
                records.append(record)
            return records

    @staticmethod
    def _canonical_snapshot_from_session(session, entity_type: str, entity_id: str, tenant_id: str) -> dict:
        if entity_type == "request":
            request = get_request_state(entity_id, tenant_id)
            if request is not None:
                return {
                    "id": request.id,
                    "entity_type": entity_type,
                    "status": request.status.value if hasattr(request.status, "value") else str(request.status),
                    "title": request.title,
                }
        if entity_type == "artifact":
            artifact_row = (
                session.query(ArtifactTable)
                .filter(ArtifactTable.id == entity_id)
                .first()
            )
            if artifact_row is not None and get_request_state(artifact_row.request_id, tenant_id) is not None:
                return {
                    "id": artifact_row.id,
                    "entity_type": entity_type,
                    "status": artifact_row.status,
                    "title": artifact_row.name,
                }
        if entity_type == "agent_session":
            session_row = session.query(AgentSessionTable).filter(AgentSessionTable.id == entity_id, AgentSessionTable.tenant_id == tenant_id).first()
            if session_row is not None:
                return {
                    "id": session_row.id,
                    "entity_type": entity_type,
                    "status": session_row.status,
                    "title": session_row.agent_label,
                    "session_status": session_row.status,
                    "environment_ref": f"environment:{session_row.external_session_ref}" if session_row.external_session_ref else None,
                    "thread_ref": f"thread:{session_row.id}",
                    "turn_ref": f"turn:{session_row.id}:latest",
                    "operation_count": 0,
                    "artifact_count": 0,
                    "governed_entities": [
                        {"entity_type": name, "summary": f"Projected {name} summary"}
                        for name in ["environment", "thread", "turn", "operation", "artifact"]
                    ],
                }
        return {}

    @staticmethod
    def _canonical_snapshot(session, row: ProjectionMappingTable) -> dict:
        return ProjectionService._canonical_snapshot_from_session(session, row.entity_type, row.entity_id, row.tenant_id)

    @staticmethod
    def _record_from_row(row: ProjectionMappingTable) -> ProjectionMappingRecord:
        external_state = row.external_state or {}
        adapter_type = external_state.get("adapter_type")
        adapter_capabilities = external_state.get("adapter_capabilities") or []
        sync_source = external_state.get("sync_source")

        if not adapter_type or not adapter_capabilities or not sync_source:
            with SessionLocal() as session:
                integration = (
                    session.query(IntegrationTable)
                    .filter(
                        IntegrationTable.id == row.integration_id,
                        IntegrationTable.tenant_id == row.tenant_id,
                    )
                    .first()
                )
            if integration is not None:
                adapter = projection_adapter_service.resolve_adapter(integration)
                adapter_type = adapter_type or getattr(adapter, "adapter_type", None)
                adapter_capabilities = adapter_capabilities or list(getattr(adapter, "capabilities", []))
                sync_source = sync_source or (f"adapter:{adapter_type}" if adapter_type else None)

        payload = {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "integration_id": row.integration_id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "external_system": row.external_system,
            "external_ref": row.external_ref,
            "external_state": external_state,
            "projection_status": row.projection_status,
            "last_projected_at": row.last_projected_at,
            "last_synced_at": row.last_synced_at,
            "adapter_type": adapter_type,
            "adapter_capabilities": adapter_capabilities,
            "sync_source": sync_source,
            "supported_resolution_actions": ProjectionService._supported_resolution_actions(adapter_type),
            "resolution_guidance": ProjectionService._resolution_guidance(adapter_type),
        }
        return ProjectionMappingRecord.model_validate(payload)

    @staticmethod
    def _supported_resolution_actions(adapter_type: str | None) -> list[str]:
        if adapter_type == "repository_projection":
            return ["accept_internal", "accept_external", "merge"]
        if adapter_type == "runtime_projection":
            return ["accept_internal", "accept_external", "retry_sync"]
        if adapter_type == "identity_projection":
            return ["accept_internal", "accept_external", "reprovision"]
        if adapter_type in {"agent_projection", "openai_projection", "anthropic_projection", "microsoft_projection"}:
            return ["accept_internal", "accept_external", "resume_session"]
        if adapter_type == "sbcl_agent_projection":
            return ["accept_internal", "accept_external", "resume_runtime", "approve_runtime_checkpoint", "import_runtime_artifact"]
        return ["accept_internal", "accept_external", "merge"]

    @staticmethod
    def _resolution_guidance(adapter_type: str | None) -> str | None:
        if adapter_type == "repository_projection":
            return "Use merge when canonical and external repository state should both be preserved."
        if adapter_type == "runtime_projection":
            return "Use retry_sync when execution state should be refreshed from the runtime substrate."
        if adapter_type == "identity_projection":
            return "Use reprovision when governance-approved identity state must be reapplied to the external identity system."
        if adapter_type in {"agent_projection", "openai_projection", "anthropic_projection", "microsoft_projection"}:
            return "Use resume_session when the external agent session should be resumed under governed state."
        if adapter_type == "sbcl_agent_projection":
            return "Use resume_runtime or approve_runtime_checkpoint when governed sbcl-agent work should continue, and import_runtime_artifact when a runtime-produced artifact should become a first-class RGP artifact."
        return "Select the resolution action that best preserves canonical governance intent."

    @staticmethod
    def _get_projection_row(session, projection_id: str, tenant_id: str | None = None) -> ProjectionMappingTable:
        row = (
            session.query(ProjectionMappingTable)
            .filter(ProjectionMappingTable.id == projection_id)
            .one()
        )
        if tenant_id is None:
            return row
        if row.entity_type == "request":
            request = get_request_state(row.entity_id, tenant_id)
            if request is None or row.tenant_id != request.tenant_id:
                raise StopIteration(projection_id)
            return row
        if row.entity_type == "artifact":
            artifact_row = (
                session.query(ArtifactTable)
                .filter(ArtifactTable.id == row.entity_id)
                .first()
            )
            if artifact_row is None:
                raise StopIteration(projection_id)
            request = get_request_state(artifact_row.request_id, tenant_id)
            if request is None or row.tenant_id != request.tenant_id:
                raise StopIteration(projection_id)
            return row
        if row.tenant_id != tenant_id:
            raise StopIteration(projection_id)
        return row


projection_service = ProjectionService()
