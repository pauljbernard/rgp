"""Async dispatch service — enqueues background tasks via Celery or local threads.

Mirrors the check_dispatch_service pattern: supports both 'local' (thread) and
'celery' backends for promotion execution, workflow step advancement, and
deployment operations.
"""

from __future__ import annotations

import logging
import threading

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_async_app = Celery("rgp-async-dispatch", broker=settings.redis_url, backend=settings.redis_url)


class AsyncDispatchService:
    """Enqueues async tasks for promotion, workflow, and deployment operations."""

    def __init__(self) -> None:
        self._local_lock = threading.Lock()

    @property
    def _backend(self) -> str:
        return getattr(settings, "async_dispatch_backend", None) or getattr(settings, "check_dispatch_backend", "local")

    def enqueue_promotion_execution(
        self,
        promotion_id: str,
        actor_id: str,
        tenant_id: str,
    ) -> str:
        """Enqueue async promotion execution. Returns task ID."""
        if self._backend == "celery":
            result = celery_async_app.send_task(
                "rgp.execute_promotion",
                args=[promotion_id, actor_id, tenant_id],
            )
            logger.info("Enqueued promotion execution %s via Celery: %s", promotion_id, result.id)
            return result.id
        return self._run_local("promotion", promotion_id, self._execute_promotion_local, promotion_id, actor_id, tenant_id)

    def enqueue_workflow_step_advance(
        self,
        execution_id: str,
        actor_id: str = "system",
    ) -> str:
        """Enqueue async workflow step advancement. Returns task ID."""
        if self._backend == "celery":
            result = celery_async_app.send_task(
                "rgp.advance_workflow_step",
                args=[execution_id, actor_id],
            )
            logger.info("Enqueued workflow advance %s via Celery: %s", execution_id, result.id)
            return result.id
        return self._run_local("workflow", execution_id, self._advance_workflow_local, execution_id, actor_id)

    def enqueue_deployment(
        self,
        promotion_id: str,
        request_id: str,
        target: str,
        strategy: str,
        integration_id: str | None = None,
        actor_id: str | None = None,
    ) -> str:
        """Enqueue async deployment. Returns task ID."""
        if self._backend == "celery":
            result = celery_async_app.send_task(
                "rgp.run_deployment",
                args=[promotion_id, request_id, target, strategy, integration_id, actor_id],
            )
            logger.info("Enqueued deployment for %s via Celery: %s", promotion_id, result.id)
            return result.id
        return self._run_local(
            "deployment", promotion_id,
            self._run_deployment_local,
            promotion_id, request_id, target, strategy, integration_id, actor_id,
        )

    # ------------------------------------------------------------------
    # Local execution (thread-based, for dev/test)
    # ------------------------------------------------------------------

    def _run_local(self, task_type: str, task_key: str, fn, *args) -> str:
        task_id = f"local_{task_type}_{task_key}"

        def _runner():
            try:
                fn(*args)
            except Exception:
                logger.exception("Local async task %s failed", task_id)

        thread = threading.Thread(target=_runner, daemon=True)
        thread.start()
        logger.info("Started local thread for %s", task_id)
        return task_id

    @staticmethod
    def _execute_promotion_local(promotion_id: str, actor_id: str, tenant_id: str) -> None:
        from app.repositories.governance_repository import governance_repository
        from app.models.governance import PromotionActionRequest

        payload = PromotionActionRequest(actor_id=actor_id, action="execute", reason="Async promotion execution")
        governance_repository.apply_promotion_action(promotion_id, payload, tenant_id)

    @staticmethod
    def _advance_workflow_local(execution_id: str, actor_id: str) -> None:
        from app.services.workflow_engine_service import workflow_engine_service

        workflow_engine_service.advance_step(execution_id, actor_id)

    @staticmethod
    def _run_deployment_local(
        promotion_id: str, request_id: str, target: str,
        strategy: str, integration_id: str | None, actor_id: str | None,
    ) -> None:
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
        http_deployment_adapter.execute_deployment(payload)


async_dispatch_service = AsyncDispatchService()
