"""Unit tests for the substrate abstraction layer."""

import importlib
import os
import sys
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


class SbclAgentRuntimeAdapterTest(unittest.TestCase):
    def test_dispatch_carries_governed_runtime_binding_contract(self) -> None:
        from app.domain.substrate.adapters.sbcl_agent_runtime_adapter import SbclAgentRuntimeAdapter

        adapter = SbclAgentRuntimeAdapter()
        with patch("app.domain.substrate.adapters.sbcl_agent_runtime_adapter.runtime_dispatch_service") as mock_service:
            mock_service.dispatch.return_value = {"external_reference": "sbcl-agent:run_1", "summary": "bound"}

            payload = CanonicalRunDispatch(
                request_id="req_1",
                run_id="run_1",
                integration_id="int_1",
                metadata={"tenant_id": "tenant_1", "projection_id": "pm_1", "agent_session_id": "as_1"},
            )
            with patch.object(adapter, "_resolve_integration", return_value=SimpleNamespace(id="int_1", endpoint="sbcl://local-image", settings={})):
                result = adapter.dispatch_run(payload)

        self.assertEqual(result.status, "dispatched")
        self.assertEqual(result.external_reference, "sbcl-agent:run_1")
        dispatched_payload = mock_service.dispatch.call_args.kwargs["payload"]
        self.assertEqual(dispatched_payload["runtime_subtype"], "sbcl_agent")
        self.assertEqual(dispatched_payload["session_kind"], "stateful_runtime")
        self.assertEqual(dispatched_payload["binding"]["agent_session_id"], "as_1")
        self.assertEqual(dispatched_payload["projection_contract"]["artifact_import_rule"], "sbcl_agent_governed_runtime")

    def test_query_run_status_returns_governed_runtime_payload(self) -> None:
        from app.domain.substrate.adapters.sbcl_agent_runtime_adapter import SbclAgentRuntimeAdapter

        adapter = SbclAgentRuntimeAdapter()
        with patch("app.domain.substrate.adapters.sbcl_agent_runtime_adapter.runtime_dispatch_service.export_sbcl_agent_snapshot") as export_snapshot:
            export_snapshot.return_value = {
                "binding": {"request_id": "req_1"},
                "governed_runtime": {"runtime_subtype": "sbcl_agent", "session_kind": "stateful_runtime"},
                "approvals": [{"id": "wi_1"}],
                "artifacts": [{"id": "art_1"}],
            }
            result = adapter.query_run_status("sbcl-agent:run_1")

        self.assertEqual(result.run_id, "sbcl-agent:run_1")
        self.assertEqual(result.status, "waiting_on_human")
        self.assertEqual(result.current_step, "governed_runtime")
        self.assertEqual(result.raw_payload["governed_runtime"]["runtime_subtype"], "sbcl_agent")
        self.assertIn("import_runtime_artifact", result.raw_payload["resolution_actions"])

    def test_runtime_control_actions_and_artifacts_are_specialized(self) -> None:
        from app.domain.substrate.adapters.sbcl_agent_runtime_adapter import SbclAgentRuntimeAdapter

        adapter = SbclAgentRuntimeAdapter()
        with patch("app.domain.substrate.adapters.sbcl_agent_runtime_adapter.runtime_dispatch_service.resume_sbcl_agent_session") as resume_session, \
             patch("app.domain.substrate.adapters.sbcl_agent_runtime_adapter.runtime_dispatch_service.approve_sbcl_agent_checkpoint") as approve_checkpoint, \
             patch("app.domain.substrate.adapters.sbcl_agent_runtime_adapter.runtime_dispatch_service.list_sbcl_agent_artifacts") as list_artifacts:
            resume_session.return_value = {"status": "resumed"}
            approve_checkpoint.return_value = {"status": "approved"}
            list_artifacts.return_value = [{
                "artifact_key": "runtime-summary",
                "import_rule": "sbcl_agent_governed_runtime",
                "lineage": {"relation": "imported_from_sbcl_agent_session"},
            }]

            resumed = adapter.resume_session("session_ref", approval_token="wi_1")
            approved = adapter.approve_operation("session_ref", "wi_1")
            artifacts = adapter.list_artifacts("session_ref")

        self.assertEqual(resumed["action"], "resume_runtime")
        self.assertEqual(approved["action"], "approve_runtime_checkpoint")
        self.assertEqual(artifacts[0]["import_rule"], "sbcl_agent_governed_runtime")
        self.assertEqual(artifacts[0]["lineage"]["relation"], "imported_from_sbcl_agent_session")


class SbclAgentDeploymentAdapterTest(unittest.TestCase):
    def test_query_deployment_status_uses_canonical_fields(self) -> None:
        from app.domain.substrate.adapters.sbcl_agent_runtime_adapter import SbclAgentDeploymentAdapter

        adapter = SbclAgentDeploymentAdapter()
        with patch("app.domain.substrate.adapters.sbcl_agent_runtime_adapter.deployment_service") as mock_service:
            mock_service.execute.return_value = {"external_reference": "dep_1", "summary": "queued"}

            payload = CanonicalDeploymentRequest(
                promotion_id="promo_1",
                request_id="req_1",
                target="production",
                strategy="rolling",
                integration_id="int_1",
            )
            result = adapter.execute_deployment(payload)
        status = adapter.query_deployment_status("dep_1")

        self.assertEqual(result.external_reference, "dep_1")
        self.assertEqual(status.deployment_id, "dep_1")
        self.assertEqual(status.raw_payload["deployment_subtype"], "sbcl_agent")


class RuntimeDispatchServiceSbclAgentTest(unittest.TestCase):
    def test_dispatch_supports_local_sbcl_endpoint(self) -> None:
        from app.services.runtime_dispatch_service import RuntimeDispatchService

        service = RuntimeDispatchService()
        integration = SimpleNamespace(id="int_1", endpoint="sbcl://local-image", settings={"working_directory": "/tmp/sbcl-agent"})
        with patch.object(service, "_run_sbcl_agent_command") as run_command:
            run_command.return_value = {
                "status": "bound",
                "binding": {"request_id": "req_1"},
                "governed_runtime": {"runtime_subtype": "sbcl_agent"},
            }
            result = service.dispatch(
                integration,
                {
                    "request_id": "req_1",
                    "run_id": "run_1",
                    "binding": {"agent_session_id": "ags_1", "request_id": "req_1"},
                },
            )

        self.assertEqual(result["status"], "bound")
        self.assertIn("external_reference", result)
        command = run_command.call_args.args[0]
        self.assertEqual(command[0], "bind")
        self.assertIn("--environment", command)
        self.assertIn("--agent-session-id", command)


class SbclAgentTurnRenderingTest(unittest.TestCase):
    def test_response_text_and_summary_reflect_governed_runtime_state(self) -> None:
        with patch.dict(os.environ, {"RGP_DATABASE_URL": "sqlite+pysqlite:///:memory:"}, clear=False):
            sys.modules.pop("app.core.config", None)
            sys.modules.pop("app.db.session", None)
            sys.modules.pop("app.repositories.governance_repository", None)
            GovernanceRepository = importlib.import_module("app.repositories.governance_repository").GovernanceRepository

        session_row = SimpleNamespace(agent_label="Runtime Agent", external_session_ref="env:req_1:as_1")
        latest_human_message = SimpleNamespace(message_type="guidance", body="Resume after finance approval.")
        bundle = SimpleNamespace(
            contents={
                "sbcl_agent_binding": {"environment_ref": "env:req_1:as_1"},
                "sbcl_agent_runtime": {
                    "thread_ref": "thread:as_1",
                    "turn_ref": "turn:as_1:latest",
                    "thread_count": 1,
                    "work_item_count": 2,
                    "incident_count": 0,
                },
                "sbcl_agent_approvals": [{"id": "wi_1", "wait_reason": "finance_approval"}],
                "sbcl_agent_artifacts": [{"id": "art_1", "title": "Execution log"}],
            }
        )

        response_text = GovernanceRepository._sbcl_agent_response_text(session_row, latest_human_message, bundle)
        summary = GovernanceRepository._sbcl_agent_turn_summary(session_row, bundle)

        self.assertIn("governed sbcl-agent runtime", response_text)
        self.assertIn("Environment ref: env:req_1:as_1", response_text)
        self.assertIn("Latest guidance: Resume after finance approval.", response_text)
        self.assertIn("Pending approvals: wi_1:finance_approval", response_text)
        self.assertIn("Importable artifacts: Execution log", response_text)
        self.assertEqual(summary, "Runtime Agent is waiting on governed runtime approval")


if __name__ == "__main__":
    unittest.main()
