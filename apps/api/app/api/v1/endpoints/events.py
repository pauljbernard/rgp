import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse

from app.core.auth import get_principal
from app.models.security import Principal
from app.services.governance_service import governance_service

router = APIRouter()


@router.get("/ledger")
def list_event_ledger(
    principal: Annotated[Principal, Depends(get_principal)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_id: str | None = Query(default=None),
    run_id: str | None = Query(default=None),
    artifact_id: str | None = Query(default=None),
    promotion_id: str | None = Query(default=None),
    check_run_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
):
    return governance_service.list_event_ledger(
        page=page,
        page_size=page_size,
        principal=principal,
        request_id=request_id,
        run_id=run_id,
        artifact_id=artifact_id,
        promotion_id=promotion_id,
        check_run_id=check_run_id,
        event_type=event_type,
    )


@router.get("/outbox")
def list_event_outbox(
    principal: Annotated[Principal, Depends(get_principal)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    request_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    topic: str | None = Query(default=None),
):
    return governance_service.list_event_outbox(
        page=page,
        page_size=page_size,
        principal=principal,
        request_id=request_id,
        status=status,
        topic=topic,
    )


@router.get("/check-runs")
async def stream_check_runs(
    request: Request,
    principal: Annotated[Principal, Depends(get_principal)],
    request_id: str | None = Query(default=None),
    promotion_id: str | None = Query(default=None),
) -> StreamingResponse:
    if bool(request_id) == bool(promotion_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Specify exactly one of request_id or promotion_id")

    async def event_stream():
        last_payload = None
        while True:
            if await request.is_disconnected():
                break
            try:
                if request_id:
                    rows = governance_service.list_request_check_runs(request_id, principal)
                else:
                    rows = governance_service.list_promotion_check_runs(promotion_id or "", principal)
            except StopIteration:
                yield "event: error\ndata: not_found\n\n"
                break
            except PermissionError:
                yield "event: error\ndata: forbidden\n\n"
                break

            payload = json.dumps([row.model_dump(mode="json") for row in rows], sort_keys=True)
            if payload != last_payload:
                yield f"event: check-runs\ndata: {payload}\n\n"
                last_payload = payload
            else:
                yield ": keep-alive\n\n"
            await asyncio.sleep(1.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
