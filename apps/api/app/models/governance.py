from datetime import datetime, timezone
from enum import StrEnum

from pydantic import Field

from app.models.common import RgpModel
from app.models.request import RequestPriority, RequestRecord, RequestStatus, seed_request
from app.models.template import TemplateRecord, TemplateStatus


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    FAILED = "failed"
    COMPLETED = "completed"
    PAUSED = "paused"


class StepStatus(StrEnum):
    COMPLETED = "completed"
    ACTIVE = "active"
    BLOCKED = "blocked"
    FAILED = "failed"
    PENDING = "pending"


class ReviewState(StrEnum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    BLOCKED = "blocked"
    COMMENTED = "commented"
    PENDING = "pending"


class CapabilityStatus(StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    DEPRECATED = "deprecated"


class CheckRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CheckRunRecord(RgpModel):
    id: str
    request_id: str
    promotion_id: str | None = None
    scope: str
    status: CheckRunStatus
    trigger_reason: str
    enqueued_by: str
    worker_task_id: str | None = None
    error_message: str | None = None
    queued_at: str
    started_at: str | None = None
    completed_at: str | None = None


class RuntimeDispatchRecord(RgpModel):
    id: str
    run_id: str
    request_id: str
    integration_id: str
    dispatch_type: str
    status: str
    external_reference: str | None = None
    detail: str
    payload: dict = Field(default_factory=dict)
    response_payload: dict = Field(default_factory=dict)
    dispatched_at: str


class RuntimeSignalRecord(RgpModel):
    event_id: str
    source: str
    status: str
    current_step: str | None = None
    detail: str
    payload: dict = Field(default_factory=dict)
    received_at: str


class RuntimeRunCallbackRequest(RgpModel):
    event_id: str
    occurred_at: str
    source: str = "runtime"
    status: str
    current_step: str | None = None
    detail: str = "Runtime status updated"
    progress_percent: int | None = None
    waiting_reason: str | None = None
    failure_reason: str | None = None
    payload: dict = Field(default_factory=dict)


class RunCommandRequest(RgpModel):
    actor_id: str = "user_demo"
    command: str
    reason: str = "Runtime command requested"


class RunStep(RgpModel):
    id: str
    name: str
    status: StepStatus
    owner: str
    started_at: str | None = None
    ended_at: str | None = None


class RunRecord(RgpModel):
    id: str
    request_id: str
    workflow: str
    status: RunStatus
    current_step: str
    elapsed_time: str
    waiting_reason: str | None = None
    updated_at: str
    owner_team: str


class RunDetail(RunRecord):
    workflow_identity: str
    progress_percent: int
    current_step_input_summary: str
    current_step_output_summary: str
    failure_reason: str | None = None
    command_surface: list[str]
    steps: list[RunStep]
    run_context: list[tuple[str, str]]
    conversation_thread_id: str
    runtime_dispatches: list[RuntimeDispatchRecord] = Field(default_factory=list)
    runtime_signals: list[RuntimeSignalRecord] = Field(default_factory=list)


class ArtifactVersion(RgpModel):
    id: str
    label: str
    status: str
    created_at: str
    author: str
    summary: str
    content: str
    content_ref: str | None = None


class ArtifactRecord(RgpModel):
    id: str
    type: str
    name: str
    current_version: str
    status: str
    request_id: str
    updated_at: str
    owner: str
    review_state: str
    promotion_relevant: bool


class ArtifactDetail(RgpModel):
    artifact: ArtifactRecord
    versions: list[ArtifactVersion]
    selected_version_id: str
    review_state: ReviewState
    stale_review: bool
    history: list["ArtifactEvent"] = Field(default_factory=list)
    lineage: list["ArtifactLineageEdge"] = Field(default_factory=list)


class ArtifactEvent(RgpModel):
    timestamp: str
    actor: str
    action: str
    detail: str
    artifact_version_id: str | None = None


class ArtifactLineageEdge(RgpModel):
    from_version_id: str | None = None
    to_version_id: str
    relation: str
    created_at: str


class ReviewQueueItem(RgpModel):
    id: str
    request_id: str
    review_scope: str
    artifact_or_changeset: str
    type: str
    priority: RequestPriority
    sla: str
    blocking_status: str
    assigned_reviewer: str
    stale: bool


class PromotionCheck(RgpModel):
    name: str
    state: str
    detail: str


class PromotionApproval(RgpModel):
    reviewer: str
    state: str
    scope: str


class CheckResult(RgpModel):
    id: str
    request_id: str
    promotion_id: str | None = None
    name: str
    state: str
    detail: str
    severity: str
    evidence: str
    evaluated_at: str
    evaluated_by: str


class CheckOverride(RgpModel):
    id: str
    check_result_id: str
    request_id: str
    promotion_id: str | None = None
    state: str
    reason: str
    requested_by: str
    decided_by: str
    created_at: str
    decided_at: str


class PromotionHistoryEntry(RgpModel):
    timestamp: str
    actor: str
    action: str


class EventLedgerRecord(RgpModel):
    id: int
    tenant_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    request_id: str | None = None
    run_id: str | None = None
    artifact_id: str | None = None
    promotion_id: str | None = None
    check_run_id: str | None = None
    actor: str
    detail: str
    payload: dict = Field(default_factory=dict)
    occurred_at: str


class EventOutboxRecord(RgpModel):
    id: int
    event_store_id: int
    tenant_id: str
    topic: str
    partition_key: str
    payload: dict = Field(default_factory=dict)
    status: str
    backend: str
    error_message: str | None = None
    created_at: str
    published_at: str | None = None


class DeploymentExecutionRecord(RgpModel):
    id: str
    promotion_id: str
    request_id: str
    integration_id: str
    target: str
    strategy: str
    status: str
    external_reference: str | None = None
    detail: str
    payload: dict = Field(default_factory=dict)
    response_payload: dict = Field(default_factory=dict)
    executed_at: str


class PromotionDetail(RgpModel):
    id: str
    request_id: str
    target: str
    strategy: str
    required_checks: list[PromotionCheck]
    check_results: list[CheckResult] = Field(default_factory=list)
    check_runs: list[CheckRunRecord] = Field(default_factory=list)
    overrides: list[CheckOverride] = Field(default_factory=list)
    required_approvals: list[PromotionApproval]
    stale_warnings: list[str]
    execution_readiness: str
    deployment_executions: list[DeploymentExecutionRecord] = Field(default_factory=list)
    promotion_history: list[PromotionHistoryEntry]


class ReviewDecisionRequest(RgpModel):
    actor_id: str = "user_demo"
    decision: str
    reason: str = "Review decision recorded"


class ReviewAssignmentOverrideRequest(RgpModel):
    actor_id: str = "user_demo"
    assigned_reviewer: str
    reason: str = "Review reassigned"


class PromotionActionRequest(RgpModel):
    actor_id: str = "user_demo"
    action: str
    reason: str = "Promotion action recorded"


class PromotionApprovalOverrideRequest(RgpModel):
    actor_id: str = "user_demo"
    reviewer: str
    replacement_reviewer: str
    reason: str = "Promotion approver reassigned"


class CheckEvaluationRequest(RgpModel):
    actor_id: str = "user_demo"
    state: str
    detail: str
    evidence: str = "Manual evaluation recorded"


class CheckOverrideRequest(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Override requested"


class CheckRunRequest(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Automated checks executed"


class CapabilityRecord(RgpModel):
    id: str
    name: str
    type: str
    version: str
    status: CapabilityStatus
    owner: str
    updated_at: str
    usage_count: int


class CapabilityDetail(RgpModel):
    capability: CapabilityRecord
    definition: str
    lineage: list[str]
    usage: list[tuple[str, str]]
    performance: list[tuple[str, str]]
    history: list[PromotionHistoryEntry]


class AnalyticsWorkflowRow(RgpModel):
    workflow: str
    avg_cycle_time: str
    p95_duration: str
    failure_rate: str
    review_delay: str
    cost_per_execution: str
    trend: str


class AnalyticsAgentRow(RgpModel):
    agent: str
    invocations: int
    success_rate: str
    retry_rate: str
    avg_duration: str
    cost_per_invocation: str
    quality_score: str


class AnalyticsBottleneckRow(RgpModel):
    workflow: str
    step: str
    avg_wait_time: str
    block_count: int
    reviewer_delay: str
    trend: str


class WorkflowTrendPoint(RgpModel):
    period_start: str
    request_count: int
    failed_count: int
    avg_cycle_time_hours: float
    review_stale_count: int
    cost_per_execution: float


class AgentTrendPoint(RgpModel):
    period_start: str
    invocation_count: int
    success_rate: float
    retry_rate: float
    avg_duration_minutes: float
    quality_score: float


class PerformanceRouteSummary(RgpModel):
    route: str
    method: str
    request_count: int
    error_rate: str
    avg_duration_ms: float
    p95_duration_ms: float
    apdex: str


class PerformanceSloSummary(RgpModel):
    route: str
    method: str
    availability_slo: str
    latency_slo_ms: int
    availability_actual: str
    p95_duration_ms: float
    status: str
    error_budget_remaining: str


class PerformanceMetricRecord(RgpModel):
    id: int
    route: str
    method: str
    status_code: int
    duration_ms: float
    trace_id: str | None = None
    span_id: str | None = None
    correlation_id: str | None = None
    occurred_at: str


class PerformanceTrendPoint(RgpModel):
    period_start: str
    route: str
    method: str
    request_count: int
    avg_duration_ms: float
    p95_duration_ms: float
    error_rate: str


class PerformanceOperationsSummary(RgpModel):
    queued_checks: int
    running_checks: int
    waiting_runs: int
    failed_runs: int
    stale_reviews: int
    pending_promotions: int
    avg_check_queue_minutes: float
    avg_runtime_queue_minutes: float


class PerformanceOperationsTrendPoint(RgpModel):
    period_start: str
    queued_checks: int
    running_checks: int
    waiting_runs: int
    failed_runs: int
    stale_reviews: int
    pending_promotions: int


class UserRecord(RgpModel):
    id: str
    display_name: str
    email: str
    role_summary: list[str] = Field(default_factory=list)
    status: str


class TeamMemberRecord(RgpModel):
    user_id: str
    display_name: str
    email: str
    role: str


class TeamRecord(RgpModel):
    id: str
    name: str
    kind: str
    status: str
    member_count: int
    members: list[TeamMemberRecord] = Field(default_factory=list)


class PortfolioRecord(RgpModel):
    id: str
    name: str
    status: str
    owner_team_id: str
    scope_keys: list[str] = Field(default_factory=list)


class CreateUserRequest(RgpModel):
    id: str
    display_name: str
    email: str
    role_summary: list[str] = Field(default_factory=list)
    status: str = "active"


class UpdateUserRequest(RgpModel):
    display_name: str
    email: str
    role_summary: list[str] = Field(default_factory=list)
    status: str = "active"


class CreateTeamRequest(RgpModel):
    id: str
    name: str
    kind: str = "delivery"
    status: str = "active"


class UpdateTeamRequest(RgpModel):
    name: str
    kind: str = "delivery"
    status: str = "active"


class AddTeamMembershipRequest(RgpModel):
    team_id: str
    user_id: str
    role: str = "member"


class CreatePortfolioRequest(RgpModel):
    id: str
    name: str
    owner_team_id: str
    scope_keys: list[str] = Field(default_factory=list)
    status: str = "active"


class PortfolioSummary(RgpModel):
    portfolio_id: str
    portfolio_name: str
    owner_team_id: str
    team_count: int
    member_count: int
    request_count: int
    active_request_count: int
    completed_request_count: int
    deployment_count: int


class DeliveryDoraRow(RgpModel):
    scope_type: str
    scope_key: str
    deployment_frequency: str
    lead_time_hours: float
    change_failure_rate: str
    mean_time_to_restore_hours: float


class DeliveryLifecycleRow(RgpModel):
    scope_type: str
    scope_key: str
    throughput_30d: int
    lead_time_hours: float
    cycle_time_hours: float
    execution_time_hours: float
    queue_time_hours: float
    review_time_hours: float
    approval_time_hours: float
    promotion_time_hours: float


class DeliveryTrendPoint(RgpModel):
    period_start: str
    completed_count: int
    failed_count: int
    deployment_count: int
    throughput_count: int
    lead_time_hours: float


class DeliveryForecastPoint(RgpModel):
    period_start: str
    projected_throughput_count: float
    projected_deployment_count: float
    projected_lead_time_hours: float


class DeliveryForecastSummary(RgpModel):
    forecast_days: int
    avg_daily_throughput: float
    avg_daily_deployments: float
    projected_total_throughput: float
    projected_total_deployments: float
    projected_lead_time_hours: float


class AuditEntry(RgpModel):
    timestamp: str
    actor: str
    action: str
    object_type: str
    object_id: str
    reason_or_evidence: str


class RequestRelationship(RgpModel):
    request_id: str
    relationship_type: str


class PolicyRecord(RgpModel):
    id: str
    name: str
    status: str
    scope: str
    rules: list[str] = Field(default_factory=list)
    transition_gates: list["PolicyGateRule"] = Field(default_factory=list)
    updated_at: str


class PolicyRuleUpdateRequest(RgpModel):
    rules: list[str] = Field(default_factory=list)


class PolicyGateRule(RgpModel):
    transition_target: str
    required_check_name: str


class IntegrationRecord(RgpModel):
    id: str
    name: str
    type: str
    status: str
    endpoint: str
    settings: dict = Field(default_factory=dict)
    has_api_key: bool = False
    has_access_token: bool = False
    resolved_endpoint: str | None = None
    supports_direct_assignment: bool = False
    supports_interactive_sessions: bool = False
    provider: str | None = None


class CreateIntegrationRequest(RgpModel):
    id: str
    name: str
    type: str
    status: str = "connected"
    endpoint: str
    settings: dict = Field(default_factory=dict)


class UpdateIntegrationRequest(RgpModel):
    name: str
    type: str
    status: str = "connected"
    endpoint: str
    settings: dict = Field(default_factory=dict)
    clear_api_key: bool = False
    clear_access_token: bool = False


class AgentSessionMessageRecord(RgpModel):
    id: str
    session_id: str
    request_id: str
    sender_type: str
    sender_id: str
    message_type: str
    body: str
    created_at: str


class AgentSessionRecord(RgpModel):
    id: str
    request_id: str
    integration_id: str
    integration_name: str
    agent_label: str
    provider: str | None = None
    status: str
    awaiting_human: bool
    summary: str
    external_session_ref: str | None = None
    resume_request_status: str | None = None
    assigned_by: str
    assigned_at: str
    updated_at: str
    latest_message: AgentSessionMessageRecord | None = None
    message_count: int = 0


class AgentSessionDetail(AgentSessionRecord):
    messages: list[AgentSessionMessageRecord] = Field(default_factory=list)


class AssignAgentSessionRequest(RgpModel):
    actor_id: str = "user_demo"
    integration_id: str
    initial_prompt: str
    agent_label: str | None = None
    reason: str = "Request assigned to interactive agent session"


class AgentSessionMessageCreateRequest(RgpModel):
    actor_id: str = "user_demo"
    body: str
    message_type: str = "message"
    reason: str = "Human guidance provided to agent session"


class CompleteAgentSessionRequest(RgpModel):
    actor_id: str = "user_demo"
    reason: str = "Accepted agent response and resumed workflow"
    target_status: str | None = None


class RequestDetail(RgpModel):
    request: RequestRecord
    latest_run_id: str | None = None
    latest_artifact_ids: list[str] = Field(default_factory=list)
    active_blockers: list[str] = Field(default_factory=list)
    check_results: list[CheckResult] = Field(default_factory=list)
    check_runs: list[CheckRunRecord] = Field(default_factory=list)
    agent_sessions: list[AgentSessionRecord] = Field(default_factory=list)
    next_required_action: str
    predecessors: list[RequestRelationship] = Field(default_factory=list)
    successors: list[RequestRelationship] = Field(default_factory=list)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def seed_templates() -> list[TemplateRecord]:
    now = iso_now()
    return [
        TemplateRecord(
            id="tmpl_curriculum",
            version="3.1.0",
            name="Curriculum Generation",
            description="Generates a governed instructional unit.",
            status=TemplateStatus.PUBLISHED,
            schema={
                "required": ["subject", "grade_level"],
                "routing": {
                    "owner_team_by_field": {
                        "subject": {
                            "Math": "team_curriculum_math",
                            "Science": "team_curriculum_science",
                            "ELA": "team_curriculum_literacy",
                            "History": "team_curriculum_social_studies",
                        }
                    },
                    "workflow_binding_by_field": {
                        "subject": {
                            "Math": "wf_curriculum_math_v3",
                            "Science": "wf_curriculum_science_v3",
                            "ELA": "wf_curriculum_ela_v3",
                            "History": "wf_curriculum_history_v3",
                        }
                    },
                    "reviewers_by_field": {
                        "subject": {
                            "Math": ["reviewer_maya", "reviewer_olivia"],
                            "Science": ["reviewer_nina", "reviewer_liam"],
                            "ELA": ["reviewer_zoe", "reviewer_maya"],
                            "History": ["reviewer_liam", "reviewer_isaac"],
                        }
                    },
                    "promotion_approvers_by_field": {
                        "subject": {
                            "Math": ["ops_isaac"],
                            "Science": ["ops_isaac"],
                            "ELA": ["ops_maya"],
                            "History": ["ops_maya"],
                        }
                    },
                },
                "properties": {
                    "subject": {
                        "type": "string",
                        "title": "Subject",
                        "enum": ["Math", "Science", "ELA", "History"],
                        "default": "Math",
                    },
                    "grade_level": {
                        "type": "string",
                        "title": "Grade Level",
                        "enum": ["Grade 3", "Grade 4", "Grade 5", "Grade 6"],
                    },
                    "locale": {
                        "type": "string",
                        "title": "Locale",
                        "enum": ["en-US", "en-GB", "es-US"],
                        "default": "en-US",
                    },
                    "delivery_model": {
                        "type": "string",
                        "title": "Delivery Model",
                        "enum": ["Core", "Intervention", "Enrichment"],
                        "default": "Core",
                    },
                    "lab_materials": {
                        "type": "string",
                        "title": "Lab Materials",
                        "description": "Required for science requests. Include enough detail for the governed lab plan.",
                        "min_length": 10,
                    },
                    "reading_focus": {
                        "type": "string",
                        "title": "Reading Focus",
                        "description": "Required for ELA requests to determine the correct review package.",
                        "enum": ["Literary analysis", "Informational text", "Foundational skills"],
                    },
                },
                "conditional_required": [
                    {
                        "when": {"field": "subject", "equals": "Science"},
                        "field": "lab_materials",
                        "message": "Template validation failed for lab_materials: Science requests require lab materials.",
                    },
                    {
                        "when": {"field": "subject", "equals": "ELA"},
                        "field": "reading_focus",
                        "message": "Template validation failed for reading_focus: ELA requests require a reading focus.",
                    },
                ],
            },
            created_at=now,
            updated_at=now,
        ),
        TemplateRecord(
            id="tmpl_assessment",
            version="1.4.0",
            name="Assessment Revision",
            description="Revision workflow for governed assessment assets.",
            status=TemplateStatus.PUBLISHED,
            schema={
                "required": ["assessment_id", "revision_reason"],
                "routing": {
                    "owner_team": "team_assessment_quality",
                    "workflow_binding": "wf_assessment_revision_v1",
                    "reviewers": ["reviewer_liam", "reviewer_nina"],
                    "promotion_approvers": ["ops_isaac"],
                },
                "properties": {
                    "assessment_id": {"type": "string", "title": "Assessment ID", "pattern": r"asm_[A-Za-z0-9_-]+$"},
                    "revision_reason": {
                        "type": "string",
                        "title": "Revision Reason",
                        "enum": ["Standards alignment", "Difficulty adjustment", "Quality remediation"],
                    },
                    "target_window": {"type": "string", "title": "Target Window", "default": "Spring 2026", "min_length": 6},
                },
            },
            created_at=now,
            updated_at=now,
        ),
    ]


def seed_requests() -> list[RequestRecord]:
    return [
        seed_request("req_001", "Generate Grade 5 Math Unit", RequestStatus.AWAITING_REVIEW, RequestPriority.HIGH, "team_curriculum"),
        seed_request("req_002", "Revise Algebra Assessment", RequestStatus.IN_EXECUTION, RequestPriority.URGENT, "team_assessment"),
        seed_request("req_003", "Publish Science Lab Artifact", RequestStatus.CHANGES_REQUESTED, RequestPriority.MEDIUM, "team_science"),
        seed_request("req_004", "Promote Writing Rubric", RequestStatus.PROMOTION_PENDING, RequestPriority.HIGH, "team_literacy"),
    ]


def seed_runs() -> list[RunDetail]:
    now = iso_now()
    return [
        RunDetail(
            id="run_001",
            request_id="req_001",
            workflow="Curriculum Authoring",
            status=RunStatus.WAITING,
            current_step="Human Review",
            elapsed_time="1h 24m",
            waiting_reason="Awaiting reviewer approval",
            updated_at=now,
            owner_team="team_curriculum",
            workflow_identity="wf_curriculum_v3",
            progress_percent=78,
            current_step_input_summary="Generated unit structure and standards map submitted for review.",
            current_step_output_summary="Draft artifact package ready.",
            command_surface=["Pause", "Resume", "Retry Step", "Cancel Run"],
            steps=[
                RunStep(id="step_1", name="Validate Inputs", status=StepStatus.COMPLETED, owner="system", started_at=now, ended_at=now),
                RunStep(id="step_2", name="Generate Outline", status=StepStatus.COMPLETED, owner="agent-curriculum", started_at=now, ended_at=now),
                RunStep(id="step_3", name="Human Review", status=StepStatus.BLOCKED, owner="reviewer_olivia", started_at=now),
                RunStep(id="step_4", name="Publish Artifact", status=StepStatus.PENDING, owner="system"),
            ],
            run_context=[("Template", "tmpl_curriculum@3.1.0"), ("Priority", "high"), ("Blocking", "Reviewer pending")],
            conversation_thread_id="thr_run_001",
        ),
        RunDetail(
            id="run_002",
            request_id="req_002",
            workflow="Assessment Revision",
            status=RunStatus.RUNNING,
            current_step="Regenerate Questions",
            elapsed_time="34m",
            updated_at=now,
            owner_team="team_assessment",
            workflow_identity="wf_assessment_v1",
            progress_percent=45,
            current_step_input_summary="Question bank diff approved for generation.",
            current_step_output_summary="Generating replacement item set.",
            command_surface=["Pause", "Retry Step", "Cancel Run"],
            steps=[
                RunStep(id="step_1", name="Load Change Set", status=StepStatus.COMPLETED, owner="system", started_at=now, ended_at=now),
                RunStep(id="step_2", name="Regenerate Questions", status=StepStatus.ACTIVE, owner="agent-assessment", started_at=now),
                RunStep(id="step_3", name="Quality Review", status=StepStatus.PENDING, owner="reviewer_nina"),
            ],
            run_context=[("Template", "tmpl_assessment@1.4.0"), ("Priority", "urgent"), ("Current run mode", "active")],
            conversation_thread_id="thr_run_002",
        ),
    ]


def seed_artifacts() -> list[ArtifactDetail]:
    now = iso_now()
    return [
        ArtifactDetail(
            artifact=ArtifactRecord(
                id="art_001",
                type="curriculum_unit",
                name="Grade 5 Fractions Unit",
                current_version="v3",
                status="awaiting_review",
                request_id="req_001",
                updated_at=now,
                owner="team_curriculum",
                review_state="pending",
                promotion_relevant=True,
            ),
            versions=[
                ArtifactVersion(id="artv_001", label="v1", status="superseded", created_at=now, author="agent-curriculum", summary="Initial draft.", content="Outline draft with standards mapping."),
                ArtifactVersion(id="artv_002", label="v2", status="changes_requested", created_at=now, author="agent-curriculum", summary="Updated with feedback.", content="Added vocabulary sequence and remediation notes."),
                ArtifactVersion(id="artv_003", label="v3", status="awaiting_review", created_at=now, author="agent-curriculum", summary="Current review candidate.", content="Full unit body with lesson sequence and artifacts."),
            ],
            selected_version_id="artv_003",
            review_state=ReviewState.PENDING,
            stale_review=False,
        ),
        ArtifactDetail(
            artifact=ArtifactRecord(
                id="art_002",
                type="assessment",
                name="Algebra Readiness Assessment",
                current_version="v5",
                status="in_revision",
                request_id="req_002",
                updated_at=now,
                owner="team_assessment",
                review_state="changes_requested",
                promotion_relevant=False,
            ),
            versions=[
                ArtifactVersion(id="artv_010", label="v4", status="approved", created_at=now, author="agent-assessment", summary="Last approved version.", content="Approved item bank."),
                ArtifactVersion(id="artv_011", label="v5", status="changes_requested", created_at=now, author="agent-assessment", summary="Current revision set.", content="Rewritten question set with distractor updates."),
            ],
            selected_version_id="artv_011",
            review_state=ReviewState.CHANGES_REQUESTED,
            stale_review=True,
        ),
    ]


def seed_review_queue() -> list[ReviewQueueItem]:
    return [
        ReviewQueueItem(
            id="revq_001",
            request_id="req_001",
            review_scope="artifact_version",
            artifact_or_changeset="Grade 5 Fractions Unit v3",
            type="content_review",
            priority=RequestPriority.HIGH,
            sla="Due in 2h",
            blocking_status="Blocking request progress",
            assigned_reviewer="reviewer_olivia",
            stale=False,
        ),
        ReviewQueueItem(
            id="revq_002",
            request_id="req_003",
            review_scope="artifact_version",
            artifact_or_changeset="Science Lab Artifact v2",
            type="quality_review",
            priority=RequestPriority.MEDIUM,
            sla="Overdue by 4h",
            blocking_status="Changes requested",
            assigned_reviewer="reviewer_liam",
            stale=True,
        ),
    ]


def seed_promotions() -> list[PromotionDetail]:
    now = iso_now()
    return [
        PromotionDetail(
            id="pro_001",
            request_id="req_004",
            target="Production Curriculum Library",
            strategy="Blue/Green content promotion",
            required_checks=[
                PromotionCheck(name="Policy Bundle", state="passed", detail="All mandatory checks passed."),
                PromotionCheck(name="Localization Validation", state="pending", detail="Spanish localization not yet attached."),
            ],
            required_approvals=[
                PromotionApproval(reviewer="reviewer_maya", state="approved", scope="content"),
                PromotionApproval(reviewer="ops_isaac", state="pending", scope="promotion"),
            ],
            stale_warnings=["Assessment references changed after initial approval."],
            execution_readiness="Blocked until pending localization validation and operator approval are complete.",
            promotion_history=[
                PromotionHistoryEntry(timestamp=now, actor="system", action="Promotion request created"),
                PromotionHistoryEntry(timestamp=now, actor="reviewer_maya", action="Content approval recorded"),
            ],
        )
    ]


def seed_capabilities() -> list[CapabilityDetail]:
    now = iso_now()
    return [
        CapabilityDetail(
            capability=CapabilityRecord(
                id="cap_001",
                name="Curriculum Unit Generator",
                type="agent_definition",
                version="2.3.0",
                status=CapabilityStatus.ACTIVE,
                owner="team_curriculum",
                updated_at=now,
                usage_count=184,
            ),
            definition="Hosted agent with curriculum planning, artifact synthesis, and rubric alignment steps.",
            lineage=["cap_001@1.9.0", "cap_001@2.0.0", "cap_001@2.3.0"],
            usage=[("30d Invocations", "184"), ("Active Workflows", "6")],
            performance=[("Success Rate", "97.2%"), ("Median Duration", "9m 12s")],
            history=[PromotionHistoryEntry(timestamp=now, actor="admin_sara", action="Activated v2.3.0")],
        ),
        CapabilityDetail(
            capability=CapabilityRecord(
                id="cap_002",
                name="Assessment Revision Workflow",
                type="workflow_definition",
                version="1.4.0",
                status=CapabilityStatus.PENDING,
                owner="team_assessment",
                updated_at=now,
                usage_count=42,
            ),
            definition="Workflow definition coordinating question regeneration, QA review, and approval routing.",
            lineage=["cap_002@1.1.0", "cap_002@1.2.0", "cap_002@1.4.0"],
            usage=[("30d Invocations", "42"), ("Linked Templates", "2")],
            performance=[("Failure Rate", "4.8%"), ("Review Delay", "3h 10m")],
            history=[PromotionHistoryEntry(timestamp=now, actor="author_jon", action="Published pending version 1.4.0")],
        ),
    ]


def seed_workflow_analytics() -> list[AnalyticsWorkflowRow]:
    return [
        AnalyticsWorkflowRow(workflow="Curriculum Authoring", avg_cycle_time="18h", p95_duration="31h", failure_rate="3.1%", review_delay="5h", cost_per_execution="$14.80", trend="Improving"),
        AnalyticsWorkflowRow(workflow="Assessment Revision", avg_cycle_time="9h", p95_duration="16h", failure_rate="6.4%", review_delay="2h", cost_per_execution="$9.15", trend="Stable"),
    ]


def seed_agent_analytics() -> list[AnalyticsAgentRow]:
    return [
        AnalyticsAgentRow(agent="Curriculum Unit Generator", invocations=184, success_rate="97.2%", retry_rate="1.9%", avg_duration="9m 12s", cost_per_invocation="$2.41", quality_score="4.7/5"),
        AnalyticsAgentRow(agent="Assessment Rewrite Agent", invocations=91, success_rate="93.6%", retry_rate="4.2%", avg_duration="6m 48s", cost_per_invocation="$1.83", quality_score="4.4/5"),
    ]


def seed_bottleneck_analytics() -> list[AnalyticsBottleneckRow]:
    return [
        AnalyticsBottleneckRow(workflow="Curriculum Authoring", step="Human Review", avg_wait_time="4h 50m", block_count=12, reviewer_delay="High", trend="Worsening"),
        AnalyticsBottleneckRow(workflow="Assessment Revision", step="Localization Validation", avg_wait_time="2h 15m", block_count=5, reviewer_delay="Moderate", trend="Stable"),
    ]


def seed_audit_entries() -> list[AuditEntry]:
    now = iso_now()
    return [
        AuditEntry(timestamp=now, actor="user_demo", action="Submitted", object_type="request", object_id="req_001", reason_or_evidence="Initial request submission"),
        AuditEntry(timestamp=now, actor="system", action="Run Started", object_type="run", object_id="run_001", reason_or_evidence="Workflow binding wf_curriculum_v3"),
        AuditEntry(timestamp=now, actor="agent-curriculum", action="Artifact Registered", object_type="artifact", object_id="art_001", reason_or_evidence="Draft package stored"),
    ]


def seed_policies() -> list[PolicyRecord]:
    now = iso_now()
    return [
        PolicyRecord(id="pol_001", name="Content Safety Bundle", status="active", scope="curriculum", updated_at=now),
        PolicyRecord(id="pol_002", name="Assessment Integrity Checks", status="active", scope="assessment", updated_at=now),
    ]


def seed_integrations() -> list[IntegrationRecord]:
    return [
        IntegrationRecord(
            id="int_001",
            name="Microsoft Foundry",
            type="runtime",
            status="connected",
            endpoint="foundry://rgp-primary",
            settings={"provider": "microsoft", "base_url": "http://localhost:8001/api/v1/runtime/mock"},
        ),
        IntegrationRecord(id="int_002", name="GitHub MCP", type="repository", status="connected", endpoint="github://rgp"),
        IntegrationRecord(id="int_003", name="Enterprise IdP", type="identity", status="connected", endpoint="oidc://enterprise"),
        IntegrationRecord(
            id="int_agent_copilot",
            name="Microsoft Copilot",
            type="agent_runtime",
            status="connected",
            endpoint="copilot://enterprise",
            settings={"provider": "microsoft", "base_url": "https://graph.microsoft.com/beta/copilot"},
            supports_direct_assignment=True,
            supports_interactive_sessions=True,
            provider="microsoft",
        ),
        IntegrationRecord(
            id="int_agent_codex",
            name="OpenAI Codex",
            type="agent_runtime",
            status="connected",
            endpoint="codex://rgp",
            settings={"provider": "openai", "base_url": "https://api.openai.com/v1", "model": "gpt-5.4"},
            supports_direct_assignment=True,
            supports_interactive_sessions=True,
            provider="openai",
        ),
        IntegrationRecord(
            id="int_agent_claude",
            name="Anthropic Claude Code",
            type="agent_runtime",
            status="connected",
            endpoint="claude-code://rgp",
            settings={"provider": "anthropic", "base_url": "https://api.anthropic.com/v1", "model": "claude-sonnet-4-5"},
            supports_direct_assignment=True,
            supports_interactive_sessions=True,
            provider="anthropic",
        ),
    ]
