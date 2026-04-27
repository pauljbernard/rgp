import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from app.api.v1.endpoints import requests as request_endpoints
from app.models.common import PaginatedResponse
from app.models.governance import (
    AuditEntry,
    InstructionalContentKind,
    InstructionalWorkflowDecision,
    InstructionalWorkflowDecisionRequest,
    InstructionalWorkflowProjectionRecord,
    InstructionalWorkflowStageId,
    InstructionalWorkflowStatus,
)
from app.models.request import RequestStatus
from app.models.security import Principal, PrincipalRole
from app.repositories.governance_repository import GovernanceRepository


class _FakeSession:
    def __init__(self, row):
        self._row = row
        self.committed = False
        self.refreshed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, model, request_id):
        return self._row if self._row and self._row.id == request_id else None

    def commit(self):
        self.committed = True

    def refresh(self, row):
        self.refreshed = True


class _FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _FakeListSession:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self, query):
        return _FakeScalarResult(self._rows)


class _FakeAnalyticsSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def scalars(self, query):
        return _FakeScalarResult([])


class GovernanceRepositoryInstructionalWorkflowTest(unittest.TestCase):
    def _row(self, **overrides):
        base = {
            "id": "req_instr_001",
            "tenant_id": "tenant_demo",
            "template_id": "tmpl_assessment",
            "template_version": "v1",
            "title": "Assessment Review",
            "status": RequestStatus.UNDER_REVIEW.value,
            "input_payload": {
                "flightos_content_entry_id": "entry_001",
                "flightos_schema_id": "assessment",
            },
            "updated_at": datetime.now(timezone.utc),
            "updated_by": "user_submitter",
            "version": 3,
        }
        base.update(overrides)
        return SimpleNamespace(**base)

    def _audit_entry(self, *, actor: str, action: str, timestamp: str, reason: str = "") -> AuditEntry:
        return AuditEntry(
            timestamp=timestamp,
            actor=actor,
            action=action,
            object_type="request",
            object_id="req_instr_001",
            reason_or_evidence=reason,
        )

    def test_build_projection_marks_first_pending_stage_active(self) -> None:
        row = self._row()

        projection = GovernanceRepository._build_instructional_projection_from_row(row, [])

        self.assertEqual(projection.request_id, "req_instr_001")
        self.assertEqual(projection.flightos_content_entry_id, "entry_001")
        self.assertEqual(projection.workflow_status, InstructionalWorkflowStatus.IN_REVIEW)
        self.assertEqual(projection.current_stage_id, InstructionalWorkflowStageId.INSTRUCTIONAL_DESIGN_REVIEW)
        self.assertEqual(projection.stages[0].status.value, "ACTIVE")
        self.assertTrue(all(stage.status.value == "PENDING" for stage in projection.stages[1:]))

    def test_build_projection_uses_audit_history_for_decisions(self) -> None:
        row = self._row(status=RequestStatus.CHANGES_REQUESTED.value)
        audit_entries = [
            self._audit_entry(actor="user_submitter", action="Submitted", timestamp="2026-04-09T12:00:00Z"),
            self._audit_entry(
                actor="reviewer_1",
                action="Instructional Stage Approved: INSTRUCTIONAL_DESIGN_REVIEW",
                timestamp="2026-04-09T12:10:00Z",
                reason="Looks good",
            ),
            self._audit_entry(
                actor="reviewer_2",
                action="Instructional Stage Changes Requested: SME_REVIEW",
                timestamp="2026-04-09T12:20:00Z",
                reason="Need SME revision",
            ),
        ]

        projection = GovernanceRepository._build_instructional_projection_from_row(row, audit_entries)

        self.assertEqual(projection.submitted_by_user_id, "user_submitter")
        self.assertEqual(projection.workflow_status, InstructionalWorkflowStatus.CHANGES_REQUESTED)
        self.assertEqual(projection.current_stage_id, InstructionalWorkflowStageId.SME_REVIEW)
        self.assertEqual(projection.stages[0].status.value, "APPROVED")
        self.assertEqual(projection.stages[1].status.value, "CHANGES_REQUESTED")
        self.assertEqual(projection.stages[1].decided_by_user_id, "reviewer_2")
        self.assertEqual(projection.stages[1].notes, "Need SME revision")

    def test_decide_instructional_stage_approves_final_stage(self) -> None:
        repository = GovernanceRepository()
        row = self._row(status=RequestStatus.UNDER_REVIEW.value, version=7)
        payload = InstructionalWorkflowDecisionRequest(
            actor_id="reviewer_final",
            stage_id=InstructionalWorkflowStageId.CERTIFICATION_COMPLIANCE_REVIEW,
            decision=InstructionalWorkflowDecision.APPROVE,
            notes="Ready for release",
        )
        projection_before = GovernanceRepository._build_instructional_projection_from_row(
            row,
            [
                self._audit_entry(actor="user_submitter", action="Submitted", timestamp="2026-04-09T12:00:00Z"),
                self._audit_entry(
                    actor="reviewer_1",
                    action="Instructional Stage Approved: INSTRUCTIONAL_DESIGN_REVIEW",
                    timestamp="2026-04-09T12:10:00Z",
                    reason="ok",
                ),
                self._audit_entry(
                    actor="reviewer_2",
                    action="Instructional Stage Approved: SME_REVIEW",
                    timestamp="2026-04-09T12:15:00Z",
                    reason="ok",
                ),
                self._audit_entry(
                    actor="reviewer_3",
                    action="Instructional Stage Approved: ASSESSMENT_REVIEW",
                    timestamp="2026-04-09T12:20:00Z",
                    reason="ok",
                ),
            ],
        )
        projection_after = projection_before.model_copy(
            update={
                "request_status": RequestStatus.APPROVED,
                "workflow_status": InstructionalWorkflowStatus.APPROVED_FOR_RELEASE,
                "current_stage_id": InstructionalWorkflowStageId.CERTIFICATION_COMPLIANCE_REVIEW,
            }
        )
        events = []
        transition_calls = []
        fake_session = _FakeSession(row)

        with patch("app.repositories.governance_repository.SessionLocal", return_value=fake_session), \
             patch.object(repository, "_ensure_request_tenant_access"), \
             patch.object(repository, "list_audit_entries", side_effect=[[self._audit_entry(actor="user_submitter", action="Submitted", timestamp="2026-04-09T12:00:00Z")], []]), \
             patch.object(repository, "_build_instructional_projection_from_row", side_effect=[projection_before, projection_after]), \
             patch.object(repository, "_apply_transition_side_effects", side_effect=lambda session, request_row, current_status, target_status, actor: transition_calls.append((current_status, target_status, actor))), \
             patch.object(repository, "_append_event", side_effect=lambda **kwargs: events.append((kwargs["action"], kwargs["reason_or_evidence"]))):
            result = repository.decide_instructional_workflow_stage("req_instr_001", payload, "tenant_demo")

        self.assertEqual(result.workflow_status, InstructionalWorkflowStatus.APPROVED_FOR_RELEASE)
        self.assertEqual(row.status, RequestStatus.APPROVED.value)
        self.assertEqual(row.updated_by, "reviewer_final")
        self.assertEqual(row.version, 8)
        self.assertTrue(fake_session.committed)
        self.assertTrue(fake_session.refreshed)
        self.assertEqual(
            transition_calls,
            [(RequestStatus.UNDER_REVIEW, RequestStatus.APPROVED, "reviewer_final")],
        )
        self.assertEqual(
            events,
            [
                ("Instructional Stage Approved: CERTIFICATION_COMPLIANCE_REVIEW", "Ready for release"),
                ("Transitioned to approved", "Ready for release"),
            ],
        )


class GovernanceRepositoryRequestListingTest(unittest.TestCase):
    def test_list_canonical_request_records_stays_sql_only_for_sqlalchemy_backend(self) -> None:
        repository = GovernanceRepository()
        row = SimpleNamespace(
            id="req_001",
            tenant_id="tenant_demo",
            request_type="change",
            template_id="tmpl_001",
            template_version="v1",
            title="Request",
            summary="Summary",
            status=RequestStatus.QUEUED.value,
            priority="medium",
            sla_policy_id=None,
            submitter_id="submitter_1",
            owner_team_id="team_1",
            owner_user_id="owner_1",
            execution_mode="central",
            assigned_node_id=None,
            local_binding_id=None,
            local_status=None,
            last_node_update_at=None,
            origin="rgp",
            origin_node_id=None,
            workflow_binding_id=None,
            current_run_id=None,
            policy_context={},
            input_payload={},
            tags=[],
            created_at=datetime.now(timezone.utc),
            created_by="submitter_1",
            updated_at=datetime.now(timezone.utc),
            updated_by="submitter_1",
            version=1,
            is_archived=False,
        )
        session = _FakeListSession([row])

        with patch("app.repositories.governance_repository.settings.request_persistence_backend", "sqlalchemy"), \
             patch("app.repositories.governance_repository.settings.persistence_backend", "sqlalchemy"):
            records = repository._list_canonical_request_records(session, tenant_id="tenant_demo")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, "req_001")

    def test_delivery_lifecycle_handles_naive_request_datetimes(self) -> None:
        repository = GovernanceRepository()
        request_row = SimpleNamespace(
            id="req_002",
            tenant_id="tenant_demo",
            status=RequestStatus.COMPLETED.value,
            created_at=datetime(2026, 4, 1, 10, 0, 0),
            updated_at=datetime(2026, 4, 2, 10, 0, 0),
        )

        with patch("app.repositories.governance_repository.SessionLocal", return_value=_FakeAnalyticsSession()), \
             patch.object(repository, "_list_canonical_request_records", return_value=[request_row]), \
             patch.object(repository, "_filter_request_rows_for_analytics", return_value=[request_row]), \
             patch.object(
                 repository,
                 "_requests_by_scope",
                 return_value={("team", "team_1"): [request_row]},
             ):
            rows = repository.list_delivery_lifecycle("tenant_demo")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].throughput_30d, 1)
        self.assertEqual(rows[0].lead_time_hours, 24.0)

    def test_workflow_trends_handles_naive_request_datetimes(self) -> None:
        repository = GovernanceRepository()
        request_row = SimpleNamespace(
            id="req_003",
            tenant_id="tenant_demo",
            workflow_binding_id="wf_1",
            template_id="tmpl_001",
            priority="medium",
            status=RequestStatus.COMPLETED.value,
            created_at=datetime(2026, 4, 1, 10, 0, 0),
            updated_at=datetime(2026, 4, 2, 16, 0, 0),
        )

        with patch("app.repositories.governance_repository.SessionLocal", return_value=_FakeAnalyticsSession()), \
             patch.object(repository, "_list_canonical_request_records", return_value=[request_row]), \
             patch.object(repository, "_filter_request_rows_for_analytics", return_value=[request_row]):
            rows = repository.list_workflow_trends(days=30, tenant_id="tenant_demo")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].request_count, 1)
        self.assertEqual(rows[0].avg_cycle_time_hours, 30.0)


class InstructionalWorkflowEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.principal = Principal(
            user_id="reviewer_1",
            tenant_id="tenant_demo",
            roles=[PrincipalRole.REVIEWER, PrincipalRole.OPERATOR],
        )
        self.projection = InstructionalWorkflowProjectionRecord(
            request_id="req_instr_001",
            tenant_id="tenant_demo",
            flightos_content_entry_id="entry_001",
            flightos_schema_id="assessment",
            template_id="tmpl_assessment",
            template_version="v1",
            title="Assessment Review",
            request_status=RequestStatus.UNDER_REVIEW,
            workflow_status=InstructionalWorkflowStatus.IN_REVIEW,
            content_kind=InstructionalContentKind.ASSESSMENT,
            current_stage_id=InstructionalWorkflowStageId.INSTRUCTIONAL_DESIGN_REVIEW,
            stages=[],
        )

    def test_list_instructional_workflows_delegates_to_service(self) -> None:
        paginated = PaginatedResponse.create(items=[self.projection], page=1, page_size=25, total_count=1)
        with patch.object(request_endpoints.governance_service, "list_instructional_workflow_projections", return_value=paginated) as list_mock:
            result = request_endpoints.list_instructional_workflows(
                page=1,
                page_size=25,
                flightos_content_entry_id="entry_001",
                template_id="tmpl_assessment",
                workflow_status="IN_REVIEW",
                principal=self.principal,
            )

        self.assertEqual(result.items[0].request_id, "req_instr_001")
        list_mock.assert_called_once_with(
            page=1,
            page_size=25,
            principal=self.principal,
            flightos_content_entry_id="entry_001",
            template_id="tmpl_assessment",
            workflow_status="IN_REVIEW",
        )

    def test_get_instructional_workflow_translates_value_error_to_http_409(self) -> None:
        with patch.object(request_endpoints.governance_service, "get_instructional_workflow_projection", side_effect=ValueError("unsupported")):
            with self.assertRaises(HTTPException) as excinfo:
                request_endpoints.get_instructional_workflow("req_instr_001", self.principal)

        self.assertEqual(excinfo.exception.status_code, 409)
        self.assertEqual(excinfo.exception.detail, "unsupported")

    def test_decide_instructional_workflow_stage_injects_actor_and_uses_idempotency_scope(self) -> None:
        payload = InstructionalWorkflowDecisionRequest(
            stage_id=InstructionalWorkflowStageId.INSTRUCTIONAL_DESIGN_REVIEW,
            decision=InstructionalWorkflowDecision.APPROVE,
            notes="Approved",
        )
        captured = {}

        def fake_replay_or_execute(**kwargs):
            captured.update(kwargs)
            return kwargs["operation"]()

        with patch.object(request_endpoints.governance_service, "decide_instructional_workflow_stage", return_value=self.projection) as decide_mock, \
             patch.object(request_endpoints.idempotency_service, "replay_or_execute", side_effect=fake_replay_or_execute):
            result = request_endpoints.decide_instructional_workflow_stage(
                "req_instr_001",
                payload,
                self.principal,
                idempotency_key="idem-1",
            )

        self.assertEqual(result.request_id, "req_instr_001")
        self.assertEqual(captured["scope"], "requests:req_instr_001:instructional-workflow:decision")
        self.assertEqual(captured["idempotency_key"], "idem-1")
        self.assertEqual(captured["payload"]["actor_id"], "reviewer_1")
        decide_mock.assert_called_once()
        delegated_payload = decide_mock.call_args.args[1]
        self.assertEqual(delegated_payload.actor_id, "reviewer_1")
        self.assertEqual(delegated_payload.stage_id, InstructionalWorkflowStageId.INSTRUCTIONAL_DESIGN_REVIEW)


if __name__ == "__main__":
    unittest.main()
