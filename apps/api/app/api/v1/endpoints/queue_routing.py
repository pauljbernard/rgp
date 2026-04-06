from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.auth import get_principal
from app.models.queue_assignment import AssignmentGroupRecord, CreateAssignmentGroupRequest, CreateEscalationRuleRequest, CreateSlaDefinitionRequest, EscalationExecutionRecord, EscalationRuleRecord, RemediateSlaBreachRequest, RoutingRecommendationRecord, SlaBreachAuditRecord, SlaDefinitionRecord
from app.models.security import Principal
from app.services.queue_routing_service import queue_routing_service
from app.services.sla_enforcement_service import sla_enforcement_service

router = APIRouter()


@router.get("/groups", response_model=list[AssignmentGroupRecord])
def list_assignment_groups(
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return queue_routing_service.list_assignment_groups(principal.tenant_id)


@router.post("/groups", response_model=AssignmentGroupRecord, status_code=status.HTTP_201_CREATED)
def create_assignment_group(
    payload: CreateAssignmentGroupRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return queue_routing_service.create_assignment_group(payload.model_dump(), principal.tenant_id)


@router.get("/sla-definitions", response_model=list[SlaDefinitionRecord])
def list_sla_definitions(
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return sla_enforcement_service.list_sla_definitions(principal.tenant_id)


@router.post("/sla-definitions", response_model=SlaDefinitionRecord, status_code=status.HTTP_201_CREATED)
def create_sla_definition(
    payload: CreateSlaDefinitionRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return sla_enforcement_service.create_sla_definition(
        name=payload.name,
        scope_type=payload.scope_type,
        scope_id=payload.scope_id,
        response_hours=payload.response_target_hours,
        resolution_hours=payload.resolution_target_hours,
        review_hours=payload.review_deadline_hours,
        tenant_id=principal.tenant_id,
    )


@router.get("/escalation-rules", response_model=list[EscalationRuleRecord])
def list_escalation_rules(
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return queue_routing_service.list_escalation_rules(principal.tenant_id)


@router.post("/escalation-rules", response_model=EscalationRuleRecord, status_code=status.HTTP_201_CREATED)
def create_escalation_rule(
    payload: CreateEscalationRuleRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return queue_routing_service.create_escalation_rule(payload.model_dump(), principal.tenant_id)


@router.get("/sla-breaches", response_model=list[SlaBreachAuditRecord])
def list_sla_breaches(
    request_id: str | None = None,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return sla_enforcement_service.list_breaches(principal.tenant_id, request_id=request_id)


@router.post("/sla-breaches/{breach_id}/remediate", response_model=SlaBreachAuditRecord)
def remediate_sla_breach(
    breach_id: str,
    payload: RemediateSlaBreachRequest,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return sla_enforcement_service.remediate_breach(
        breach_id=breach_id,
        remediation_action=payload.remediation_action,
        tenant_id=principal.tenant_id,
        actor=principal.user_id,
    )


@router.get("/requests/{request_id}/recommendation", response_model=RoutingRecommendationRecord)
def get_routing_recommendation(
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    recommendation = queue_routing_service.recommend_assignment(request_id, principal.tenant_id)
    sla = sla_enforcement_service.evaluate_sla_compliance(request_id, principal.tenant_id)
    escalations = queue_routing_service.evaluate_escalations(request_id, principal.tenant_id)
    recommendation["sla_status"] = sla.get("status", "unknown")
    recommendation["escalation_targets"] = [item["escalation_target"] for item in escalations]
    return recommendation


@router.get("/requests/{request_id}/escalations", response_model=list[EscalationRuleRecord])
def list_request_escalations(
    request_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return queue_routing_service.evaluate_escalations(request_id, principal.tenant_id)


@router.post("/requests/{request_id}/escalations/{rule_id}/execute", response_model=EscalationExecutionRecord)
def execute_request_escalation(
    request_id: str,
    rule_id: str,
    principal: Annotated[Principal, Depends(get_principal)] = None,
):
    return queue_routing_service.execute_escalation(
        request_id=request_id,
        rule_id=rule_id,
        tenant_id=principal.tenant_id,
        actor=principal.user_id,
    )
