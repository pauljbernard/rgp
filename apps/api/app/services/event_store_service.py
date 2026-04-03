from datetime import datetime, timezone

from app.db.models import EventStoreTable
from app.services.event_publisher_service import event_publisher_service


class EventStoreService:
    def append(
        self,
        session,
        *,
        tenant_id: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        actor: str,
        detail: str,
        request_id: str | None = None,
        run_id: str | None = None,
        artifact_id: str | None = None,
        promotion_id: str | None = None,
        check_run_id: str | None = None,
        payload: dict | None = None,
    ) -> None:
        event_row = EventStoreTable(
                tenant_id=tenant_id,
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                request_id=request_id,
                run_id=run_id,
                artifact_id=artifact_id,
                promotion_id=promotion_id,
                check_run_id=check_run_id,
                actor=actor,
                detail=detail,
                payload=payload or {},
                occurred_at=datetime.now(timezone.utc),
            )
        session.add(event_row)
        session.flush()
        event_publisher_service.enqueue(session, event_row.id)


event_store_service = EventStoreService()
