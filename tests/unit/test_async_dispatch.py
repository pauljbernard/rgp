"""Unit tests for the async dispatch service."""

import unittest
from unittest.mock import patch, MagicMock

from app.services.async_dispatch_service import AsyncDispatchService


class AsyncDispatchLocalTest(unittest.TestCase):
    """Test local (thread) dispatch mode."""

    def _service(self) -> AsyncDispatchService:
        return AsyncDispatchService(MagicMock())

    def test_enqueue_promotion_returns_task_id(self) -> None:
        service = self._service()
        with patch.object(service, "_execute_promotion_local"):
            task_id = service.enqueue_promotion_execution("promo_1", "user_1", "tenant_1")
        self.assertTrue(task_id.startswith("local_promotion_"))

    def test_enqueue_workflow_returns_task_id(self) -> None:
        service = self._service()
        with patch.object(service, "_advance_workflow_local"):
            task_id = service.enqueue_workflow_step_advance("wfe_1")
        self.assertTrue(task_id.startswith("local_workflow_"))

    def test_enqueue_deployment_returns_task_id(self) -> None:
        service = self._service()
        with patch.object(service, "_run_deployment_local"):
            task_id = service.enqueue_deployment("promo_1", "req_1", "production", "rolling")
        self.assertTrue(task_id.startswith("local_deployment_"))


class AsyncDispatchCeleryTest(unittest.TestCase):
    """Test Celery dispatch mode."""

    @patch("app.services.async_dispatch_service.celery_async_app")
    def test_celery_promotion_dispatch(self, mock_celery: MagicMock) -> None:
        service = AsyncDispatchService(MagicMock())
        mock_result = MagicMock()
        mock_result.id = "celery-task-123"
        mock_celery.send_task.return_value = mock_result

        with patch.object(type(service), "_backend", new_callable=lambda: property(lambda self: "celery")):
            task_id = service.enqueue_promotion_execution("promo_1", "user_1", "tenant_1")

        self.assertEqual(task_id, "celery-task-123")
        mock_celery.send_task.assert_called_once_with(
            "rgp.execute_promotion",
            args=["promo_1", "user_1", "tenant_1"],
        )

    @patch("app.services.async_dispatch_service.celery_async_app")
    def test_celery_workflow_dispatch(self, mock_celery: MagicMock) -> None:
        service = AsyncDispatchService(MagicMock())
        mock_result = MagicMock()
        mock_result.id = "celery-task-456"
        mock_celery.send_task.return_value = mock_result

        with patch.object(type(service), "_backend", new_callable=lambda: property(lambda self: "celery")):
            task_id = service.enqueue_workflow_step_advance("wfe_1", "user_1")

        self.assertEqual(task_id, "celery-task-456")

    @patch("app.services.async_dispatch_service.celery_async_app")
    def test_celery_deployment_dispatch(self, mock_celery: MagicMock) -> None:
        service = AsyncDispatchService(MagicMock())
        mock_result = MagicMock()
        mock_result.id = "celery-task-789"
        mock_celery.send_task.return_value = mock_result

        with patch.object(type(service), "_backend", new_callable=lambda: property(lambda self: "celery")):
            task_id = service.enqueue_deployment("promo_1", "req_1", "prod", "rolling", "int_1", "user_1")

        self.assertEqual(task_id, "celery-task-789")


if __name__ == "__main__":
    unittest.main()
