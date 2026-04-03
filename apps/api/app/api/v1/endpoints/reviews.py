from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.core.auth import ensure_roles, get_principal
from app.models.common import PaginatedResponse
from app.models.governance import ReviewAssignmentOverrideRequest, ReviewDecisionRequest, ReviewQueueItem
from app.models.security import Principal, PrincipalRole
from app.services.governance_service import governance_service
from app.services.idempotency_service import idempotency_service

router = APIRouter()


@router.get("/queue", response_model=PaginatedResponse[ReviewQueueItem])
def list_review_queue(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    assigned_reviewer: str | None = Query(default=None),
    blocking_only: bool = Query(default=False),
    stale_only: bool = Query(default=False),
    request_id: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[ReviewQueueItem]:
    return governance_service.list_review_queue(page, page_size, assigned_reviewer, blocking_only, stale_only, request_id, principal.tenant_id)


@router.post("/queue/{review_id}/decision", response_model=ReviewQueueItem, status_code=status.HTTP_200_OK)
def record_review_decision(
    review_id: str,
    payload: ReviewDecisionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ReviewQueueItem:
    try:
        ensure_roles(principal, PrincipalRole.REVIEWER, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"reviews:{review_id}:decision",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=ReviewQueueItem,
            operation=lambda: governance_service.record_review_decision(review_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review item not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/queue/{review_id}/override-assignment", response_model=ReviewQueueItem, status_code=status.HTTP_200_OK)
def override_review_assignment(
    review_id: str,
    payload: ReviewAssignmentOverrideRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ReviewQueueItem:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"reviews:{review_id}:override-assignment",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=ReviewQueueItem,
            operation=lambda: governance_service.override_review_assignment(review_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review item not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
