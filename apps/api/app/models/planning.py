"""Pydantic models for planning constructs."""
from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from app.models.common import RgpModel

class PlanningConstructType(StrEnum):
    INITIATIVE = "initiative"
    PROGRAM = "program"
    RELEASE = "release"
    MILESTONE = "milestone"
    CAMPAIGN = "campaign"

class PlanningConstructRecord(RgpModel):
    id: str
    tenant_id: str
    type: str
    name: str
    description: str | None = None
    owner_team_id: str | None = None
    status: str = "active"
    priority: int = 0
    target_date: datetime | None = None
    capacity_budget: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

class PlanningMembershipRecord(RgpModel):
    id: str
    planning_construct_id: str
    request_id: str
    sequence: int = 0
    priority: int = 0
    added_at: datetime | None = None

class CreatePlanningConstructRequest(RgpModel):
    type: PlanningConstructType
    name: str
    description: str | None = None
    owner_team_id: str | None = None
    priority: int = 0
    target_date: datetime | None = None
    capacity_budget: int | None = None
