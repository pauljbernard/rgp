"""Pydantic models for collaboration mode governance."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from app.models.common import RgpModel


class CollaborationMode(StrEnum):
    HUMAN_LED = "human_led"
    AGENT_ASSISTED = "agent_assisted"
    AGENT_LED = "agent_led"


class ModeTransitionRecord(RgpModel):
    id: str
    tenant_id: str
    request_id: str
    from_mode: str
    to_mode: str
    actor: str
    reason: str | None = None
    policy_basis: dict | None = None
    created_at: datetime | None = None


class SwitchModeRequest(RgpModel):
    actor_id: str
    target_mode: CollaborationMode
    reason: str = ""
