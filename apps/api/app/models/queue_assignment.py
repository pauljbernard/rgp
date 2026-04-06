"""Pydantic models for advanced queue routing and SLA enforcement."""
from __future__ import annotations
from datetime import datetime
from typing import Any
from app.models.common import RgpModel

class AssignmentGroupRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    skill_tags: list[str] = []
    max_capacity: int | None = None
    current_load: int = 0
    status: str = "active"
    created_at: datetime | None = None

class EscalationRuleRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    condition: dict[str, Any] = {}
    escalation_target: str = ""
    escalation_type: str = "reassign"
    delay_minutes: int = 60
    status: str = "active"
    created_at: datetime | None = None

class SlaDefinitionRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    scope_type: str
    scope_id: str | None = None
    response_target_hours: float | None = None
    resolution_target_hours: float | None = None
    review_deadline_hours: float | None = None
    warning_threshold_pct: int = 70
    status: str = "active"
    created_at: datetime | None = None

class SlaBreachAuditRecord(RgpModel):
    id: str
    tenant_id: str
    sla_definition_id: str
    request_id: str
    breach_type: str
    target_hours: float
    actual_hours: float
    severity: str
    remediation_action: str | None = None
    breached_at: datetime | None = None


class RoutingRecommendationRecord(RgpModel):
    request_id: str
    recommended_group_id: str | None = None
    recommended_group_name: str | None = None
    matched_skills: list[str] = []
    route_basis: list[str] = []
    current_load: int | None = None
    max_capacity: int | None = None
    sla_status: str = "unknown"
    escalation_targets: list[str] = []


class EscalationExecutionRecord(RgpModel):
    request_id: str
    rule_id: str
    escalation_type: str
    escalation_target: str
    outcome: str
    executed_at: datetime | None = None

class CreateAssignmentGroupRequest(RgpModel):
    name: str
    skill_tags: list[str] = []
    max_capacity: int | None = None

class CreateEscalationRuleRequest(RgpModel):
    name: str
    condition: dict[str, Any] = {}
    escalation_target: str
    escalation_type: str = "reassign"
    delay_minutes: int = 60


class CreateSlaDefinitionRequest(RgpModel):
    name: str
    scope_type: str
    scope_id: str | None = None
    response_target_hours: float | None = None
    resolution_target_hours: float | None = None
    review_deadline_hours: float | None = None


class RemediateSlaBreachRequest(RgpModel):
    remediation_action: str
