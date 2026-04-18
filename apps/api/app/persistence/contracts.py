from typing import Protocol

from app.models.common import PaginatedResponse
from app.models.governance import (
    AddTeamMembershipRequest,
    AgentSessionContextDetail,
    AgentSessionDetail,
    AgentSessionMessageCreateRequest,
    AgentSessionRecord,
    AnalyticsAgentRow,
    AnalyticsBottleneckRow,
    AnalyticsWorkflowRow,
    AgentTrendPoint,
    ArtifactDetail,
    ArtifactRecord,
    ImportAgentSessionArtifactRequest,
    AssignAgentSessionRequest,
    AuditEntry,
    CapabilityDetail,
    CapabilityRecord,
    CheckEvaluationRequest,
    CheckOverrideRequest,
    CheckRunRecord,
    CheckRunRequest,
    CompleteAgentSessionRequest,
    CreateIntegrationRequest,
    CreateOrganizationRequest,
    CreatePortfolioRequest,
    CreateTenantRequest,
    CreateTeamRequest,
    CreateUserRequest,
    DeliveryDoraRow,
    DeliveryForecastPoint,
    DeliveryForecastSummary,
    DeliveryLifecycleRow,
    DeliveryTrendPoint,
    EventLedgerRecord,
    EventOutboxRecord,
    IntegrationRecord,
    InstructionalWorkflowDecisionRequest,
    InstructionalWorkflowProjectionRecord,
    OrganizationRecord,
    PolicyRecord,
    PolicyRuleUpdateRequest,
    PerformanceOperationsSummary,
    PerformanceOperationsTrendPoint,
    PortfolioRecord,
    PortfolioSummary,
    PromotionActionRequest,
    PromotionApprovalOverrideRequest,
    PromotionDetail,
    RequestDetail,
    ReviewAssignmentOverrideRequest,
    ReviewDecisionRequest,
    ReviewQueueItem,
    RunCommandRequest,
    RunDetail,
    RunRecord,
    RuntimeRunCallbackRequest,
    TeamRecord,
    TenantRecord,
    UpdateAgentSessionGovernanceRequest,
    UpdateIntegrationRequest,
    UpdateOrganizationRequest,
    UpdateTenantRequest,
    UpdateTeamRequest,
    UpdateUserRequest,
    UserRecord,
    WorkflowTrendPoint,
)
from app.models.request import (
    AmendRequest,
    CancelRequest,
    CloneRequest,
    CreateRequestDraft,
    RequestCheckRun,
    RequestRecord,
    SubmitRequest,
    SupersedeRequest,
    TransitionRequest,
)
from app.models.security import Principal, PublicRegistrationRequest, RegistrationSubmissionResponse
from app.models.template import (
    CreateTemplateVersionRequest,
    TemplateRecord,
    TemplateStatus,
    TemplateValidationResult,
    UpdateTemplateDefinitionRequest,
)


class RequestPersistencePort(Protocol):
    def list_requests(self, page: int, page_size: int) -> PaginatedResponse[RequestRecord]:
        ...

    def create_request_draft(self, payload: CreateRequestDraft, actor_id: str, tenant_id: str) -> RequestRecord:
        ...

    def submit_request(self, request_id: str, payload: SubmitRequest, tenant_id: str) -> RequestRecord:
        ...

    def amend_request(self, request_id: str, payload: AmendRequest, tenant_id: str) -> RequestRecord:
        ...

    def cancel_request(self, request_id: str, payload: CancelRequest, tenant_id: str) -> RequestRecord:
        ...

    def transition_request(self, request_id: str, payload: TransitionRequest, tenant_id: str) -> RequestRecord:
        ...

    def clone_request(self, request_id: str, payload: CloneRequest, tenant_id: str) -> RequestRecord:
        ...

    def supersede_request(self, request_id: str, payload: SupersedeRequest, tenant_id: str) -> RequestRecord:
        ...

    def run_request_checks(self, request_id: str, payload: RequestCheckRun, tenant_id: str) -> RequestRecord:
        ...


class TemplatePersistencePort(Protocol):
    def list_templates(self, tenant_id: str, include_non_published: bool = False) -> list[TemplateRecord]:
        ...

    def create_template_version(self, payload: CreateTemplateVersionRequest, actor_id: str, tenant_id: str) -> TemplateRecord:
        ...

    def update_template_definition(
        self,
        template_id: str,
        version: str,
        payload: UpdateTemplateDefinitionRequest,
        actor_id: str,
        tenant_id: str,
    ) -> TemplateRecord:
        ...

    def validate_template_definition(self, template_id: str, version: str, tenant_id: str) -> TemplateValidationResult:
        ...

    def delete_template_version(self, template_id: str, version: str, actor_id: str, tenant_id: str) -> None:
        ...

    def update_template_status(
        self,
        template_id: str,
        version: str,
        status: TemplateStatus,
        actor_id: str,
        tenant_id: str,
        note: str | None,
    ) -> TemplateRecord:
        ...


class RequestLifecyclePort(Protocol):
    def list_requests(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        owner_team_id: str | None = None,
        workflow: str | None = None,
        request_id: str | None = None,
        federation: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[RequestRecord]:
        ...

    def get_request(self, request_id: str, tenant_id: str | None = None) -> RequestDetail:
        ...

    def create_public_registration_request(self, payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
        ...

    def list_audit_entries(self, request_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        ...

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        ...

    def list_instructional_workflow_projections(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        flightos_content_entry_id: str | None = None,
        template_id: str | None = None,
        workflow_status: str | None = None,
    ) -> PaginatedResponse[InstructionalWorkflowProjectionRecord]:
        ...

    def get_instructional_workflow_projection(self, request_id: str, tenant_id: str | None = None) -> InstructionalWorkflowProjectionRecord:
        ...

    def decide_instructional_workflow_stage(
        self,
        request_id: str,
        payload: InstructionalWorkflowDecisionRequest,
        tenant_id: str,
    ) -> InstructionalWorkflowProjectionRecord:
        ...


class PromotionPersistencePort(Protocol):
    def list_review_queue(
        self,
        page: int,
        page_size: int,
        assigned_reviewer: str | None = None,
        blocking_only: bool = False,
        stale_only: bool = False,
        request_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[ReviewQueueItem]:
        ...

    def get_promotion(self, promotion_id: str, tenant_id: str | None = None) -> PromotionDetail:
        ...

    def record_review_decision(self, review_id: str, payload: ReviewDecisionRequest, tenant_id: str) -> ReviewQueueItem:
        ...

    def override_review_assignment(self, review_id: str, payload: ReviewAssignmentOverrideRequest, tenant_id: str) -> ReviewQueueItem:
        ...

    def apply_promotion_action(self, promotion_id: str, payload: PromotionActionRequest, tenant_id: str) -> PromotionDetail:
        ...

    def evaluate_check(self, promotion_id: str, check_id: str, payload: CheckEvaluationRequest, tenant_id: str) -> PromotionDetail:
        ...

    def override_check(self, promotion_id: str, check_id: str, payload: CheckOverrideRequest, tenant_id: str) -> PromotionDetail:
        ...

    def run_promotion_checks(self, promotion_id: str, payload: CheckRunRequest, tenant_id: str) -> PromotionDetail:
        ...

    def override_promotion_approval(self, promotion_id: str, payload: PromotionApprovalOverrideRequest, tenant_id: str) -> PromotionDetail:
        ...

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        ...

    def list_promotion_check_runs(self, promotion_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        ...


class OrganizationPersistencePort(Protocol):
    def list_tenants(self) -> list[TenantRecord]:
        ...

    def create_tenant(self, payload: CreateTenantRequest) -> TenantRecord:
        ...

    def update_tenant(self, tenant_id: str, payload: UpdateTenantRequest) -> TenantRecord:
        ...

    def list_users(self, tenant_id: str | None = None) -> list[UserRecord]:
        ...

    def create_user(self, payload: CreateUserRequest, tenant_id: str) -> UserRecord:
        ...

    def update_user(self, user_id: str, payload: UpdateUserRequest, tenant_id: str) -> UserRecord:
        ...

    def authenticate_local_user(self, email: str, password: str, tenant_id: str | None = None) -> Principal:
        ...

    def list_organizations(self, tenant_id: str | None = None) -> list[OrganizationRecord]:
        ...

    def create_organization(self, payload: CreateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        ...

    def update_organization(self, organization_id: str, payload: UpdateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        ...

    def list_teams(self, tenant_id: str | None = None) -> list[TeamRecord]:
        ...

    def create_team(self, payload: CreateTeamRequest, tenant_id: str) -> TeamRecord:
        ...

    def update_team(self, team_id: str, payload: UpdateTeamRequest, tenant_id: str) -> TeamRecord:
        ...

    def add_team_membership(self, payload: AddTeamMembershipRequest, tenant_id: str) -> TeamRecord:
        ...

    def list_portfolios(self, tenant_id: str | None = None) -> list[PortfolioRecord]:
        ...

    def create_portfolio(self, payload: CreatePortfolioRequest, tenant_id: str) -> PortfolioRecord:
        ...

    def list_portfolio_summaries(self, tenant_id: str | None = None) -> list[PortfolioSummary]:
        ...

    def list_integrations(self, tenant_id: str | None = None) -> list[IntegrationRecord]:
        ...

    def create_integration(self, payload: CreateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        ...

    def update_integration(self, integration_id: str, payload: UpdateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        ...

    def delete_integration(self, integration_id: str, tenant_id: str) -> None:
        ...

    def list_policies(self, tenant_id: str | None = None) -> list[PolicyRecord]:
        ...

    def update_policy_rules(self, policy_id: str, payload: PolicyRuleUpdateRequest, tenant_id: str) -> PolicyRecord:
        ...


class AnalyticsQueryPort(Protocol):
    def list_workflow_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsWorkflowRow]:
        ...

    def list_workflow_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        workflow: str | None = None,
    ) -> list[WorkflowTrendPoint]:
        ...

    def list_agent_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsAgentRow]:
        ...

    def list_agent_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        agent: str | None = None,
    ) -> list[AgentTrendPoint]:
        ...

    def list_bottleneck_analytics(self, days: int = 30, tenant_id: str | None = None) -> list[AnalyticsBottleneckRow]:
        ...

    def list_delivery_dora(
        self,
        tenant_id: str | None = None,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryDoraRow]:
        ...

    def list_delivery_lifecycle(
        self,
        tenant_id: str | None = None,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryLifecycleRow]:
        ...

    def list_delivery_trends(
        self,
        tenant_id: str | None = None,
        days: int = 30,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryTrendPoint]:
        ...

    def get_delivery_forecast(
        self,
        tenant_id: str | None = None,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> DeliveryForecastSummary:
        ...

    def list_delivery_forecast_points(
        self,
        tenant_id: str | None = None,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryForecastPoint]:
        ...

    def get_performance_operations_summary(self, tenant_id: str | None = None) -> PerformanceOperationsSummary:
        ...

    def list_performance_operations_trends(self, tenant_id: str | None = None, days: int = 30) -> list[PerformanceOperationsTrendPoint]:
        ...


class EventQueryPort(Protocol):
    def list_event_ledger(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        request_id: str | None = None,
        run_id: str | None = None,
        artifact_id: str | None = None,
        promotion_id: str | None = None,
        check_run_id: str | None = None,
        event_type: str | None = None,
    ) -> PaginatedResponse[EventLedgerRecord]:
        ...

    def list_event_outbox(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        request_id: str | None = None,
        status: str | None = None,
        topic: str | None = None,
    ) -> PaginatedResponse[EventOutboxRecord]:
        ...


class GovernanceRuntimePort(Protocol):
    def list_agent_integrations_for_request(self, request_id: str, tenant_id: str | None = None) -> list[IntegrationRecord]:
        ...

    def preview_agent_assignment_context(
        self,
        request_id: str,
        integration_id: str,
        collaboration_mode: str,
        agent_operating_profile: str,
        tenant_id: str,
    ) -> AgentSessionContextDetail:
        ...

    def assign_agent_session(self, request_id: str, payload: AssignAgentSessionRequest, tenant_id: str) -> AgentSessionRecord:
        ...

    def get_agent_session(self, request_id: str, session_id: str, tenant_id: str | None = None) -> AgentSessionDetail:
        ...

    def get_agent_session_context(self, request_id: str, session_id: str, tenant_id: str | None = None) -> AgentSessionContextDetail:
        ...

    def post_agent_session_message(
        self,
        request_id: str,
        session_id: str,
        payload: AgentSessionMessageCreateRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        ...

    def update_agent_session_governance(
        self,
        request_id: str,
        session_id: str,
        payload: UpdateAgentSessionGovernanceRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        ...

    def stream_agent_session_response(self, request_id: str, session_id: str, tenant_id: str | None = None):
        ...

    def complete_agent_session(
        self,
        request_id: str,
        session_id: str,
        payload: CompleteAgentSessionRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        ...

    def import_agent_session_artifact(
        self,
        request_id: str,
        session_id: str,
        payload: ImportAgentSessionArtifactRequest,
        tenant_id: str,
    ) -> ArtifactDetail:
        ...

    def list_templates(self, tenant_id: str | None = None) -> list[TemplateRecord]:
        ...

    def list_runs(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        workflow: str | None = None,
        owner: str | None = None,
        request_id: str | None = None,
        federation: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[RunRecord]:
        ...

    def get_run(self, run_id: str, tenant_id: str | None = None) -> RunDetail:
        ...

    def list_run_audit_entries(self, run_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        ...

    def command_run(self, run_id: str, payload: RunCommandRequest, tenant_id: str) -> RunDetail:
        ...

    def reconcile_run(self, run_id: str, payload: RuntimeRunCallbackRequest) -> RunDetail:
        ...

    def list_artifacts(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[ArtifactRecord]:
        ...

    def get_artifact(self, artifact_id: str, tenant_id: str | None = None) -> ArtifactDetail:
        ...

    def list_capabilities(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[CapabilityRecord]:
        ...

    def get_capability(self, capability_id: str, tenant_id: str | None = None) -> CapabilityDetail:
        ...

    def list_workflow_audit_entries(self, workflow: str, tenant_id: str | None = None, limit: int = 200) -> list[AuditEntry]:
        ...

    def validate_template_definition(self, template_id: str, version: str, tenant_id: str) -> TemplateValidationResult:
        ...

    def delete_template_version(self, template_id: str, version: str, actor_id: str, tenant_id: str) -> None:
        ...

    def update_template_status(
        self,
        template_id: str,
        version: str,
        status: TemplateStatus,
        actor_id: str,
        tenant_id: str,
        note: str | None,
    ) -> TemplateRecord:
        ...
