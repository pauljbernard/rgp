"""Reconciliation service — detects and resolves conflicts between RGP and external state.

Works with ``ProjectionMappingTable`` and ``ReconciliationLogTable`` to
detect divergences and record resolution actions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import desc

from app.db.models import ProjectionMappingTable, ReconciliationLogTable
from app.db.session import SessionLocal
from app.models.federation import ReconciliationLogRecord
from app.services.projection_adapter_service import projection_adapter_service
from app.services.projection_service import projection_service


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
                action = self._determine_action(proj.id, proj)
                if action == "conflict":
                    proj.projection_status = "conflict"
                elif action == "synced":
                    proj.projection_status = "synced"
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

    def list_logs(
        self,
        integration_id: str,
        tenant_id: str,
    ) -> list[ReconciliationLogRecord]:
        with SessionLocal() as session:
            rows = (
                session.query(ReconciliationLogTable)
                .join(
                    ProjectionMappingTable,
                    ProjectionMappingTable.id == ReconciliationLogTable.projection_id,
                )
                .filter(
                    ProjectionMappingTable.integration_id == integration_id,
                    ProjectionMappingTable.tenant_id == tenant_id,
                )
                .order_by(desc(ReconciliationLogTable.created_at))
                .limit(50)
                .all()
            )
            return [ReconciliationLogRecord.model_validate(row) for row in rows]

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
            canonical_state = projection_service._canonical_snapshot(session, proj)
            adapter_type = (proj.external_state or {}).get("adapter_type")
            supported_actions = self._supported_actions(adapter_type)
            if action not in supported_actions:
                raise ValueError(f"Action {action} is not supported for adapter {adapter_type or 'unknown'}")
            adapter = projection_adapter_service.resolve_adapter_by_type(adapter_type)
            proj.projection_status = "reconciled"
            proj.last_synced_at = now
            proj.external_state = adapter.apply_resolution(action, proj.external_state or {}, canonical_state)
            if action == "retry_sync":
                proj.projection_status = "pending"

            log_row = ReconciliationLogTable(
                id=log_id,
                projection_id=projection_id,
                action=action,
                detail=self._resolution_detail(action, resolved_by, adapter_type),
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
    def _determine_action(projection_id: str, proj: ProjectionMappingTable) -> str:
        """Determine the reconciliation action for a projection."""
        if proj.external_state is None:
            return "missing_external_state"
        if projection_service.detect_conflicts(projection_id):
            return "conflict"
        return "synced"

    @staticmethod
    def _describe_action(proj: ProjectionMappingTable, action: str) -> str:
        """Build a human-readable description of the reconciliation action."""
        if action == "missing_external_state":
            return f"Projection {proj.id} has no external state yet"
        if action == "conflict":
            ext_status = (proj.external_state or {}).get("status", "unknown")
            with SessionLocal() as session:
                internal_status = projection_service._canonical_snapshot(session, proj).get("status", "unknown")
            return (
                f"Projection {proj.id} conflict: internal='{internal_status}' "
                f"vs external='{ext_status}'"
            )
        return f"Projection {proj.id} is in sync"

    @staticmethod
    def _supported_actions(adapter_type: str | None) -> list[str]:
        return projection_service._supported_resolution_actions(adapter_type)

    @staticmethod
    def _resolution_detail(action: str, resolved_by: str, adapter_type: str | None) -> str:
        if action == "retry_sync":
            return f"Resolved by {resolved_by}: retry substrate synchronization for {adapter_type or 'projection'}"
        if action == "reprovision":
            return f"Resolved by {resolved_by}: reprovision governed identity state into {adapter_type or 'projection'}"
        if action == "resume_session":
            return f"Resolved by {resolved_by}: resume governed agent session on {adapter_type or 'projection'}"
        return f"Resolved by {resolved_by}: {action}"


reconciliation_service = ReconciliationService()
