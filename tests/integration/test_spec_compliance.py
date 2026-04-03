import json
import os
import unittest
import urllib.request
from pathlib import Path


REPO_ROOT = Path("/Volumes/data/development/rgp")
API_BASE = os.environ.get("RGP_API_BASE", "http://127.0.0.1:8001")
WEB_BASE = os.environ.get("RGP_WEB_BASE", "http://127.0.0.1:3000")


class SpecComplianceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.admin_token = cls._issue_dev_token(["platform_admin", "operator", "reviewer", "submitter"])

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
    def _api_get(cls, path: str):
        request = urllib.request.Request(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {cls.admin_token}"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _file_text(path: str) -> str:
        return (REPO_ROOT / path).read_text(encoding="utf-8")

    def test_constitution_and_requirements_explicitly_cover_account_lifecycle(self) -> None:
        constitution = self._file_text("constitution.md")
        requirements = self._file_text("requirements.md")
        build_pack = self._file_text("build_pack_1.md")

        self.assertIn("governed user and account onboarding lifecycle", constitution)
        self.assertIn("FR-REQ-008", requirements)
        self.assertIn("FR-REQ-009", requirements)
        self.assertIn("FR-REQ-010", requirements)
        self.assertIn("FR-REQ-011", requirements)
        self.assertIn("FR-TPL-013", requirements)
        self.assertIn("registration still materialize as Request records", build_pack)
        self.assertIn("platform administrators", constitution)
        self.assertIn("tenant-admin journeys", build_pack)

    def test_live_system_exposes_registration_template_and_public_registration_route(self) -> None:
        templates = self._api_get("/api/v1/templates")
        registration_templates = [template for template in templates if template["id"] == "tmpl_user_registration"]
        self.assertTrue(registration_templates, "Expected tmpl_user_registration to be published")

        request = urllib.request.Request(f"{WEB_BASE}/register", method="GET")
        with urllib.request.urlopen(request, timeout=60) as response:
            html = response.read().decode("utf-8")
        self.assertIn("Create Account Request", html)
        self.assertIn("Registration requests are routed as governed work.", html)

    def test_compliance_surfaces_are_checked_by_code(self) -> None:
        self.assertTrue((REPO_ROOT / "apps/web/app/forbidden/page.tsx").exists())
        self.assertTrue((REPO_ROOT / "tests/integration/test_live_web_routes.py").exists())
        self.assertTrue((REPO_ROOT / "tests/e2e/USER_STORIES.md").exists())

    def test_live_system_exposes_tenant_catalog_for_platform_admin(self) -> None:
        tenants = self._api_get("/api/v1/admin/org/tenants")
        self.assertTrue(any(tenant["id"] == "tenant_demo" for tenant in tenants))
        self.assertTrue(any(tenant["id"] == "tenant_other" for tenant in tenants))
