from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.auth import ensure_roles, get_principal
from app.models.governance import CheckEvaluationRequest, CheckOverrideRequest, CheckRunRequest, PromotionActionRequest, PromotionApprovalOverrideRequest, PromotionDetail
from app.models.security import Principal, PrincipalRole
from app.services.governance_service import governance_service
from app.services.idempotency_service import idempotency_service

router = APIRouter()


@router.get("/{promotion_id}", response_model=PromotionDetail)
def get_promotion(promotion_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> PromotionDetail:
    try:
        return governance_service.get_promotion(promotion_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{promotion_id}/actions", response_model=PromotionDetail, status_code=status.HTTP_200_OK)
def apply_promotion_action(
    promotion_id: str,
    payload: PromotionActionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PromotionDetail:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"promotions:{promotion_id}:actions",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=PromotionDetail,
            operation=lambda: governance_service.apply_promotion_action(promotion_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{promotion_id}/checks/{check_id}/evaluate", response_model=PromotionDetail, status_code=status.HTTP_200_OK)
def evaluate_check(
    promotion_id: str,
    check_id: str,
    payload: CheckEvaluationRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PromotionDetail:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"promotions:{promotion_id}:checks:{check_id}:evaluate",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=PromotionDetail,
            operation=lambda: governance_service.evaluate_check(promotion_id, check_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{promotion_id}/checks/{check_id}/override", response_model=PromotionDetail, status_code=status.HTTP_200_OK)
def override_check(
    promotion_id: str,
    check_id: str,
    payload: CheckOverrideRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PromotionDetail:
    try:
        ensure_roles(principal, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"promotions:{promotion_id}:checks:{check_id}:override",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=PromotionDetail,
            operation=lambda: governance_service.override_check(promotion_id, check_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{promotion_id}/checks/run", response_model=PromotionDetail, status_code=status.HTTP_200_OK)
def run_promotion_checks(
    promotion_id: str,
    payload: CheckRunRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PromotionDetail:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"promotions:{promotion_id}:checks:run",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=PromotionDetail,
            operation=lambda: governance_service.run_promotion_checks(promotion_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{promotion_id}/override-approval", response_model=PromotionDetail, status_code=status.HTTP_200_OK)
def override_promotion_approval(
    promotion_id: str,
    payload: PromotionApprovalOverrideRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> PromotionDetail:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"promotions:{promotion_id}:override-approval",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=PromotionDetail,
            operation=lambda: governance_service.override_promotion_approval(promotion_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
