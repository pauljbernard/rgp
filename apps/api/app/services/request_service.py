from app.models.common import PaginatedResponse
from app.models.request import AmendRequest, CancelRequest, CloneRequest, CreateRequestDraft, RequestCheckRun, RequestRecord, SubmitRequest, SupersedeRequest, TransitionRequest
from app.models.security import Principal
from app.repositories.governance_repository import governance_repository


class RequestService:
    def list_requests(self, page: int, page_size: int) -> PaginatedResponse[RequestRecord]:
        return governance_repository.list_requests(page=page, page_size=page_size)

    def create_draft(self, payload: CreateRequestDraft, principal: Principal) -> RequestRecord:
        return governance_repository.create_request_draft(payload, principal.user_id, principal.tenant_id)

    def submit(self, request_id: str, payload: SubmitRequest, principal: Principal) -> RequestRecord:
        return governance_repository.submit_request(request_id, payload, principal.tenant_id)

    def amend(self, request_id: str, payload: AmendRequest, principal: Principal) -> RequestRecord:
        return governance_repository.amend_request(request_id, payload, principal.tenant_id)

    def cancel(self, request_id: str, payload: CancelRequest, principal: Principal) -> RequestRecord:
        return governance_repository.cancel_request(request_id, payload, principal.tenant_id)

    def transition(self, request_id: str, payload: TransitionRequest, principal: Principal) -> RequestRecord:
        return governance_repository.transition_request(request_id, payload, principal.tenant_id)

    def clone(self, request_id: str, payload: CloneRequest, principal: Principal) -> RequestRecord:
        return governance_repository.clone_request(request_id, payload, principal.tenant_id)

    def supersede(self, request_id: str, payload: SupersedeRequest, principal: Principal) -> RequestRecord:
        return governance_repository.supersede_request(request_id, payload, principal.tenant_id)

    def run_checks(self, request_id: str, payload: RequestCheckRun, principal: Principal) -> RequestRecord:
        return governance_repository.run_request_checks(request_id, payload, principal.tenant_id)


request_service = RequestService()
