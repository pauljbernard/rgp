import os
import sys
from pathlib import Path

from celery import Celery


redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

api_app_path = Path(__file__).resolve().parents[2] / "api"
if str(api_app_path) not in sys.path:
    sys.path.insert(0, str(api_app_path))

celery_app = Celery("rgp-worker", broker=redis_url, backend=redis_url)


@celery_app.task(name="rgp.healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@celery_app.task(name="rgp.run_check_run")
def run_check_run(check_run_id: str) -> dict[str, str]:
    from app.services.check_dispatch_service import check_dispatch_service

    check_dispatch_service.execute_check_run(check_run_id)
    return {"status": "ok", "check_run_id": check_run_id}


@celery_app.task(name="rgp.execute_promotion")
def execute_promotion(promotion_id: str, actor_id: str, tenant_id: str) -> dict[str, str]:
    """Execute a promotion deployment asynchronously."""
    from app.repositories.governance_repository import governance_repository
    from app.models.governance import PromotionActionRequest

    payload = PromotionActionRequest(actor_id=actor_id, action="execute", reason="Async promotion execution")
    governance_repository.apply_promotion_action(promotion_id, payload, tenant_id)
    return {"status": "ok", "promotion_id": promotion_id}


@celery_app.task(name="rgp.advance_workflow_step")
def advance_workflow_step(execution_id: str, actor_id: str = "system") -> dict[str, str]:
    """Advance a workflow execution to the next step asynchronously."""
    from app.services.workflow_engine_service import workflow_engine_service

    result = workflow_engine_service.advance_step(execution_id, actor_id)
    return {"status": "ok", "execution_id": execution_id, "new_status": result.status}


@celery_app.task(name="rgp.run_deployment")
def run_deployment(
    promotion_id: str,
    request_id: str,
    target: str,
    strategy: str,
    integration_id: str | None = None,
    actor_id: str | None = None,
) -> dict[str, str]:
    """Execute a deployment via the substrate adapter asynchronously."""
    from app.domain.substrate.adapters.http_deployment_adapter import http_deployment_adapter
    from app.domain.substrate.canonical import CanonicalDeploymentRequest

    payload = CanonicalDeploymentRequest(
        promotion_id=promotion_id,
        request_id=request_id,
        target=target,
        strategy=strategy,
        integration_id=integration_id,
        actor_id=actor_id,
    )
    result = http_deployment_adapter.execute_deployment(payload)
    return {"status": result.status, "promotion_id": promotion_id, "summary": result.summary}
