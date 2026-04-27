import asyncio
import json
import unittest
from unittest.mock import patch

from app.core.auth import get_principal
from app.factory import create_app
from app.models.security import Principal, PrincipalRole
from app.transport import _configure_http_runtime, _register_http_shell


def _principal() -> Principal:
    return Principal(
        user_id="user_demo",
        tenant_id="tenant_demo",
        roles=[PrincipalRole.ADMIN, PrincipalRole.OPERATOR, PrincipalRole.SUBMITTER],
    )


def _observer_principal() -> Principal:
    return Principal(
        user_id="observer_demo",
        tenant_id="tenant_demo",
        roles=[PrincipalRole.OBSERVER],
    )


class ApiFunctionalContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        app = create_app()
        _configure_http_runtime(app)
        _register_http_shell(app)
        app.dependency_overrides[get_principal] = _principal
        self.app = app

    def _request(self, method: str, path: str, payload: dict | None = None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        headers = [(b"host", b"testserver")]
        if payload is not None:
            headers.append((b"content-type", b"application/json"))
            headers.append((b"content-length", str(len(body)).encode("ascii")))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "root_path": "",
        }
        request_sent = False
        events: list[dict] = []

        async def receive():
            nonlocal request_sent
            if request_sent:
                return {"type": "http.disconnect"}
            request_sent = True
            return {"type": "http.request", "body": body, "more_body": False}

        async def send(message):
            events.append(message)

        asyncio.run(self.app(scope, receive, send))

        start = next(event for event in events if event["type"] == "http.response.start")
        chunks = [event.get("body", b"") for event in events if event["type"] == "http.response.body"]
        response_body = b"".join(chunks).decode("utf-8")
        return _AsgiResponse(
            status_code=start["status"],
            headers={key.decode("latin-1"): value.decode("latin-1") for key, value in start["headers"]},
            body=response_body,
        )

    def test_healthcheck_returns_status_and_correlation_id(self) -> None:
        response = self._request("GET", "/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertTrue(response.headers["x-correlation-id"].startswith("corr_"))

    def test_create_request_draft_validation_failure_uses_standard_error_envelope(self) -> None:
        response = self._request(
            "POST",
            "/api/v1/requests",
            {
                "template_id": "tmpl_assessment",
                "template_version": "1.4.0",
                "summary": "Missing title and priority.",
            },
        )

        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "REQUEST_VALIDATION_FAILED")
        self.assertEqual(payload["error"]["message"], "Request payload failed validation.")
        self.assertTrue(any(item["field"] == "title" for item in payload["error"]["details"]))
        self.assertTrue(any(item["field"] == "priority" for item in payload["error"]["details"]))
        self.assertTrue(response.headers["x-correlation-id"].startswith("corr_"))

    def test_create_request_draft_conflict_maps_to_http_error_envelope(self) -> None:
        with patch(
            "app.api.v1.endpoints.requests.idempotency_service.replay_or_execute",
            side_effect=ValueError("Duplicate request draft"),
        ):
            response = self._request(
                "POST",
                "/api/v1/requests",
                {
                    "template_id": "tmpl_assessment",
                    "template_version": "1.4.0",
                    "title": "Assessment Refresh",
                    "summary": "Attempted duplicate request.",
                    "priority": "medium",
                    "input_payload": {"assessment_id": "asm_001"},
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {
                "error": {
                    "code": "CONFLICT",
                    "message": "Duplicate request draft",
                    "details": [],
                    "correlation_id": response.headers["x-correlation-id"],
                    "retryable": False,
                }
            },
        )

    def test_create_request_draft_enforces_role_authorization(self) -> None:
        self.app.dependency_overrides[get_principal] = _observer_principal

        response = self._request(
            "POST",
            "/api/v1/requests",
            {
                "template_id": "tmpl_assessment",
                "template_version": "1.4.0",
                "title": "Assessment Refresh",
                "summary": "Observer should not be able to create drafts.",
                "priority": "medium",
            },
        )

        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "FORBIDDEN")
        self.assertIn("Requires one of roles", payload["error"]["message"])

    def test_submit_request_permission_error_maps_to_forbidden_envelope(self) -> None:
        with patch(
            "app.api.v1.endpoints.requests.idempotency_service.replay_or_execute",
            side_effect=PermissionError("Tenant mismatch"),
        ):
            response = self._request(
                "POST",
                "/api/v1/requests/req_001/submit",
                {
                    "reason": "Submit the request"
                },
            )

        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "FORBIDDEN")
        self.assertEqual(payload["error"]["message"], "Tenant mismatch")
        self.assertTrue(response.headers["x-correlation-id"].startswith("corr_"))
        self.assertEqual(payload["error"]["details"], [])

    def test_routing_recommendation_composes_queue_sla_and_escalations(self) -> None:
        with patch(
            "app.api.v1.endpoints.queue_routing.queue_routing_service.recommend_assignment",
            return_value={
                "request_id": "req_001",
                "recommended_group_id": "ag_001",
                "recommended_group_name": "Assessment Reviewers",
                "recommended_node_id": "node_001",
                "recommended_node_name": "Trusted Employee Node",
                "recommended_node_employment_model": "employee",
                "recommended_node_trust_tier": "trusted",
                "recommended_node_billing_profile": "organization_funded",
                "recommended_node_readiness_state": "ready",
                "recommended_node_drain_state": "active",
                "matched_skills": ["review"],
                "route_basis": ["skill overlap: review"],
                "current_load": 2,
                "max_capacity": 6,
                "fleet_basis": ["preferred ready employee-capable node pool"],
            },
        ), patch(
            "app.api.v1.endpoints.queue_routing.sla_enforcement_service.evaluate_sla_compliance",
            return_value={"status": "yellow"},
        ), patch(
            "app.api.v1.endpoints.queue_routing.queue_routing_service.evaluate_escalations",
            return_value=[
                {"id": "er_001", "escalation_target": "queue_lead"},
                {"id": "er_002", "escalation_target": "ops_manager"},
            ],
        ):
            response = self._request("GET", "/api/v1/queue-routing/requests/req_001/recommendation")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["recommended_group_name"], "Assessment Reviewers")
        self.assertEqual(payload["recommended_node_name"], "Trusted Employee Node")
        self.assertEqual(payload["sla_status"], "yellow")
        self.assertEqual(payload["escalation_targets"], ["queue_lead", "ops_manager"])

    def test_missing_routing_recommendation_request_returns_not_found_envelope(self) -> None:
        with patch(
            "app.api.v1.endpoints.queue_routing.queue_routing_service.recommend_assignment",
            side_effect=StopIteration("req_missing"),
        ):
            response = self._request("GET", "/api/v1/queue-routing/requests/req_missing/recommendation")

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "NOT_FOUND")
        self.assertEqual(payload["error"]["message"], "Request not found")

    def test_list_sla_breaches_maps_missing_request_to_not_found_envelope(self) -> None:
        with patch(
            "app.api.v1.endpoints.queue_routing.sla_enforcement_service.list_breaches",
            side_effect=StopIteration("req_missing"),
        ):
            response = self._request("GET", "/api/v1/queue-routing/sla-breaches")

        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "NOT_FOUND")
        self.assertEqual(payload["error"]["message"], "Request not found")

class _AsgiResponse:
    def __init__(self, *, status_code: int, headers: dict[str, str], body: str) -> None:
        self.status_code = status_code
        self.headers = headers
        self.body = body

    def json(self):
        return json.loads(self.body)


if __name__ == "__main__":
    unittest.main()
