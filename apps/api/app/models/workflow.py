"""Pydantic models for the workflow execution engine."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from app.models.common import RgpModel


class WorkflowExecutionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class WorkflowStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class WorkflowCommand(StrEnum):
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    RETRY_STEP = "retry_step"
    SKIP_STEP = "skip_step"


class WorkflowDefinitionStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

class WorkflowStepDefinition(RgpModel):
    name: str
    type: str = "action"
    config: dict[str, Any] = {}
    timeout_seconds: int | None = None
    retry_max: int = 0


class WorkflowDefinitionRecord(RgpModel):
    id: str
    tenant_id: str
    name: str
    version: str
    template_id: str | None = None
    steps: list[WorkflowStepDefinition] = []
    status: str = WorkflowDefinitionStatus.DRAFT
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowStepExecutionRecord(RgpModel):
    id: str
    workflow_execution_id: str
    step_index: int
    step_name: str
    status: str = WorkflowStepStatus.PENDING
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    error_message: str | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class WorkflowExecutionRecord(RgpModel):
    id: str
    tenant_id: str
    run_id: str
    request_id: str
    workflow_definition_id: str | None = None
    status: str = WorkflowExecutionStatus.QUEUED
    current_step_index: int = 0
    pause_reason: str | None = None
    cancel_reason: str | None = None
    failure_reason: str | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    paused_at: datetime | None = None
    resumed_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowExecutionDetail(WorkflowExecutionRecord):
    steps: list[WorkflowStepExecutionRecord] = []
    definition: WorkflowDefinitionRecord | None = None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class WorkflowCommandRequest(RgpModel):
    actor_id: str
    command: WorkflowCommand
    reason: str = ""
    step_index: int | None = None
