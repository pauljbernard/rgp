from app.core.config import settings
from app.db.models import CheckRunTable, IntegrationTable, ProjectionMappingTable, PromotionTable, ReviewQueueTable
from app.db.session import SessionLocal
from app.models.common import PaginatedResponse
from app.models.federation import CreateProjectionRequest, ProjectionMappingRecord, ReconciliationLogRecord, ResolveProjectionRequest, UpdateProjectionExternalStateRequest
from app.models.governance import (
    AnalyticsAgentRow,
    AgentSessionContextDetail,
    AgentSessionDetail,
    AgentSessionRecord,
    AgentSessionMessageCreateRequest,
    UpdateAgentSessionGovernanceRequest,
    AnalyticsBottleneckRow,
    AnalyticsWorkflowRow,
    AgentTrendPoint,
    AssignAgentSessionRequest,
    ImportAgentSessionArtifactRequest,
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
    ApproveAgentSessionCheckpointRequest,
    CreateIntegrationRequest,
    CreateOrganizationRequest,
    CreatePortfolioRequest,
    CreateTenantRequest,
    CreateTeamRequest,
    CreateUserRequest,
    EventLedgerRecord,
    EventOutboxRecord,
    OrganizationRecord,
    InstructionalWorkflowDecisionRequest,
    InstructionalWorkflowProjectionRecord,
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
    ResumeAgentSessionRuntimeRequest,
    ReviewAssignmentOverrideRequest,
    ReviewDecisionRequest,
    ReviewQueueItem,
    RunDetail,
    RunRecord,
)
from app.models.request import RequestRecord
from app.models.security import LocalLoginRequest, Principal, PrincipalRole, PublicRegistrationRequest, RegistrationSubmissionResponse
from app.models.template import TemplateRecord
from app.persistence import (
    AnalyticsQueryPort,
    DynamoDbGovernancePersistenceAdapter,
    EventQueryPort,
    GovernanceRuntimePort,
    OrganizationPersistencePort,
    PromotionPersistencePort,
    RequestLifecyclePort,
    SqlAlchemyAnalyticsAdapter,
    SqlAlchemyEventQueryAdapter,
    SqlAlchemyGovernanceRuntimeAdapter,
    SqlAlchemyOrganizationAdapter,
    SqlAlchemyPromotionAdapter,
    SqlAlchemyRequestLifecycleAdapter,
)
from app.services.performance_metrics_service import performance_metrics_service
from app.services.projection_service import projection_service
from app.services.reconciliation_service import reconciliation_service
from app.services.request_state_bridge import get_request_state


class GovernanceService:
    def __init__(
        self,
        governance_runtime: GovernanceRuntimePort,
        request_lifecycle: RequestLifecyclePort,
        promotion_store: PromotionPersistencePort,
        organization_store: OrganizationPersistencePort,
        analytics_store: AnalyticsQueryPort,
        event_query_store: EventQueryPort,
    ) -> None:
        self._governance_runtime = governance_runtime
        self._request_lifecycle = request_lifecycle
        self._promotion_store = promotion_store
        self._organization_store = organization_store
        self._analytics_store = analytics_store
        self._event_query_store = event_query_store

    @staticmethod
    def _admin_scope(principal: Principal) -> str | None:
        return None if PrincipalRole.PLATFORM_ADMIN in principal.roles else principal.tenant_id

    def _integration_scope_tenant(self, integration_id: str, principal: Principal) -> str:
        with SessionLocal() as session:
            row = session.get(IntegrationTable, integration_id)
            if row is None:
                raise StopIteration(integration_id)
            if PrincipalRole.PLATFORM_ADMIN in principal.roles:
                return row.tenant_id
            if row.tenant_id != principal.tenant_id:
                raise StopIteration(integration_id)
            return row.tenant_id

    def _projection_scope_tenant(self, projection_id: str, principal: Principal) -> str:
        with SessionLocal() as session:
            row = session.get(ProjectionMappingTable, projection_id)
            if row is None:
                raise StopIteration(projection_id)
            if PrincipalRole.PLATFORM_ADMIN in principal.roles:
                return row.tenant_id
            if row.tenant_id != principal.tenant_id:
                raise StopIteration(projection_id)
            return row.tenant_id

    def _request_scope_tenant(self, request_id: str, principal: Principal) -> str:
        request = get_request_state(request_id, None if PrincipalRole.PLATFORM_ADMIN in principal.roles else principal.tenant_id)
        if request is None:
            raise StopIteration(request_id)
        return request.tenant_id

    def _review_scope_tenant(self, review_id: str, principal: Principal) -> str:
        with SessionLocal() as session:
            row = session.get(ReviewQueueTable, review_id)
            if row is None:
                raise StopIteration(review_id)
        return self._request_scope_tenant(row.request_id, principal)

    def _promotion_scope_tenant(self, promotion_id: str, principal: Principal) -> str:
        with SessionLocal() as session:
            row = session.get(PromotionTable, promotion_id)
            if row is None:
                raise StopIteration(promotion_id)
        return self._request_scope_tenant(row.request_id, principal)

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
        tenant_scope = tenant_id or None
        if request_id is not None and tenant_scope is not None and get_request_state(request_id, tenant_scope) is None:
            raise StopIteration(request_id)
        return self._request_lifecycle.list_requests(page, page_size, status, owner_team_id, workflow, request_id, federation, tenant_scope)

    def get_request(self, request_id: str, principal: Principal) -> RequestDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._request_lifecycle.get_request(request_id, tenant_id)

    def list_instructional_workflow_projections(
        self,
        page: int,
        page_size: int,
        principal: Principal,
        flightos_content_entry_id: str | None = None,
        template_id: str | None = None,
        workflow_status: str | None = None,
    ) -> PaginatedResponse[InstructionalWorkflowProjectionRecord]:
        tenant_scope = None if PrincipalRole.PLATFORM_ADMIN in principal.roles else principal.tenant_id
        return self._request_lifecycle.list_instructional_workflow_projections(
            page=page,
            page_size=page_size,
            tenant_id=tenant_scope,
            flightos_content_entry_id=flightos_content_entry_id,
            template_id=template_id,
            workflow_status=workflow_status,
        )

    def get_instructional_workflow_projection(self, request_id: str, principal: Principal) -> InstructionalWorkflowProjectionRecord:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._request_lifecycle.get_instructional_workflow_projection(request_id, tenant_id)

    def decide_instructional_workflow_stage(
        self,
        request_id: str,
        payload: InstructionalWorkflowDecisionRequest,
        principal: Principal,
    ) -> InstructionalWorkflowProjectionRecord:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._request_lifecycle.decide_instructional_workflow_stage(request_id, payload, tenant_id)

    def list_agent_integrations_for_request(self, request_id: str, principal: Principal) -> list[IntegrationRecord]:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.list_agent_integrations_for_request(request_id, tenant_id)

    def preview_agent_assignment_context(
        self,
        request_id: str,
        integration_id: str,
        collaboration_mode: str,
        agent_operating_profile: str,
        principal: Principal,
    ) -> AgentSessionContextDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.preview_agent_assignment_context(
            request_id,
            integration_id,
            collaboration_mode,
            agent_operating_profile,
            tenant_id,
        )

    def assign_agent_session(self, request_id: str, payload: AssignAgentSessionRequest, principal: Principal) -> AgentSessionRecord:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.assign_agent_session(request_id, payload, tenant_id)

    def get_agent_session(self, request_id: str, session_id: str, principal: Principal) -> AgentSessionDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.get_agent_session(request_id, session_id, tenant_id)

    def get_agent_session_context(self, request_id: str, session_id: str, principal: Principal) -> AgentSessionContextDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.get_agent_session_context(request_id, session_id, tenant_id)

    def post_agent_session_message(
        self,
        request_id: str,
        session_id: str,
        payload: AgentSessionMessageCreateRequest,
        principal: Principal,
    ) -> AgentSessionDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.post_agent_session_message(request_id, session_id, payload, tenant_id)

    def update_agent_session_governance(
        self,
        request_id: str,
        session_id: str,
        payload: UpdateAgentSessionGovernanceRequest,
        principal: Principal,
    ) -> AgentSessionDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.update_agent_session_governance(request_id, session_id, payload, tenant_id)

    def stream_agent_session_response(
        self,
        request_id: str,
        session_id: str,
        principal: Principal,
    ):
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.stream_agent_session_response(request_id, session_id, tenant_id)

    def complete_agent_session(
        self,
        request_id: str,
        session_id: str,
        payload: CompleteAgentSessionRequest,
        principal: Principal,
    ) -> AgentSessionDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.complete_agent_session(request_id, session_id, payload, tenant_id)

    def resume_agent_session_runtime(
        self,
        request_id: str,
        session_id: str,
        payload: ResumeAgentSessionRuntimeRequest,
        principal: Principal,
    ) -> AgentSessionDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.resume_agent_session_runtime(request_id, session_id, payload, tenant_id)

    def approve_agent_session_checkpoint(
        self,
        request_id: str,
        session_id: str,
        payload: ApproveAgentSessionCheckpointRequest,
        principal: Principal,
    ) -> AgentSessionDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.approve_agent_session_checkpoint(request_id, session_id, payload, tenant_id)

    def import_agent_session_artifact(
        self,
        request_id: str,
        session_id: str,
        payload: ImportAgentSessionArtifactRequest,
        principal: Principal,
    ) -> ArtifactDetail:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return self._governance_runtime.import_agent_session_artifact(request_id, session_id, payload, tenant_id)

    def list_templates(self, principal: Principal) -> list[TemplateRecord]:
        return self._governance_runtime.list_templates(principal.tenant_id)

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
        tenant_scope = tenant_id or None
        if request_id is not None and tenant_scope is not None and get_request_state(request_id, tenant_scope) is None:
            raise StopIteration(request_id)
        return self._governance_runtime.list_runs(page, page_size, status, workflow, owner, request_id, federation, tenant_scope)

    def get_run(self, run_id: str, principal: Principal) -> RunDetail:
        return self._governance_runtime.get_run(run_id, principal.tenant_id)

    def get_run_history(self, run_id: str, principal: Principal) -> list[AuditEntry]:
        return self._governance_runtime.list_run_audit_entries(run_id, principal.tenant_id)

    def command_run(self, run_id: str, payload: RunCommandRequest, principal: Principal) -> RunDetail:
        return self._governance_runtime.command_run(run_id, payload, principal.tenant_id)

    def reconcile_run(self, run_id: str, payload: RuntimeRunCallbackRequest) -> RunDetail:
        return self._governance_runtime.reconcile_run(run_id, payload)

    def list_artifacts(self, page: int, page_size: int, tenant_id: str | None = None) -> PaginatedResponse[ArtifactRecord]:
        return self._governance_runtime.list_artifacts(page, page_size, tenant_id)

    def get_artifact(self, artifact_id: str, principal: Principal) -> ArtifactDetail:
        return self._governance_runtime.get_artifact(artifact_id, principal.tenant_id)

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
        tenant_scope = tenant_id or None
        if request_id is not None and tenant_scope is not None and get_request_state(request_id, tenant_scope) is None:
            raise StopIteration(request_id)
        return self._promotion_store.list_review_queue(page, page_size, assigned_reviewer, blocking_only, stale_only, request_id, tenant_scope)

    def record_review_decision(self, review_id: str, payload: ReviewDecisionRequest, principal: Principal) -> ReviewQueueItem:
        tenant_id = self._review_scope_tenant(review_id, principal)
        return self._promotion_store.record_review_decision(review_id, payload, tenant_id)

    def override_review_assignment(self, review_id: str, payload: ReviewAssignmentOverrideRequest, principal: Principal) -> ReviewQueueItem:
        tenant_id = self._review_scope_tenant(review_id, principal)
        return self._promotion_store.override_review_assignment(review_id, payload, tenant_id)

    def get_promotion(self, promotion_id: str, principal: Principal) -> PromotionDetail:
        tenant_id = self._promotion_scope_tenant(promotion_id, principal)
        return self._promotion_store.get_promotion(promotion_id, tenant_id)

    def apply_promotion_action(self, promotion_id: str, payload: PromotionActionRequest, principal: Principal) -> PromotionDetail:
        tenant_id = self._promotion_scope_tenant(promotion_id, principal)
        return self._promotion_store.apply_promotion_action(promotion_id, payload, tenant_id)

    def override_promotion_approval(self, promotion_id: str, payload: PromotionApprovalOverrideRequest, principal: Principal) -> PromotionDetail:
        tenant_id = self._promotion_scope_tenant(promotion_id, principal)
        return self._promotion_store.override_promotion_approval(promotion_id, payload, tenant_id)

    def evaluate_check(self, promotion_id: str, check_id: str, payload: CheckEvaluationRequest, principal: Principal) -> PromotionDetail:
        tenant_id = self._promotion_scope_tenant(promotion_id, principal)
        return self._promotion_store.evaluate_check(promotion_id, check_id, payload, tenant_id)

    def override_check(self, promotion_id: str, check_id: str, payload: CheckOverrideRequest, principal: Principal) -> PromotionDetail:
        tenant_id = self._promotion_scope_tenant(promotion_id, principal)
        return self._promotion_store.override_check(promotion_id, check_id, payload, tenant_id)

    def run_promotion_checks(self, promotion_id: str, payload: CheckRunRequest, principal: Principal) -> PromotionDetail:
        tenant_id = self._promotion_scope_tenant(promotion_id, principal)
        return self._promotion_store.run_promotion_checks(promotion_id, payload, tenant_id)

    def list_capabilities(self, page: int, page_size: int, principal: Principal) -> PaginatedResponse[CapabilityRecord]:
        return self._governance_runtime.list_capabilities(page, page_size, principal.tenant_id)

    def get_capability(self, capability_id: str, principal: Principal) -> CapabilityDetail:
        return self._governance_runtime.get_capability(capability_id, principal.tenant_id)

    def list_workflow_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsWorkflowRow]:
        return self._analytics_store.list_workflow_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_workflow_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        workflow: str | None = None,
    ) -> list[WorkflowTrendPoint]:
        return self._analytics_store.list_workflow_trends(days, tenant_id, team_id, user_id, portfolio_id, workflow)

    def get_workflow_history(self, workflow: str, principal: Principal, limit: int = 200) -> list[AuditEntry]:
        return self._governance_runtime.list_workflow_audit_entries(workflow, principal.tenant_id, limit)

    def list_agent_analytics(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
    ) -> list[AnalyticsAgentRow]:
        return self._analytics_store.list_agent_analytics(days, tenant_id, team_id, user_id, portfolio_id)

    def list_agent_trends(
        self,
        days: int = 30,
        tenant_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
        portfolio_id: str | None = None,
        agent: str | None = None,
    ) -> list[AgentTrendPoint]:
        return self._analytics_store.list_agent_trends(days, tenant_id, team_id, user_id, portfolio_id, agent)

    def list_bottleneck_analytics(self, days: int = 30, tenant_id: str | None = None) -> list[AnalyticsBottleneckRow]:
        return self._analytics_store.list_bottleneck_analytics(days, tenant_id)

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
        return self._analytics_store.get_performance_operations_summary(principal.tenant_id)

    def list_performance_operations_trends(self, principal: Principal, days: int = 30) -> list[PerformanceOperationsTrendPoint]:
        return self._analytics_store.list_performance_operations_trends(principal.tenant_id, days)

    def list_audit_entries(self, request_id: str, principal: Principal) -> list[AuditEntry]:
        return self._request_lifecycle.list_audit_entries(request_id, principal.tenant_id)

    def list_policies(self, principal: Principal) -> list[PolicyRecord]:
        return self._organization_store.list_policies(principal.tenant_id)

    def update_policy_rules(self, policy_id: str, payload: PolicyRuleUpdateRequest, principal: Principal) -> PolicyRecord:
        return self._organization_store.update_policy_rules(policy_id, payload, principal.tenant_id)

    def list_request_check_runs(self, request_id: str, principal: Principal) -> list[CheckRunRecord]:
        return self._request_lifecycle.list_request_check_runs(request_id, principal.tenant_id)

    def list_promotion_check_runs(self, promotion_id: str, principal: Principal) -> list[CheckRunRecord]:
        try:
            tenant_id = self._promotion_scope_tenant(promotion_id, principal)
            return self._promotion_store.list_promotion_check_runs(promotion_id, tenant_id)
        except PermissionError as exc:
            raise StopIteration(promotion_id) from exc

    def list_integrations(self, principal: Principal) -> list[IntegrationRecord]:
        return self._organization_store.list_integrations(self._admin_scope(principal))

    def create_integration(self, payload: CreateIntegrationRequest, principal: Principal) -> IntegrationRecord:
        return self._organization_store.create_integration(payload, principal.tenant_id)

    def update_integration(self, integration_id: str, payload: UpdateIntegrationRequest, principal: Principal) -> IntegrationRecord:
        return self._organization_store.update_integration(integration_id, payload, principal.tenant_id)

    def delete_integration(self, integration_id: str, principal: Principal) -> None:
        self._organization_store.delete_integration(integration_id, principal.tenant_id)

    def list_integration_projections(self, integration_id: str, principal: Principal) -> list[ProjectionMappingRecord]:
        tenant_id = self._integration_scope_tenant(integration_id, principal)
        return projection_service.list_projections(tenant_id, integration_id)

    def list_request_projections(self, request_id: str, principal: Principal) -> list[ProjectionMappingRecord]:
        tenant_id = self._request_scope_tenant(request_id, principal)
        return projection_service.list_projections(
            tenant_id,
            entity_type="request",
            entity_id=request_id,
        )

    def create_integration_projection(
        self,
        integration_id: str,
        payload: CreateProjectionRequest,
        principal: Principal,
    ) -> ProjectionMappingRecord:
        tenant_id = self._integration_scope_tenant(integration_id, principal)
        return projection_service.project_entity(payload.entity_type, payload.entity_id, integration_id, tenant_id)

    def sync_integration_projection(self, projection_id: str, principal: Principal) -> ProjectionMappingRecord:
        tenant_id = self._projection_scope_tenant(projection_id, principal)
        return projection_service.sync_external_state(projection_id, tenant_id)

    def update_integration_projection_external_state(
        self,
        projection_id: str,
        payload: UpdateProjectionExternalStateRequest,
        principal: Principal,
    ) -> ProjectionMappingRecord:
        tenant_id = self._projection_scope_tenant(projection_id, principal)
        return projection_service.update_external_state(
            projection_id=projection_id,
            external_status=payload.external_status,
            external_title=payload.external_title,
            external_ref=payload.external_ref,
            tenant_id=tenant_id,
        )

    def list_integration_reconciliation_logs(
        self,
        integration_id: str,
        principal: Principal,
    ) -> list[ReconciliationLogRecord]:
        tenant_id = self._integration_scope_tenant(integration_id, principal)
        return reconciliation_service.list_logs(integration_id, tenant_id)

    def reconcile_integration(self, integration_id: str, principal: Principal) -> list[ReconciliationLogRecord]:
        tenant_id = self._integration_scope_tenant(integration_id, principal)
        return reconciliation_service.reconcile_integration(integration_id, tenant_id)

    def resolve_integration_projection(
        self,
        projection_id: str,
        payload: ResolveProjectionRequest,
        principal: Principal,
    ) -> ReconciliationLogRecord:
        tenant_id = self._projection_scope_tenant(projection_id, principal)
        return reconciliation_service.apply_resolution(
            projection_id=projection_id,
            action=payload.action,
            resolved_by=payload.resolved_by or principal.user_id,
            tenant_id=tenant_id,
        )

    def list_users(self, principal: Principal) -> list[UserRecord]:
        return self._organization_store.list_users(self._admin_scope(principal))

    def list_tenants(self, principal: Principal) -> list[TenantRecord]:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            raise PermissionError("Tenant catalog requires platform administration scope")
        return self._organization_store.list_tenants()

    def create_tenant(self, payload: CreateTenantRequest, principal: Principal) -> TenantRecord:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            raise PermissionError("Tenant creation requires platform administration scope")
        return self._organization_store.create_tenant(payload)

    def update_tenant(self, tenant_id: str, payload: UpdateTenantRequest, principal: Principal) -> TenantRecord:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            raise PermissionError("Tenant updates require platform administration scope")
        return self._organization_store.update_tenant(tenant_id, payload)

    def create_user(self, payload: CreateUserRequest, principal: Principal) -> UserRecord:
        return self._organization_store.create_user(payload, principal.tenant_id)

    def update_user(self, user_id: str, payload: UpdateUserRequest, principal: Principal) -> UserRecord:
        return self._organization_store.update_user(user_id, payload, principal.tenant_id)

    def authenticate_local_user(self, payload: LocalLoginRequest) -> Principal:
        return self._organization_store.authenticate_local_user(payload.email, payload.password, payload.tenant_id)

    def create_public_registration_request(self, payload: PublicRegistrationRequest) -> RegistrationSubmissionResponse:
        return self._request_lifecycle.create_public_registration_request(payload)

    def list_organizations(self, principal: Principal) -> list[OrganizationRecord]:
        return self._organization_store.list_organizations(self._admin_scope(principal))

    def create_organization(self, payload: CreateOrganizationRequest, principal: Principal) -> OrganizationRecord:
        if PrincipalRole.PLATFORM_ADMIN not in principal.roles:
            payload = payload.model_copy(update={"tenant_id": principal.tenant_id})
        return self._organization_store.create_organization(payload, principal.tenant_id)

    def update_organization(self, organization_id: str, payload: UpdateOrganizationRequest, principal: Principal) -> OrganizationRecord:
        return self._organization_store.update_organization(organization_id, payload, principal.tenant_id)

    def list_public_registration_teams(self, tenant_id: str) -> list[TeamRecord]:
        return self._organization_store.list_teams(tenant_id)

    def list_teams(self, principal: Principal) -> list[TeamRecord]:
        return self._organization_store.list_teams(self._admin_scope(principal))

    def create_team(self, payload: CreateTeamRequest, principal: Principal) -> TeamRecord:
        return self._organization_store.create_team(payload, principal.tenant_id)

    def update_team(self, team_id: str, payload: UpdateTeamRequest, principal: Principal) -> TeamRecord:
        return self._organization_store.update_team(team_id, payload, principal.tenant_id)

    def add_team_membership(self, payload: AddTeamMembershipRequest, principal: Principal) -> TeamRecord:
        return self._organization_store.add_team_membership(payload, principal.tenant_id)

    def list_portfolios(self, principal: Principal) -> list[PortfolioRecord]:
        return self._organization_store.list_portfolios(self._admin_scope(principal))

    def create_portfolio(self, payload: CreatePortfolioRequest, principal: Principal) -> PortfolioRecord:
        return self._organization_store.create_portfolio(payload, principal.tenant_id)

    def list_portfolio_summaries(self, principal: Principal) -> list[PortfolioSummary]:
        return self._organization_store.list_portfolio_summaries(principal.tenant_id)

    def list_delivery_dora(
        self,
        principal: Principal,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryDoraRow]:
        return self._analytics_store.list_delivery_dora(principal.tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_lifecycle(
        self,
        principal: Principal,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryLifecycleRow]:
        return self._analytics_store.list_delivery_lifecycle(principal.tenant_id, portfolio_id, team_id, user_id)

    def list_delivery_trends(
        self,
        principal: Principal,
        days: int = 30,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryTrendPoint]:
        return self._analytics_store.list_delivery_trends(principal.tenant_id, days, portfolio_id, team_id, user_id)

    def get_delivery_forecast(
        self,
        principal: Principal,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> DeliveryForecastSummary:
        return self._analytics_store.get_delivery_forecast(principal.tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

    def list_delivery_forecast_points(
        self,
        principal: Principal,
        history_days: int = 30,
        forecast_days: int = 14,
        portfolio_id: str | None = None,
        team_id: str | None = None,
        user_id: str | None = None,
    ) -> list[DeliveryForecastPoint]:
        return self._analytics_store.list_delivery_forecast_points(principal.tenant_id, history_days, forecast_days, portfolio_id, team_id, user_id)

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
        tenant_scope = None if PrincipalRole.PLATFORM_ADMIN in principal.roles else principal.tenant_id
        if request_id is not None and get_request_state(request_id, tenant_scope) is None:
            raise StopIteration(request_id)
        if run_id is not None:
            try:
                self._governance_runtime.get_run(run_id, tenant_scope)
            except PermissionError as exc:
                raise StopIteration(run_id) from exc
        if artifact_id is not None:
            try:
                self._governance_runtime.get_artifact(artifact_id, tenant_scope)
            except PermissionError as exc:
                raise StopIteration(artifact_id) from exc
        if promotion_id is not None:
            try:
                self._promotion_store.get_promotion(promotion_id, tenant_scope)
            except PermissionError as exc:
                raise StopIteration(promotion_id) from exc
        if check_run_id is not None:
            with SessionLocal() as session:
                check_run = session.get(CheckRunTable, check_run_id)
            if check_run is None:
                raise StopIteration(check_run_id)
            if check_run.promotion_id is not None:
                try:
                    self._promotion_store.get_promotion(check_run.promotion_id, tenant_scope)
                except PermissionError as exc:
                    raise StopIteration(check_run_id) from exc
            elif check_run.request_id is not None and get_request_state(check_run.request_id, tenant_scope) is None:
                raise StopIteration(check_run_id)
        return self._event_query_store.list_event_ledger(
            page=page,
            page_size=page_size,
            tenant_id=tenant_scope,
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
        tenant_scope = None if PrincipalRole.PLATFORM_ADMIN in principal.roles else principal.tenant_id
        if request_id is not None and get_request_state(request_id, tenant_scope) is None:
            raise StopIteration(request_id)
        return self._event_query_store.list_event_outbox(
            page=page,
            page_size=page_size,
            tenant_id=tenant_scope,
            request_id=request_id,
            status=status,
            topic=topic,
        )


def _build_request_lifecycle_store() -> RequestLifecyclePort:
    backend = (settings.request_persistence_backend or settings.persistence_backend or "sqlalchemy").lower()
    if backend == "dynamodb":
        return DynamoDbGovernancePersistenceAdapter()
    return SqlAlchemyRequestLifecycleAdapter()


governance_service = GovernanceService(
    governance_runtime=SqlAlchemyGovernanceRuntimeAdapter(),
    request_lifecycle=_build_request_lifecycle_store(),
    promotion_store=SqlAlchemyPromotionAdapter(),
    organization_store=SqlAlchemyOrganizationAdapter(),
    analytics_store=SqlAlchemyAnalyticsAdapter(),
    event_query_store=SqlAlchemyEventQueryAdapter(),
)
