"""Pydantic models for the extensible policy engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.common import RgpModel


class PolicyCondition(RgpModel):
    """JSON-serializable policy condition (evaluated by policy_dsl)."""
    field: str | None = None
    op: str = "eq"
    value: Any = None
    conditions: list[dict] | None = None
    condition: dict | None = None


class PolicyAction(RgpModel):
    """JSON-serializable policy action."""
    type: str
    reason: str | None = None
    target_team: str | None = None
    to: str | None = None
    reviewer: str | None = None
    workflow: str | None = None
    tag: str | None = None
    field: str | None = None
    value: Any = None


class PolicyRuleRecord(RgpModel):
    id: str
    tenant_id: str
    policy_id: str
    name: str
    condition: dict = {}
    actions: list[dict] = []
    priority: int = 0
    active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CreatePolicyRuleRequest(RgpModel):
    name: str
    condition: dict = {}
    actions: list[dict] = []
    priority: int = 0
    active: bool = True


class UpdatePolicyRuleRequest(RgpModel):
    name: str | None = None
    condition: dict | None = None
    actions: list[dict] | None = None
    priority: int | None = None
    active: bool | None = None


class CheckTypeDefinition(RgpModel):
    id: str
    tenant_id: str
    name: str
    handler_key: str
    config: dict | None = None
    severity: str = "required"
    status: str = "active"
    created_at: datetime | None = None


class CreateCheckTypeRequest(RgpModel):
    name: str
    handler_key: str
    config: dict | None = None
    severity: str = "required"
