"""Unit tests for Phase 3 Pydantic models and enums."""

import unittest

from app.models.domain_pack import DomainPackRecord, CreateDomainPackRequest, ActivateDomainPackRequest
from app.models.workspace import WorkspaceRecord, ChangeSetRecord, CreateWorkspaceRequest, CreateChangeSetRequest
from app.models.editorial import (
    EditorialWorkflowRecord, EditorialStage, ContentProjectionRecord,
    EditorialRole, CreateEditorialWorkflowRequest,
)
from app.models.knowledge import KnowledgeArtifactRecord, KnowledgeVersionRecord, CreateKnowledgeArtifactRequest
from app.models.planning import (
    PlanningConstructRecord, PlanningMembershipRecord,
    PlanningConstructType, CreatePlanningConstructRequest,
)


class DomainPackModelsTest(unittest.TestCase):
    def test_create_request(self) -> None:
        req = CreateDomainPackRequest(name="Source Control Pack", version="1.0",
                                       contributed_templates=["tpl_pr", "tpl_branch"])
        self.assertEqual(req.name, "Source Control Pack")
        self.assertEqual(len(req.contributed_templates), 2)

    def test_record_defaults(self) -> None:
        rec = DomainPackRecord(id="dp_1", tenant_id="t1", name="Test", version="1.0")
        self.assertEqual(rec.status, "draft")
        self.assertEqual(rec.contributed_workflows, [])

    def test_activate_request(self) -> None:
        req = ActivateDomainPackRequest(actor_id="user_1")
        self.assertEqual(req.reason, "")


class WorkspaceModelsTest(unittest.TestCase):
    def test_workspace_defaults(self) -> None:
        rec = WorkspaceRecord(id="ws_1", tenant_id="t1", request_id="req_1", name="feature-branch")
        self.assertEqual(rec.status, "created")
        self.assertEqual(rec.protected_targets, [])

    def test_change_set_defaults(self) -> None:
        rec = ChangeSetRecord(id="cs_1", tenant_id="t1", request_id="req_1")
        self.assertEqual(rec.status, "draft")
        self.assertEqual(rec.applicable_type, "generic")
        self.assertEqual(rec.version, 1)

    def test_create_workspace_request(self) -> None:
        req = CreateWorkspaceRequest(request_id="req_1", name="ws", owner_id="user_1",
                                      protected_targets=["main", "production"])
        self.assertEqual(len(req.protected_targets), 2)


class EditorialModelsTest(unittest.TestCase):
    def test_editorial_roles(self) -> None:
        self.assertEqual(EditorialRole.AUTHOR, "author")
        self.assertEqual(EditorialRole.PUBLISHER, "publisher")
        self.assertEqual(len(list(EditorialRole)), 6)

    def test_editorial_stage(self) -> None:
        stage = EditorialStage(name="legal_review", required_role="legal_reviewer")
        self.assertEqual(stage.status, "pending")

    def test_workflow_record(self) -> None:
        rec = EditorialWorkflowRecord(id="ew_1", tenant_id="t1", request_id="req_1")
        self.assertEqual(rec.current_stage, "drafting")
        self.assertEqual(rec.stages, [])

    def test_projection_record(self) -> None:
        rec = ContentProjectionRecord(id="cp_1", tenant_id="t1", artifact_id="art_1", channel="web")
        self.assertEqual(rec.projection_status, "pending")


class KnowledgeModelsTest(unittest.TestCase):
    def test_artifact_defaults(self) -> None:
        rec = KnowledgeArtifactRecord(id="ka_1", tenant_id="t1", name="API Guide")
        self.assertEqual(rec.status, "draft")
        self.assertEqual(rec.content_type, "text")
        self.assertEqual(rec.version, 1)
        self.assertEqual(rec.tags, [])
        self.assertEqual(rec.provenance, [])

    def test_version_record(self) -> None:
        ver = KnowledgeVersionRecord(id="kav_1", artifact_id="ka_1", version=2, author="user_1")
        self.assertEqual(ver.version, 2)

    def test_create_request(self) -> None:
        req = CreateKnowledgeArtifactRequest(name="Onboarding", tags=["new_hire", "process"])
        self.assertEqual(len(req.tags), 2)


class PlanningModelsTest(unittest.TestCase):
    def test_construct_types(self) -> None:
        self.assertEqual(PlanningConstructType.INITIATIVE, "initiative")
        self.assertEqual(PlanningConstructType.RELEASE, "release")
        self.assertEqual(len(list(PlanningConstructType)), 5)

    def test_construct_record(self) -> None:
        rec = PlanningConstructRecord(id="pc_1", tenant_id="t1", type="release", name="Q2 Release")
        self.assertEqual(rec.status, "active")
        self.assertEqual(rec.priority, 0)

    def test_membership_record(self) -> None:
        mem = PlanningMembershipRecord(id="pm_1", planning_construct_id="pc_1", request_id="req_1")
        self.assertEqual(mem.sequence, 0)

    def test_create_request(self) -> None:
        req = CreatePlanningConstructRequest(type=PlanningConstructType.MILESTONE,
                                              name="Alpha", priority=1)
        self.assertEqual(req.type, "milestone")


if __name__ == "__main__":
    unittest.main()
