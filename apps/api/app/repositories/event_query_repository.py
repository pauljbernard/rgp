"""Event query repository — owns event ledger and outbox read operations.

Delegates to governance_repository for now; the actual method implementations
will be migrated here incrementally as the monolith is decomposed.
"""

from __future__ import annotations

from app.models.common import PaginatedResponse
from app.models.governance import EventLedgerRecord, EventOutboxRecord
from app.repositories.governance_repository import governance_repository


class EventQueryRepository:
    """Encapsulates event ledger and outbox queries."""

    def list_event_ledger(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        request_id: str | None = None,
        run_id: str | None = None,
        artifact_id: str | None = None,
        promotion_id: str | None = None,
        check_run_id: str | None = None,
        event_type: str | None = None,
    ) -> PaginatedResponse[EventLedgerRecord]:
        return governance_repository.list_event_ledger(
            page=page, page_size=page_size, tenant_id=tenant_id,
            request_id=request_id, run_id=run_id, artifact_id=artifact_id,
            promotion_id=promotion_id, check_run_id=check_run_id, event_type=event_type,
        )

    def list_event_outbox(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        request_id: str | None = None,
        status: str | None = None,
        topic: str | None = None,
    ) -> PaginatedResponse[EventOutboxRecord]:
        return governance_repository.list_event_outbox(
            page=page, page_size=page_size, tenant_id=tenant_id,
            request_id=request_id, status=status, topic=topic,
        )


event_query_repository = EventQueryRepository()
