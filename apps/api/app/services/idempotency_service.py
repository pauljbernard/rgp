import hashlib
import json
from datetime import datetime, timezone
from typing import Callable, TypeVar

from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import IdempotencyKeyTable
from app.db.session import SessionLocal
from app.models.security import Principal

T = TypeVar("T", bound=BaseModel)


class IdempotencyService:
    @staticmethod
    def _payload_hash(payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def replay_or_execute(
        self,
        *,
        idempotency_key: str | None,
        scope: str,
        principal: Principal,
        payload: dict,
        response_model: type[T],
        operation: Callable[[], T],
    ) -> T:
        if not idempotency_key:
            return operation()

        payload_hash = self._payload_hash(payload)
        with SessionLocal() as session:
            existing = session.scalars(
                select(IdempotencyKeyTable).where(
                    IdempotencyKeyTable.tenant_id == principal.tenant_id,
                    IdempotencyKeyTable.scope == scope,
                    IdempotencyKeyTable.idempotency_key == idempotency_key,
                )
            ).first()
            if existing is not None:
                if existing.payload_hash != payload_hash:
                    raise ValueError("Idempotency-Key reuse with different payload")
                return response_model.model_validate(existing.response_body)

        result = operation()

        with SessionLocal() as session:
            session.add(
                IdempotencyKeyTable(
                    tenant_id=principal.tenant_id,
                    actor_id=principal.user_id,
                    scope=scope,
                    idempotency_key=idempotency_key,
                    payload_hash=payload_hash,
                    response_status=200,
                    response_body=result.model_dump(mode="json", by_alias=True),
                    created_at=datetime.now(timezone.utc),
                )
            )
            session.commit()

        return result


idempotency_service = IdempotencyService()
