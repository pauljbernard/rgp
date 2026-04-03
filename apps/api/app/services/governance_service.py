from app.models.common import PaginatedResponse
from app.models.governance import (
    AnalyticsAgentRow,
    AgentSessionDetail,
    AgentSessionRecord,
    AgentSessionMessageCreateRequest,
    AnalyticsBottleneckRow,
    AnalyticsWorkflowRow,
    AgentTrendPoint,
    AssignAgentSessionRequest,
    ArtifactDetail,
    ArtifactRecord,
    AuditEntry,
    CapabilityDetail,
    CapabilityRecord,
    DeliveryDoraRow,
    DeliveryForecastPoint,
    DeliveryForecastSummary,
    DeliveryLifecycleRow,
    DeliveryTrendPoint,
    IntegrationRecord,
    PolicyRecord,
    PolicyRuleUpdateRequest,
    PerformanceRouteSummary,
    PerformanceSloSummary,
    PerformanceMetricRecord,
    PerformanceOperationsSummary,
    PerformanceOperationsTrendPoint,
    PerformanceTrendPoint,
    PortfolioRecord,
    PortfolioSummary,
    PromotionDetail,
    PromotionActionRequest,
    PromotionApprovalOverrideRequest,
    CheckEvaluationRequest,
    CheckRunRequest,
    CheckOverrideRequest,
    CheckRunRecord,
    CompleteAgentSessionRequest,
    CreateIntegrationRequest,
    CreateOrganizationRequest,
    CreatePortfolioRequest,
    CreateTenantRequest,
    CreateTeamRequest,
    CreateUserRequest,
    EventLedgerRecord,
    EventOutboxRecord,
    OrganizationRecord,
    RunCommandRequest,
    RuntimeRunCallbackRequest,
    AddTeamMembershipRequest,
    TeamRecord,
    TenantRecord,
    UpdateIntegrationRequest,
    UpdateOrganizationRequest,
    UpdateTenantRequest,
    UpdateTeamRequest,
    UpdateUserRequest,
    UserRecord,
    WorkflowTrendPoint,
    RequestDetail,
    ReviewAssignmentOverrideRequest,
    ReviewDecisionRequest,
    ReviewQueueItem,
    RunDetail,
    RunRecord,
)
from app.models.request import RequestRecord
from app.models.security import LocalLoginRequest, Principal, PrincipalRole, PublicRegistrationRequest, RegistrationSubmissionResponse
from app.models.template import TemplateRecord
from app.repositories.governance_repository import governance_repository
from app.services.performance_metrics_service import performance_metrics_service


class GovernanceService:
    @staticmethod
    def _admin_scope(principal: Principal) -> str | None:
        return None if PrincipalRole.PLATFORM_ADMIN in principal.roles else principal.tenant_id

    def list_requests(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        owner_team_id: str | None = None,
        workflow: str | None = None,
        request_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[RequestRecord]:
        return governance_repository.list_requests(page, page_size, status, owner_team_id, workflow, request_id, tenant_id)

    def get_request(self, request_id: str, principal: Principal) -> RequestDetail:
        return governance_repository.get_request(request_id, principal.tenant_id)

    def list_agent_integrations_for_request(self, request_id: str, principal: Principal) -> list[IntegrationRecord]:
        return governance_repository.list_agent_integrations_for_request(request_id, principal.tenant_id)

    def assign_agent_session(self, request_id: str, payload: AssignAgentSessionRequest, principal: Principal) -> AgentSessionRecord:
        return governance_repository.assign_agent_session(request_id, payload, principal.tenant_id)

    def get_agent_session(self, request_id: str, session_id: str, principal: Principal) -> AgentSessionDetail:
        return governance_repository.get_agent_session(request_id, session_id, principal.tenant_id)

    def post_agent_session_message(
        self,
        request_id: str,
        session_id: str,
        payload: AgentSessionMessageCreateRequest,
        principal: Principal,
    ) -> AgentSessionDetail:
        return governance_repository.post_agent_session_message(request_id, session_id, payload, principal.tenant_id)

    def stream_agent_session_response(
        self,
        request_id: str,
        session_id: str,
        principal: Principal,
    ):
        return governance_repository.stream_agent_session_response(request_id, session_id, principal.tenant_id)

    def complete_agent_session(
        self,
        request_id: str,
        session_id: str,
        payload: CompleteAgentSessionRequest,
        principal: Principal,
    ) -> AgentSessionDetail:
        return governance_repository.complete_agent_session(request_id, session_id, payload, principal.tenant_id)

    def list_templates(self, principal: Principal) -> list[TemplateRecord]:
        return governance_repository.list_templates(principal.tenant_id)

    def list_runs(
        self,
        page: int,
        page_size: int,
        status: str | None = None,
        workflow: str | None = None,
        owner: str | None = None,
        request_id: str | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[RunRecord]:
        return governance_repository.list_runs(page, page_size, status, workflow, owner, request_id, tenant_id)

    def get_run(self, run_id: str, principal: Principal) -> RunDetail:
        return governance_repository.get_run(run_id, principal.tenant_id)

    def command_run(self, run_id: str, payload: RunCommandRequest, principal: Principal) -> RunDetail:
        return governance_repository.command_run(run_id, payload, principal.tenant_id)

    def reconcile_run(self, run_id: str, payload: RuntimeRunCallbackRequest) -> RunDetail:
        return governance_repository.reconcile_run(run_id, payload)

    def list_artifacts(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[ArtifactRecord]:
        return governance_repository.list_artifacts(page, page_size, tenant_id)

    def get_artifact(self, artifact_id: str, principal: Principal) -> ArtifactDetail:
        return governance_repository.get_artifact(artifact_id, principal.tenant_id)

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
        return governance_repository.list_review_queue(page, page_size, assigned_reviewer, blocking_only, stale_only, request_id, tenant_id)

    def record_review_decision(self, review_id: str, payload: ReviewDecisionRequest, principal: Principal) -> ReviewQueueItem:
        return governance_repository.record_review_decision(review_id, payload, principal.tenant_id)

    def override_review_assignment(self, review_id: str, payload: ReviewAssignmentOverrideRequest, principal: Principal) -> ReviewQueueItem:
        return governance_repository.override_review_assignment(review_id, payload, principal.tenant_id)

    def get_promotion(self, promotion_id: str, principal: Principal) -> PromotionDetail:
        return governance_repository.get_promotion(promotion_id, principal.tenant_id)

    def apply_promotion_action(self, promotion_id: str, payload: PromotionActionRequest, principal: Principal) -> PromotionDetail:
        return governance_repository.apply_promotion_action(promotion_id, payload, principal.tenant_id)

    def override_promotion_approval(self, promotion_id: str, payload: PromotionApprovalOverrideRequest, principal: Principal) -> PromotionDetail:
        return governance_repository.override_promotion_approval(promotion_id, payload, principal.tenant_id)

    def evaluate_check(self, promotion_id: str, check_id: str, payload: CheckEvaluationRequest, principal: Principal) -> PromotionDetail:
        return governance_repository.evaluate_check(promotion_id, check_id, payload, principal.tenant_id)

    def override_check(self, promotion_id: str, check_id: str, payload: CheckOverrideRequest, principal: Principal) -> PromotionDetail:
        return governance_repository.override_check(promotion_id, check_id, payload, principal.tenant_id)

    def run_promotion_checks(self, promotion_id: str, payload: CheckRunRequest, principal: Principal) -> PromotionDetail:
        return governance_repository.run_promotion_checks(promotion_id, payload, principal.tenant_id)

    def list_capabilities(self, page: int, page_size: int, principal: Principal) -> PaginatedResponse[CapabilityRecord]:
        return governance_repository.list_capabilities(page, page_size, principal.tenant_id)

    def get_capability(self, capability_id: str, principal: Principal) -> CapabilityDetail:
        return governance_repository.get_capability(capability_id, principal.tenant_id)

    def list_workflow_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsWorkflowRow]:
        return governance_repository.list_workflow_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_workflow_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        workflow: str | None = None,
    ) -> list[WorkflowTrendPoint]:
        return governance_repository.list_workflow_trends(days, tenant_id, team_id, user_id, portfolio_id, workflow)

    def list_agent_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsAgentRow]:
        return governance_repository.list_agent_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_agent_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        agent: str | None = None,
    ) -> list[AgentTrendPoint]:
        return governance_repository.list_agent_trends(days, tenant_id, team_id, user_id, portfolio_id, agent)

    def list_bottleneck_analytics(self, days: int = 30, tenant_id: str | None = None) -> list[AnalyticsBottleneckRow]:
        return governance_repository.list_bottleneck_analytics(days, tenant_id)

    def list_performance_route_summaries(
        self, page: int, page_size: int, days: int, principal: Principal
    ) -> PaginatedResponse[PerformanceRouteSummary]:
        return performance_metrics_service.list_route_summaries(
            tenant_id=principal.tenant_id,
            days=days,
            page=page,
            page_size=page_size,
        )

    def list_performance_slo_summaries(
        self, page: int, page_size: int, days: int, principal: Principal
    ) -> PaginatedResponse[PerformanceSloSummary]:
        return performance_metrics_service.list_slo_summaries(
            tenant_id=principal.tenant_id,
            days=days,
            page=page,
            page_size=page_size,
        )

    def list_performance_metrics(
        self,
        page: int,
        page_size: int,
        days: int,
        principal: Principal,
        route: str | None = None,
        method: str | None = None,
        status_code: int | None = None,
    ) -> PaginatedResponse[PerformanceMetricRecord]:
        return performance_metrics_service.list_raw_metrics(
            tenant_id=principal.tenant_id,
            days=days,
            page=page,
            page_size=page_size,
            route=route,
            method=method,
            status_code=status_code,
        )

    def list_performance_trends(
        self,
        page: int,
        page_size: int,
        days: int,
        principal: Principal,
        route: str | None = None,
        method: str | None = None,
    ) -> PaginatedResponse[PerformanceTrendPoint]:
        return performance_metrics_service.list_route_trends(
            tenant_id=principal.tenant_id,
            days=days,
            page=page,
            page_size=page_size,
            route=route,
            method=method,
        )

    def get_performance_operations_summary(self, principal: Principal) -> PerformanceOperationsSummary:
        return governance_repository.get_performance_operations_summary(principal.tenant_id)

    def list_performance_operations_trends(self, principal: Principal, days: int = 30) -> list[PerformanceOperationsTrendPoint]:
        return governance_repository.list_performance_operations_trends(principal.tenant_id, days)

    def list_audit_entries(self, request_id: str, principal: Principal) -> list[AuditEntry]:
        return governance_repository.list_audit_entries(request_id, principal.tenant_id)

    def list_policies(self, principal: Principal) -> list[PolicyRecord]:
        return governance_repository.list_policies(principal.tenant_id)

    def update_policy_rules(self, policy_id: str, payload: PolicyRuleUpdateRequest, principal: Principal) -> PolicyRecord:
        return governance_repository.update_policy_rules(policy_id, payload, principal.tenant_id)

    def list_request_check_runs(self, request_id: str, principal: Principal) -> list[CheckRunRecord]:
        return governance_repository.list_request_check_runs(request_id, principal.tenant_id)

    def list_promotion_check_runs(self, promotion_id: str, principal: Principal) -> list[CheckRunRecord]:
        return governance_repository.list_promotion_check_runs(promotion_id, principal.tenant_id)

    def list_integrations(self, principal: Principal) -> list[IntegrationRecord]:
        return governance_repository.list_integrations(self._admin_scope(principal))

    def create_integration(self, payload: CreateIntegrationRequest, principal: Principal) -> IntegrationRecord:
        return governance_repository.create_integration(payload, principal.tenant_id)

    def update_integration(self, integration_id: str, payload: UpdateIntegrationRequest, principal: Principal) -> IntegrationRecord:
        return governance_repository.update_integration(integration_id, payload, principal.tenant_id)

    def delete_integration(self, integration_id: str, principal: Principal) -> None:
        governance_repository.delete_integration(integration_id, principal.tenant_id)

    def list_users(self, principal: Principal) -> list[UserRecord]:
        return governance_repository.list_users(self._admin_scope(principal))

    def list_tenants(self, principal: Principal) -> list[TenantRecord]:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            raise PermissionError("Tenant catalog requires platform administration scope")
        return governance_repository.list_tenants()

    def create_tenant(self, payload: CreateTenantRequest, principal: Principal) -> TenantRecord:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            raise PermissionError("Tenant creation requires platform administration scope")
        return governance_repository.create_tenant(payload)

    def update_tenant(self, tenant_id: str, payload: UpdateTenantRequest, principal: Principal) -> TenantRecord:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            raise PermissionError("Tenant updates require platform administration scope")
        return governance_repository.update_tenant(tenant_id, payload)

    def create_user(self, payload: CreateUserRequest, principal: Principal) -> UserRecord:
        return governance_repository.create_user(payload, principal.tenant_id)

    def update_user(self, user_id: str, payload: UpdateUserRequest, principal: Principal) -> UserRecord:
        return governance_repository.update_user(user_id, payload, principal.tenant_id)

    def authenticate_local_user(self, payload: LocalLoginRequest) -> Principal:
        return governance_repository.authenticate_local_user(payload.email, payload.password, payload.tenant_id)

    def create_public_registration_request(self, payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
        return governance_repository.create_public_registration_request(payload)

    def list_organizations(self, principal: Principal) -> list[OrganizationRecord]:
        return governance_repository.list_organizations(self._admin_scope(principal))

    def create_organization(self, payload: CreateOrganizationRequest, principal: Principal) -> OrganizationRecord:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            payload = payload.model_copy(update={"tenant_id": principal.tenant_id})
        return governance_repository.create_organization(payload, principal.tenant_id)

    def update_organization(self, organization_id: str, payload: UpdateOrganizationRequest, principal: Principal) -> OrganizationRecord:
        return governance_repository.update_organization(organization_id, payload, principal.tenant_id)

    def list_public_registration_teams(self, tenant_id: str) -> list[TeamRecord]:
        return governance_repository.list_teams(tenant_id)

    def list_teams(self, principal: Principal) -> list[TeamRecord]:
        return governance_repository.list_teams(self._admin_scope(principal))

    def create_team(self, payload: CreateTeamRequest, principal: Principal) -> TeamRecord:
        return governance_repository.create_team(payload, principal.tenant_id)

    def update_team(self, team_id: str, payload: UpdateTeamRequest, principal: Principal) -> TeamRecord:
        return governance_repository.update_team(team_id, payload, principal.tenant_id)

    def add_team_membership(self, payload: AddTeamMembershipRequest, principal: Principal) -> TeamRecord:
        return governance_repository.add_team_membership(payload, principal.tenant_id)

    def list_portfolios(self, principal: Principal) -> list[PortfolioRecord]:
        return governance_repository.list_portfolios(self._admin_scope(principal))

    def create_portfolio(self, payload: CreatePortfolioRequest, principal: Principal) -> PortfolioRecord:
        return governance_repository.create_portfolio(payload, principal.tenant_id)

    def list_portfolio_summaries(self, principal: Principal) -> list[PortfolioSummary]:
        return governance_repository.list_portfolio_summaries(principal.tenant_id)

    def list_delivery_dora(
        self,
        principal: Principal,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryDoraRow]:
        return governance_repository.list_delivery_dora(principal.tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_lifecycle(
        self,
        principal: Principal,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryLifecycleRow]:
        return governance_repository.list_delivery_lifecycle(principal.tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_trends(
        self,
        principal: Principal,
        days: int = 30,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryTrendPoint]:
        return governance_repository.list_delivery_trends(principal.tenant_id, days, portfolio_id, team_id, user_id)

    def get_delivery_forecast(
        self,
        principal: Principal,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> DeliveryForecastSummary:
        return governance_repository.get_delivery_forecast(principal.tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

    def list_delivery_forecast_points(
        self,
        principal: Principal,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryForecastPoint]:
        return governance_repository.list_delivery_forecast_points(principal.tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

    def list_event_ledger(
        self,
        page: int,
        page_size: int,
        principal: Principal,
        request_id: str | None = None,
        run_id: str | None = None,
        artifact_id: str | None = None,
        promotion_id: str | None = None,
        check_run_id: str | None = None,
        event_type: str | None = None,
    ) -> PaginatedResponse[EventLedgerRecord]:
        return governance_repository.list_event_ledger(
            page=page,
            page_size=page_size,
            tenant_id=principal.tenant_id,
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
        principal: Principal,
        request_id: str | None = None,
        status: str | None = None,
        topic: str | None = None,
    ) -> PaginatedResponse[EventOutboxRecord]:
        return governance_repository.list_event_outbox(
            page=page,
            page_size=page_size,
            tenant_id=principal.tenant_id,
            request_id=request_id,
            status=status,
            topic=topic,
        )


governance_service = GovernanceService()
