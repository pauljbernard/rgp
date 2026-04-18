from __future__ import annotations

from datetime import datetime, timezone

from app.db.models import RequestEventTable, RequestTable
from app.db.session import SessionLocal
from app.models.request import RequestRecord, RequestStatus


def get_request_state(request_id: str, tenant_id: str | None) -> RequestRecord | None:
    with SessionLocal() as session:
        row = session.get(RequestTable, request_id)
        if row is not None:
            if tenant_id is not None and row.tenant_id != tenant_id:
                return None
            from app.repositories.governance_repository import governance_repository

            return governance_repository._request_from_row(row)

    from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

    dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
    if tenant_id is not None:
        item = dynamodb_adapter._get_request_item(tenant_id, request_id)
    else:
        item = next(
            (
                candidate
                for candidate in dynamodb_adapter._scan_items()
                if candidate.get("record_type") == "request" and candidate.get("id") == request_id
            ),
            None,
        )
    if item is None:
        return None
    return dynamodb_adapter._request_item_to_record(item)


def update_request_state(request_id: str, tenant_id: str, actor_id: str, **updates) -> RequestRecord:
    now = datetime.now(timezone.utc)
    with SessionLocal() as session:
        row = session.get(RequestTable, request_id)
        if row is not None:
            if row.tenant_id != tenant_id:
                raise PermissionError(f"Tenant {tenant_id} cannot access request {request_id}")
            for field, value in updates.items():
                setattr(row, field, value.value if isinstance(value, RequestStatus) else value)
            row.updated_at = updates.get("updated_at", now)
            row.updated_by = updates.get("updated_by", actor_id)
            row.version = updates.get("version", row.version + 1)
            session.commit()
            session.refresh(row)
            from app.repositories.governance_repository import governance_repository

            return governance_repository._request_from_row(row)

    from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

    dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
    item = dynamodb_adapter._get_request_item(tenant_id, request_id)
    if item is None:
        raise StopIteration(request_id)
    record = dynamodb_adapter._request_item_to_record(item)
    normalized_updates = {
        **updates,
        "updated_at": updates.get("updated_at", now),
        "updated_by": updates.get("updated_by", actor_id),
        "version": updates.get("version", record.version + 1),
    }
    updated = record.model_copy(update=normalized_updates)
    dynamodb_adapter._put_request_item(dynamodb_adapter._request_record_to_item(updated))
    return updated


def record_request_event(
    request_id: str,
    tenant_id: str,
    actor: str,
    action: str,
    reason_or_evidence: str,
    *,
    status: str | None = None,
) -> None:
    request = get_request_state(request_id, tenant_id)
    event_status = status or (request.status.value if request is not None and hasattr(request.status, "value") else str(request.status) if request is not None else None)

    with SessionLocal() as session:
        session.add(
            RequestEventTable(
                request_id=request_id,
                timestamp=datetime.now(timezone.utc),
                actor=actor,
                action=action,
                object_type="request",
                object_id=request_id,
                reason_or_evidence=reason_or_evidence,
            )
        )
        from app.services.event_store_service import event_store_service

        event_store_service.append(
            session,
            tenant_id=tenant_id,
            event_type="request.event_recorded",
            aggregate_type="request",
            aggregate_id=request_id,
            request_id=request_id,
            actor=actor,
            detail=action,
            payload={"reason_or_evidence": reason_or_evidence, "status": event_status},
        )
        session.commit()

    if request is not None:
        from app.persistence.dynamodb_governance_adapter import DynamoDbGovernancePersistenceAdapter

        dynamodb_adapter = DynamoDbGovernancePersistenceAdapter()
        if dynamodb_adapter._get_request_item(tenant_id, request_id) is not None:
            dynamodb_adapter._put_request_event(
                tenant_id=tenant_id,
                request_id=request_id,
                actor_id=actor,
                action=action,
                reason_or_evidence=reason_or_evidence,
            )
