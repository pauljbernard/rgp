import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib import error
from unittest.mock import Mock, patch

from app.services.agent_provider_service import AgentProviderService
from app.services.check_dispatch_service import CheckDispatchService
from app.services.deployment_service import DeploymentService
from app.services.event_publisher_service import EventPublisherService
from app.services.event_store_service import EventStoreService
from app.services.integration_security_service import integration_security_service
from app.services.object_store_service import ObjectStoreService
from app.services.performance_metrics_service import PerformanceMetricsService
from app.services.policy_check_service import PolicyCheckService
from app.services.runtime_dispatch_service import RuntimeDispatchService
from app.models.request import RequestStatus


class DummyResponse:
    def __init__(self, payload: dict | None = None, status_code: int = 200) -> None:
        self._payload = payload or {}
        self._status_code = status_code

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def getcode(self) -> int:
        return self._status_code

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyStreamingResponse:
    def __init__(self, lines: list[str], status_code: int = 200) -> None:
        self._lines = [line.encode("utf-8") for line in lines]
        self._status_code = status_code

    def __iter__(self):
        return iter(self._lines)

    def getcode(self) -> int:
        return self._status_code

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyScalarResult:
    def __init__(self, *, items=None, first=None) -> None:
        self._items = [] if items is None else items
        self._first = first

    def all(self):
        return self._items

    def first(self):
        return self._first


class ObjectStoreServiceTest(unittest.TestCase):
    def test_put_get_and_exists_round_trip(self) -> None:
        service = ObjectStoreService()
        with tempfile.TemporaryDirectory() as tempdir:
            with patch("app.services.object_store_service.settings.object_store_root", tempdir):
                key = "artifacts/art_001/body.txt"
                written_key = service.put_text(key, "stored text")

                self.assertEqual(written_key, key)
                self.assertTrue(service.exists(key))
                self.assertEqual(service.get_text(key), "stored text")
                self.assertEqual(service._resolve_path(key), Path(tempdir) / key)


class EventPublisherServiceTest(unittest.TestCase):
    def test_topic_family_is_derived_from_event_type_prefix(self) -> None:
        service = EventPublisherService()
        with patch("app.services.event_publisher_service.settings.event_bus_topic_prefix", "rgp"):
            self.assertEqual(service._topic_for("request.submitted"), "rgp.request")
            self.assertEqual(service._topic_for("check_run.completed"), "rgp.check_run")

    def test_publish_pending_marks_rows_published_for_outbox_backend(self) -> None:
        service = EventPublisherService()
        row = SimpleNamespace(
            status="pending",
            error_message="old",
            published_at=None,
            topic="rgp.request",
            partition_key="req_001",
            payload={},
            event_store_id=1,
        )
        session = SimpleNamespace(
            scalars=lambda _stmt: SimpleNamespace(all=lambda: [row]),
        )

        with patch("app.services.event_publisher_service.settings.event_bus_enabled", True), patch(
            "app.services.event_publisher_service.settings.event_bus_backend", "outbox"
        ):
            processed = service.publish_pending(session)

        self.assertEqual(processed, 1)
        self.assertEqual(row.status, "published")
        self.assertIsNotNone(row.published_at)
        self.assertIsNone(row.error_message)

    def test_publish_pending_marks_deferred_when_bus_disabled(self) -> None:
        service = EventPublisherService()
        row = SimpleNamespace(
            status="pending",
            error_message=None,
            published_at=None,
            topic="rgp.request",
            partition_key="req_001",
            payload={},
            event_store_id=1,
        )
        session = SimpleNamespace(
            scalars=lambda _stmt: SimpleNamespace(all=lambda: [row]),
        )

        with patch("app.services.event_publisher_service.settings.event_bus_enabled", False):
            processed = service.publish_pending(session)

        self.assertEqual(processed, 1)
        self.assertEqual(row.status, "deferred")
        self.assertEqual(row.error_message, "Event bus disabled; retained in outbox")

    def test_publish_http_posts_expected_payload(self) -> None:
        service = EventPublisherService()
        row = SimpleNamespace(
            topic="rgp.request",
            partition_key="req_001",
            payload={"event_type": "request.submitted", "detail": "ok"},
            event_store_id=12,
        )

        captured: dict[str, object] = {}

        def fake_urlopen(req, timeout=0):
            captured["url"] = req.full_url
            captured["body"] = req.data.decode("utf-8")
            captured["timeout"] = timeout
            return DummyResponse(status_code=202)

        with patch("app.services.event_publisher_service.settings.event_bus_http_endpoint", "http://127.0.0.1:8001/mock"), patch(
            "app.services.event_publisher_service.urllib_request.urlopen", fake_urlopen
        ):
            service._publish_http(row)

        self.assertEqual(captured["url"], "http://127.0.0.1:8001/mock/rgp.request")
        self.assertIn('"partition_key": "req_001"', str(captured["body"]))


class AgentProviderServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AgentProviderService()

    def test_setting_reads_trimmed_strings_only(self) -> None:
        integration = SimpleNamespace(settings={"provider": " openai ", "empty": "   "})
        self.assertEqual(self.service._setting(integration, "provider"), "openai")
        self.assertIsNone(self.service._setting(integration, "empty"))
        self.assertIsNone(self.service._setting(integration, "missing"))

    def test_provider_prefers_config_then_name_inference(self) -> None:
        explicit = SimpleNamespace(name="Anything", settings={"provider": "anthropic"})
        codex = SimpleNamespace(name="OpenAI Codex", settings={})
        claude = SimpleNamespace(name="Anthropic Claude Code", settings={})
        copilot = SimpleNamespace(name="Microsoft Copilot", settings={})

        self.assertEqual(self.service._provider(explicit), "anthropic")
        self.assertEqual(self.service._provider(codex), "openai")
        self.assertEqual(self.service._provider(claude), "anthropic")
        self.assertEqual(self.service._provider(copilot), "microsoft")

    def test_fallback_continue_turn_includes_latest_guidance(self) -> None:
        turn = self.service._fallback_continue_turn("Codex", "Use exactly three bullets.", "ext-1")
        self.assertIn("Use exactly three bullets.", turn.assistant_text)
        self.assertEqual(turn.external_session_ref, "ext-1")

    def test_chunk_text_emits_incremental_and_done_chunks(self) -> None:
        chunks = list(self.service._chunk_text("one two", "ext-1"))
        self.assertEqual([chunk.delta_text for chunk in chunks[:-1]], ["one", " two"])
        self.assertEqual(chunks[-1].assistant_text, "one two")
        self.assertTrue(chunks[-1].done)

    def test_extract_microsoft_content_reads_common_response_shapes(self) -> None:
        self.assertEqual(
            self.service._extract_microsoft_content({"message": {"content": "primary"}}),
            "primary",
        )
        self.assertEqual(
            self.service._extract_microsoft_content({"messages": [{"role": "assistant", "text": "from messages"}]}),
            "from messages",
        )
        self.assertEqual(
            self.service._extract_microsoft_content({"value": [{"from": "bot", "content": "from value"}]}),
            "from value",
        )

    def test_json_request_uses_ssl_context_and_decodes_json(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(req, context=None, timeout=0):
            captured["url"] = req.full_url
            captured["context"] = context
            captured["timeout"] = timeout
            return DummyResponse({"ok": True})

        with patch("app.services.agent_provider_service.request.urlopen", fake_urlopen):
            payload = self.service._json_request(
                "https://example.test/chat",
                headers={"Authorization": "Bearer token"},
                payload={"message": "hello"},
            )

        self.assertEqual(payload, {"ok": True})
        self.assertIs(captured["context"], self.service._ssl_context)
        self.assertEqual(captured["timeout"], 60)

    def test_secret_settings_are_decrypted_for_provider_calls(self) -> None:
        encrypted = integration_security_service.encrypt_secret("super-secret")
        integration = SimpleNamespace(name="OpenAI Codex", settings={"api_key": encrypted, "base_url": "https://api.openai.com/v1"})
        with patch.object(self.service, "_json_request", return_value={"choices": [{"message": {"content": "ok"}}]}) as json_request:
            result = self.service._openai_turn(integration, [{"role": "user", "content": "hi"}])
        self.assertEqual(result.assistant_text, "ok")
        self.assertEqual(json_request.call_args.kwargs["headers"]["Authorization"], "Bearer super-secret")

    def test_provider_base_url_must_be_allowlisted(self) -> None:
        integration = SimpleNamespace(name="OpenAI Codex", settings={"base_url": "https://evil.example.com/v1"})
        with self.assertRaisesRegex(ValueError, "allowlist"):
            self.service._validated_provider_base_url(integration, "https://api.openai.com/v1", ["api.openai.com"])

    def test_start_session_routes_to_provider_handlers(self) -> None:
        integration = SimpleNamespace(name="OpenAI Codex", settings={})
        with patch.object(self.service, "_openai_turn", return_value=SimpleNamespace(assistant_text="ok")) as openai_turn:
            result = self.service.start_session(integration, "Title", "Prompt", [{"role": "user", "content": "hi"}])
        self.assertEqual(result.assistant_text, "ok")
        openai_turn.assert_called_once()

    def test_continue_session_routes_to_fallback_when_provider_unknown(self) -> None:
        integration = SimpleNamespace(name="Custom Agent", settings={})
        result = self.service.continue_session(integration, "Custom", [], "More detail", "sess-1")
        self.assertIn("More detail", result.assistant_text)
        self.assertEqual(result.external_session_ref, "sess-1")

    def test_stream_session_routes_to_provider_stream(self) -> None:
        integration = SimpleNamespace(name="Anthropic Claude Code", settings={})
        expected = [SimpleNamespace(delta_text="a", assistant_text="a", done=False), SimpleNamespace(delta_text="", assistant_text="a", done=True)]
        with patch.object(self.service, "_anthropic_stream_turn", return_value=iter(expected)) as stream_turn:
            result = list(self.service.stream_start_session(integration, "Title", "Prompt", []))
        self.assertEqual(result, expected)
        stream_turn.assert_called_once()

    def test_start_and_continue_session_cover_other_provider_branches_and_error_fallback(self) -> None:
        anthropic = SimpleNamespace(name="Anthropic Claude Code", settings={})
        microsoft = SimpleNamespace(name="Microsoft Copilot", settings={})

        with patch.object(self.service, "_anthropic_turn", return_value=SimpleNamespace(assistant_text="anthropic")) as anthropic_turn:
            result = self.service.start_session(anthropic, "Title", "Prompt", [])
        self.assertEqual(result.assistant_text, "anthropic")
        anthropic_turn.assert_called_once()

        with patch.object(self.service, "_microsoft_start_turn", return_value=SimpleNamespace(assistant_text="microsoft")) as microsoft_turn:
            result = self.service.start_session(microsoft, "Title", "Prompt", [])
        self.assertEqual(result.assistant_text, "microsoft")
        microsoft_turn.assert_called_once()

        with patch.object(self.service, "_anthropic_turn", side_effect=ValueError("boom")), patch(
            "app.services.agent_provider_service.settings.agent_provider_fallback_mode",
            "simulate",
        ):
            result = self.service.start_session(anthropic, "Title", "Prompt", [])
        self.assertIn("Anthropic Claude Code session started", result.assistant_text)

        with patch.object(self.service, "_microsoft_continue_turn", return_value=SimpleNamespace(assistant_text="continued")) as microsoft_continue:
            result = self.service.continue_session(microsoft, "Copilot", [], "Need more", "sess-1")
        self.assertEqual(result.assistant_text, "continued")
        microsoft_continue.assert_called_once()

        with patch.object(self.service, "_openai_turn", side_effect=ValueError("boom")), patch(
            "app.services.agent_provider_service.settings.agent_provider_fallback_mode",
            "simulate",
        ):
            result = self.service.continue_session(SimpleNamespace(name="OpenAI Codex", settings={}), "Codex", [], "Need more", "sess-1")
        self.assertIn("Codex received your guidance", result.assistant_text)

    def test_stream_start_and_continue_cover_fallback_and_provider_branches(self) -> None:
        anthropic = SimpleNamespace(name="Anthropic Claude Code", settings={})
        microsoft = SimpleNamespace(name="Microsoft Copilot", settings={})
        expected = [SimpleNamespace(delta_text="x", assistant_text="x", done=False), SimpleNamespace(delta_text="", assistant_text="x", done=True)]

        with patch.object(self.service, "_microsoft_stream_start_turn", return_value=iter(expected)) as microsoft_stream:
            result = list(self.service.stream_start_session(microsoft, "Title", "Prompt", []))
        self.assertEqual(result, expected)
        microsoft_stream.assert_called_once()

        with patch.object(self.service, "_anthropic_stream_turn", side_effect=ValueError("boom")), patch(
            "app.services.agent_provider_service.settings.agent_provider_fallback_mode",
            "simulate",
        ):
            result = list(self.service.stream_start_session(anthropic, "Title", "Prompt", []))
        self.assertTrue(result[-1].done)
        self.assertIn("Anthropic Claude Code session started", result[-1].assistant_text)

        with patch.object(self.service, "_anthropic_stream_turn", return_value=iter(expected)) as anthropic_stream:
            result = list(self.service.stream_continue_session(anthropic, "Claude", [], "Need more", "sess-1"))
        self.assertEqual(result, expected)
        anthropic_stream.assert_called_once()

        with patch.object(self.service, "_microsoft_stream_continue_turn", side_effect=ValueError("boom")), patch(
            "app.services.agent_provider_service.settings.agent_provider_fallback_mode",
            "simulate",
        ):
            result = list(self.service.stream_continue_session(microsoft, "Copilot", [], "Need more", "sess-1"))
        self.assertTrue(result[-1].done)
        self.assertIn("Copilot received your guidance", result[-1].assistant_text)

    def test_fallback_or_raise_obeys_mode(self) -> None:
        with patch("app.services.agent_provider_service.settings.agent_provider_fallback_mode", "simulate"):
            turn = self.service._fallback_or_raise("OpenAI Codex")
        self.assertIn("OpenAI Codex session started", turn.assistant_text)
        with patch("app.services.agent_provider_service.settings.agent_provider_fallback_mode", "error"):
            with self.assertRaises(ValueError):
                self.service._fallback_or_raise("OpenAI Codex")

    def test_openai_turn_parses_string_and_list_content(self) -> None:
        integration = SimpleNamespace(name="OpenAI Codex", settings={"api_key": "key", "base_url": "https://api.openai.com/v1", "model": "gpt-test"})
        with patch.object(self.service, "_json_request", return_value={"choices": [{"message": {"content": "plain text"}}]}):
            result = self.service._openai_turn(integration, [])
        self.assertEqual(result.assistant_text, "plain text")

        with patch.object(self.service, "_json_request", return_value={"choices": [{"message": {"content": [{"text": "part1"}, {"text": "part2"}]}}]}):
            result = self.service._openai_turn(integration, [])
        self.assertEqual(result.assistant_text, "part1part2")

    def test_openai_turn_without_content_raises(self) -> None:
        integration = SimpleNamespace(name="OpenAI Codex", settings={"api_key": "key", "base_url": "https://api.openai.com/v1", "model": "gpt-test"})
        with patch.object(self.service, "_json_request", return_value={"choices": [{"message": {}}]}):
            with self.assertRaises(ValueError):
                self.service._openai_turn(integration, [])

    def test_openai_turn_without_api_key_uses_fallback(self) -> None:
        integration = SimpleNamespace(name="OpenAI Codex", settings={})
        with patch("app.services.agent_provider_service.settings.agent_provider_fallback_mode", "simulate"):
            result = self.service._openai_turn(integration, [])
        self.assertIn("Governed Request", result.assistant_text)

    def test_openai_stream_without_api_key_uses_fallback_stream(self) -> None:
        integration = SimpleNamespace(name="OpenAI Codex", settings={})
        chunks = list(self.service._openai_stream_turn(integration, []))
        self.assertTrue(chunks[-1].done)
        self.assertIn("OpenAI", chunks[-1].assistant_text)

    def test_openai_stream_turn_parses_stream_and_error_paths(self) -> None:
        integration = SimpleNamespace(name="OpenAI Codex", settings={"api_key": "key", "base_url": "https://api.openai.com/v1", "model": "gpt-test"})
        response = DummyStreamingResponse([
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            "data: [DONE]",
        ])
        with patch("app.services.agent_provider_service.request.urlopen", return_value=response):
            chunks = list(self.service._openai_stream_turn(integration, []))
        self.assertEqual(chunks[-1].assistant_text, "Hello world")
        self.assertTrue(chunks[-1].done)

        http_error = error.HTTPError("https://api.openai.com/v1", 500, "boom", hdrs=None, fp=None)
        http_error.read = lambda: b"bad"
        with patch("app.services.agent_provider_service.request.urlopen", side_effect=http_error):
            with self.assertRaises(ValueError):
                list(self.service._openai_stream_turn(integration, []))

        with patch("app.services.agent_provider_service.request.urlopen", side_effect=error.URLError("offline")):
            with self.assertRaises(ValueError):
                list(self.service._openai_stream_turn(integration, []))

        empty = DummyStreamingResponse(['data: {"choices":[{"delta":{}}]}', "data: [DONE]"])
        with patch("app.services.agent_provider_service.request.urlopen", return_value=empty):
            with self.assertRaises(ValueError):
                list(self.service._openai_stream_turn(integration, []))

    def test_anthropic_turn_parses_text_parts_and_raises_on_empty(self) -> None:
        integration = SimpleNamespace(name="Anthropic Claude Code", settings={"api_key": "key", "base_url": "https://api.anthropic.com/v1", "model": "claude-test"})
        with patch.object(self.service, "_json_request", return_value={"content": [{"type": "text", "text": "hello "} , {"type": "text", "text": "world"}]}):
            result = self.service._anthropic_turn(integration, [])
        self.assertEqual(result.assistant_text, "hello world")

        with patch.object(self.service, "_json_request", return_value={"content": []}):
            with self.assertRaises(ValueError):
                self.service._anthropic_turn(integration, [])

    def test_anthropic_stream_turn_parses_stream_and_error_paths(self) -> None:
        integration = SimpleNamespace(name="Anthropic Claude Code", settings={"api_key": "key", "base_url": "https://api.anthropic.com/v1", "model": "claude-test"})
        response = DummyStreamingResponse([
            'data: {"type":"content_block_delta","delta":{"text":"Hello"}}',
            'data: {"type":"content_block_delta","delta":{"text":" world"}}',
            "data: [DONE]",
        ])
        with patch("app.services.agent_provider_service.request.urlopen", return_value=response):
            chunks = list(self.service._anthropic_stream_turn(integration, []))
        self.assertEqual(chunks[-1].assistant_text, "Hello world")
        self.assertTrue(chunks[-1].done)

        http_error = error.HTTPError("https://api.anthropic.com/v1", 500, "boom", hdrs=None, fp=None)
        http_error.read = lambda: b"bad"
        with patch("app.services.agent_provider_service.request.urlopen", side_effect=http_error):
            with self.assertRaises(ValueError):
                list(self.service._anthropic_stream_turn(integration, []))

        with patch("app.services.agent_provider_service.request.urlopen", side_effect=error.URLError("offline")):
            with self.assertRaises(ValueError):
                list(self.service._anthropic_stream_turn(integration, []))

        empty = DummyStreamingResponse(['data: {"type":"message_start"}', "data: [DONE]"])
        with patch("app.services.agent_provider_service.request.urlopen", return_value=empty):
            with self.assertRaises(ValueError):
                list(self.service._anthropic_stream_turn(integration, []))

    def test_microsoft_start_and_continue_turn_handle_missing_data(self) -> None:
        integration = SimpleNamespace(name="Microsoft Copilot", settings={"access_token": "token", "base_url": "https://graph.microsoft.com/beta/copilot"})
        with patch.object(self.service, "_json_request", return_value={"conversationId": "conv-1"}), patch.object(
            self.service,
            "_microsoft_continue_turn",
            return_value=SimpleNamespace(assistant_text="done", external_session_ref="conv-1"),
        ):
            result = self.service._microsoft_start_turn(integration, "Title", "Prompt")
        self.assertEqual(result.external_session_ref, "conv-1")

        with patch.object(self.service, "_json_request", return_value={"id": ""}):
            with self.assertRaises(ValueError):
                self.service._microsoft_start_turn(integration, "Title", "Prompt")

        with self.assertRaises(ValueError):
            self.service._microsoft_continue_turn(integration, "hello", None)

    def test_microsoft_continue_turn_reads_content_and_raises_when_empty(self) -> None:
        integration = SimpleNamespace(name="Microsoft Copilot", settings={"access_token": "token", "base_url": "https://graph.microsoft.com/beta/copilot"})
        with patch.object(self.service, "_json_request", return_value={"message": {"content": "response"}}):
            result = self.service._microsoft_continue_turn(integration, "hello", "conv-1")
        self.assertEqual(result.assistant_text, "response")

        with patch.object(self.service, "_json_request", return_value={"message": {}}):
            with self.assertRaises(ValueError):
                self.service._microsoft_continue_turn(integration, "hello", "conv-1")

    def test_microsoft_stream_helpers_and_extract_text_paths(self) -> None:
        integration = SimpleNamespace(name="Microsoft Copilot", settings={"access_token": "token", "base_url": "https://graph.microsoft.com/beta/copilot"})
        with patch.object(self.service, "_microsoft_start_turn", return_value=SimpleNamespace(assistant_text="hello world", external_session_ref="conv-1")):
            chunks = list(self.service._microsoft_stream_start_turn(integration, "Title", "Prompt"))
        self.assertEqual(chunks[-1].assistant_text, "hello world")

        with patch.object(self.service, "_microsoft_continue_turn", return_value=SimpleNamespace(assistant_text="next turn", external_session_ref="conv-1")):
            chunks = list(self.service._microsoft_stream_continue_turn(integration, "Need more", "conv-1"))
        self.assertEqual(chunks[-1].assistant_text, "next turn")

        self.assertEqual(self.service._extract_microsoft_content({"message": {"text": "from text"}}), "from text")
        self.assertEqual(
            self.service._extract_microsoft_content({"messages": [{"role": "user", "text": "ignore"}, {"role": "assistant", "content": "assistant content"}]}),
            "assistant content",
        )

    def test_json_request_wraps_http_and_url_errors(self) -> None:
        http_error = error.HTTPError("https://example.test", 500, "boom", hdrs=None, fp=None)
        http_error.read = lambda: b"bad"
        with patch("app.services.agent_provider_service.request.urlopen", side_effect=http_error):
            with self.assertRaises(ValueError):
                self.service._json_request("https://example.test", {}, {})

        with patch("app.services.agent_provider_service.request.urlopen", side_effect=error.URLError("offline")):
            with self.assertRaises(ValueError):
                self.service._json_request("https://example.test", {}, {})


class CheckDispatchServiceTest(unittest.TestCase):
    def test_dispatch_local_marks_worker_task_and_invokes_local_runner(self) -> None:
        service = CheckDispatchService()
        check_run = SimpleNamespace(worker_task_id=None)
        session = SimpleNamespace(
            get=lambda _model, _id: check_run,
            flush=lambda: None,
        )

        with patch("app.services.check_dispatch_service.settings.check_dispatch_backend", "local"), patch.object(
            service, "_dispatch_local"
        ) as dispatch_local:
            service._dispatch(session, "cr_123")

        self.assertEqual(check_run.worker_task_id, "local:cr_123")
        dispatch_local.assert_called_once_with("cr_123")

    def test_next_check_run_id_uses_highest_existing_suffix(self) -> None:
        service = CheckDispatchService()
        session = SimpleNamespace(
            scalars=lambda _stmt: SimpleNamespace(all=lambda: ["cr_001", "cr_014", "cr_009"]),
        )
        self.assertEqual(service._next_check_run_id(session), "cr_015")

    def test_has_pending_request_and_promotion_check_runs(self) -> None:
        session = SimpleNamespace(scalars=lambda _stmt: DummyScalarResult(first=object()))
        self.assertTrue(CheckDispatchService.has_pending_request_check_run(session, "req_001"))
        self.assertTrue(CheckDispatchService.has_pending_promotion_check_run(session, "pro_001"))

        session = SimpleNamespace(scalars=lambda _stmt: DummyScalarResult(first=None))
        self.assertFalse(CheckDispatchService.has_pending_request_check_run(session, "req_001"))
        self.assertFalse(CheckDispatchService.has_pending_promotion_check_run(session, "pro_001"))

    def test_enqueue_request_checks_returns_existing_run(self) -> None:
        service = CheckDispatchService()
        existing = SimpleNamespace(id="cr_001")
        session = SimpleNamespace(scalars=lambda _stmt: DummyScalarResult(first=existing))
        result = service.enqueue_request_checks(session, "req_001", "user_demo", "submit")
        self.assertIs(result, existing)

    def test_enqueue_request_checks_creates_run_and_appends_event(self) -> None:
        service = CheckDispatchService()
        added: list[object] = []
        session = SimpleNamespace(
            scalars=Mock(side_effect=[DummyScalarResult(first=None)]),
            add=added.append,
            flush=lambda: None,
            get=lambda model, identifier: SimpleNamespace(id=identifier, tenant_id="tenant_demo"),
        )
        with patch.object(service, "_next_check_run_id", return_value="cr_010"), patch.object(service, "_dispatch") as dispatch, patch(
            "app.services.check_dispatch_service.event_store_service.append"
        ) as append:
            check_run = service.enqueue_request_checks(session, "req_001", "user_demo", "submit")

        self.assertEqual(check_run.id, "cr_010")
        self.assertEqual(check_run.scope, "request")
        self.assertEqual(len(added), 1)
        append.assert_called_once()
        dispatch.assert_called_once_with(session, "cr_010")

    def test_enqueue_promotion_checks_creates_run(self) -> None:
        service = CheckDispatchService()
        added: list[object] = []
        session = SimpleNamespace(
            scalars=Mock(side_effect=[DummyScalarResult(first=None)]),
            add=added.append,
            flush=lambda: None,
            get=lambda model, identifier: SimpleNamespace(id=identifier, tenant_id="tenant_demo"),
        )
        with patch.object(service, "_next_check_run_id", return_value="cr_011"), patch.object(service, "_dispatch") as dispatch, patch(
            "app.services.check_dispatch_service.event_store_service.append"
        ):
            check_run = service.enqueue_promotion_checks(session, "pro_001", "req_001", "user_demo", "authorize")

        self.assertEqual(check_run.id, "cr_011")
        self.assertEqual(check_run.scope, "promotion")
        dispatch.assert_called_once_with(session, "cr_011")

    def test_dispatch_celery_sets_worker_id_and_raises_on_failure(self) -> None:
        service = CheckDispatchService()
        check_run = SimpleNamespace(worker_task_id=None)
        session = SimpleNamespace(get=lambda _model, _id: check_run, flush=lambda: None)

        with patch("app.services.check_dispatch_service.settings.check_dispatch_backend", "celery"), patch(
            "app.services.check_dispatch_service.celery_dispatch_app.send_task",
            return_value=SimpleNamespace(id="celery-123"),
        ):
            service._dispatch(session, "cr_123")
        self.assertEqual(check_run.worker_task_id, "celery-123")

        with patch("app.services.check_dispatch_service.settings.check_dispatch_backend", "celery"), patch(
            "app.services.check_dispatch_service.celery_dispatch_app.send_task",
            side_effect=RuntimeError("offline"),
        ):
            with self.assertRaises(ValueError):
                service._dispatch(session, "cr_124")

    def test_dispatch_local_skips_duplicate_inflight_runs(self) -> None:
        service = CheckDispatchService()
        service._local_inflight.add("cr_200")
        with patch("app.services.check_dispatch_service.threading.Thread") as thread_cls:
            service._dispatch_local("cr_200")
        thread_cls.assert_not_called()

    def test_dispatch_local_starts_thread_for_new_run(self) -> None:
        service = CheckDispatchService()
        thread_mock = Mock()
        with patch("app.services.check_dispatch_service.threading.Thread", return_value=thread_mock) as thread_cls:
            service._dispatch_local("cr_201")
        thread_cls.assert_called_once()
        thread_mock.start.assert_called_once()

    def test_execute_check_run_request_scope_completes(self) -> None:
        service = CheckDispatchService()
        check_run = SimpleNamespace(
            id="cr_001",
            request_id="req_001",
            promotion_id=None,
            scope="request",
            status="queued",
            started_at=None,
            completed_at=None,
            error_message=None,
            enqueued_by="user_demo",
            trigger_reason="submit",
        )
        request_row = SimpleNamespace(id="req_001", tenant_id="tenant_demo")
        session = SimpleNamespace(
            get=lambda model, identifier: check_run if identifier == "cr_001" else request_row,
            flush=lambda: None,
            add=lambda _obj: None,
            commit=Mock(),
            rollback=Mock(),
        )

        class DummySessionContext:
            def __enter__(self_inner):
                return session

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("app.services.check_dispatch_service.SessionLocal", return_value=DummySessionContext()), patch(
            "app.services.check_dispatch_service.policy_check_service.run_request_checks"
        ) as run_checks, patch("app.services.check_dispatch_service.event_store_service.append"):
            service.execute_check_run("cr_001")

        self.assertEqual(check_run.status, "completed")
        self.assertIsNotNone(check_run.started_at)
        self.assertIsNotNone(check_run.completed_at)
        run_checks.assert_called_once()
        session.commit.assert_called_once()

    def test_execute_check_run_failure_marks_failed(self) -> None:
        service = CheckDispatchService()
        check_run = SimpleNamespace(
            id="cr_002",
            request_id="req_001",
            promotion_id=None,
            scope="request",
            status="queued",
            started_at=None,
            completed_at=None,
            error_message=None,
            enqueued_by="user_demo",
            trigger_reason="submit",
        )
        request_row = SimpleNamespace(id="req_001", tenant_id="tenant_demo")
        session = SimpleNamespace(
            get=lambda model, identifier: check_run if identifier == "cr_002" else request_row,
            flush=lambda: None,
            add=lambda _obj: None,
            commit=Mock(),
            rollback=Mock(),
        )

        class DummySessionContext:
            def __enter__(self_inner):
                return session

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch("app.services.check_dispatch_service.SessionLocal", return_value=DummySessionContext()), patch(
            "app.services.check_dispatch_service.policy_check_service.run_request_checks",
            side_effect=RuntimeError("bad check"),
        ), patch("app.services.check_dispatch_service.event_store_service.append"):
            with self.assertRaises(RuntimeError):
                service.execute_check_run("cr_002")

        self.assertEqual(check_run.status, "failed")
        self.assertEqual(check_run.error_message, "bad check")
        session.rollback.assert_called_once()


class EventStoreServiceTest(unittest.TestCase):
    def test_append_adds_event_and_enqueues_publisher(self) -> None:
        service = EventStoreService()
        added: list[object] = []
        session = SimpleNamespace(add=added.append, flush=Mock())
        with patch("app.services.event_store_service.event_publisher_service.enqueue") as enqueue:
            service.append(
                session,
                tenant_id="tenant_demo",
                event_type="request.submitted",
                aggregate_type="request",
                aggregate_id="req_001",
                actor="user_demo",
                detail="submitted",
                request_id="req_001",
                payload={"state": "submitted"},
            )
        self.assertEqual(len(added), 1)
        session.flush.assert_called_once()
        enqueue.assert_called_once()


class PolicyCheckServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PolicyCheckService()

    def test_parse_request_transition_rules_validates_format_targets_and_checks(self) -> None:
        parsed = self.service.parse_request_transition_rules(["validated: Intake Completeness", "awaiting_review: Review Package Readiness", "  "])
        self.assertEqual(parsed, [("validated", "Intake Completeness"), ("awaiting_review", "Review Package Readiness")])

        with self.assertRaises(ValueError):
            self.service.parse_request_transition_rules(["missing colon"])
        with self.assertRaises(ValueError):
            self.service.parse_request_transition_rules(["bad_target: Intake Completeness"])
        with self.assertRaises(ValueError):
            self.service.parse_request_transition_rules(["validated: Unknown Check"])

    def test_active_transition_gates_and_transition_readiness(self) -> None:
        gate = SimpleNamespace(required_check_name="Intake Completeness")
        session = SimpleNamespace(
            scalars=Mock(
                side_effect=[
                    DummyScalarResult(items=[gate]),
                    DummyScalarResult(items=[gate]),
                    DummyScalarResult(items=[SimpleNamespace(name="Intake Completeness", state="passed")]),
                    DummyScalarResult(items=[gate]),
                    DummyScalarResult(items=[SimpleNamespace(name="Intake Completeness", state="failed")]),
                ]
            )
        )

        names = self.service.active_transition_gate_check_names(session, RequestStatus.VALIDATED, "tenant_demo")
        self.assertEqual(names, {"Intake Completeness"})
        self.service.assert_request_transition_ready(session, "req_001", RequestStatus.VALIDATED, "tenant_demo")
        with self.assertRaises(ValueError):
            self.service.assert_request_transition_ready(session, "req_001", RequestStatus.VALIDATED, "tenant_demo")

    def test_ensure_request_and_promotion_check_records_create_missing_rows(self) -> None:
        added: list[object] = []
        session = SimpleNamespace(
            scalars=Mock(side_effect=[DummyScalarResult(items=[]), DummyScalarResult(items=[])]),
            add=added.append,
            flush=Mock(),
        )
        request_row = SimpleNamespace(id="req_001")
        promotion_row = SimpleNamespace(id="pro_001", request_id="req_001")

        self.service.ensure_request_check_records(session, request_row, "user_demo")
        self.service.ensure_promotion_check_records(session, promotion_row, "user_demo")

        self.assertEqual(len(added), len(self.service.REQUEST_CHECK_DEFINITIONS) + len(self.service.PROMOTION_CHECK_DEFINITIONS))
        session.flush.assert_called()

    def test_run_request_checks_updates_states_for_ready_and_missing_inputs(self) -> None:
        ready_checks = [
            SimpleNamespace(name="Intake Completeness", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
            SimpleNamespace(name="Review Package Readiness", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
            SimpleNamespace(name="Approval Freshness", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
        ]
        artifact = SimpleNamespace(id="art_001", stale_review=False)
        review = SimpleNamespace(id="rev_001", blocking_status="Approved")
        session = SimpleNamespace(
            scalars=Mock(
                side_effect=[
                    DummyScalarResult(first=artifact),
                    DummyScalarResult(first=review),
                    DummyScalarResult(items=ready_checks),
                ]
            )
        )

        with patch.object(PolicyCheckService, "ensure_request_check_records"):
            self.service.run_request_checks(session, SimpleNamespace(id="req_001", title="Title", summary="Summary", template_id="tmpl_001"), "user_demo")

        self.assertEqual([check.state for check in ready_checks], ["passed", "passed", "passed"])

        missing_checks = [
            SimpleNamespace(name="Intake Completeness", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
            SimpleNamespace(name="Review Package Readiness", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
            SimpleNamespace(name="Approval Freshness", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
        ]
        missing_session = SimpleNamespace(
            scalars=Mock(
                side_effect=[
                    DummyScalarResult(first=None),
                    DummyScalarResult(first=None),
                    DummyScalarResult(items=missing_checks),
                ]
            )
        )

        with patch.object(PolicyCheckService, "ensure_request_check_records"):
            self.service.run_request_checks(missing_session, SimpleNamespace(id="req_001", title=" ", summary="", template_id=""), "user_demo")

        self.assertEqual([check.state for check in missing_checks], ["failed", "pending", "pending"])

    def test_sync_promotion_and_readiness_helpers(self) -> None:
        check_rows = [
            SimpleNamespace(id="chk_1", name="Policy Bundle", state="passed", detail="ok"),
            SimpleNamespace(id="chk_2", name="Approval Freshness", state="pending", detail="wait"),
        ]
        override_rows = [SimpleNamespace(check_result_id="chk_2", state="approved")]
        promotion_row = SimpleNamespace(id="pro_001", required_checks=[])
        session = SimpleNamespace(
            scalars=Mock(side_effect=[DummyScalarResult(items=check_rows), DummyScalarResult(items=override_rows)])
        )

        self.service.sync_promotion_checks(session, promotion_row)
        self.assertEqual(len(promotion_row.required_checks), 2)
        self.assertTrue(self.service.promotion_ready(check_rows, override_rows, [{"state": "approved"}]))
        self.assertEqual(self.service.promotion_readiness(check_rows, override_rows, [{"state": "approved"}]), "Approved for promotion execution.")
        self.assertIn("Blocked until", self.service.promotion_readiness(check_rows, [], [{"state": "pending"}]))

    def test_promotion_readiness_from_db_and_run_promotion_checks(self) -> None:
        promotion_checks = [
            SimpleNamespace(id="chk_1", name="Policy Bundle", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
            SimpleNamespace(id="chk_2", name="Approval Freshness", state="pending", detail="", evidence="", evaluated_at=None, evaluated_by=None),
        ]
        promotion_row = SimpleNamespace(id="pro_001", request_id="req_001", required_approvals=[{"state": "approved"}], promotion_history=[])
        request_row = SimpleNamespace(id="req_001", policy_context={"policy_bundle_passed": False})
        artifact = SimpleNamespace(stale_review=True)
        review = SimpleNamespace(blocking_status="Pending")
        session = SimpleNamespace(
            scalars=Mock(
                side_effect=[
                    DummyScalarResult(items=promotion_checks),
                    DummyScalarResult(items=[]),
                    DummyScalarResult(first=artifact),
                    DummyScalarResult(first=review),
                    DummyScalarResult(items=promotion_checks),
                ]
            )
        )

        with patch.object(PolicyCheckService, "ensure_promotion_check_records"), patch.object(PolicyCheckService, "sync_promotion_checks") as sync_checks:
            self.service.run_promotion_checks(session, request_row, promotion_row, "user_demo")

        self.assertEqual([check.state for check in promotion_checks], ["pending", "pending"])
        sync_checks.assert_called_once()

        readiness = self.service.promotion_readiness_from_db(
            SimpleNamespace(scalars=Mock(side_effect=[DummyScalarResult(items=promotion_checks), DummyScalarResult(items=[])])),
            promotion_row,
        )
        self.assertIn("Blocked until", readiness)


class EventPublisherAdditionalTest(unittest.TestCase):
    def test_enqueue_adds_outbox_row_and_partition_key_fallback(self) -> None:
        service = EventPublisherService()
        event_row = SimpleNamespace(
            id=12,
            event_type="request.submitted",
            aggregate_type="request",
            aggregate_id="req_001",
            tenant_id="tenant_demo",
            request_id="req_001",
            run_id=None,
            artifact_id=None,
            promotion_id=None,
            check_run_id=None,
            actor="user_demo",
            detail="submitted",
            payload={"state": "submitted"},
            occurred_at=SimpleNamespace(isoformat=lambda: "2026-04-02T00:00:00+00:00"),
        )
        added = []
        session = SimpleNamespace(get=lambda _model, _id: event_row, add=added.append)
        with patch("app.services.event_publisher_service.settings.event_bus_backend", "http"), patch(
            "app.services.event_publisher_service.settings.event_bus_topic_prefix",
            "rgp",
        ):
            service.enqueue(session, 12)
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0].topic, "rgp.request")
        self.assertEqual(added[0].partition_key, "req_001")

    def test_enqueue_missing_event_raises_and_publish_row_backend_errors(self) -> None:
        service = EventPublisherService()
        session = SimpleNamespace(get=lambda _model, _id: None)
        with self.assertRaises(StopIteration):
            service.enqueue(session, 99)

        with patch("app.services.event_publisher_service.settings.event_bus_backend", "unsupported"):
            with self.assertRaises(ValueError):
                service._publish_row(SimpleNamespace())

    def test_publish_http_validates_endpoint_and_status_code(self) -> None:
        row = SimpleNamespace(topic="rgp.request", event_store_id=12, partition_key="req_001", payload={})
        with patch("app.services.event_publisher_service.settings.event_bus_http_endpoint", ""):
            with self.assertRaises(ValueError):
                EventPublisherService._publish_http(row)

        with patch("app.services.event_publisher_service.settings.event_bus_http_endpoint", "http://127.0.0.1:8001/mock"), patch(
            "app.services.event_publisher_service.urllib_request.urlopen",
            return_value=DummyResponse(status_code=500),
        ):
            with self.assertRaises(RuntimeError):
                EventPublisherService._publish_http(row)


class PerformanceMetricsServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PerformanceMetricsService()
        self.rows = [
            SimpleNamespace(
                id=1,
                route="/api/v1/requests",
                method="GET",
                status_code=200,
                duration_ms=120.0,
                trace_id="trace-1",
                span_id="span-1",
                correlation_id="corr-1",
                occurred_at=SimpleNamespace(astimezone=lambda _tz: SimpleNamespace(strftime=lambda _fmt: "2026-04-02"), isoformat=lambda: "2026-04-02T00:00:00+00:00"),
            ),
            SimpleNamespace(
                id=2,
                route="/api/v1/requests",
                method="GET",
                status_code=503,
                duration_ms=240.0,
                trace_id="trace-2",
                span_id="span-2",
                correlation_id="corr-2",
                occurred_at=SimpleNamespace(astimezone=lambda _tz: SimpleNamespace(strftime=lambda _fmt: "2026-04-02"), isoformat=lambda: "2026-04-02T01:00:00+00:00"),
            ),
            SimpleNamespace(
                id=3,
                route="/api/v1/reviews",
                method="POST",
                status_code=200,
                duration_ms=80.0,
                trace_id="trace-3",
                span_id="span-3",
                correlation_id="corr-3",
                occurred_at=SimpleNamespace(astimezone=lambda _tz: SimpleNamespace(strftime=lambda _fmt: "2026-04-01"), isoformat=lambda: "2026-04-01T01:00:00+00:00"),
            ),
        ]

    def test_route_summaries_group_request_metrics(self) -> None:
        with patch.object(self.service, "_load_api_rows", return_value=self.rows):
            result = self.service.list_route_summaries(tenant_id="tenant_demo", days=30, page=1, page_size=10)

        request_summary = next(item for item in result.items if item.route == "/api/v1/requests")
        self.assertEqual(request_summary.request_count, 2)
        self.assertEqual(request_summary.error_rate, "50.0%")
        self.assertEqual(request_summary.avg_duration_ms, 180.0)

    def test_slo_summaries_classify_breached_routes(self) -> None:
        with patch.object(self.service, "_load_api_rows", return_value=self.rows):
            result = self.service.list_slo_summaries(tenant_id="tenant_demo", days=30, page=1, page_size=10)

        request_slo = next(item for item in result.items if item.route == "/api/v1/requests")
        self.assertEqual(request_slo.status, "breached")
        self.assertEqual(request_slo.availability_actual, "50.00%")

    def test_raw_metrics_filters_route_and_method(self) -> None:
        with patch.object(self.service, "_load_api_rows", return_value=self.rows):
            result = self.service.list_raw_metrics(
                tenant_id="tenant_demo",
                days=30,
                page=1,
                page_size=10,
                route="/api/v1/reviews",
                method="POST",
            )

        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].route, "/api/v1/reviews")

    def test_route_trends_group_by_day_route_and_method(self) -> None:
        with patch.object(self.service, "_load_api_rows", return_value=self.rows):
            result = self.service.list_route_trends(tenant_id="tenant_demo", days=30, page=1, page_size=10)

        request_trend = next(item for item in result.items if item.route == "/api/v1/requests")
        self.assertEqual(request_trend.period_start, "2026-04-02")
        self.assertEqual(request_trend.request_count, 2)


class IntegrationSecurityServiceTest(unittest.TestCase):
    def test_prepare_and_sanitize_settings_masks_secrets(self) -> None:
        stored = integration_security_service.prepare_settings_for_storage(
            None,
            {
                "provider": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": "secret-key",
                "access_token": "oauth-token",
            },
        )
        self.assertTrue(str(stored["api_key"]).startswith("enc:"))
        self.assertTrue(str(stored["access_token"]).startswith("enc:"))
        self.assertEqual(integration_security_service.decrypt_secret(stored["api_key"]), "secret-key")
        self.assertEqual(integration_security_service.decrypt_secret(stored["access_token"]), "oauth-token")

        sanitized = integration_security_service.sanitize_settings_for_response(stored)
        self.assertNotIn("api_key", sanitized)
        self.assertNotIn("access_token", sanitized)
        self.assertTrue(integration_security_service.has_secret(stored, "api_key"))
        self.assertTrue(integration_security_service.has_secret(stored, "access_token"))

    def test_prepare_settings_preserves_existing_secrets_and_supports_clear(self) -> None:
        existing = integration_security_service.prepare_settings_for_storage(None, {"api_key": "old", "access_token": "token"})
        updated = integration_security_service.prepare_settings_for_storage(existing, {"provider": "openai"})
        self.assertEqual(integration_security_service.decrypt_secret(updated["api_key"]), "old")
        self.assertEqual(integration_security_service.decrypt_secret(updated["access_token"]), "token")

        cleared = integration_security_service.prepare_settings_for_storage(
            updated,
            {"provider": "openai"},
            clear_api_key=True,
            clear_access_token=True,
        )
        self.assertNotIn("api_key", cleared)
        self.assertNotIn("access_token", cleared)

    def test_validate_outbound_target_rejects_non_allowlisted_or_plain_http(self) -> None:
        self.assertEqual(
            integration_security_service.validate_outbound_target(
                "https://api.openai.com/v1",
                allowed_hosts=["api.openai.com"],
                allow_http_loopback=True,
            ),
            "https://api.openai.com/v1",
        )
        with self.assertRaisesRegex(ValueError, "allowlist"):
            integration_security_service.validate_outbound_target(
                "https://evil.example.com/v1",
                allowed_hosts=["api.openai.com"],
                allow_http_loopback=True,
            )
        with self.assertRaisesRegex(ValueError, "Plain HTTP"):
            integration_security_service.validate_outbound_target(
                "http://api.openai.com/v1",
                allowed_hosts=["api.openai.com"],
                allow_http_loopback=True,
            )


class RuntimeAndDeploymentSecurityTest(unittest.TestCase):
    def test_runtime_dispatch_rejects_unapproved_host(self) -> None:
        service = RuntimeDispatchService()
        integration = SimpleNamespace(endpoint="https://evil.example.com/hook", settings={})
        with self.assertRaisesRegex(ValueError, "allowlist"):
            service.resolve_endpoint(integration)

    def test_deployment_dispatch_rejects_unapproved_host(self) -> None:
        service = DeploymentService()
        integration = SimpleNamespace(endpoint="https://evil.example.com/hook", settings={})
        with self.assertRaisesRegex(ValueError, "allowlist"):
            service.resolve_endpoint(integration)


if __name__ == "__main__":
    unittest.main()
