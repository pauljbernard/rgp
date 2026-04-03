"""Projection service — projects RGP entities into external systems.

Manages bidirectional projection mappings between internal RGP entities
(requests, artifacts, etc.) and their counterparts in external systems
(Jira, GitHub, ServiceNow, etc.).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import ProjectionMappingTable, IntegrationTable
from app.db.session import SessionLocal
from app.models.federation import ProjectionMappingRecord


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
                external_ref=None,
                external_state=None,
                projection_status="pending",
                last_projected_at=now,
                last_synced_at=None,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return ProjectionMappingRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def sync_external_state(
        self, projection_id: str
    ) -> ProjectionMappingRecord:
        """Refresh the projection mapping with latest external state.

        In a production implementation this would call the adapter for
        the external system.  Here we update the sync timestamp and mark
        the projection as ``synced``.
        """
        now = datetime.now(timezone.utc)

        with SessionLocal() as session:
            row = (
                session.query(ProjectionMappingTable)
                .filter(ProjectionMappingTable.id == projection_id)
                .one()
            )
            row.last_synced_at = now
            row.projection_status = "synced"
            session.commit()
            session.refresh(row)
            return ProjectionMappingRecord.model_validate(row)

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, projection_id: str) -> list[dict]:
        """Detect conflicts between internal and external state.

        Returns a list of conflict dicts, each describing a field-level
        divergence.  If the external state has not been synced yet an
        empty list is returned.
        """
        with SessionLocal() as session:
            row = (
                session.query(ProjectionMappingTable)
                .filter(ProjectionMappingTable.id == projection_id)
                .one()
            )

            if row.external_state is None:
                return []

            conflicts: list[dict] = []
            external = row.external_state or {}

            # Compare external status to projection status as a baseline
            # conflict signal.
            ext_status = external.get("status")
            if ext_status and ext_status != row.projection_status:
                conflicts.append(
                    {
                        "field": "status",
                        "internal": row.projection_status,
                        "external": ext_status,
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
            rows = query.all()
            return [ProjectionMappingRecord.model_validate(r) for r in rows]


projection_service = ProjectionService()
