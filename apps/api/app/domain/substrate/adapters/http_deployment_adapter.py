"""HTTP deployment adapter wrapping the existing DeploymentService."""

from __future__ import annotations

from types import SimpleNamespace

from app.domain.substrate.canonical import (
    CanonicalDeploymentRequest,
    DeploymentResult,
    DeploymentStatusResult,
)
from app.services.deployment_service import deployment_service


class HttpDeploymentAdapter:
    """Implements ``DeploymentAdapter`` by delegating to the legacy HTTP executor."""

    def execute_deployment(self, payload: CanonicalDeploymentRequest) -> DeploymentResult:
        integration = self._resolve_integration(payload.integration_id)
        raw_payload = {
            "promotion_id": payload.promotion_id,
            "request_id": payload.request_id,
            "target": payload.target,
            "strategy": payload.strategy,
            "actor_id": payload.actor_id,
            **(payload.metadata or {}),
        }
        try:
            response = deployment_service.execute(integration, raw_payload)
            return DeploymentResult(
                status="success",
                external_reference=response.get("external_reference"),
                summary=response.get("summary", ""),
                raw_response=response,
            )
        except ValueError as exc:
            return DeploymentResult(
                status="failed",
                summary=str(exc),
            )

    def query_deployment_status(self, external_ref: str) -> DeploymentStatusResult:
        return DeploymentStatusResult(
            deployment_id="",
            status="unknown",
            detail="Status query not supported by HTTP adapter",
        )

    @staticmethod
    def _resolve_integration(integration_id: str | None) -> SimpleNamespace:
        """Load an IntegrationTable row from the database."""
        if not integration_id:
            raise ValueError("integration_id is required for HTTP deployment")
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


http_deployment_adapter = HttpDeploymentAdapter()
