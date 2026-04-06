from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TenantTable(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class RequestTable(Base):
    __tablename__ = "requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_type: Mapped[str] = mapped_column(String(128), nullable=False)
    template_id: Mapped[str] = mapped_column(String(128), nullable=False)
    template_version: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    sla_policy_id: Mapped[str | None] = mapped_column(String(128))
    submitter_id: Mapped[str] = mapped_column(String(64), nullable=False)
    owner_team_id: Mapped[str | None] = mapped_column(String(64))
    owner_user_id: Mapped[str | None] = mapped_column(String(64))
    workflow_binding_id: Mapped[str | None] = mapped_column(String(128))
    current_run_id: Mapped[str | None] = mapped_column(String(64))
    policy_context: Mapped[dict] = mapped_column(JSON, default=dict)
    input_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TemplateTable(Base):
    __tablename__ = "templates"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    id: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    template_schema: Mapped[dict] = mapped_column("schema", JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class UserTable(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role_summary: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    password_hash: Mapped[str | None] = mapped_column(Text)
    password_reset_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    registration_request_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class OrganizationTable(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class TeamTable(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    organization_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class TeamMembershipTable(Base):
    __tablename__ = "team_memberships"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    team_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class PortfolioTable(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    owner_team_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class PortfolioScopeTable(Base):
    __tablename__ = "portfolio_scopes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    portfolio_id: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(128), nullable=False)


class RunTable(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    workflow: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    current_step: Mapped[str] = mapped_column(String(255), nullable=False)
    elapsed_time: Mapped[str] = mapped_column(String(64), nullable=False)
    waiting_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    owner_team: Mapped[str] = mapped_column(String(64), nullable=False)
    workflow_identity: Mapped[str] = mapped_column(String(255), nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    current_step_input_summary: Mapped[str] = mapped_column(Text, nullable=False)
    current_step_output_summary: Mapped[str] = mapped_column(Text, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    command_surface: Mapped[list[str]] = mapped_column(JSON, default=list)
    steps: Mapped[list[dict]] = mapped_column(JSON, default=list)
    run_context: Mapped[list[list[str]]] = mapped_column(JSON, default=list)
    conversation_thread_id: Mapped[str] = mapped_column(String(128), nullable=False)


class RuntimeDispatchTable(Base):
    __tablename__ = "runtime_dispatches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    integration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    dispatch_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    dispatched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class RuntimeSignalTable(Base):
    __tablename__ = "runtime_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    received_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class PerformanceMetricTable(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    metric_type: Mapped[str] = mapped_column(String(64), nullable=False)
    route: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_ms: Mapped[float] = mapped_column(nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64))
    span_id: Mapped[str | None] = mapped_column(String(64))
    correlation_id: Mapped[str | None] = mapped_column(String(128))
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class ArtifactTable(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    current_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    owner: Mapped[str] = mapped_column(String(64), nullable=False)
    review_state: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    versions: Mapped[list[dict]] = mapped_column(JSON, default=list)
    selected_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    stale_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ReviewQueueTable(Base):
    __tablename__ = "review_queue"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    review_scope: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_or_changeset: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    sla: Mapped[str] = mapped_column(String(128), nullable=False)
    blocking_status: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_reviewer: Mapped[str] = mapped_column(String(128), nullable=False)
    stale: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class PromotionTable(Base):
    __tablename__ = "promotions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy: Mapped[str] = mapped_column(String(255), nullable=False)
    required_checks: Mapped[list[dict]] = mapped_column(JSON, default=list)
    required_approvals: Mapped[list[dict]] = mapped_column(JSON, default=list)
    stale_warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    execution_readiness: Mapped[str] = mapped_column(Text, nullable=False)
    promotion_history: Mapped[list[dict]] = mapped_column(JSON, default=list)


class DeploymentExecutionTable(Base):
    __tablename__ = "deployment_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    integration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    executed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class CheckResultTable(Base):
    __tablename__ = "check_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_id: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluated_by: Mapped[str] = mapped_column(String(128), nullable=False)


class CheckOverrideTable(Base):
    __tablename__ = "check_overrides"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    check_result_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_id: Mapped[str | None] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    decided_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class CheckRunTable(Base):
    __tablename__ = "check_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    promotion_id: Mapped[str | None] = mapped_column(String(64))
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)
    enqueued_by: Mapped[str] = mapped_column(String(128), nullable=False)
    worker_task_id: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    queued_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class CapabilityTable(Base):
    __tablename__ = "capabilities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    owner: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    lineage: Mapped[list[str]] = mapped_column(JSON, default=list)
    usage: Mapped[list[list[str]]] = mapped_column(JSON, default=list)
    performance: Mapped[list[list[str]]] = mapped_column(JSON, default=list)
    history: Mapped[list[dict]] = mapped_column(JSON, default=list)


class PolicyTable(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(128), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class TransitionGateTable(Base):
    __tablename__ = "transition_gates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    policy_id: Mapped[str] = mapped_column(String(64), nullable=False)
    gate_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    transition_target: Mapped[str] = mapped_column(String(64), nullable=False)
    required_check_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gate_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class IntegrationTable(Base):
    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)


class AgentSessionTable(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    integration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    agent_label: Mapped[str] = mapped_column(String(255), nullable=False)
    collaboration_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="agent_assisted")
    agent_operating_profile: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    awaiting_human: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    external_session_ref: Mapped[str | None] = mapped_column(String(255))
    resume_request_status: Mapped[str | None] = mapped_column(String(32))
    assigned_by: Mapped[str] = mapped_column(String(128), nullable=False)
    assigned_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentSessionMessageTable(Base):
    __tablename__ = "agent_session_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, default="tenant_demo")
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(32), nullable=False)
    sender_id: Mapped[str] = mapped_column(String(128), nullable=False)
    message_type: Mapped[str] = mapped_column(String(32), nullable=False, default="message")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class IdempotencyKeyTable(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class EventStoreTable(Base):
    __tablename__ = "event_store"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64))
    run_id: Mapped[str | None] = mapped_column(String(64))
    artifact_id: Mapped[str | None] = mapped_column(String(64))
    promotion_id: Mapped[str | None] = mapped_column(String(64))
    check_run_id: Mapped[str | None] = mapped_column(String(64))
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class EventOutboxTable(Base):
    __tablename__ = "event_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_store_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    partition_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    backend: Mapped[str] = mapped_column(String(32), nullable=False, default="outbox")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class RequestEventTable(Base):
    __tablename__ = "request_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_or_evidence: Mapped[str] = mapped_column(Text, nullable=False)


class RequestRelationshipTable(Base):
    __tablename__ = "request_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)


class ArtifactEventTable(Base):
    __tablename__ = "artifact_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_version_id: Mapped[str | None] = mapped_column(String(64))
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)


class ArtifactLineageEdgeTable(Base):
    __tablename__ = "artifact_lineage_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[str] = mapped_column(String(64), nullable=False)
    from_version_id: Mapped[str | None] = mapped_column(String(64))
    to_version_id: Mapped[str] = mapped_column(String(64), nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Workflow execution engine tables
# ---------------------------------------------------------------------------

class WorkflowDefinitionTable(Base):
    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    template_id: Mapped[str | None] = mapped_column(String(64))
    steps: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkflowExecutionTable(Base):
    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    workflow_definition_id: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    current_step_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    step_states: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    pause_reason: Mapped[str | None] = mapped_column(Text)
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    paused_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    resumed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkflowStepExecutionTable(Base):
    __tablename__ = "workflow_step_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workflow_execution_id: Mapped[str] = mapped_column(String(64), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    input_payload: Mapped[dict | None] = mapped_column(JSON)
    output_payload: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


# ---------------------------------------------------------------------------
# Policy engine tables (Phase 2, Area A)
# ---------------------------------------------------------------------------

class PolicyRuleTable(Base):
    __tablename__ = "policy_rules"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    actions: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class CheckTypeDefinitionTable(Base):
    __tablename__ = "check_type_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    handler_key: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict | None] = mapped_column(JSON)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="required")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Collaboration mode tables (Phase 2, Area B)
# ---------------------------------------------------------------------------

class CollaborationModeTransitionTable(Base):
    __tablename__ = "collaboration_mode_transitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    from_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    to_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    policy_basis: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Context bundle tables (Phase 2, Area C)
# ---------------------------------------------------------------------------

class ContextBundleTable(Base):
    __tablename__ = "context_bundles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    bundle_type: Mapped[str] = mapped_column(String(32), nullable=False, default="assignment")
    contents: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    policy_scope: Mapped[dict | None] = mapped_column(JSON)
    assembled_by: Mapped[str] = mapped_column(String(128), nullable=False)
    assembled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)


class ContextAccessLogTable(Base):
    __tablename__ = "context_access_log"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    bundle_id: Mapped[str] = mapped_column(String(64), nullable=False)
    accessor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    accessor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    accessed_resource: Mapped[str] = mapped_column(String(255), nullable=False)
    access_result: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_basis: Mapped[dict | None] = mapped_column(JSON)
    accessed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Saga orchestration tables (Phase 2, Area D)
# ---------------------------------------------------------------------------

class SagaDefinitionTable(Base):
    __tablename__ = "saga_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    steps: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


class SagaExecutionTable(Base):
    __tablename__ = "saga_executions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    saga_definition_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    step_states: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    compensation_log: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


# ---------------------------------------------------------------------------
# Federation tables (Phase 2, Area E)
# ---------------------------------------------------------------------------

class ProjectionMappingTable(Base):
    __tablename__ = "projection_mappings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    integration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    external_system: Mapped[str] = mapped_column(String(128), nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(255))
    external_state: Mapped[dict | None] = mapped_column(JSON)
    projection_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    last_projected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))


class ReconciliationLogTable(Base):
    __tablename__ = "reconciliation_log"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    projection_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    resolved_by: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Phase 3: Domain pack tables (Area A)
# ---------------------------------------------------------------------------

class DomainPackTable(Base):
    __tablename__ = "domain_packs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    contributed_templates: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    contributed_artifact_types: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    contributed_workflows: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    contributed_policies: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    activated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class DomainPackInstallationTable(Base):
    __tablename__ = "domain_pack_installations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    pack_id: Mapped[str] = mapped_column(String(64), nullable=False)
    installed_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="installed")
    installed_by: Mapped[str] = mapped_column(String(128), nullable=False)
    installed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

# ---------------------------------------------------------------------------
# Phase 3: Workspace & change set tables (Area B)
# ---------------------------------------------------------------------------

class WorkspaceTable(Base):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="created")
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(255))
    target_ref: Mapped[str | None] = mapped_column(String(255))
    protected_targets: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class ChangeSetTable(Base):
    __tablename__ = "change_sets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    workspace_id: Mapped[str | None] = mapped_column(String(64))
    artifact_id: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    diff_metadata: Mapped[dict | None] = mapped_column(JSON)
    lineage: Mapped[dict | None] = mapped_column(JSON)
    applicable_type: Mapped[str] = mapped_column(String(64), nullable=False, default="generic")
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

# ---------------------------------------------------------------------------
# Phase 3: Editorial workflow tables (Area C)
# ---------------------------------------------------------------------------

class EditorialWorkflowTable(Base):
    __tablename__ = "editorial_workflows"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_id: Mapped[str | None] = mapped_column(String(64))
    current_stage: Mapped[str] = mapped_column(String(64), nullable=False, default="drafting")
    stages: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    role_assignments: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class ContentProjectionTable(Base):
    __tablename__ = "content_projections"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    artifact_id: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(128), nullable=False)
    projection_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    projected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    external_ref: Mapped[str | None] = mapped_column(String(255))
    config: Mapped[dict | None] = mapped_column(JSON)

# ---------------------------------------------------------------------------
# Phase 3: Knowledge artifact tables (Area D)
# ---------------------------------------------------------------------------

class KnowledgeArtifactTable(Base):
    __tablename__ = "knowledge_artifacts"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(64), nullable=False, default="text")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    policy_scope: Mapped[dict | None] = mapped_column(JSON)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    tags: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class KnowledgeArtifactVersionTable(Base):
    __tablename__ = "knowledge_artifact_versions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    artifact_id: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

# ---------------------------------------------------------------------------
# Phase 3: Planning construct tables (Area E)
# ---------------------------------------------------------------------------

class PlanningConstructTable(Base):
    __tablename__ = "planning_constructs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_team_id: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    capacity_budget: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class PlanningMembershipTable(Base):
    __tablename__ = "planning_memberships"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    planning_construct_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    added_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)


# ---------------------------------------------------------------------------
# Phase 4: Data governance tables
# ---------------------------------------------------------------------------

class DataClassificationTable(Base):
    __tablename__ = "data_classifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    classification_level: Mapped[str] = mapped_column(String(32), nullable=False, default="internal")
    residency_zone: Mapped[str | None] = mapped_column(String(64))
    retention_policy_id: Mapped[str | None] = mapped_column(String(64))
    classified_by: Mapped[str] = mapped_column(String(128), nullable=False)
    classified_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class RetentionPolicyTable(Base):
    __tablename__ = "retention_policies"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    action_on_expiry: Mapped[str] = mapped_column(String(32), nullable=False, default="archive")
    applies_to: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class DataLineageTable(Base):
    __tablename__ = "data_lineage_records"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    transformation: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

# ---------------------------------------------------------------------------
# Phase 4: Billing & quota tables
# ---------------------------------------------------------------------------

class UsageMeterTable(Base):
    __tablename__ = "usage_meters"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    meter_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="count")
    cost_amount: Mapped[float | None] = mapped_column(nullable=True)
    cost_currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    attributed_to: Mapped[str | None] = mapped_column(String(128))
    recorded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class QuotaDefinitionTable(Base):
    __tablename__ = "quota_definitions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    meter_type: Mapped[str] = mapped_column(String(64), nullable=False)
    limit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String(32), nullable=False, default="monthly")
    enforcement: Mapped[str] = mapped_column(String(32), nullable=False, default="soft")
    budget_amount: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

# ---------------------------------------------------------------------------
# Phase 4: Queue & assignment tables
# ---------------------------------------------------------------------------

class AssignmentGroupTable(Base):
    __tablename__ = "assignment_groups"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    skill_tags: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    max_capacity: Mapped[int | None] = mapped_column(Integer)
    current_load: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class EscalationRuleTable(Base):
    __tablename__ = "escalation_rules"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    condition: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    escalation_target: Mapped[str] = mapped_column(String(128), nullable=False)
    escalation_type: Mapped[str] = mapped_column(String(32), nullable=False, default="reassign")
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class SlaDefinitionTable(Base):
    __tablename__ = "sla_definitions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_id: Mapped[str | None] = mapped_column(String(64))
    response_target_hours: Mapped[float | None] = mapped_column(nullable=True)
    resolution_target_hours: Mapped[float | None] = mapped_column(nullable=True)
    review_deadline_hours: Mapped[float | None] = mapped_column(nullable=True)
    warning_threshold_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=70)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class SlaBreachAuditTable(Base):
    __tablename__ = "sla_breach_audit"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sla_definition_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    breach_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_hours: Mapped[float] = mapped_column(nullable=False)
    actual_hours: Mapped[float] = mapped_column(nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    remediation_action: Mapped[str | None] = mapped_column(String(255))
    breached_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

# ---------------------------------------------------------------------------
# Phase 4: View, replay, and deployment environment tables
# ---------------------------------------------------------------------------

class ViewDefinitionTable(Base):
    __tablename__ = "view_definitions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    view_type: Mapped[str] = mapped_column(String(32), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_by: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class EventReplayCheckpointTable(Base):
    __tablename__ = "event_replay_checkpoints"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    replay_scope: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_id: Mapped[str] = mapped_column(String(64), nullable=False)
    last_event_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    replayed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

class DeploymentEnvironmentTable(Base):
    __tablename__ = "deployment_environments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="saas")
    isolation_level: Mapped[str] = mapped_column(String(32), nullable=False, default="shared")
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
