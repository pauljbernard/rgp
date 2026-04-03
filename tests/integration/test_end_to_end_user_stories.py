import json
import os
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4


API_BASE = os.environ.get("RGP_API_BASE", "http://127.0.0.1:8001")
TOKEN_PATH = Path("/tmp/rgp-token.txt")


class ApiError(AssertionError):
    def __init__(self, status: int, payload, path: str) -> None:
        self.status = status
        self.payload = payload
        self.path = path
        super().__init__(f"{status} for {path}: {payload}")


class EndToEndUserStoriesTest(unittest.TestCase):
    token: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.token = cls._issue_dev_token()
        TOKEN_PATH.write_text(cls.token, encoding="utf-8")
        health = cls._request("GET", "/healthz", token=None)
        cls._assert_equal(health["status"], "ok")

    @staticmethod
    def _assert_equal(left, right, message: str | None = None) -> None:
        if left != right:
            raise AssertionError(message or f"Expected {right!r}, got {left!r}")

    @classmethod
    def _issue_dev_token(cls) -> str:
        response = cls._request(
            "POST",
            "/api/v1/auth/dev-token",
            token=None,
            body={
                "user_id": "user_demo",
                "tenant_id": "tenant_demo",
                "roles": ["admin", "operator", "reviewer", "submitter"],
                "expires_in_seconds": 3600,
            },
            expected_statuses={201},
        )
        return response["access_token"]

    @classmethod
    def _request(
        cls,
        method: str,
        path: str,
        *,
        token: str | None = None,
        body: dict | list | None = None,
        query: dict[str, str | int | None] | None = None,
        expected_statuses: set[int] | None = None,
    ):
        expected_statuses = expected_statuses or {200}
        url = f"{API_BASE}{path}"
        if query:
            filtered = {key: value for key, value in query.items() if value is not None}
            if filtered:
                url = f"{url}?{urllib.parse.urlencode(filtered)}"
        data = None
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read().decode("utf-8")
                if response.status not in expected_statuses:
                    raise ApiError(response.status, payload, path)
                if not payload:
                    return None
                return json.loads(payload)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                payload = raw
            if exc.code in expected_statuses:
                return payload
            raise ApiError(exc.code, payload, path) from exc

    @classmethod
    def _request_with_status(
        cls,
        method: str,
        path: str,
        *,
        token: str | None = None,
        body: dict | list | None = None,
        query: dict[str, str | int | None] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> tuple[int, object]:
        expected_statuses = expected_statuses or {200}
        url = f"{API_BASE}{path}"
        if query:
            filtered = {key: value for key, value in query.items() if value is not None}
            if filtered:
                url = f"{url}?{urllib.parse.urlencode(filtered)}"
        data = None
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read().decode("utf-8")
                parsed = json.loads(payload) if payload else None
                if response.status not in expected_statuses:
                    raise ApiError(response.status, parsed, path)
                return response.status, parsed
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                payload = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                payload = raw
            if exc.code not in expected_statuses:
                raise ApiError(exc.code, payload, path) from exc
            return exc.code, payload

    def _suffix(self) -> str:
        return uuid4().hex[:8]

    def _poll(self, fn, predicate, *, timeout: float = 30.0, interval: float = 1.0, message: str = "Poll timed out"):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            last = fn()
            if predicate(last):
                return last
            time.sleep(interval)
        raise AssertionError(f"{message}. Last value: {last}")

    def _create_request(self, title: str, assessment_id: str) -> dict:
        return self._request(
            "POST",
            "/api/v1/requests",
            token=self.token,
            body={
                "template_id": "tmpl_assessment",
                "template_version": "1.4.0",
                "title": title,
                "summary": "Automated end-to-end validation request.",
                "priority": "medium",
                "input_payload": {
                    "assessment_id": assessment_id,
                    "revision_reason": "Standards alignment",
                    "target_window": "Spring 2026",
                },
            },
            expected_statuses={201},
        )

    def _get_request_detail(self, request_id: str) -> dict:
        return self._request("GET", f"/api/v1/requests/{request_id}", token=self.token)

    def _submit_request(self, request_id: str) -> dict:
        return self._request(
            "POST",
            f"/api/v1/requests/{request_id}/submit",
            token=self.token,
            body={},
        )

    def _transition_request(self, request_id: str, target_status: str) -> dict:
        while True:
            status, payload = self._request_with_status(
                "POST",
                f"/api/v1/requests/{request_id}/transition",
                token=self.token,
                body={"target_status": target_status},
                expected_statuses={200, 409},
            )
            if status == 200:
                return payload
            message = self._error_message(payload)
            if "queued or running" in message or "Automated evaluation queued" in message:
                time.sleep(1)
                continue
            raise AssertionError(f"Transition to {target_status} failed: {message}")

    def _wait_for_agent_response(self, request_id: str, session_id: str) -> dict:
        return self._poll(
            lambda: self._request("GET", f"/api/v1/requests/{request_id}/agent-sessions/{session_id}", token=self.token),
            lambda payload: payload["status"] == "waiting_on_human" and bool(payload["messages"][-1]["body"]),
            timeout=60,
            interval=1,
            message=f"Agent session {session_id} did not reach waiting_on_human",
        )

    def _lookup_promotion_id(self, request_id: str) -> str:
        detail = self._get_request_detail(request_id)
        for check_run in detail["check_runs"]:
            if check_run.get("promotion_id"):
                return str(check_run["promotion_id"])
        raise AssertionError(f"No promotion found for {request_id}")

    def _execute_promotion(self, promotion_id: str) -> dict:
        while True:
            status, payload = self._request_with_status(
                "POST",
                f"/api/v1/promotions/{promotion_id}/actions",
                token=self.token,
                body={"action": "execute"},
                expected_statuses={200, 409},
            )
            if status == 200:
                return payload
            message = self._error_message(payload)
            if "queued or running" in message:
                time.sleep(1)
                continue
            raise AssertionError(f"Promotion execute failed: {message}")

    @staticmethod
    def _error_message(payload) -> str:
        if isinstance(payload, dict):
            if isinstance(payload.get("error"), dict):
                return str(payload["error"].get("message", ""))
            if "detail" in payload:
                return str(payload["detail"])
        return str(payload)

    def test_story_01_template_authoring_lifecycle(self) -> None:
        suffix = self._suffix()
        template_id = f"tmpl_e2e_{suffix}"
        version = "0.1.0"

        created = self._request(
            "POST",
            "/api/v1/admin/templates/versions",
            token=self.token,
            body={
                "template_id": template_id,
                "version": version,
                "name": f"E2E Template {suffix}",
                "description": "End-to-end authored template.",
            },
            expected_statuses={201},
        )
        self._assert_equal(created["status"], "draft")

        updated = self._request(
            "PUT",
            f"/api/v1/admin/templates/{template_id}/versions/{version}",
            token=self.token,
            body={
                "name": f"E2E Template {suffix}",
                "description": "Validated and published via integration test.",
                "schema": {
                    "required": ["ticket_id"],
                    "routing": {
                        "owner_team": "team_assessment_quality",
                        "workflow_binding": "wf_assessment_revision_v1",
                        "reviewers": ["reviewer_liam"],
                        "promotion_approvers": ["ops_isaac"],
                    },
                    "properties": {
                        "ticket_id": {"type": "string", "title": "Ticket ID", "min_length": 4},
                        "context": {"type": "string", "title": "Context", "default": "Default context"},
                    },
                },
            },
        )
        self._assert_equal(updated["status"], "draft")

        validation = self._request(
            "POST",
            f"/api/v1/admin/templates/{template_id}/versions/{version}/validate",
            token=self.token,
        )
        self._assert_equal(validation["valid"], True)
        self.assertGreaterEqual(validation["preview"]["field_count"], 1)

        published = self._request(
            "POST",
            f"/api/v1/admin/templates/{template_id}/versions/{version}/publish",
            token=self.token,
            body={"note": "publish for e2e"},
        )
        self._assert_equal(published["status"], "published")

        public_templates = self._request("GET", "/api/v1/templates", token=self.token)
        self.assertTrue(any(row["id"] == template_id and row["version"] == version for row in public_templates))

        draft_v2 = self._request(
            "POST",
            "/api/v1/admin/templates/versions",
            token=self.token,
            body={
                "template_id": template_id,
                "version": "0.1.1",
                "source_version": version,
                "name": f"E2E Template {suffix}",
                "description": "Successor draft",
            },
            expected_statuses={201},
        )
        self._assert_equal(draft_v2["status"], "draft")
        self._request(
            "DELETE",
            f"/api/v1/admin/templates/{template_id}/versions/0.1.1",
            token=self.token,
            expected_statuses={204},
        )
        admin_templates = self._request("GET", "/api/v1/admin/templates", token=self.token)
        self.assertFalse(any(row["id"] == template_id and row["version"] == "0.1.1" for row in admin_templates))

    def test_story_02_org_and_integration_administration(self) -> None:
        suffix = self._suffix()
        user_id = f"user_e2e_{suffix}"
        team_id = f"team_e2e_{suffix}"
        portfolio_id = f"port_e2e_{suffix}"
        integration_id = f"int_e2e_{suffix}"

        created_user = self._request(
            "POST",
            "/api/v1/admin/org/users",
            token=self.token,
            body={
                "id": user_id,
                "display_name": f"E2E User {suffix}",
                "email": f"{user_id}@example.test",
                "role_summary": ["submitter", "reviewer"],
            },
            expected_statuses={201},
        )
        self._assert_equal(created_user["id"], user_id)

        updated_user = self._request(
            "PUT",
            f"/api/v1/admin/org/users/{user_id}",
            token=self.token,
            body={
                "display_name": f"E2E User {suffix} Updated",
                "email": f"{user_id}@example.test",
                "role_summary": ["submitter", "reviewer", "operator"],
                "status": "active",
            },
        )
        self.assertIn("operator", updated_user["role_summary"])

        created_team = self._request(
            "POST",
            "/api/v1/admin/org/teams",
            token=self.token,
            body={"id": team_id, "name": f"E2E Team {suffix}", "kind": "delivery"},
            expected_statuses={201},
        )
        self._assert_equal(created_team["id"], team_id)

        updated_team = self._request(
            "PUT",
            f"/api/v1/admin/org/teams/{team_id}",
            token=self.token,
            body={"name": f"E2E Team {suffix} Updated", "kind": "delivery", "status": "active"},
        )
        self.assertTrue(updated_team["name"].endswith("Updated"))

        team_with_member = self._request(
            "POST",
            "/api/v1/admin/org/team-memberships",
            token=self.token,
            body={"team_id": team_id, "user_id": user_id, "role": "lead"},
        )
        self.assertTrue(any(member["user_id"] == user_id for member in team_with_member["members"]))

        created_portfolio = self._request(
            "POST",
            "/api/v1/admin/org/portfolios",
            token=self.token,
            body={"id": portfolio_id, "name": f"E2E Portfolio {suffix}", "owner_team_id": team_id, "scope_keys": [team_id]},
            expected_statuses={201},
        )
        self._assert_equal(created_portfolio["id"], portfolio_id)

        teams = self._request("GET", "/api/v1/org/teams", token=self.token)
        self.assertTrue(any(team["id"] == team_id and team["member_count"] >= 1 for team in teams))

        integration = self._request(
            "POST",
            "/api/v1/admin/integrations",
            token=self.token,
            body={
                "id": integration_id,
                "name": f"E2E Integration {suffix}",
                "type": "agent_runtime",
                "endpoint": "https://example.test/agent",
                "settings": {"provider": "openai", "base_url": "https://api.openai.com/v1", "model": "gpt-5.4"},
            },
            expected_statuses={201},
        )
        self._assert_equal(integration["id"], integration_id)

        updated_integration = self._request(
            "PUT",
            f"/api/v1/admin/integrations/{integration_id}",
            token=self.token,
            body={
                "name": f"E2E Integration {suffix} Updated",
                "type": "agent_runtime",
                "status": "connected",
                "endpoint": "https://example.test/agent/v2",
                "settings": {"provider": "openai", "base_url": "https://api.openai.com/v1", "model": "gpt-5.4", "workspace_id": "ws-e2e"},
            },
        )
        self._assert_equal(updated_integration["settings"]["workspace_id"], "ws-e2e")
        self._request("DELETE", f"/api/v1/admin/integrations/{integration_id}", token=self.token, expected_statuses={204})
        integrations = self._request("GET", "/api/v1/admin/integrations", token=self.token)
        self.assertFalse(any(item["id"] == integration_id for item in integrations))

    def test_story_03_request_mutation_controls(self) -> None:
        suffix = self._suffix()
        request = self._create_request(f"Mutation Story {suffix}", f"asm_mutation_{suffix}")
        request_id = request["id"]
        self._submit_request(request_id)
        self._transition_request(request_id, "validated")

        amended = self._request(
            "POST",
            f"/api/v1/requests/{request_id}/amend",
            token=self.token,
            body={"title": f"Mutation Story {suffix} Amended", "reason": "Refine intake before proceeding"},
        )
        self._assert_equal(amended["status"], "draft")

        self._submit_request(request_id)
        cloned = self._request(
            "POST",
            f"/api/v1/requests/{request_id}/clone",
            token=self.token,
            body={"title": f"Clone {suffix}", "reason": "Create successor draft"},
            expected_statuses={201},
        )
        clone_id = cloned["id"]
        self.assertNotEqual(clone_id, request_id)

        canceled_clone = self._request(
            "POST",
            f"/api/v1/requests/{clone_id}/cancel",
            token=self.token,
            body={"reason": "Cancel cloned draft"},
        )
        self._assert_equal(canceled_clone["status"], "canceled")

        successor = self._request(
            "POST",
            f"/api/v1/requests/{request_id}/clone",
            token=self.token,
            body={"title": f"Replacement {suffix}", "reason": "Create replacement request"},
            expected_statuses={201},
        )
        replacement_id = successor["id"]
        superseded = self._request(
            "POST",
            f"/api/v1/requests/{request_id}/supersede",
            token=self.token,
            body={"replacement_request_id": replacement_id, "reason": "Superseded in e2e flow"},
        )
        self._assert_equal(superseded["status"], "archived")

        history = self._request("GET", f"/api/v1/requests/{request_id}/history", token=self.token)
        actions = {entry["action"] for entry in history}
        self.assertTrue({"Submitted", "Amended", "Cloned", "Superseded"}.issubset(actions))

        detail = self._get_request_detail(request_id)
        successor_ids = {row["request_id"] for row in detail["successors"]}
        self.assertIn(replacement_id, successor_ids)

    def test_story_04_agent_assisted_governed_request(self) -> None:
        suffix = self._suffix()
        request = self._create_request(f"Agent Story {suffix}", f"asm_agent_{suffix}")
        request_id = request["id"]
        self._submit_request(request_id)

        session = self._request(
            "POST",
            f"/api/v1/requests/{request_id}/agent-sessions",
            token=self.token,
            body={
                "integration_id": "int_agent_codex",
                "initial_prompt": "Provide a concise revision plan with one summary, two changes, and one reviewer risk.",
            },
            expected_statuses={201},
        )
        session_id = session["id"]
        first_turn = self._wait_for_agent_response(request_id, session_id)
        first_body = first_turn["messages"][-1]["body"]
        self.assertTrue(first_body)
        self.assertNotIn("received your guidance", first_body.lower())

        self._request(
            "POST",
            f"/api/v1/requests/{request_id}/agent-sessions/{session_id}/messages",
            token=self.token,
            body={"body": "Rewrite it as exactly three bullets, under 12 words each."},
        )
        second_turn = self._wait_for_agent_response(request_id, session_id)
        second_body = second_turn["messages"][-1]["body"]
        self.assertTrue(second_body.startswith("-"))

        completed_session = self._request(
            "POST",
            f"/api/v1/requests/{request_id}/agent-sessions/{session_id}/complete",
            token=self.token,
            body={},
        )
        self._assert_equal(completed_session["status"], "completed")

        resumed_request = self._get_request_detail(request_id)
        self._assert_equal(resumed_request["request"]["status"], "submitted")

    def test_story_05_review_promotion_and_completion(self) -> None:
        suffix = self._suffix()
        request = self._create_request(f"Lifecycle Story {suffix}", f"asm_lifecycle_{suffix}")
        request_id = request["id"]
        self._submit_request(request_id)

        for target in ["validated", "classified", "ownership_resolved", "planned", "queued", "in_execution", "awaiting_review"]:
            self._transition_request(request_id, target)

        self._poll(
            lambda: self._get_request_detail(request_id),
            lambda payload: not any("Checks queued" in blocker for blocker in payload["active_blockers"]),
            timeout=30,
            interval=1,
            message="Review-entry checks did not clear",
        )

        review_queue = self._request(
            "GET",
            "/api/v1/reviews/queue",
            token=self.token,
            query={"request_id": request_id},
        )
        review_id = review_queue["items"][0]["id"]
        review_result = self._request(
            "POST",
            f"/api/v1/reviews/queue/{review_id}/decision",
            token=self.token,
            body={"decision": "approve"},
        )
        self._assert_equal(review_result["blocking_status"], "Approved")

        self._transition_request(request_id, "promotion_pending")
        promotion_id = self._lookup_promotion_id(request_id)

        self._poll(
            lambda: self._request("GET", f"/api/v1/promotions/{promotion_id}", token=self.token),
            lambda payload: "queued" not in str(payload["execution_readiness"]).lower(),
            timeout=30,
            interval=1,
            message="Promotion checks did not settle",
        )

        authorized = self._request(
            "POST",
            f"/api/v1/promotions/{promotion_id}/actions",
            token=self.token,
            body={"action": "authorize"},
        )
        self.assertTrue(all(item["state"] == "approved" for item in authorized["required_approvals"]))

        executed = self._execute_promotion(promotion_id)
        self.assertGreaterEqual(len(executed["deployment_executions"]), 1)

        completed = self._request(
            "POST",
            f"/api/v1/requests/{request_id}/transition",
            token=self.token,
            body={"target_status": "completed"},
        )
        self._assert_equal(completed["status"], "completed")

        detail = self._get_request_detail(request_id)
        self._assert_equal(detail["request"]["status"], "completed")
        self.assertEqual(detail["active_blockers"], [])

    def test_story_06_events_analytics_and_observability(self) -> None:
        ledger = self._request("GET", "/api/v1/events/ledger", token=self.token, query={"page_size": 10})
        self.assertGreaterEqual(ledger["total_count"], 1)
        self.assertIn("event_type", ledger["items"][0])

        outbox = self._request("GET", "/api/v1/events/outbox", token=self.token, query={"page_size": 10})
        self.assertGreaterEqual(outbox["total_count"], 1)
        self.assertIn("topic", outbox["items"][0])

        users = self._request("GET", "/api/v1/org/users", token=self.token)
        teams = self._request("GET", "/api/v1/org/teams", token=self.token)
        portfolios = self._request("GET", "/api/v1/org/portfolio-summaries", token=self.token)
        self.assertGreaterEqual(len(users), 1)
        self.assertGreaterEqual(len(teams), 1)
        self.assertGreaterEqual(len(portfolios), 1)

        dora = self._request("GET", "/api/v1/analytics/delivery/dora", token=self.token)
        lifecycle = self._request("GET", "/api/v1/analytics/delivery/lifecycle", token=self.token)
        trends = self._request("GET", "/api/v1/analytics/delivery/trends", token=self.token, query={"days": 30})
        forecast = self._request("GET", "/api/v1/analytics/delivery/forecast", token=self.token, query={"history_days": 30, "forecast_days": 14})
        workflows = self._request("GET", "/api/v1/analytics/workflows", token=self.token, query={"days": 30})
        workflow_trends = self._request("GET", "/api/v1/analytics/workflows/trends", token=self.token, query={"days": 30})
        agents = self._request("GET", "/api/v1/analytics/agents", token=self.token, query={"days": 30})
        agent_trends = self._request("GET", "/api/v1/analytics/agents/trends", token=self.token, query={"days": 30})
        bottlenecks = self._request("GET", "/api/v1/analytics/bottlenecks", token=self.token, query={"days": 30})
        perf_routes = self._request("GET", "/api/v1/analytics/performance/routes", token=self.token, query={"page_size": 10, "days": 30})
        perf_slo = self._request("GET", "/api/v1/analytics/performance/slo", token=self.token, query={"page_size": 10, "days": 30})
        perf_metrics = self._request("GET", "/api/v1/analytics/performance/metrics", token=self.token, query={"page_size": 10, "days": 30})
        perf_trends = self._request("GET", "/api/v1/analytics/performance/trends", token=self.token, query={"page_size": 10, "days": 30})
        perf_ops = self._request("GET", "/api/v1/analytics/performance/operations", token=self.token)
        perf_ops_trends = self._request("GET", "/api/v1/analytics/performance/operations/trends", token=self.token, query={"days": 30})

        self.assertGreaterEqual(len(dora), 1)
        self.assertIn("lead_time_hours", dora[0])
        self.assertGreaterEqual(len(lifecycle), 1)
        self.assertIn("throughput_30d", lifecycle[0])
        self.assertGreaterEqual(len(trends), 1)
        self.assertIn("throughput_count", trends[0])
        self.assertIn("projected_total_throughput", forecast)
        self.assertGreaterEqual(len(workflows), 1)
        self.assertGreaterEqual(len(workflow_trends), 1)
        self.assertGreaterEqual(len(agents), 1)
        self.assertGreaterEqual(len(agent_trends), 1)
        self.assertGreaterEqual(len(bottlenecks), 1)
        self.assertGreaterEqual(perf_routes["total_count"], 1)
        self.assertGreaterEqual(perf_slo["total_count"], 1)
        self.assertGreaterEqual(perf_metrics["total_count"], 1)
        self.assertGreaterEqual(perf_trends["total_count"], 1)
        self.assertIn("queued_checks", perf_ops)
        self.assertGreaterEqual(len(perf_ops_trends), 1)


if __name__ == "__main__":
    unittest.main()
