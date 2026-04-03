"""Adapter registry service — manages adapter lifecycle and capability discovery.

Maintains an in-memory registry of adapter instances keyed by integration id,
backed by ``IntegrationTable`` for persistent metadata.  Adapters describe
their capabilities so that callers can discover what operations a given
integration supports.
"""

from __future__ import annotations

from app.db.models import IntegrationTable
from app.db.session import SessionLocal


class AdapterRegistryService:
    """In-memory adapter registry backed by IntegrationTable."""

    def __init__(self) -> None:
        # In-memory cache: integration_id -> adapter metadata dict.
        self._adapters: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_adapter(
        self,
        integration_id: str,
        adapter_type: str,
        capabilities: list[str],
    ) -> dict:
        """Register an adapter for an integration.

        Verifies that the integration exists in the database and then
        caches the adapter metadata in memory.

        Args:
            integration_id: The integration this adapter serves.
            adapter_type: Adapter implementation type (e.g.
                ``"http"``, ``"grpc"``, ``"sdk"``).
            capabilities: List of capability identifiers the adapter
                supports (e.g. ``["create_issue", "sync_status"]``).

        Returns:
            The adapter metadata dict.
        """
        with SessionLocal() as session:
            integration = (
                session.query(IntegrationTable)
                .filter(IntegrationTable.id == integration_id)
                .one()
            )

            adapter_entry = {
                "integration_id": integration.id,
                "integration_name": integration.name,
                "tenant_id": integration.tenant_id,
                "adapter_type": adapter_type,
                "capabilities": capabilities,
                "status": "active",
            }
            self._adapters[integration_id] = adapter_entry
            return adapter_entry

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_adapters(self, tenant_id: str | None = None) -> list[dict]:
        """Return all registered adapters, optionally filtered by tenant.

        If no adapters have been registered in memory, falls back to
        listing integrations from the database.
        """
        if self._adapters:
            adapters = list(self._adapters.values())
            if tenant_id:
                adapters = [a for a in adapters if a.get("tenant_id") == tenant_id]
            return adapters

        # Fallback: build entries from IntegrationTable.
        with SessionLocal() as session:
            query = session.query(IntegrationTable)
            if tenant_id:
                query = query.filter(IntegrationTable.tenant_id == tenant_id)
            rows = query.all()
            return [
                {
                    "integration_id": row.id,
                    "integration_name": row.name,
                    "tenant_id": row.tenant_id,
                    "adapter_type": row.type,
                    "capabilities": [],
                    "status": row.status,
                }
                for row in rows
            ]

    def get_adapter(self, integration_id: str) -> dict:
        """Retrieve a single adapter by integration id.

        Checks the in-memory cache first, then falls back to the
        database.

        Raises:
            KeyError: If no adapter or integration is found.
        """
        if integration_id in self._adapters:
            return self._adapters[integration_id]

        with SessionLocal() as session:
            row = (
                session.query(IntegrationTable)
                .filter(IntegrationTable.id == integration_id)
                .first()
            )
            if row is None:
                raise KeyError(
                    f"No adapter or integration found for '{integration_id}'"
                )
            return {
                "integration_id": row.id,
                "integration_name": row.name,
                "tenant_id": row.tenant_id,
                "adapter_type": row.type,
                "capabilities": [],
                "status": row.status,
            }


adapter_registry_service = AdapterRegistryService()
