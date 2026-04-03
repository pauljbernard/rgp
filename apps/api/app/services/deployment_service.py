import json
from urllib import error, request

from app.core.config import settings
from app.db.models import IntegrationTable
from app.services.integration_security_service import integration_security_service


class DeploymentService:
    @staticmethod
    def resolve_endpoint(integration: IntegrationTable) -> str:
        if integration.endpoint.startswith("http://") or integration.endpoint.startswith("https://"):
            return integration_security_service.validate_outbound_target(
                integration.endpoint,
                allowed_hosts=settings.integration_deployment_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )
        if integration.endpoint.startswith("foundry://"):
            base_url = (settings.deployment_adapter_base_url or settings.runtime_adapter_base_url or "http://localhost:8001/api/v1/runtime/mock").rstrip("/")
            base_url = integration_security_service.validate_outbound_target(
                base_url,
                allowed_hosts=settings.integration_deployment_allowed_hosts,
                allow_http_loopback=settings.integration_allow_http_loopback,
            )
            return f"{base_url}/deployments/foundry"
        raise ValueError(f"Unsupported runtime integration endpoint: {integration.endpoint}")

    def execute(self, integration: IntegrationTable, payload: dict) -> dict:
        url = self.resolve_endpoint(integration)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with request.urlopen(req, timeout=10) as response:  # nosec B310 - URL is validated by resolve_endpoint()
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ValueError(f"Runtime target rejected deployment: {detail or exc.reason}") from exc
        except error.URLError as exc:
            raise ValueError(f"Runtime target unavailable: {exc.reason}") from exc


deployment_service = DeploymentService()
