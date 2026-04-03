"""Unit tests for the substrate abstraction layer."""

import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from app.domain.substrate.canonical import (
    CanonicalDeploymentRequest,
    CanonicalEvent,
    CanonicalRunDispatch,
    DeploymentResult,
    DispatchResult,
    RunStatusResult,
)
from app.domain.substrate.contracts import RuntimeAdapter, DeploymentAdapter, EventSink
from app.domain.substrate.event_normalizer import (
    normalize_from_event_store_row,
    normalize_from_runtime_signal,
)


class CanonicalModelsTest(unittest.TestCase):
    def test_run_dispatch_serialization(self) -> None:
        dispatch = CanonicalRunDispatch(
            request_id="req_1",
            run_id="run_1",
            workflow_binding_id="wf_standard",
            priority="high",
        )
        data = dispatch.model_dump()
        self.assertEqual(data["request_id"], "req_1")
        self.assertEqual(data["dispatch_type"], "workflow")
        self.assertIsInstance(data["metadata"], dict)

    def test_dispatch_result_defaults(self) -> None:
        result = DispatchResult(status="dispatched")
        self.assertIsNone(result.external_reference)
        self.assertEqual(result.summary, "")

    def test_deployment_request_serialization(self) -> None:
        req = CanonicalDeploymentRequest(
            promotion_id="promo_1",
            request_id="req_1",
            target="production",
            strategy="rolling",
        )
        data = req.model_dump()
        self.assertEqual(data["target"], "production")

    def test_canonical_event_with_raw_substrate(self) -> None:
        event = CanonicalEvent(
            tenant_id="t1",
            event_type="run.completed",
            aggregate_type="run",
            aggregate_id="run_1",
            timestamp=datetime.now(timezone.utc),
            actor="system",
            raw_substrate_event={"github_action_id": "123"},
            substrate_source="github",
        )
        self.assertEqual(event.substrate_source, "github")


class EventNormalizerTest(unittest.TestCase):
    def test_normalize_event_store_row(self) -> None:
        row = SimpleNamespace(
            tenant_id="t1",
            event_type="request.submitted",
            aggregate_type="request",
            aggregate_id="req_1",
            occurred_at=datetime(2026, 4, 3, 12, 0, 0, tzinfo=timezone.utc),
            actor="user_1",
            detail="Submitted for review",
            payload={"status": "submitted"},
            request_id="req_1",
            run_id=None,
            artifact_id=None,
            promotion_id=None,
            check_run_id=None,
        )
        event = normalize_from_event_store_row(row)
        self.assertIsInstance(event, CanonicalEvent)
        self.assertEqual(event.tenant_id, "t1")
        self.assertEqual(event.event_type, "request.submitted")
        self.assertEqual(event.request_id, "req_1")

    def test_normalize_runtime_signal(self) -> None:
        signal = SimpleNamespace(
            tenant_id="t1",
            run_id="run_1",
            request_id="req_1",
            status="completed",
            source="foundry",
            detail="Run completed successfully",
            payload={"exit_code": 0},
            received_at=datetime(2026, 4, 3, 12, 0, 0, tzinfo=timezone.utc),
        )
        event = normalize_from_runtime_signal(signal)
        self.assertEqual(event.event_type, "runtime.signal.completed")
        self.assertEqual(event.substrate_source, "foundry")
        self.assertEqual(event.raw_substrate_event, {"exit_code": 0})


class HttpRuntimeAdapterTest(unittest.TestCase):
    @patch("app.domain.substrate.adapters.http_runtime_adapter.runtime_dispatch_service")
    def test_dispatch_success(self, mock_service: MagicMock) -> None:
        from app.domain.substrate.adapters.http_runtime_adapter import HttpRuntimeAdapter
        adapter = HttpRuntimeAdapter()
        mock_service.dispatch.return_value = {"external_reference": "ext_123", "summary": "ok"}

        payload = CanonicalRunDispatch(
            request_id="req_1",
            run_id="run_1",
            integration_id="int_1",
        )
        with patch.object(adapter, "_resolve_integration", return_value=SimpleNamespace(id="int_1", endpoint="https://example.com", settings={})):
            result = adapter.dispatch_run(payload)
        self.assertEqual(result.status, "dispatched")
        self.assertEqual(result.external_reference, "ext_123")

    @patch("app.domain.substrate.adapters.http_runtime_adapter.runtime_dispatch_service")
    def test_dispatch_failure(self, mock_service: MagicMock) -> None:
        from app.domain.substrate.adapters.http_runtime_adapter import HttpRuntimeAdapter
        adapter = HttpRuntimeAdapter()
        mock_service.dispatch.side_effect = ValueError("Connection refused")

        payload = CanonicalRunDispatch(
            request_id="req_1",
            run_id="run_1",
            integration_id="int_1",
        )
        with patch.object(adapter, "_resolve_integration", return_value=SimpleNamespace(id="int_1", endpoint="https://example.com", settings={})):
            result = adapter.dispatch_run(payload)
        self.assertEqual(result.status, "failed")
        self.assertIn("Connection refused", result.summary)


class HttpDeploymentAdapterTest(unittest.TestCase):
    @patch("app.domain.substrate.adapters.http_deployment_adapter.deployment_service")
    def test_deploy_success(self, mock_service: MagicMock) -> None:
        from app.domain.substrate.adapters.http_deployment_adapter import HttpDeploymentAdapter
        adapter = HttpDeploymentAdapter()
        mock_service.execute.return_value = {"external_reference": "dep_456", "summary": "deployed"}

        payload = CanonicalDeploymentRequest(
            promotion_id="promo_1",
            request_id="req_1",
            target="production",
            strategy="rolling",
            integration_id="int_1",
        )
        with patch.object(adapter, "_resolve_integration", return_value=SimpleNamespace(id="int_1", endpoint="https://example.com", settings={})):
            result = adapter.execute_deployment(payload)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.external_reference, "dep_456")


class ProtocolComplianceTest(unittest.TestCase):
    """Verify adapters satisfy protocol contracts at import time."""

    def test_http_runtime_adapter_is_runtime_adapter(self) -> None:
        from app.domain.substrate.adapters.http_runtime_adapter import HttpRuntimeAdapter
        adapter = HttpRuntimeAdapter()
        self.assertTrue(hasattr(adapter, "dispatch_run"))
        self.assertTrue(hasattr(adapter, "query_run_status"))

    def test_http_deployment_adapter_is_deployment_adapter(self) -> None:
        from app.domain.substrate.adapters.http_deployment_adapter import HttpDeploymentAdapter
        adapter = HttpDeploymentAdapter()
        self.assertTrue(hasattr(adapter, "execute_deployment"))
        self.assertTrue(hasattr(adapter, "query_deployment_status"))


if __name__ == "__main__":
    unittest.main()
