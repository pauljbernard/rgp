from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import get_principal
from app.models.planning import (
    AddPlanningMembershipRequest,
    CreatePlanningConstructRequest,
    PlanningConstructDetail,
    PlanningConstructRecord,
    PlanningMembershipRecord,
    PlanningRoadmapEntry,
    UpdatePlanningMembershipRequest,
)
from app.models.security import Principal
from app.services.planning_service import planning_service


router = APIRouter()


@router.get("", response_model=list[PlanningConstructRecord])
def list_planning_constructs(
    type: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return planning_service.list_constructs(principal.tenant_id, type=type)


@router.post("", response_model=PlanningConstructRecord, status_code=201)
def create_planning_construct(
    payload: CreatePlanningConstructRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return planning_service.create_construct(payload, actor_id=principal.user_id, tenant_id=principal.tenant_id)


@router.get("/roadmap", response_model=list[PlanningRoadmapEntry])
def get_planning_roadmap(
    type: str | None = Query(default=None),
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return planning_service.get_roadmap_view(principal.tenant_id, type=type)


@router.get("/{construct_id}", response_model=PlanningConstructDetail)
def get_planning_construct(
    construct_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        detail = planning_service.get_construct_detail(construct_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Planning construct not found") from exc
    if detail.construct.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=404, detail="Planning construct not found")
    return detail


@router.post("/{construct_id}/memberships", response_model=PlanningMembershipRecord, status_code=201)
def add_planning_membership(
    construct_id: str,
    payload: AddPlanningMembershipRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        detail = planning_service.get_construct_detail(construct_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Planning construct not found") from exc
    if detail.construct.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=404, detail="Planning construct not found")
    return planning_service.add_request(
        construct_id,
        payload.request_id,
        sequence=payload.sequence,
        priority=payload.priority,
    )


@router.post("/{construct_id}/memberships/{request_id}", response_model=PlanningMembershipRecord)
def update_planning_membership(
    construct_id: str,
    request_id: str,
    payload: UpdatePlanningMembershipRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        detail = planning_service.get_construct_detail(construct_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Planning construct not found") from exc
    if detail.construct.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=404, detail="Planning construct not found")
    rows = planning_service.reorder_requests(
        construct_id,
        [{"request_id": request_id, "sequence": payload.sequence, "priority": payload.priority}],
    )
    for row in rows:
        if row.request_id == request_id:
            return row
    raise HTTPException(status_code=404, detail="Planning membership not found")


@router.delete("/{construct_id}/memberships/{request_id}", status_code=204)
def remove_planning_membership(
    construct_id: str,
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    try:
        detail = planning_service.get_construct_detail(construct_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Planning construct not found") from exc
    if detail.construct.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=404, detail="Planning construct not found")
    try:
        planning_service.remove_request(construct_id, request_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Planning membership not found") from exc
    return None
