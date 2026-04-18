"""Request lifecycle repository — owns all request CRUD and state transitions.

Delegates to governance_repository for now; the actual method implementations
will be migrated here incrementally as the monolith is decomposed.
"""

from __future__ import annotations

from app.models.common import PaginatedResponse
from app.models.governance import (
    AuditEntry,
    CheckRunRecord,
    InstructionalWorkflowDecisionRequest,
    InstructionalWorkflowProjectionRecord,
    RequestDetail,
)
from app.models.request import (
    AmendRequest,
    CancelRequest,
    CloneRequest,
    CreateRequestDraft,
    RequestCheckRun,
    RequestRecord,
    SubmitRequest,
    SupersedeRequest,
    TransitionRequest,
)
from app.models.security import PublicRegistrationRequest, RegistrationSubmissionResponse
from app.repositories.governance_repository import governance_repository


class RequestLifecycleRepository:
    """Encapsulates all request lifecycle operations."""

    def list_requests(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        owner_team_id: str | None = None,
        workflow: str | None = None,
        request_id: str | None = None,
        federation: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[RequestRecord]:
        return governance_repository.list_requests(page, page_size, status, owner_team_id, workflow, request_id, federation, tenant_id)

    def get_request(self, request_id: str, tenant_id: str | None = None) -> RequestDetail:
        return governance_repository.get_request(request_id, tenant_id)

    def create_request_draft(self, payload: CreateRequestDraft, actor_id: str, tenant_id: str) -> RequestRecord:
        return governance_repository.create_request_draft(payload, actor_id, tenant_id)

    def submit_request(self, request_id: str, payload: SubmitRequest, tenant_id: str) -> RequestRecord:
        return governance_repository.submit_request(request_id, payload, tenant_id)

    def amend_request(self, request_id: str, payload: AmendRequest, tenant_id: str) -> RequestRecord:
        return governance_repository.amend_request(request_id, payload, tenant_id)

    def cancel_request(self, request_id: str, payload: CancelRequest, tenant_id: str) -> RequestRecord:
        return governance_repository.cancel_request(request_id, payload, tenant_id)

    def transition_request(self, request_id: str, payload: TransitionRequest, tenant_id: str) -> RequestRecord:
        return governance_repository.transition_request(request_id, payload, tenant_id)

    def clone_request(self, request_id: str, payload: CloneRequest, tenant_id: str) -> RequestRecord:
        return governance_repository.clone_request(request_id, payload, tenant_id)

    def supersede_request(self, request_id: str, payload: SupersedeRequest, tenant_id: str) -> RequestRecord:
        return governance_repository.supersede_request(request_id, payload, tenant_id)

    def run_request_checks(self, request_id: str, payload: RequestCheckRun, tenant_id: str) -> RequestRecord:
        return governance_repository.run_request_checks(request_id, payload, tenant_id)

    def create_public_registration_request(self, payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
        return governance_repository.create_public_registration_request(payload)

    def list_audit_entries(self, request_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        return governance_repository.list_audit_entries(request_id, tenant_id)

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        return governance_repository.list_request_check_runs(request_id, tenant_id)

    def list_instructional_workflow_projections(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        flightos_content_entry_id: str | None = None,
        template_id: str | None = None,
        workflow_status: str | None = None,
    ):
        return governance_repository.list_instructional_workflow_projections(
            page=page,
            page_size=page_size,
            tenant_id=tenant_id,
            flightos_content_entry_id=flightos_content_entry_id,
            template_id=template_id,
            workflow_status=workflow_status,
        )

    def get_instructional_workflow_projection(self, request_id: str, tenant_id: str | None = None) -> InstructionalWorkflowProjectionRecord:
        return governance_repository.get_instructional_workflow_projection(request_id, tenant_id)

    def decide_instructional_workflow_stage(
        self,
        request_id: str,
        payload: InstructionalWorkflowDecisionRequest,
        tenant_id: str,
    ) -> InstructionalWorkflowProjectionRecord:
        return governance_repository.decide_instructional_workflow_stage(request_id, payload, tenant_id)


request_lifecycle_repository = RequestLifecycleRepository()
