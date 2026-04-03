import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Header, HTTPException, Request, status

from app.core.config import settings
from app.models.governance import RunDetail, RuntimeRunCallbackRequest
from app.services.governance_service import governance_service

router = APIRouter()


def _parse_callback_timestamp(raw_timestamp: str | None) -> datetime:
    if not raw_timestamp:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing runtime callback timestamp")
    try:
        parsed = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid runtime callback timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _verify_runtime_callback(raw_body: bytes, secret_header: str | None, signature_header: str | None, timestamp_header: str | None) -> None:
    if signature_header:
        callback_timestamp = _parse_callback_timestamp(timestamp_header)
        now = datetime.now(timezone.utc)
        if abs(now - callback_timestamp) > timedelta(seconds=settings.runtime_callback_max_skew_seconds):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Runtime callback timestamp outside allowed skew")
        expected = hmac.new(
            settings.runtime_callback_hmac_secret.encode("utf-8"),
            timestamp_header.encode("utf-8") + b"." + raw_body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature_header, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid runtime callback signature")
        return
    if secret_header != settings.runtime_callback_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid runtime callback credentials")


@router.post("/mock/deployments/{environment}", status_code=status.HTTP_200_OK)
def execute_mock_deployment(environment: str, payload: dict = Body(default_factory=dict)) -> dict:
    request_id = payload.get("request_id", "unknown")
    promotion_id = payload.get("promotion_id", "unknown")
    return {
        "status": "deployed",
        "environment": environment,
        "deployment_id": f"dep_{promotion_id}_{environment}",
        "target_url": f"https://{environment}.mock.rgp.local/deployments/{request_id}",
        "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": f"Deployment accepted for {request_id} in {environment}",
    }


@router.post("/mock/runs/{environment}", status_code=status.HTTP_200_OK)
def execute_mock_run_dispatch(environment: str, payload: dict = Body(default_factory=dict)) -> dict:
    request_id = payload.get("request_id", "unknown")
    run_id = payload.get("run_id", "unknown")
    dispatch_type = payload.get("dispatch_type", "enqueue")
    return {
        "status": "accepted",
        "environment": environment,
        "dispatch_id": f"rtd_{run_id}_{dispatch_type}",
        "target_url": f"https://{environment}.mock.rgp.local/runs/{run_id}",
        "received_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "summary": f"Runtime accepted {dispatch_type} for {request_id}/{run_id}",
    }


@router.post("/mock/events/{topic:path}", status_code=status.HTTP_202_ACCEPTED)
def publish_mock_event(topic: str, payload: dict = Body(default_factory=dict)) -> dict:
    event_id = payload.get("event_id", "unknown")
    partition_key = payload.get("partition_key", "unknown")
    return {
        "status": "accepted",
        "topic": topic,
        "event_id": event_id,
        "partition_key": partition_key,
        "accepted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "delivery_id": f"evt_{topic.replace('/', '_')}_{event_id}",
    }


@router.post("/callbacks/runs/{run_id}", response_model=RunDetail, status_code=status.HTTP_200_OK)
async def reconcile_runtime_run(
    run_id: str,
    request: Request,
    payload: RuntimeRunCallbackRequest,
    x_rgp_runtime_secret: str | None = Header(default=None),
    x_rgp_runtime_signature: str | None = Header(default=None),
    x_rgp_runtime_timestamp: str | None = Header(default=None),
) -> RunDetail:
    raw_body = await request.body()
    _verify_runtime_callback(raw_body, x_rgp_runtime_secret, x_rgp_runtime_signature, x_rgp_runtime_timestamp)
    try:
        return governance_service.reconcile_run(run_id, payload)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
