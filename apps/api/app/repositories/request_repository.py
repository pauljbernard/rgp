from app.models.common import PaginatedResponse
from app.models.request import (
    CreateRequestDraft,
    RequestPriority,
    RequestRecord,
    RequestStatus,
    seed_request,
)


class InMemoryRequestRepository:
    def __init__(self) -> None:
        self._items = [
            seed_request("req_001", "Generate Grade 5 Math Unit", RequestStatus.AWAITING_REVIEW, RequestPriority.HIGH, "team_curriculum"),
            seed_request("req_002", "Revise Algebra Assessment", RequestStatus.IN_EXECUTION, RequestPriority.URGENT, "team_assessment"),
            seed_request("req_003", "Publish Science Lab Artifact", RequestStatus.CHANGES_REQUESTED, RequestPriority.MEDIUM, "team_science"),
        ]

    def list(self, page: int, page_size: int) -> PaginatedResponse[RequestRecord]:
        start = (page - 1) * page_size
        end = start + page_size
        items = self._items[start:end]
        return PaginatedResponse[RequestRecord].create(
            items=items,
            page=page,
            page_size=page_size,
            total_count=len(self._items),
        )

    def create_draft(self, payload: CreateRequestDraft) -> RequestRecord:
        next_id = f"req_{len(self._items) + 1:03d}"
        record = RequestRecord.model_validate(
            {
                "id": next_id,
                "tenant_id": "tenant_demo",
                "request_type": "custom",
                "template_id": payload.template_id,
                "template_version": payload.template_version,
                "title": payload.title,
                "summary": payload.summary,
                "status": RequestStatus.DRAFT,
                "priority": payload.priority,
                "submitter_id": "user_demo",
                "policy_context": {},
                "input_payload": payload.input_payload,
                "tags": [],
                "created_at": "2026-03-30T00:00:00Z",
                "created_by": "user_demo",
                "updated_at": "2026-03-30T00:00:00Z",
                "updated_by": "user_demo",
                "version": 1,
                "is_archived": False,
            }
        )
        self._items.insert(0, record)
        return record


request_repository = InMemoryRequestRepository()
