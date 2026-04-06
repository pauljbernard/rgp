from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from app.core.auth import ensure_roles, get_principal
from app.models.common import PaginatedResponse
from app.models.governance import AuditEntry, RunCommandRequest, RunDetail, RunRecord
from app.models.security import Principal, PrincipalRole
from app.services.governance_service import governance_service
from app.services.idempotency_service import idempotency_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[RunRecord])
def list_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = Query(default=None),
    workflow: str | None = Query(default=None),
    owner: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    federation: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[RunRecord]:
    return governance_service.list_runs(page, page_size, status, workflow, owner, request_id, federation, principal.tenant_id)


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> RunDetail:
    try:
        return governance_service.get_run(run_id, principal)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Run not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/{run_id}/history", response_model=list[AuditEntry])
def get_run_history(run_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> list[AuditEntry]:
    try:
        return governance_service.get_run_history(run_id, principal)
    except StopIteration:
        raise HTTPException(status_code=404, detail="Run not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/{run_id}/commands", response_model=RunDetail)
def command_run(
    run_id: str,
    payload: RunCommandRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RunDetail:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"runs:{run_id}:commands",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RunDetail,
            operation=lambda: governance_service.command_run(run_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=404, detail="Run not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
