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

    def test_constitution_and_requirements_cover_account_lifecycle_and_substrate_neutrality(self) -> None:
        constitution = self._file_text("constitution.md")
        requirements = self._file_text("requirements.md")
        build_pack = self._file_text("build_pack_1.md")

        self.assertIn("governed user and account onboarding lifecycle", constitution)
        self.assertIn("2.4 External Substrate Neutrality", constitution)
        self.assertIn("RGP SHALL operate as a universal governance control plane independent of any specific execution, storage, or management substrate.", constitution)
        self.assertIn("All work types across all substrate classes SHALL be representable within a single unified, domain-neutral model", constitution)
        self.assertIn("All artifacts SHALL be substrate-agnostic representations", constitution)
        self.assertIn("4.19 Normalized Event Semantics", constitution)
        self.assertIn("4.20 Relationship Graph", constitution)
        self.assertIn("4.21 Governed Context Principle", constitution)
        self.assertIn("4.22 Agent Specificity Principle", constitution)
        self.assertIn("4.23 Governed Tool and Context Access Principle", constitution)
        self.assertIn("6.17 Managed Target", constitution)
        self.assertIn("6.18 Record", constitution)
        self.assertIn("6.19 Revision", constitution)
        self.assertIn("6.20 Projection", constitution)
        self.assertIn("6.21 Binding", constitution)
        self.assertIn("6.22 Context Bundle", constitution)
        self.assertIn("6.23 Context Binding", constitution)
        self.assertIn("6.24 Agent Operating Profile", constitution)
        self.assertIn("7.4 Extensible Lifecycle Principle", constitution)
        self.assertIn("queue-based routing", constitution)
        self.assertIn("agent-assisted collaboration", constitution)
        self.assertIn("No agent assignment without governed context", constitution)
        self.assertIn("No agent tool access without policy-scoped authorization", constitution)
        self.assertIn("18A. SLA / SLO CONSTITUTION", constitution)
        self.assertIn("19A. SUBSTRATE CAPABILITY CONSTITUTION", constitution)
        self.assertIn("21A. DOMAIN CAPABILITY CONSTITUTION", constitution)
        self.assertIn("21B. PLANNING CONSTITUTION", constitution)
        self.assertIn("21C. KNOWLEDGE AND MEMORY CONSTITUTION", constitution)
        self.assertIn("13A. FEDERATED IDENTITY EXTENSION", constitution)
        self.assertIn("17A. UNIFIED TIMELINE CONSTITUTION", constitution)
        self.assertIn("21D. FEDERATED GOVERNANCE CONSTITUTION", constitution)
        self.assertIn("21E. PROJECTION & SYNCHRONIZATION CONSTITUTION", constitution)
        self.assertIn("21F. SYSTEM OF RECORD CONSTITUTION", constitution)
        self.assertIn("21G. ADAPTER CONSTITUTION", constitution)
        self.assertIn("21H. RECONCILIATION CONSTITUTION", constitution)
        self.assertIn("21I. CROSS-SYSTEM ORCHESTRATION CONSTITUTION", constitution)
        self.assertIn("21J. AGENT CONTEXT CONSTITUTION", constitution)
        self.assertIn("21K. MCP & CONTEXT INTEGRATION CONSTITUTION", constitution)
        self.assertIn("coexistence with existing systems", constitution)
        self.assertIn("bidirectional synchronization", constitution)
        self.assertIn("Robust MCP-style integration SHALL be treated as a first-class mechanism", constitution)
        self.assertIn("FR-REQ-008", requirements)
        self.assertIn("FR-REQ-009", requirements)
        self.assertIn("FR-REQ-010", requirements)
        self.assertIn("FR-REQ-011", requirements)
        self.assertIn("FR-SUB-001", requirements)
        self.assertIn("FR-SUB-005", requirements)
        self.assertIn("FR-REL-001", requirements)
        self.assertIn("FR-REL-006", requirements)
        self.assertIn("FR-LIFE-001", requirements)
        self.assertIn("FR-LIFE-006", requirements)
        self.assertIn("FR-QUE-001", requirements)
        self.assertIn("FR-QUE-006", requirements)
        self.assertIn("FR-SLA-001", requirements)
        self.assertIn("FR-SLA-005", requirements)
        self.assertIn("FR-WFB-006", requirements)
        self.assertIn("FR-TPL-013", requirements)
        self.assertIn("FR-ART-007", requirements)
        self.assertIn("FR-CONT-001", requirements)
        self.assertIn("FR-CONT-006", requirements)
        self.assertIn("FR-MAS-001", requirements)
        self.assertIn("FR-MAS-005", requirements)
        self.assertIn("FR-REV-007", requirements)
        self.assertIn("WORKSPACE & CHANGE MANAGEMENT (SUBSTRATE-NEUTRAL)", requirements)
        self.assertIn("FR-CODE-008", requirements)
        self.assertIn("FR-PRO-006", requirements)
        self.assertIn("FR-ADP-001", requirements)
        self.assertIn("FR-ADP-003", requirements)
        self.assertIn("FR-ADP-004", requirements)
        self.assertIn("FR-ADP-006", requirements)
        self.assertIn("FR-EVT-001", requirements)
        self.assertIn("FR-EVT-003", requirements)
        self.assertIn("FR-ING-001", requirements)
        self.assertIn("FR-ING-004", requirements)
        self.assertIn("FR-AGT-006", requirements)
        self.assertIn("FR-AGT-007", requirements)
        self.assertIn("FR-AGT-010", requirements)
        self.assertIn("FR-CTX-001", requirements)
        self.assertIn("FR-CTX-006", requirements)
        self.assertIn("FR-MCP-001", requirements)
        self.assertIn("FR-MCP-006", requirements)
        self.assertIn("FR-DOM-001", requirements)
        self.assertIn("FR-DOM-004", requirements)
        self.assertIn("FR-DEX-001", requirements)
        self.assertIn("FR-DEX-004", requirements)
        self.assertIn("FR-PLAN-001", requirements)
        self.assertIn("FR-PLAN-007", requirements)
        self.assertIn("FR-KNOW-001", requirements)
        self.assertIn("FR-KNOW-005", requirements)
        self.assertIn("FR-COL-001", requirements)
        self.assertIn("FR-COL-004", requirements)
        self.assertIn("FR-POL-001", requirements)
        self.assertIn("FR-POL-004", requirements)
        self.assertIn("FR-ORCH-001", requirements)
        self.assertIn("FR-ORCH-004", requirements)
        self.assertIn("FR-ORCH-005", requirements)
        self.assertIn("FR-ORCH-006", requirements)
        self.assertIn("FR-INTEL-013", requirements)
        self.assertIn("FR-VIEW-001", requirements)
        self.assertIn("FR-VIEW-003", requirements)
        self.assertIn("FR-AUD-001", requirements)
        self.assertIn("FR-AUD-004", requirements)
        self.assertIn("FR-FED-001", requirements)
        self.assertIn("FR-FED-003", requirements)
        self.assertIn("FR-PROJ-001", requirements)
        self.assertIn("FR-PROJ-004", requirements)
        self.assertIn("FR-SYNC-001", requirements)
        self.assertIn("FR-SYNC-004", requirements)
        self.assertIn("FR-CONF-001", requirements)
        self.assertIn("FR-CONF-003", requirements)
        self.assertIn("FR-ID-006", requirements)
        self.assertIn("FR-ID-007", requirements)
        self.assertIn("FR-TIME-001", requirements)
        self.assertIn("FR-TIME-003", requirements)
        self.assertIn("FR-INT-LVL-001", requirements)
        self.assertIn("FR-INT-LVL-002", requirements)
        self.assertIn("30. REQUIRED GUARDRAILS FOR MULTI-VERTICAL EVOLUTION", requirements)
        self.assertIn("No repository-first thinking", requirements)
        self.assertIn("GitHub is an adapter", requirements)
        self.assertIn("Promotion is the universal apply-change mechanism.", requirements)
        self.assertIn("30.2 No Vertical-First Core Redefinition", requirements)
        self.assertIn("30.3 Relationship Graph as Canonical Coordination Layer", requirements)
        self.assertIn("registration still materialize as Request records", build_pack)
        self.assertIn("platform administrators", constitution)
        self.assertIn("tenant-admin journeys", build_pack)
        self.assertIn("heterogeneous enterprise systems", constitution)

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
