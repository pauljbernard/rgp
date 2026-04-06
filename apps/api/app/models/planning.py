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


class AddPlanningMembershipRequest(RgpModel):
    request_id: str
    sequence: int = 0
    priority: int = 0


class UpdatePlanningMembershipRequest(RgpModel):
    sequence: int = 0
    priority: int = 0


class PlanningProgressRecord(RgpModel):
    construct_id: str
    total: int
    status_counts: dict[str, int]
    completion_pct: float


class PlanningRoadmapEntry(RgpModel):
    id: str
    type: str
    name: str
    status: str
    priority: int
    target_date: str | None = None
    capacity_budget: int | None = None
    member_count: int
    completion_pct: float = 0.0
    completed_count: int = 0
    in_progress_count: int = 0
    blocked_count: int = 0
    schedule_state: str = "unscheduled"
    owner_team_id: str | None = None


class PlanningConstructDetail(RgpModel):
    construct: PlanningConstructRecord
    memberships: list[PlanningMembershipRecord]
    progress: PlanningProgressRecord

class CreatePlanningConstructRequest(RgpModel):
    type: PlanningConstructType
    name: str
    description: str | None = None
    owner_team_id: str | None = None
    priority: int = 0
    target_date: datetime | None = None
    capacity_budget: int | None = None
