"""HTTP runtime adapter wrapping the existing RuntimeDispatchService."""

from __future__ import annotations

from types import SimpleNamespace

from app.domain.substrate.canonical import (
    CanonicalRunDispatch,
    DispatchResult,
    RunStatusResult,
)
from app.services.runtime_dispatch_service import runtime_dispatch_service


class HttpRuntimeAdapter:
    """Implements ``RuntimeAdapter`` by delegating to the legacy HTTP dispatcher."""

    def dispatch_run(self, payload: CanonicalRunDispatch) -> DispatchResult:
        integration = self._resolve_integration(payload.integration_id)
        raw_payload = {
            "request_id": payload.request_id,
            "run_id": payload.run_id,
            "dispatch_type": payload.dispatch_type,
            "workflow_binding_id": payload.workflow_binding_id,
            "template_id": payload.template_id,
            "template_version": payload.template_version,
            "priority": payload.priority,
            "actor_id": payload.actor_id,
            **(payload.metadata or {}),
        }
        try:
            response = runtime_dispatch_service.dispatch(integration, raw_payload)
            return DispatchResult(
                status="dispatched",
                external_reference=response.get("external_reference"),
                summary=response.get("summary", ""),
                raw_response=response,
            )
        except ValueError as exc:
            return DispatchResult(
                status="failed",
                summary=str(exc),
            )

    def query_run_status(self, external_ref: str) -> RunStatusResult:
        return RunStatusResult(
            run_id="",
            status="unknown",
            detail="Status query not supported by HTTP adapter",
        )

    @staticmethod
    def _resolve_integration(integration_id: str | None) -> SimpleNamespace:
        """Load an IntegrationTable row from the database."""
        if not integration_id:
            raise ValueError("integration_id is required for HTTP runtime dispatch")
        from app.db.session import SessionLocal
        from app.db.models import IntegrationTable
        with SessionLocal() as session:
            row = session.get(IntegrationTable, integration_id)
            if row is None:
                raise ValueError(f"Integration {integration_id} not found")
            return SimpleNamespace(
                id=row.id,
                endpoint=row.endpoint,
                settings=row.settings,
            )


http_runtime_adapter = HttpRuntimeAdapter()
