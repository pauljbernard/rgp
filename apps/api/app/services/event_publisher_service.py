from datetime import datetime, timezone
import json
from urllib import error, request as urllib_request

from sqlalchemy import select

from app.core.config import settings
from app.db.models import EventOutboxTable, EventStoreTable


class EventPublisherService:
    def enqueue(self, session, event_store_id: int) -> None:
        event_row = session.get(EventStoreTable, event_store_id)
        if event_row is None:
            raise StopIteration(event_store_id)
        topic = self._topic_for(event_row.event_type)
        partition_key = event_row.request_id or event_row.run_id or event_row.artifact_id or event_row.promotion_id or event_row.aggregate_id
        session.add(
            EventOutboxTable(
                event_store_id=event_store_id,
                tenant_id=event_row.tenant_id,
                topic=topic,
                partition_key=partition_key,
                payload={
                    "event_id": event_row.id,
                    "event_type": event_row.event_type,
                    "aggregate_type": event_row.aggregate_type,
                    "aggregate_id": event_row.aggregate_id,
                    "tenant_id": event_row.tenant_id,
                    "request_id": event_row.request_id,
                    "run_id": event_row.run_id,
                    "artifact_id": event_row.artifact_id,
                    "promotion_id": event_row.promotion_id,
                    "check_run_id": event_row.check_run_id,
                    "actor": event_row.actor,
                    "detail": event_row.detail,
                    "payload": event_row.payload,
                    "occurred_at": event_row.occurred_at.isoformat().replace("+00:00", "Z"),
                },
                status="pending",
                backend=settings.event_bus_backend,
                error_message=None,
                created_at=datetime.now(timezone.utc),
                published_at=None,
            )
        )

    def publish_pending(self, session, limit: int = 100) -> int:
        rows = session.scalars(
            select(EventOutboxTable)
            .where(EventOutboxTable.status == "pending")
            .order_by(EventOutboxTable.id)
            .limit(limit)
        ).all()
        for row in rows:
            if not settings.event_bus_enabled:
                row.status = "deferred"
                row.error_message = "Event bus disabled; retained in outbox"
                continue
            try:
                self._publish_row(row)
                row.status = "published"
                row.published_at = datetime.now(timezone.utc)
                row.error_message = None
            except Exception as exc:  # pragma: no cover - defensive publish boundary
                row.status = "failed"
                row.error_message = str(exc)
        return len(rows)

    @staticmethod
    def _topic_for(event_type: str) -> str:
        event_family = event_type.split(".", 1)[0]
        return f"{settings.event_bus_topic_prefix}.{event_family}"

    def _publish_row(self, row: EventOutboxTable) -> None:
        if settings.event_bus_backend == "http":
            self._publish_http(row)
            return
        if settings.event_bus_backend == "outbox":
            return
        raise ValueError(f"Unsupported event bus backend: {settings.event_bus_backend}")

    @staticmethod
    def _publish_http(row: EventOutboxTable) -> None:
        if not settings.event_bus_http_endpoint:
            raise ValueError("HTTP event bus backend requires RGP_EVENT_BUS_HTTP_ENDPOINT")
        url = f"{settings.event_bus_http_endpoint.rstrip('/')}/{row.topic}"
        body = json.dumps(
            {
                "event_id": row.event_store_id,
                "topic": row.topic,
                "partition_key": row.partition_key,
                **(row.payload or {}),
            }
        ).encode("utf-8")
        request = urllib_request.Request(
            url=url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib_request.urlopen(request, timeout=5) as response:  # nosec B310 - endpoint is explicitly configured and validated before use
                status_code = response.getcode()
        except error.URLError as exc:
            raise RuntimeError(f"HTTP event publish failed: {exc}") from exc
        if status_code < 200 or status_code >= 300:
            raise RuntimeError(f"HTTP event publish returned unexpected status {status_code}")


event_publisher_service = EventPublisherService()
