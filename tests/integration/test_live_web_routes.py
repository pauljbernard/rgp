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

    def test_admin_templates_non_admin_redirects_to_forbidden(self) -> None:
        html = self._get_web_html_with_token("/admin/templates", self.reviewer_token)
        self.assertIn("Access Restricted", html)
        self.assertIn("Attempted route:", html)
        self.assertIn("/api/v1/admin/templates", html)
