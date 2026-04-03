"""Reconciliation service — detects and resolves conflicts between RGP and external state.

Works with ``ProjectionMappingTable`` and ``ReconciliationLogTable`` to
detect divergences and record resolution actions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.db.models import ProjectionMappingTable, ReconciliationLogTable
from app.db.session import SessionLocal
from app.models.federation import ReconciliationLogRecord


class ReconciliationService:
    """Detects and resolves conflicts between internal and external state."""

    # ------------------------------------------------------------------
    # Reconciliation
    # ------------------------------------------------------------------

    def reconcile_integration(
        self,
        integration_id: str,
        tenant_id: str,
    ) -> list[ReconciliationLogRecord]:
        """Reconcile all projections for an integration.

        Iterates over every projection mapping for the given integration
        and tenant, checks for divergence between internal and external
        state, and creates a ``ReconciliationLogTable`` entry for each
        finding.

        Returns the list of newly created reconciliation log records.
        """
        now = datetime.now(timezone.utc)
        results: list[ReconciliationLogRecord] = []

        with SessionLocal() as session:
            projections = (
                session.query(ProjectionMappingTable)
                .filter(
                    ProjectionMappingTable.integration_id == integration_id,
                    ProjectionMappingTable.tenant_id == tenant_id,
                )
                .all()
            )

            for proj in projections:
                action = self._determine_action(proj)
                log_id = f"rl_{uuid.uuid4().hex[:12]}"
                log_row = ReconciliationLogTable(
                    id=log_id,
                    projection_id=proj.id,
                    action=action,
                    detail=self._describe_action(proj, action),
                    resolved_by=None,
                    created_at=now,
                )
                session.add(log_row)
                results.append(ReconciliationLogRecord.model_validate(log_row))

            session.commit()

        return results

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def apply_resolution(
        self,
        projection_id: str,
        action: str,
        resolved_by: str,
    ) -> ReconciliationLogRecord:
        """Record a resolution action for a projection conflict.

        Args:
            projection_id: The projection mapping that was reconciled.
            action: Resolution action taken (e.g. ``"accept_internal"``,
                ``"accept_external"``, ``"merge"``).
            resolved_by: Identifier of the actor who resolved the conflict.
        """
        now = datetime.now(timezone.utc)
        log_id = f"rl_{uuid.uuid4().hex[:12]}"

        with SessionLocal() as session:
            # Mark the projection as reconciled.
            proj = (
                session.query(ProjectionMappingTable)
                .filter(ProjectionMappingTable.id == projection_id)
                .one()
            )
            proj.projection_status = "reconciled"
            proj.last_synced_at = now

            log_row = ReconciliationLogTable(
                id=log_id,
                projection_id=projection_id,
                action=action,
                detail=f"Resolved by {resolved_by}: {action}",
                resolved_by=resolved_by,
                created_at=now,
            )
            session.add(log_row)
            session.commit()
            session.refresh(log_row)
            return ReconciliationLogRecord.model_validate(log_row)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_action(proj: ProjectionMappingTable) -> str:
        """Determine the reconciliation action for a projection."""
        if proj.external_state is None:
            return "created"
        ext_status = (proj.external_state or {}).get("status")
        if ext_status and ext_status != proj.projection_status:
            return "conflict"
        return "updated"

    @staticmethod
    def _describe_action(proj: ProjectionMappingTable, action: str) -> str:
        """Build a human-readable description of the reconciliation action."""
        if action == "created":
            return f"Projection {proj.id} has no external state yet"
        if action == "conflict":
            ext_status = (proj.external_state or {}).get("status", "unknown")
            return (
                f"Projection {proj.id} conflict: internal='{proj.projection_status}' "
                f"vs external='{ext_status}'"
            )
        return f"Projection {proj.id} is in sync"


reconciliation_service = ReconciliationService()
