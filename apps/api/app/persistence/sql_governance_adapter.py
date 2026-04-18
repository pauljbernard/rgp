from app.models.common import PaginatedResponse
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
from app.models.template import (
    CreateTemplateVersionRequest,
    TemplateRecord,
    TemplateStatus,
    TemplateValidationResult,
    UpdateTemplateDefinitionRequest,
)
from app.persistence.contracts import RequestPersistencePort, TemplatePersistencePort
from app.repositories.governance_repository import GovernanceRepository, governance_repository


class SqlAlchemyGovernancePersistenceAdapter(RequestPersistencePort, TemplatePersistencePort):
    """
    Transitional adapter over the current SQLAlchemy-backed governance repository.

    New service code should depend on persistence ports rather than importing the
    governance repository directly so DynamoDB-backed implementations can replace
    this adapter without changing service contracts.
    """

    def __init__(self, repository: GovernanceRepository | None = None) -> None:
        self._repository = repository or governance_repository

    def list_requests(self, page: int, page_size: int) -> PaginatedResponse[RequestRecord]:
        return self._repository.list_requests(page=page, page_size=page_size)

    def create_request_draft(self, payload: CreateRequestDraft, actor_id: str, tenant_id: str) -> RequestRecord:
        return self._repository.create_request_draft(payload, actor_id, tenant_id)

    def submit_request(self, request_id: str, payload: SubmitRequest, tenant_id: str) -> RequestRecord:
        return self._repository.submit_request(request_id, payload, tenant_id)

    def amend_request(self, request_id: str, payload: AmendRequest, tenant_id: str) -> RequestRecord:
        return self._repository.amend_request(request_id, payload, tenant_id)

    def cancel_request(self, request_id: str, payload: CancelRequest, tenant_id: str) -> RequestRecord:
        return self._repository.cancel_request(request_id, payload, tenant_id)

    def transition_request(self, request_id: str, payload: TransitionRequest, tenant_id: str) -> RequestRecord:
        return self._repository.transition_request(request_id, payload, tenant_id)

    def clone_request(self, request_id: str, payload: CloneRequest, tenant_id: str) -> RequestRecord:
        return self._repository.clone_request(request_id, payload, tenant_id)

    def supersede_request(self, request_id: str, payload: SupersedeRequest, tenant_id: str) -> RequestRecord:
        return self._repository.supersede_request(request_id, payload, tenant_id)

    def run_request_checks(self, request_id: str, payload: RequestCheckRun, tenant_id: str) -> RequestRecord:
        return self._repository.run_request_checks(request_id, payload, tenant_id)

    def list_templates(self, tenant_id: str, include_non_published: bool = False) -> list[TemplateRecord]:
        return self._repository.list_templates(tenant_id, include_non_published=include_non_published)

    def create_template_version(self, payload: CreateTemplateVersionRequest, actor_id: str, tenant_id: str) -> TemplateRecord:
        return self._repository.create_template_version(payload, actor_id, tenant_id)

    def update_template_definition(
        self,
        template_id: str,
        version: str,
        payload: UpdateTemplateDefinitionRequest,
        actor_id: str,
        tenant_id: str,
    ) -> TemplateRecord:
        return self._repository.update_template_definition(template_id, version, payload, actor_id, tenant_id)

    def validate_template_definition(self, template_id: str, version: str, tenant_id: str) -> TemplateValidationResult:
        return self._repository.validate_template_definition(template_id, version, tenant_id)

    def delete_template_version(self, template_id: str, version: str, actor_id: str, tenant_id: str) -> None:
        self._repository.delete_template_version(template_id, version, actor_id, tenant_id)

    def update_template_status(
        self,
        template_id: str,
        version: str,
        status: TemplateStatus,
        actor_id: str,
        tenant_id: str,
        note: str | None,
    ) -> TemplateRecord:
        return self._repository.update_template_status(template_id, version, status, actor_id, tenant_id, note)
