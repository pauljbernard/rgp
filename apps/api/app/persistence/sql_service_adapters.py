from __future__ import annotations

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
    ApproveAgentSessionCheckpointRequest,
    RequestDetail,
    ResumeAgentSessionRuntimeRequest,
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
from app.models.request import RequestRecord
from app.models.security import Principal, PublicRegistrationRequest, RegistrationSubmissionResponse
from app.models.template import TemplateRecord
from app.persistence.contracts import (
    AnalyticsQueryPort,
    EventQueryPort,
    GovernanceRuntimePort,
    OrganizationPersistencePort,
    PromotionPersistencePort,
    RequestLifecyclePort,
)
from app.repositories.analytics_repository import AnalyticsRepository, analytics_repository
from app.repositories.event_query_repository import EventQueryRepository, event_query_repository
from app.repositories.governance_repository import GovernanceRepository, governance_repository
from app.repositories.org_repository import OrgRepository, org_repository
from app.repositories.promotion_repository import PromotionRepository, promotion_repository
from app.repositories.request_lifecycle_repository import RequestLifecycleRepository, request_lifecycle_repository


class SqlAlchemyRequestLifecycleAdapter(RequestLifecyclePort):
    def __init__(self, repository: RequestLifecycleRepository | None = None) -> None:
        self._repository = repository or request_lifecycle_repository

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
        return self._repository.list_requests(page, page_size, status, owner_team_id, workflow, request_id, federation, tenant_id)

    def get_request(self, request_id: str, tenant_id: str | None = None) -> RequestDetail:
        return self._repository.get_request(request_id, tenant_id)

    def create_public_registration_request(self, payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
        return self._repository.create_public_registration_request(payload)

    def list_audit_entries(self, request_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        return self._repository.list_audit_entries(request_id, tenant_id)

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        return self._repository.list_request_check_runs(request_id, tenant_id)

    def list_instructional_workflow_projections(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        flightos_content_entry_id: str | None = None,
        template_id: str | None = None,
        workflow_status: str | None = None,
    ) -> PaginatedResponse[InstructionalWorkflowProjectionRecord]:
        return self._repository.list_instructional_workflow_projections(
            page=page,
            page_size=page_size,
            tenant_id=tenant_id,
            flightos_content_entry_id=flightos_content_entry_id,
            template_id=template_id,
            workflow_status=workflow_status,
        )

    def get_instructional_workflow_projection(self, request_id: str, tenant_id: str | None = None) -> InstructionalWorkflowProjectionRecord:
        return self._repository.get_instructional_workflow_projection(request_id, tenant_id)

    def decide_instructional_workflow_stage(
        self,
        request_id: str,
        payload: InstructionalWorkflowDecisionRequest,
        tenant_id: str,
    ) -> InstructionalWorkflowProjectionRecord:
        return self._repository.decide_instructional_workflow_stage(request_id, payload, tenant_id)


class SqlAlchemyPromotionAdapter(PromotionPersistencePort):
    def __init__(self, repository: PromotionRepository | None = None) -> None:
        self._repository = repository or promotion_repository

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
        return self._repository.list_review_queue(page, page_size, assigned_reviewer, blocking_only, stale_only, request_id, tenant_id)

    def get_promotion(self, promotion_id: str, tenant_id: str | None = None) -> PromotionDetail:
        return self._repository.get_promotion(promotion_id, tenant_id)

    def record_review_decision(self, review_id: str, payload: ReviewDecisionRequest, tenant_id: str) -> ReviewQueueItem:
        return self._repository.record_review_decision(review_id, payload, tenant_id)

    def override_review_assignment(self, review_id: str, payload: ReviewAssignmentOverrideRequest, tenant_id: str) -> ReviewQueueItem:
        return self._repository.override_review_assignment(review_id, payload, tenant_id)

    def apply_promotion_action(self, promotion_id: str, payload: PromotionActionRequest, tenant_id: str) -> PromotionDetail:
        return self._repository.apply_promotion_action(promotion_id, payload, tenant_id)

    def evaluate_check(self, promotion_id: str, check_id: str, payload: CheckEvaluationRequest, tenant_id: str) -> PromotionDetail:
        return self._repository.evaluate_check(promotion_id, check_id, payload, tenant_id)

    def override_check(self, promotion_id: str, check_id: str, payload: CheckOverrideRequest, tenant_id: str) -> PromotionDetail:
        return self._repository.override_check(promotion_id, check_id, payload, tenant_id)

    def run_promotion_checks(self, promotion_id: str, payload: CheckRunRequest, tenant_id: str) -> PromotionDetail:
        return self._repository.run_promotion_checks(promotion_id, payload, tenant_id)

    def override_promotion_approval(self, promotion_id: str, payload: PromotionApprovalOverrideRequest, tenant_id: str) -> PromotionDetail:
        return self._repository.override_promotion_approval(promotion_id, payload, tenant_id)

    def list_request_check_runs(self, request_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        return self._repository.list_request_check_runs(request_id, tenant_id)

    def list_promotion_check_runs(self, promotion_id: str, tenant_id: str | None = None) -> list[CheckRunRecord]:
        return self._repository.list_promotion_check_runs(promotion_id, tenant_id)


class SqlAlchemyOrganizationAdapter(OrganizationPersistencePort):
    def __init__(self, repository: OrgRepository | None = None) -> None:
        self._repository = repository or org_repository

    def list_tenants(self) -> list[TenantRecord]:
        return self._repository.list_tenants()

    def create_tenant(self, payload: CreateTenantRequest) -> TenantRecord:
        return self._repository.create_tenant(payload)

    def update_tenant(self, tenant_id: str, payload: UpdateTenantRequest) -> TenantRecord:
        return self._repository.update_tenant(tenant_id, payload)

    def list_users(self, tenant_id: str | None = None) -> list[UserRecord]:
        return self._repository.list_users(tenant_id)

    def create_user(self, payload: CreateUserRequest, tenant_id: str) -> UserRecord:
        return self._repository.create_user(payload, tenant_id)

    def update_user(self, user_id: str, payload: UpdateUserRequest, tenant_id: str) -> UserRecord:
        return self._repository.update_user(user_id, payload, tenant_id)

    def authenticate_local_user(self, email: str, password: str, tenant_id: str | None = None) -> Principal:
        return self._repository.authenticate_local_user(email, password, tenant_id)

    def list_organizations(self, tenant_id: str | None = None) -> list[OrganizationRecord]:
        return self._repository.list_organizations(tenant_id)

    def create_organization(self, payload: CreateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        return self._repository.create_organization(payload, tenant_id)

    def update_organization(self, organization_id: str, payload: UpdateOrganizationRequest, tenant_id: str) -> OrganizationRecord:
        return self._repository.update_organization(organization_id, payload, tenant_id)

    def list_teams(self, tenant_id: str | None = None) -> list[TeamRecord]:
        return self._repository.list_teams(tenant_id)

    def create_team(self, payload: CreateTeamRequest, tenant_id: str) -> TeamRecord:
        return self._repository.create_team(payload, tenant_id)

    def update_team(self, team_id: str, payload: UpdateTeamRequest, tenant_id: str) -> TeamRecord:
        return self._repository.update_team(team_id, payload, tenant_id)

    def add_team_membership(self, payload: AddTeamMembershipRequest, tenant_id: str) -> TeamRecord:
        return self._repository.add_team_membership(payload, tenant_id)

    def list_portfolios(self, tenant_id: str | None = None) -> list[PortfolioRecord]:
        return self._repository.list_portfolios(tenant_id)

    def create_portfolio(self, payload: CreatePortfolioRequest, tenant_id: str) -> PortfolioRecord:
        return self._repository.create_portfolio(payload, tenant_id)

    def list_portfolio_summaries(self, tenant_id: str | None = None) -> list[PortfolioSummary]:
        return self._repository.list_portfolio_summaries(tenant_id)

    def list_integrations(self, tenant_id: str | None = None) -> list[IntegrationRecord]:
        return self._repository.list_integrations(tenant_id)

    def create_integration(self, payload: CreateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        return self._repository.create_integration(payload, tenant_id)

    def update_integration(self, integration_id: str, payload: UpdateIntegrationRequest, tenant_id: str) -> IntegrationRecord:
        return self._repository.update_integration(integration_id, payload, tenant_id)

    def delete_integration(self, integration_id: str, tenant_id: str) -> None:
        self._repository.delete_integration(integration_id, tenant_id)

    def list_policies(self, tenant_id: str | None = None) -> list[PolicyRecord]:
        return self._repository.list_policies(tenant_id)

    def update_policy_rules(self, policy_id: str, payload: PolicyRuleUpdateRequest, tenant_id: str) -> PolicyRecord:
        return self._repository.update_policy_rules(policy_id, payload, tenant_id)


class SqlAlchemyAnalyticsAdapter(AnalyticsQueryPort):
    def __init__(self, repository: AnalyticsRepository | None = None) -> None:
        self._repository = repository or analytics_repository

    def list_workflow_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsWorkflowRow]:
        return self._repository.list_workflow_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_workflow_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        workflow: str | None = None,
    ) -> list[WorkflowTrendPoint]:
        return self._repository.list_workflow_trends(days, tenant_id, team_id, user_id, portfolio_id, workflow)

    def list_agent_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsAgentRow]:
        return self._repository.list_agent_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_agent_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        agent: str | None = None,
    ) -> list[AgentTrendPoint]:
        return self._repository.list_agent_trends(days, tenant_id, team_id, user_id, portfolio_id, agent)

    def list_bottleneck_analytics(self, days: int = 30, tenant_id: str | None = None) -> list[AnalyticsBottleneckRow]:
        return self._repository.list_bottleneck_analytics(days, tenant_id)

    def list_delivery_dora(
        self,
        tenant_id: str | None = None,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryDoraRow]:
        return self._repository.list_delivery_dora(tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_lifecycle(
        self,
        tenant_id: str | None = None,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryLifecycleRow]:
        return self._repository.list_delivery_lifecycle(tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_trends(
        self,
        tenant_id: str | None = None,
        days: int = 30,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryTrendPoint]:
        return self._repository.list_delivery_trends(tenant_id, days, portfolio_id, team_id, user_id)

    def get_delivery_forecast(
        self,
        tenant_id: str | None = None,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> DeliveryForecastSummary:
        return self._repository.get_delivery_forecast(tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

    def list_delivery_forecast_points(
        self,
        tenant_id: str | None = None,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryForecastPoint]:
        return self._repository.list_delivery_forecast_points(tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

    def get_performance_operations_summary(self, tenant_id: str | None = None) -> PerformanceOperationsSummary:
        return self._repository.get_performance_operations_summary(tenant_id)

    def list_performance_operations_trends(self, tenant_id: str | None = None, days: int = 30) -> list[PerformanceOperationsTrendPoint]:
        return self._repository.list_performance_operations_trends(tenant_id, days)


class SqlAlchemyEventQueryAdapter(EventQueryPort):
    def __init__(self, repository: EventQueryRepository | None = None) -> None:
        self._repository = repository or event_query_repository

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
        return self._repository.list_event_ledger(
            page=page,
            page_size=page_size,
            tenant_id=tenant_id,
            request_id=request_id,
            run_id=run_id,
            artifact_id=artifact_id,
            promotion_id=promotion_id,
            check_run_id=check_run_id,
            event_type=event_type,
        )

    def list_event_outbox(
        self,
        page: int,
        page_size: int,
        tenant_id: str | None = None,
        request_id: str | None = None,
        status: str | None = None,
        topic: str | None = None,
    ) -> PaginatedResponse[EventOutboxRecord]:
        return self._repository.list_event_outbox(
            page=page,
            page_size=page_size,
            tenant_id=tenant_id,
            request_id=request_id,
            status=status,
            topic=topic,
        )


class SqlAlchemyGovernanceRuntimeAdapter(GovernanceRuntimePort):
    def __init__(self, repository: GovernanceRepository | None = None) -> None:
        self._repository = repository or governance_repository

    def list_agent_integrations_for_request(self, request_id: str, tenant_id: str | None = None) -> list[IntegrationRecord]:
        return self._repository.list_agent_integrations_for_request(request_id, tenant_id)

    def preview_agent_assignment_context(
        self,
        request_id: str,
        integration_id: str,
        collaboration_mode: str,
        agent_operating_profile: str,
        tenant_id: str,
    ) -> AgentSessionContextDetail:
        return self._repository.preview_agent_assignment_context(
            request_id,
            integration_id,
            collaboration_mode,
            agent_operating_profile,
            tenant_id,
        )

    def assign_agent_session(self, request_id: str, payload: AssignAgentSessionRequest, tenant_id: str) -> AgentSessionRecord:
        return self._repository.assign_agent_session(request_id, payload, tenant_id)

    def get_agent_session(self, request_id: str, session_id: str, tenant_id: str | None = None) -> AgentSessionDetail:
        return self._repository.get_agent_session(request_id, session_id, tenant_id)

    def get_agent_session_context(self, request_id: str, session_id: str, tenant_id: str | None = None) -> AgentSessionContextDetail:
        return self._repository.get_agent_session_context(request_id, session_id, tenant_id)

    def post_agent_session_message(
        self,
        request_id: str,
        session_id: str,
        payload: AgentSessionMessageCreateRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        return self._repository.post_agent_session_message(request_id, session_id, payload, tenant_id)

    def update_agent_session_governance(
        self,
        request_id: str,
        session_id: str,
        payload: UpdateAgentSessionGovernanceRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        return self._repository.update_agent_session_governance(request_id, session_id, payload, tenant_id)

    def stream_agent_session_response(self, request_id: str, session_id: str, tenant_id: str | None = None):
        return self._repository.stream_agent_session_response(request_id, session_id, tenant_id)

    def complete_agent_session(
        self,
        request_id: str,
        session_id: str,
        payload: CompleteAgentSessionRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        return self._repository.complete_agent_session(request_id, session_id, payload, tenant_id)

    def resume_agent_session_runtime(
        self,
        request_id: str,
        session_id: str,
        payload: ResumeAgentSessionRuntimeRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        return self._repository.resume_agent_session_runtime(request_id, session_id, payload, tenant_id)

    def approve_agent_session_checkpoint(
        self,
        request_id: str,
        session_id: str,
        payload: ApproveAgentSessionCheckpointRequest,
        tenant_id: str,
    ) -> AgentSessionDetail:
        return self._repository.approve_agent_session_checkpoint(request_id, session_id, payload, tenant_id)

    def import_agent_session_artifact(
        self,
        request_id: str,
        session_id: str,
        payload: ImportAgentSessionArtifactRequest,
        tenant_id: str,
    ) -> ArtifactDetail:
        return self._repository.import_agent_session_artifact(request_id, session_id, payload, tenant_id)

    def list_templates(self, tenant_id: str | None = None) -> list[TemplateRecord]:
        return self._repository.list_templates(tenant_id)

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
        return self._repository.list_runs(page, page_size, status, workflow, owner, request_id, federation, tenant_id)

    def get_run(self, run_id: str, tenant_id: str | None = None) -> RunDetail:
        return self._repository.get_run(run_id, tenant_id)

    def list_run_audit_entries(self, run_id: str, tenant_id: str | None = None) -> list[AuditEntry]:
        return self._repository.list_run_audit_entries(run_id, tenant_id)

    def command_run(self, run_id: str, payload: RunCommandRequest, tenant_id: str) -> RunDetail:
        return self._repository.command_run(run_id, payload, tenant_id)

    def reconcile_run(self, run_id: str, payload: RuntimeRunCallbackRequest) -> RunDetail:
        return self._repository.reconcile_run(run_id, payload)

    def list_artifacts(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[ArtifactRecord]:
        return self._repository.list_artifacts(page, page_size, tenant_id)

    def get_artifact(self, artifact_id: str, tenant_id: str | None = None) -> ArtifactDetail:
        return self._repository.get_artifact(artifact_id, tenant_id)

    def list_capabilities(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[CapabilityRecord]:
        return self._repository.list_capabilities(page, page_size, tenant_id)

    def get_capability(self, capability_id: str, tenant_id: str | None = None) -> CapabilityDetail:
        return self._repository.get_capability(capability_id, tenant_id)

    def list_workflow_audit_entries(self, workflow: str, tenant_id: str | None = None, limit: int = 200) -> list[AuditEntry]:
        return self._repository.list_workflow_audit_entries(workflow, tenant_id, limit)
