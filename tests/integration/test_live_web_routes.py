import json
import os
import unittest
import urllib.request


API_BASE = os.environ.get("RGP_API_BASE", "http://127.0.0.1:8001")
WEB_BASE = os.environ.get("RGP_WEB_BASE", "http://127.0.0.1:3000")


class LiveWebRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.admin_token = cls._issue_dev_token(["admin", "operator", "reviewer", "submitter"])
        cls.reviewer_token = cls._issue_dev_token(["reviewer", "submitter"])
        cls._api_post(
            "/api/v1/admin/integrations/int_agent_codex/projections",
            {"entity_type": "request", "entity_id": "req_022"},
        )
        projections = cls._api_get("/api/v1/admin/integrations/int_agent_codex/projections")
        projection = next((row for row in projections if row["entity_id"] == "req_022"), None)
        if projection is not None:
            cls._api_post(f"/api/v1/admin/projections/{projection['id']}/external-state", {
                "external_status": "external_review",
                "external_title": "Externally Revised Request",
            })

    @classmethod
    def _issue_dev_token(cls, roles: list[str]) -> str:
        request = urllib.request.Request(
            f"{API_BASE}/api/v1/auth/dev-token",
            data=json.dumps(
                {
                    "user_id": "user_demo",
                    "tenant_id": "tenant_demo",
                    "roles": roles,
                    "expires_in_seconds": 3600,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["access_token"]

    @classmethod
    def _get_web_html(cls, path: str) -> str:
        return cls._get_web_html_with_token(path, cls.admin_token)

    @classmethod
    def _get_web_html_with_token(cls, path: str, token: str) -> str:
        request = urllib.request.Request(
            f"{WEB_BASE}{path}",
            headers={"Cookie": f"rgp_access_token={token}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")

    @classmethod
    def _api_get(cls, path: str):
        request = urllib.request.Request(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {cls.admin_token}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    @classmethod
    def _api_post(cls, path: str, payload: dict | None):
        request = urllib.request.Request(
            f"{API_BASE}{path}",
            data=(json.dumps(payload).encode("utf-8") if payload is not None else b""),
            headers={
                "Authorization": f"Bearer {cls.admin_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)

    def test_admin_templates_live_route(self) -> None:
        html = self._get_web_html("/admin/templates")
        self.assertIn("Admin Templates", html)
        self.assertIn("Catalog Summary", html)
        self.assertIn("Assessment Revision", html)
        self.assertIn("/admin/templates/tmpl_assessment/1.4.0", html)

    def test_help_live_route(self) -> None:
        html = self._get_web_html("/help")
        self.assertIn("Help and User Guide", html)
        self.assertIn("Guide Map", html)
        self.assertIn("/help/requests", html)

    def test_new_request_template_picker_live_route(self) -> None:
        html = self._get_web_html("/requests/new")
        self.assertIn("Select Request Template", html)
        self.assertIn("Search Templates", html)
        self.assertIn("Template ID", html)
        self.assertIn("Assessment Revision", html)
        self.assertNotIn("Use this template", html)

    def test_workflow_history_live_route(self) -> None:
        html = self._get_web_html("/analytics/workflows/tmpl_assessment/history")
        self.assertIn("tmpl_assessment History", html)
        self.assertIn("Open Federation View", html)
        self.assertIn("Canonical Only", html)
        self.assertIn("Resolutions", html)

    def test_workflow_federation_live_route(self) -> None:
        html = self._get_web_html("/analytics/workflows/tmpl_assessment/federation?federation=with_conflict")
        self.assertIn("tmpl_assessment Federation", html)
        self.assertIn("Affected Requests", html)
        self.assertIn("Open Workflow History", html)
        self.assertTrue("Open request" in html or "No requests matched this workflow federation view." in html)

    def test_request_federated_conflicts_live_route(self) -> None:
        html = self._get_web_html("/requests/federated-conflicts")
        self.assertIn("Federated Conflicts", html)
        self.assertTrue("Open request" in html or "No requests currently have federated conflicts." in html)
        self.assertTrue("Open history" in html or "No requests currently have federated conflicts." in html)

    def test_admin_templates_non_admin_redirects_to_forbidden(self) -> None:
        html = self._get_web_html_with_token("/admin/templates", self.reviewer_token)
        self.assertIn("Access Restricted", html)
        self.assertIn("Attempted route:", html)
        self.assertIn("/api/v1/admin/templates", html)
