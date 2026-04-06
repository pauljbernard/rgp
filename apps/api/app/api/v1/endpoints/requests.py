from typing import Annotated

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.core.auth import ensure_roles, get_principal
from app.models.common import PaginatedResponse
from app.models.governance import AgentSessionContextDetail, AgentSessionDetail, AgentSessionMessageCreateRequest, AgentSessionRecord, AssignAgentSessionRequest, AuditEntry, CompleteAgentSessionRequest, IntegrationRecord, RequestDetail, UpdateAgentSessionGovernanceRequest
from app.models.federation import ProjectionMappingRecord
from app.models.request import AmendRequest, CancelRequest, CloneRequest, CreateRequestDraft, RequestCheckRun, RequestRecord, SubmitRequest, SupersedeRequest, TransitionRequest
from app.models.security import Principal, PrincipalRole
from app.services.idempotency_service import idempotency_service
from app.services.governance_service import governance_service
from app.services.request_service import request_service


router = APIRouter()


@router.get("", response_model=PaginatedResponse[RequestRecord])
def list_requests(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: str | None = Query(default=None),
    owner_team_id: str | None = Query(default=None),
    workflow: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    federation: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> PaginatedResponse[RequestRecord]:
    return governance_service.list_requests(
        page=page,
        page_size=page_size,
        status=status,
        owner_team_id=owner_team_id,
        workflow=workflow,
        request_id=request_id,
        federation=federation,
        tenant_id=principal.tenant_id,
    )


@router.post("", response_model=RequestRecord, status_code=status.HTTP_201_CREATED)
def create_request_draft(
    payload: CreateRequestDraft,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
    try:
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope="requests:create-draft",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.create_draft(payload, principal),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/submit", response_model=RequestRecord)
def submit_request(
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
    payload: SubmitRequest | None = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload or SubmitRequest()
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"requests:{request_id}:submit",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.submit(request_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/amend", response_model=RequestRecord)
def amend_request(
    request_id: str,
    payload: AmendRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"requests:{request_id}:amend",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.amend(request_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/cancel", response_model=RequestRecord)
def cancel_request(
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
    payload: CancelRequest | None = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload or CancelRequest()
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"requests:{request_id}:cancel",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.cancel(request_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/transition", response_model=RequestRecord)
def transition_request(
    request_id: str,
    payload: TransitionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"requests:{request_id}:transition",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.transition(request_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/checks/run", response_model=RequestRecord)
def run_request_checks(
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
    payload: RequestCheckRun | None = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload or RequestCheckRun()
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"requests:{request_id}:checks:run",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.run_checks(request_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/clone", response_model=RequestRecord, status_code=status.HTTP_201_CREATED)
def clone_request(
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
    payload: CloneRequest | None = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload or CloneRequest()
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"requests:{request_id}:clone",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.clone(request_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/supersede", response_model=RequestRecord)
def supersede_request(
    request_id: str,
    payload: SupersedeRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> RequestRecord:
    try:
        ensure_roles(principal, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return idempotency_service.replay_or_execute(
            idempotency_key=idempotency_key,
            scope=f"requests:{request_id}:supersede",
            principal=principal,
            payload=payload.model_dump(mode="json"),
            response_model=RequestRecord,
            operation=lambda: request_service.supersede(request_id, payload, principal),
        )
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{request_id}", response_model=RequestDetail)
def get_request(request_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> RequestDetail:
    try:
        return governance_service.get_request(request_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{request_id}/history", response_model=list[AuditEntry])
def get_request_history(request_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> list[AuditEntry]:
    try:
        return governance_service.list_audit_entries(request_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{request_id}/projections", response_model=list[ProjectionMappingRecord])
def list_request_projections(request_id: str, principal: Annotated[Principal, Depends(get_principal)]) -> list[ProjectionMappingRecord]:
    try:
        return governance_service.list_request_projections(request_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{request_id}/agent-integrations", response_model=list[IntegrationRecord])
def list_request_agent_integrations(
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> list[IntegrationRecord]:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        return governance_service.list_agent_integrations_for_request(request_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{request_id}/agent-assignment-preview", response_model=AgentSessionContextDetail)
def get_request_agent_assignment_preview(
    request_id: str,
    integration_id: str = Query(...),
    collaboration_mode: str = Query(default="agent_assisted"),
    agent_operating_profile: str = Query(default="general"),
    principal: Annotated[Principal, Depends(get_principal)] = None,
) -> AgentSessionContextDetail:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        return governance_service.preview_agent_assignment_context(
            request_id,
            integration_id,
            collaboration_mode,
            agent_operating_profile,
            principal,
        )
    except StopIteration as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not found: {exc.args[0]}") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{request_id}/agent-sessions", response_model=AgentSessionRecord, status_code=status.HTTP_201_CREATED)
def assign_agent_session(
    request_id: str,
    payload: AssignAgentSessionRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> AgentSessionRecord:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return governance_service.assign_agent_session(request_id, payload, principal)
    except StopIteration as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Not found: {exc.args[0]}") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{request_id}/agent-sessions/{session_id}", response_model=AgentSessionDetail)
def get_agent_session(
    request_id: str,
    session_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> AgentSessionDetail:
    try:
        return governance_service.get_agent_session(request_id, session_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent session not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("/{request_id}/agent-sessions/{session_id}/context", response_model=AgentSessionContextDetail)
def get_agent_session_context(
    request_id: str,
    session_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> AgentSessionContextDetail:
    try:
        return governance_service.get_agent_session_context(request_id, session_id, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent session not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post("/{request_id}/agent-sessions/{session_id}/complete", response_model=AgentSessionDetail)
def complete_agent_session(
    request_id: str,
    session_id: str,
    payload: CompleteAgentSessionRequest | None,
    principal: Annotated[Principal, Depends(get_principal)],
) -> AgentSessionDetail:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        resolved_payload = (payload or CompleteAgentSessionRequest()).model_copy(update={"actor_id": principal.user_id})
        return governance_service.complete_agent_session(request_id, session_id, resolved_payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent session not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/agent-sessions/{session_id}/messages", response_model=AgentSessionDetail)
def post_agent_session_message(
    request_id: str,
    session_id: str,
    payload: AgentSessionMessageCreateRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> AgentSessionDetail:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return governance_service.post_agent_session_message(request_id, session_id, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent session not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{request_id}/agent-sessions/{session_id}/governance", response_model=AgentSessionDetail)
def update_agent_session_governance(
    request_id: str,
    session_id: str,
    payload: UpdateAgentSessionGovernanceRequest,
    principal: Annotated[Principal, Depends(get_principal)],
) -> AgentSessionDetail:
    try:
        ensure_roles(principal, PrincipalRole.SUBMITTER, PrincipalRole.OPERATOR, PrincipalRole.ADMIN)
        payload = payload.model_copy(update={"actor_id": principal.user_id})
        return governance_service.update_agent_session_governance(request_id, session_id, payload, principal)
    except StopIteration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent session not found") from None
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{request_id}/agent-sessions/{session_id}/stream")
def stream_agent_session_response(
    request_id: str,
    session_id: str,
    principal: Annotated[Principal, Depends(get_principal)],
) -> StreamingResponse:
    def event_stream():
        try:
            for event in governance_service.stream_agent_session_response(request_id, session_id, principal):
                payload = json.dumps(event["data"])
                yield f"event: {event['event']}\ndata: {payload}\n\n"
        except StopIteration:
            yield "event: error\ndata: {\"message\":\"Agent session not found\"}\n\n"
        except PermissionError as exc:
            payload = json.dumps({"message": str(exc)})
            yield f"event: error\ndata: {payload}\n\n"
        except ValueError as exc:
            payload = json.dumps({"message": str(exc)})
            yield f"event: error\ndata: {payload}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
