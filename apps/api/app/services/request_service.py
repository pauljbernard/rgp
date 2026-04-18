from app.core.config import settings
from app.models.common import PaginatedResponse
from app.models.request import AmendRequest, CancelRequest, CloneRequest, CreateRequestDraft, RequestCheckRun, RequestRecord, SubmitRequest, SupersedeRequest, TransitionRequest
from app.models.security import Principal
from app.persistence import DynamoDbGovernancePersistenceAdapter, RequestPersistencePort, SqlAlchemyGovernancePersistenceAdapter


class RequestService:
    def __init__(self, request_store: RequestPersistencePort) -> None:
        self._request_store = request_store

    def list_requests(self, page: int, page_size: int) -> PaginatedResponse[RequestRecord]:
        return self._request_store.list_requests(page=page, page_size=page_size)

    def create_draft(self, payload: CreateRequestDraft, principal: Principal) -> RequestRecord:
        return self._request_store.create_request_draft(payload, principal.user_id, principal.tenant_id)

    def submit(self, request_id: str, payload: SubmitRequest, principal: Principal) -> RequestRecord:
        return self._request_store.submit_request(request_id, payload, principal.tenant_id)

    def amend(self, request_id: str, payload: AmendRequest, principal: Principal) -> RequestRecord:
        return self._request_store.amend_request(request_id, payload, principal.tenant_id)

    def cancel(self, request_id: str, payload: CancelRequest, principal: Principal) -> RequestRecord:
        return self._request_store.cancel_request(request_id, payload, principal.tenant_id)

    def transition(self, request_id: str, payload: TransitionRequest, principal: Principal) -> RequestRecord:
        return self._request_store.transition_request(request_id, payload, principal.tenant_id)

    def clone(self, request_id: str, payload: CloneRequest, principal: Principal) -> RequestRecord:
        return self._request_store.clone_request(request_id, payload, principal.tenant_id)

    def supersede(self, request_id: str, payload: SupersedeRequest, principal: Principal) -> RequestRecord:
        return self._request_store.supersede_request(request_id, payload, principal.tenant_id)

    def run_checks(self, request_id: str, payload: RequestCheckRun, principal: Principal) -> RequestRecord:
        return self._request_store.run_request_checks(request_id, payload, principal.tenant_id)


def _build_request_store() -> RequestPersistencePort:
    backend = (settings.request_persistence_backend or settings.persistence_backend or "sqlalchemy").lower()
    if backend == "dynamodb":
        return DynamoDbGovernancePersistenceAdapter()
    return SqlAlchemyGovernancePersistenceAdapter()


request_service = RequestService(_build_request_store())
