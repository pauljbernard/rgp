import type {
  AnalyticsAgentRow,
  AnalyticsBottleneckRow,
  AnalyticsWorkflowRow,
  AddTeamMembershipInput,
  AgentTrendPoint,
  AgentSessionDetail,
  AgentSessionRecord,
  ArtifactDetail,
  ArtifactRecord,
  CapabilityDetail,
  CapabilityRecord,
  CreateIntegrationInput,
  CreateOrganizationInput,
  CreatePortfolioInput,
  CreateTeamInput,
  CreateTenantInput,
  CreateUserInput,
  DeliveryDoraRow,
  DeliveryForecastPoint,
  DeliveryForecastSummary,
  DeliveryLifecycleRow,
  DeliveryTrendPoint,
  PaginatedResponse,
  PolicyRecord,
  PortfolioRecord,
  PortfolioSummary,
  PerformanceMetricRecord,
  PerformanceOperationsSummary,
  PerformanceOperationsTrendPoint,
  PerformanceRouteSummary,
  PerformanceSloSummary,
  PerformanceTrendPoint,
  Principal,
  PromotionAction,
  PromotionDetail,
  RegistrationOptions,
  RequestDetail,
  RequestPriority,
  RequestRecord,
  RequestStatus,
  ReviewDecision,
  ReviewQueueItem,
  TeamRecord,
  TenantRecord,
  UpdateTeamInput,
  UpdateTenantInput,
  RunDetail,
  RunRecord,
  RunCommand,
  TemplateRecord,
  TemplateValidationResult,
  IntegrationRecord,
  OrganizationRecord,
  UpdateIntegrationInput,
  UpdateOrganizationInput,
  UpdateUserInput,
  AuditEntry,
  UserRecord,
  WorkflowTrendPoint
} from "@rgp/domain";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

type Paging = {
  page?: number;
  page_size?: number;
};

type RequestListParams = Paging & {
  status?: string;
  owner_team_id?: string;
  workflow?: string;
  request_id?: string;
};

type RunListParams = Paging & {
  status?: string;
  workflow?: string;
  owner?: string;
  request_id?: string;
};

type ReviewListParams = Paging & {
  assigned_reviewer?: string;
  blocking_only?: boolean;
  stale_only?: boolean;
  request_id?: string;
};

type AnalyticsScopeParams = {
  days?: number;
  team_id?: string;
  user_id?: string;
  portfolio_id?: string;
};

type CreateRequestDraftInput = {
  template_id: string;
  template_version: string;
  title: string;
  summary: string;
  priority: RequestPriority;
  input_payload?: Record<string, unknown>;
};

type RequestMutationInput = {
  actor_id?: string;
  reason?: string;
};

type TransitionRequestInput = RequestMutationInput & {
  target_status: RequestStatus;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
const apiToken = process.env.RGP_API_TOKEN ?? process.env.NEXT_PUBLIC_RGP_API_TOKEN;
const sessionCookieName = "rgp_access_token";

function withQuery(path: string, params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") {
      continue;
    }
    search.set(key, String(value));
  }
  return `${path}?${search.toString()}`;
}

async function bearerToken() {
  if (apiToken) {
    return apiToken;
  }
  const store = await cookies();
  const token = store.get(sessionCookieName)?.value;
  if (!token) {
    redirect("/login");
  }
  return token;
}

async function requestWithOptions<T>(path: string, init: RequestInit): Promise<T> {
  const token = await bearerToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
    ...((init.headers as Record<string, string> | undefined) ?? {})
  };
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers,
    ...init,
    cache: "no-store"
  });

  if (response.status === 401) {
    redirect("/login");
  }

  if (response.status === 403) {
    const from = encodeURIComponent(path);
    redirect(`/forbidden?from=${from}`);
  }

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string" && payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep the generic fallback when the response body is not JSON.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

async function request<T>(path: string): Promise<T> {
  return requestWithOptions<T>(path, {});
}

async function publicRequest<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function listRequests(params: RequestListParams = {}) {
  return request<PaginatedResponse<RequestRecord>>(
    withQuery("/api/v1/requests", {
      page: params.page ?? 1,
      page_size: params.page_size ?? 25,
      status: params.status,
      owner_team_id: params.owner_team_id,
      workflow: params.workflow,
      request_id: params.request_id
    })
  );
}

export function createRequestDraft(payload: CreateRequestDraftInput) {
  return requestWithOptions<RequestRecord>("/api/v1/requests", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listTemplates() {
  return request<TemplateRecord[]>("/api/v1/templates");
}

export function listPublicRegistrationOptions(tenantId = "tenant_demo") {
  return publicRequest<RegistrationOptions>(withQuery("/api/v1/auth/registration-options", { tenant_id: tenantId }));
}

export function getCurrentPrincipal() {
  return request<Principal>("/api/v1/auth/me");
}

export function getRequest(requestId: string) {
  return request<RequestDetail>(`/api/v1/requests/${requestId}`);
}

export function listRequestAgentIntegrations(requestId: string) {
  return request<IntegrationRecord[]>(`/api/v1/requests/${requestId}/agent-integrations`);
}

export function assignAgentSession(
  requestId: string,
  payload: { integration_id: string; initial_prompt: string; agent_label?: string; actor_id?: string; reason?: string }
) {
  return requestWithOptions<AgentSessionRecord>(`/api/v1/requests/${requestId}/agent-sessions`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getAgentSession(requestId: string, sessionId: string) {
  return request<AgentSessionDetail>(`/api/v1/requests/${requestId}/agent-sessions/${sessionId}`);
}

export function postAgentSessionMessage(
  requestId: string,
  sessionId: string,
  payload: { body: string; message_type?: string; actor_id?: string; reason?: string }
) {
  return requestWithOptions<AgentSessionDetail>(`/api/v1/requests/${requestId}/agent-sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function completeAgentSession(
  requestId: string,
  sessionId: string,
  payload: { reason?: string; target_status?: string; actor_id?: string } = {}
) {
  return requestWithOptions<AgentSessionDetail>(`/api/v1/requests/${requestId}/agent-sessions/${sessionId}/complete`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getRequestHistory(requestId: string) {
  return request<AuditEntry[]>(`/api/v1/requests/${requestId}/history`);
}

export function submitRequest(requestId: string, payload: RequestMutationInput = {}) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/submit`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function cancelRequest(requestId: string, payload: RequestMutationInput = {}) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/cancel`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function transitionRequest(requestId: string, payload: TransitionRequestInput) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/transition`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function runRequestChecks(requestId: string, payload: RequestMutationInput = {}) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/checks/run`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function cloneRequest(requestId: string, payload: RequestMutationInput = {}) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/clone`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listRuns(params: RunListParams = {}) {
  return request<PaginatedResponse<RunRecord>>(
    withQuery("/api/v1/runs", {
      page: params.page ?? 1,
      page_size: params.page_size ?? 25,
      status: params.status,
      workflow: params.workflow,
      owner: params.owner,
      request_id: params.request_id
    })
  );
}

export function getRun(runId: string) {
  return request<RunDetail>(`/api/v1/runs/${runId}`);
}

export function commandRun(runId: string, payload: { command: RunCommand; reason?: string; actor_id?: string }) {
  return requestWithOptions<RunDetail>(`/api/v1/runs/${runId}/commands`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listArtifacts(params: Paging = {}) {
  return request<PaginatedResponse<ArtifactRecord>>(
    withQuery("/api/v1/artifacts", {
      page: params.page ?? 1,
      page_size: params.page_size ?? 25
    })
  );
}

export function getArtifact(artifactId: string) {
  return request<ArtifactDetail>(`/api/v1/artifacts/${artifactId}`);
}

export function listReviewQueue(params: ReviewListParams = {}) {
  return request<PaginatedResponse<ReviewQueueItem>>(
    withQuery("/api/v1/reviews/queue", {
      page: params.page ?? 1,
      page_size: params.page_size ?? 25,
      assigned_reviewer: params.assigned_reviewer,
      blocking_only: params.blocking_only,
      stale_only: params.stale_only,
      request_id: params.request_id
    })
  );
}

export function recordReviewDecision(reviewId: string, payload: { decision: ReviewDecision; actor_id?: string; reason?: string }) {
  return requestWithOptions<ReviewQueueItem>(`/api/v1/reviews/queue/${reviewId}/decision`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function overrideReviewAssignment(reviewId: string, payload: { assigned_reviewer: string; actor_id?: string; reason?: string }) {
  return requestWithOptions<ReviewQueueItem>(`/api/v1/reviews/queue/${reviewId}/override-assignment`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getPromotion(promotionId: string) {
  return request<PromotionDetail>(`/api/v1/promotions/${promotionId}`);
}

export function applyPromotionAction(promotionId: string, payload: { action: PromotionAction; actor_id?: string; reason?: string }) {
  return requestWithOptions<PromotionDetail>(`/api/v1/promotions/${promotionId}/actions`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function evaluatePromotionCheck(
  promotionId: string,
  checkId: string,
  payload: { state: string; detail: string; evidence?: string; actor_id?: string }
) {
  return requestWithOptions<PromotionDetail>(`/api/v1/promotions/${promotionId}/checks/${checkId}/evaluate`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function overridePromotionCheck(
  promotionId: string,
  checkId: string,
  payload: { reason: string; actor_id?: string }
) {
  return requestWithOptions<PromotionDetail>(`/api/v1/promotions/${promotionId}/checks/${checkId}/override`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function runPromotionChecks(
  promotionId: string,
  payload: { reason?: string; actor_id?: string } = {}
) {
  return requestWithOptions<PromotionDetail>(`/api/v1/promotions/${promotionId}/checks/run`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function overridePromotionApproval(
  promotionId: string,
  payload: { reviewer: string; replacement_reviewer: string; reason?: string; actor_id?: string }
) {
  return requestWithOptions<PromotionDetail>(`/api/v1/promotions/${promotionId}/override-approval`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listCapabilities(params: Paging = {}) {
  return request<PaginatedResponse<CapabilityRecord>>(
    withQuery("/api/v1/capabilities", {
      page: params.page ?? 1,
      page_size: params.page_size ?? 25
    })
  );
}

export function getCapability(capabilityId: string) {
  return request<CapabilityDetail>(`/api/v1/capabilities/${capabilityId}`);
}

export function listWorkflowAnalytics(params: AnalyticsScopeParams = {}) {
  return request<AnalyticsWorkflowRow[]>(
    withQuery("/api/v1/analytics/workflows", {
      days: params.days ?? 30,
      team_id: params.team_id,
      user_id: params.user_id,
      portfolio_id: params.portfolio_id
    })
  );
}

export function listWorkflowTrends(params: AnalyticsScopeParams & { workflow?: string } = {}) {
  return request<WorkflowTrendPoint[]>(
    withQuery("/api/v1/analytics/workflows/trends", {
      days: params.days ?? 30,
      team_id: params.team_id,
      user_id: params.user_id,
      portfolio_id: params.portfolio_id,
      workflow: params.workflow
    })
  );
}

export function listAgentAnalytics(params: AnalyticsScopeParams = {}) {
  return request<AnalyticsAgentRow[]>(
    withQuery("/api/v1/analytics/agents", {
      days: params.days ?? 30,
      team_id: params.team_id,
      user_id: params.user_id,
      portfolio_id: params.portfolio_id
    })
  );
}

export function listAgentTrends(params: AnalyticsScopeParams & { agent?: string } = {}) {
  return request<AgentTrendPoint[]>(
    withQuery("/api/v1/analytics/agents/trends", {
      days: params.days ?? 30,
      team_id: params.team_id,
      user_id: params.user_id,
      portfolio_id: params.portfolio_id,
      agent: params.agent
    })
  );
}

export function listBottleneckAnalytics(days = 30) {
  return request<AnalyticsBottleneckRow[]>(`/api/v1/analytics/bottlenecks?days=${days}`);
}

export function listUsers() {
  return request<UserRecord[]>("/api/v1/org/users");
}

export function listTeams() {
  return request<TeamRecord[]>("/api/v1/org/teams");
}

export function listPortfolios() {
  return request<PortfolioRecord[]>("/api/v1/org/portfolios");
}

export function listPortfolioSummaries() {
  return request<PortfolioSummary[]>("/api/v1/org/portfolio-summaries");
}

export function listDeliveryDora(portfolioId?: string) {
  return request<DeliveryDoraRow[]>(withQuery("/api/v1/analytics/delivery/dora", { portfolio_id: portfolioId }));
}

export function listDeliveryLifecycle(portfolioId?: string) {
  return request<DeliveryLifecycleRow[]>(withQuery("/api/v1/analytics/delivery/lifecycle", { portfolio_id: portfolioId }));
}

export function listDeliveryTrends(params: AnalyticsScopeParams = {}) {
  return request<DeliveryTrendPoint[]>(
    withQuery("/api/v1/analytics/delivery/trends", {
      days: params.days ?? 30,
      team_id: params.team_id,
      user_id: params.user_id,
      portfolio_id: params.portfolio_id
    })
  );
}

export function getDeliveryForecast(params: AnalyticsScopeParams & { history_days?: number; forecast_days?: number } = {}) {
  return request<DeliveryForecastSummary>(
    withQuery("/api/v1/analytics/delivery/forecast", {
      history_days: params.history_days ?? params.days ?? 30,
      forecast_days: params.forecast_days ?? 14,
      team_id: params.team_id,
      user_id: params.user_id,
      portfolio_id: params.portfolio_id
    })
  );
}

export function listDeliveryForecastPoints(params: AnalyticsScopeParams & { history_days?: number; forecast_days?: number } = {}) {
  return request<DeliveryForecastPoint[]>(
    withQuery("/api/v1/analytics/delivery/forecast/trends", {
      history_days: params.history_days ?? params.days ?? 30,
      forecast_days: params.forecast_days ?? 14,
      team_id: params.team_id,
      user_id: params.user_id,
      portfolio_id: params.portfolio_id
    })
  );
}

export function listDeliveryDoraScoped(params: Omit<AnalyticsScopeParams, "days"> = {}) {
  return request<DeliveryDoraRow[]>(
    withQuery("/api/v1/analytics/delivery/dora", {
      portfolio_id: params.portfolio_id,
      team_id: params.team_id,
      user_id: params.user_id
    })
  );
}

export function listDeliveryLifecycleScoped(params: Omit<AnalyticsScopeParams, "days"> = {}) {
  return request<DeliveryLifecycleRow[]>(
    withQuery("/api/v1/analytics/delivery/lifecycle", {
      portfolio_id: params.portfolio_id,
      team_id: params.team_id,
      user_id: params.user_id
    })
  );
}

export function listPerformanceRouteSummaries(params: { days?: number; page?: number; page_size?: number } = {}) {
  return request<PaginatedResponse<PerformanceRouteSummary>>(
    withQuery("/api/v1/analytics/performance/routes", {
      days: params.days ?? 30,
      page: params.page ?? 1,
      page_size: params.page_size ?? 25
    })
  );
}

export function listPerformanceSloSummaries(params: { days?: number; page?: number; page_size?: number } = {}) {
  return request<PaginatedResponse<PerformanceSloSummary>>(
    withQuery("/api/v1/analytics/performance/slo", {
      days: params.days ?? 30,
      page: params.page ?? 1,
      page_size: params.page_size ?? 25
    })
  );
}

export function listPerformanceTrends(params: { days?: number; route?: string; method?: string; page?: number; page_size?: number } = {}) {
  return request<PaginatedResponse<PerformanceTrendPoint>>(
    withQuery("/api/v1/analytics/performance/trends", {
      days: params.days ?? 30,
      route: params.route,
      method: params.method,
      page: params.page ?? 1,
      page_size: params.page_size ?? 100
    })
  );
}

export function listPerformanceMetrics(params: { days?: number; route?: string; method?: string; status_code?: number; page?: number; page_size?: number } = {}) {
  return request<PaginatedResponse<PerformanceMetricRecord>>(
    withQuery("/api/v1/analytics/performance/metrics", {
      days: params.days ?? 30,
      route: params.route,
      method: params.method,
      status_code: params.status_code,
      page: params.page ?? 1,
      page_size: params.page_size ?? 25
    })
  );
}

export function getPerformanceOperationsSummary() {
  return request<PerformanceOperationsSummary>("/api/v1/analytics/performance/operations");
}

export function listPerformanceOperationsTrends(params: { days?: number } = {}) {
  return request<PerformanceOperationsTrendPoint[]>(
    withQuery("/api/v1/analytics/performance/operations/trends", {
      days: params.days ?? 30
    })
  );
}

export function listAdminTemplates() {
  return request<TemplateRecord[]>("/api/v1/admin/templates");
}

export function createAdminTemplateVersion(payload: {
  template_id: string;
  version: string;
  source_version?: string;
  name?: string;
  description?: string;
}) {
  return requestWithOptions<TemplateRecord>("/api/v1/admin/templates/versions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminTemplateDefinition(
  templateId: string,
  version: string,
  payload: {
    name: string;
    description: string;
    schema: Record<string, unknown>;
  }
) {
  return requestWithOptions<TemplateRecord>(`/api/v1/admin/templates/${templateId}/versions/${version}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function validateAdminTemplateDefinition(templateId: string, version: string) {
  return requestWithOptions<TemplateValidationResult>(`/api/v1/admin/templates/${templateId}/versions/${version}/validate`, {
    method: "POST",
    body: JSON.stringify({})
  });
}

export function publishAdminTemplateVersion(templateId: string, version: string, payload: { note?: string } = {}) {
  return requestWithOptions<TemplateRecord>(`/api/v1/admin/templates/${templateId}/versions/${version}/publish`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function deprecateAdminTemplateVersion(templateId: string, version: string, payload: { note?: string } = {}) {
  return requestWithOptions<TemplateRecord>(`/api/v1/admin/templates/${templateId}/versions/${version}/deprecate`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function deleteAdminTemplateVersion(templateId: string, version: string) {
  return requestWithOptions<void>(`/api/v1/admin/templates/${templateId}/versions/${version}`, {
    method: "DELETE"
  });
}

export function listPolicies() {
  return request<PolicyRecord[]>("/api/v1/admin/policies");
}

export function updatePolicyRules(policyId: string, payload: { rules: string[] }) {
  return requestWithOptions<PolicyRecord>(`/api/v1/admin/policies/${policyId}/rules`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listIntegrations() {
  return request<IntegrationRecord[]>("/api/v1/admin/integrations");
}

export function createIntegration(payload: CreateIntegrationInput) {
  return requestWithOptions<IntegrationRecord>("/api/v1/admin/integrations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateIntegration(integrationId: string, payload: UpdateIntegrationInput) {
  return requestWithOptions<IntegrationRecord>(`/api/v1/admin/integrations/${integrationId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteIntegration(integrationId: string) {
  return requestWithOptions<void>(`/api/v1/admin/integrations/${integrationId}`, {
    method: "DELETE"
  });
}

export function listAdminUsers() {
  return request<UserRecord[]>("/api/v1/admin/org/users");
}

export function listAdminTenants() {
  return request<TenantRecord[]>("/api/v1/admin/org/tenants");
}

export function createAdminTenant(payload: CreateTenantInput) {
  return requestWithOptions<TenantRecord>("/api/v1/admin/org/tenants", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminTenant(tenantId: string, payload: UpdateTenantInput) {
  return requestWithOptions<TenantRecord>(`/api/v1/admin/org/tenants/${tenantId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listAdminOrganizations() {
  return request<OrganizationRecord[]>("/api/v1/admin/org/organizations");
}

export function createAdminOrganization(payload: CreateOrganizationInput) {
  return requestWithOptions<OrganizationRecord>("/api/v1/admin/org/organizations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminOrganization(organizationId: string, payload: UpdateOrganizationInput) {
  return requestWithOptions<OrganizationRecord>(`/api/v1/admin/org/organizations/${organizationId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function createAdminUser(payload: CreateUserInput) {
  return requestWithOptions<UserRecord>("/api/v1/admin/org/users", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminUser(userId: string, payload: UpdateUserInput) {
  return requestWithOptions<UserRecord>(`/api/v1/admin/org/users/${userId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function listAdminTeams() {
  return request<TeamRecord[]>("/api/v1/admin/org/teams");
}

export function createAdminTeam(payload: CreateTeamInput) {
  return requestWithOptions<TeamRecord>("/api/v1/admin/org/teams", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminTeam(teamId: string, payload: UpdateTeamInput) {
  return requestWithOptions<TeamRecord>(`/api/v1/admin/org/teams/${teamId}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function addAdminTeamMembership(payload: AddTeamMembershipInput) {
  return requestWithOptions<TeamRecord>("/api/v1/admin/org/team-memberships", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listAdminPortfolios() {
  return request<PortfolioRecord[]>("/api/v1/admin/org/portfolios");
}

export function createAdminPortfolio(payload: CreatePortfolioInput) {
  return requestWithOptions<PortfolioRecord>("/api/v1/admin/org/portfolios", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
