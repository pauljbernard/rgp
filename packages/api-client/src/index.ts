import type {
  AnalyticsAgentRow,
  AnalyticsBottleneckRow,
  AnalyticsWorkflowRow,
  ArtifactDetail,
  ArtifactRecord,
  AuditEntry,
  CapabilityDetail,
  CapabilityRecord,
  IntegrationRecord,
  PaginatedResponse,
  PolicyRecord,
  PromotionDetail,
  PromotionAction,
  RequestDetail,
  RequestPriority,
  RequestRecord,
  RequestStatus,
  ReviewDecision,
  ReviewQueueItem,
  RunDetail,
  RunRecord,
  TemplateRecord
} from "@rgp/domain";

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

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";
const apiToken = process.env.RGP_API_TOKEN ?? process.env.NEXT_PUBLIC_RGP_API_TOKEN;
const sessionCookieName = "rgp_access_token";

function authHeaders(): Record<string, string> {
  return apiToken ? { Authorization: `Bearer ${apiToken}` } : {};
}

async function cookieToken(): Promise<string | null> {
  if (typeof window !== "undefined") {
    return document.cookie
      .split("; ")
      .find((entry) => entry.startsWith(`${sessionCookieName}=`))
      ?.split("=")[1] ?? null;
  }
  return null;
}

async function request<T>(path: string): Promise<T> {
  return requestWithOptions<T>(path, {});
}

async function requestWithOptions<T>(path: string, init: RequestInit): Promise<T> {
  const bearerToken = apiToken ?? (await cookieToken());
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(bearerToken ? { Authorization: `Bearer ${bearerToken}` } : authHeaders()),
    ...((init.headers as Record<string, string> | undefined) ?? {})
  };
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers,
    ...init,
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

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

type AmendRequestInput = RequestMutationInput & {
  title?: string;
  summary?: string;
  priority?: RequestPriority;
  input_payload?: Record<string, unknown>;
};

type CloneRequestInput = RequestMutationInput & {
  title?: string;
  summary?: string;
};

type SupersedeRequestInput = RequestMutationInput & {
  replacement_request_id: string;
};

type TransitionRequestInput = RequestMutationInput & {
  target_status: RequestStatus;
};

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

export function getRequest(requestId: string) {
  return request<RequestDetail>(`/api/v1/requests/${requestId}`);
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

export function amendRequest(requestId: string, payload: AmendRequestInput) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/amend`, {
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

export function runRequestChecks(requestId: string, payload: { reason?: string; actor_id?: string } = {}) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/checks/run`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function cloneRequest(requestId: string, payload: CloneRequestInput = {}) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/clone`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function supersedeRequest(requestId: string, payload: SupersedeRequestInput) {
  return requestWithOptions<RequestRecord>(`/api/v1/requests/${requestId}/supersede`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listTemplates() {
  return request<TemplateRecord[]>("/api/v1/templates");
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

export function listWorkflowAnalytics(days = 30) {
  return request<AnalyticsWorkflowRow[]>(`/api/v1/analytics/workflows?days=${days}`);
}

export function listAgentAnalytics(days = 30) {
  return request<AnalyticsAgentRow[]>(`/api/v1/analytics/agents?days=${days}`);
}

export function listBottleneckAnalytics(days = 30) {
  return request<AnalyticsBottleneckRow[]>(`/api/v1/analytics/bottlenecks?days=${days}`);
}

export function listAdminTemplates() {
  return request<TemplateRecord[]>("/api/v1/admin/templates");
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

export function issueDevToken(payload: {
  user_id: string;
  tenant_id: string;
  roles: string[];
  expires_in_seconds?: number;
}) {
  return requestWithOptions<{ access_token: string; token_type: string }>("/api/v1/auth/dev-token", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listIntegrations() {
  return request<IntegrationRecord[]>("/api/v1/admin/integrations");
}
