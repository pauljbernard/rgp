import { render, screen } from "@testing-library/react";
import React from "react";
import AnalyticsPage from "./analytics/page";
import AgentAnalyticsPage from "./analytics/agents/page";
import BottleneckAnalyticsPage from "./analytics/bottlenecks/page";
import AnalyticsCostPage from "./analytics/cost/page";
import DeliveryAnalyticsPage from "./analytics/delivery/page";
import PerformanceAnalyticsPage from "./analytics/performance/page";
import WorkflowAnalyticsPage from "./analytics/workflows/page";
import AdminIntegrationsPage from "./admin/integrations/page";
import AdminIntegrationDetailPage from "./admin/integrations/[integrationId]/page";
import AdminOrgPage from "./admin/org/page";
import AdminTeamDetailPage from "./admin/org/teams/[teamId]/page";
import AdminUserDetailPage from "./admin/org/users/[userId]/page";
import AdminPoliciesPage from "./admin/policies/page";
import ArtifactsPage from "./artifacts/page";
import ArtifactDetailPage from "./artifacts/[artifactId]/page";
import CapabilitiesPage from "./capabilities/page";
import CapabilityDetailPage from "./capabilities/[capabilityId]/page";
import HelpAnalyticsPage from "./help/analytics/page";
import HelpAdminPage from "./help/admin/page";
import HelpJourneysPage from "./help/journeys/page";
import HelpOperationsPage from "./help/operations/page";
import HelpOverviewPage from "./help/page";
import HelpRequestsPage from "./help/requests/page";
import PromotionPage from "./promotions/[promotionId]/page";
import PromotionPendingPage from "./promotions/pending/page";
import RequestAgentsPage from "./requests/[requestId]/agents/page";
import RequestHistoryPage from "./requests/[requestId]/history/page";
import RequestDetailPage from "./requests/[requestId]/page";
import RequestAgentSessionPage from "./requests/[requestId]/agents/[sessionId]/page";
import RunsPage from "./runs/page";
import FailedRunsPage from "./runs/failed/page";
import RunDetailPage from "./runs/[runId]/page";

vi.mock("@/lib/server-api", () => {
  const requestRecord = {
    id: "req_001",
    tenant_id: "tenant_demo",
    request_type: "assessment",
    template_id: "tmpl_assessment",
    template_version: "1.4.0",
    title: "Assessment Refresh",
    summary: "Refresh benchmark assessment.",
    status: "awaiting_review",
    priority: "high",
    sla_policy_id: null,
    submitter_id: "user_demo",
    owner_team_id: "team_assessment_quality",
    owner_user_id: "user_demo",
    workflow_binding_id: "wf_assessment_revision_v1",
    current_run_id: "run_001",
    policy_context: {},
    input_payload: { assessment_id: "asm_001" },
    tags: [],
    created_at: "2026-04-02T10:00:00Z",
    created_by: "user_demo",
    updated_at: "2026-04-02T10:30:00Z",
    updated_by: "user_demo",
    version: 1,
    is_archived: false,
    sla_risk_level: "high",
    sla_risk_reason: "Review delay"
  };

  const requestDetail = {
    request: requestRecord,
    next_required_action: "Review required",
    active_blockers: ["Awaiting reviewer decision"],
    latest_run_id: "run_001",
    latest_artifact_ids: ["art_001"],
    predecessors: [],
    successors: [],
    check_results: [
      { id: "chk_001", name: "Policy Pack", state: "passed", detail: "All checks passed", evidence: "evidence", severity: "low", evaluated_by: "system" }
    ],
    check_runs: [
      { id: "cr_001", scope: "request", status: "completed", trigger_reason: "submit", enqueued_by: "system", queued_at: "2026-04-02T10:00:00Z" }
    ],
    agent_sessions: [
      { id: "ags_001", agent_label: "Codex", status: "waiting_on_human", summary: "Ready for review", integration_name: "OpenAI Codex", message_count: 2, awaiting_human: true }
    ]
  };

  const agentSession = {
    id: "ags_001",
    request_id: "req_001",
    integration_id: "int_agent_codex",
    integration_name: "OpenAI Codex",
    provider: "openai",
    agent_label: "Codex",
    status: "waiting_on_human",
    summary: "Proposed an updated assessment outline.",
    awaiting_human: true,
    assigned_by: "user_demo",
    assigned_at: "2026-04-02T10:00:00Z",
    external_session_ref: "sess_123",
    message_count: 2,
    latest_message: { id: "msg_002", sender_type: "agent", sender_id: "codex", body: "Updated outline with three recommendations.", created_at: "2026-04-02T10:05:00Z" },
    messages: [
      { id: "msg_001", sender_type: "human", sender_id: "user_demo", body: "Please improve the assessment.", created_at: "2026-04-02T10:00:00Z" },
      { id: "msg_002", sender_type: "agent", sender_id: "codex", body: "Updated outline with three recommendations.", created_at: "2026-04-02T10:05:00Z" }
    ]
  };

  const runRecord = {
    id: "run_001",
    request_id: "req_001",
    workflow: "wf_assessment_revision_v1",
    workflow_identity: "tmpl_assessment",
    status: "awaiting_review",
    current_step: "review",
    elapsed_time: "12m",
    waiting_reason: "Awaiting review",
    owner: "team_assessment_quality",
    updated_at: "2026-04-02T10:30:00Z"
  };

  const runDetail = {
    ...runRecord,
    owner_team: "team_assessment_quality",
    progress_percent: 65,
    current_step_input_summary: "Assessment payload loaded.",
    current_step_output_summary: "Review package assembled.",
    command_surface: ["Resume", "Cancel Run"],
    run_context: [["Owner Team", "team_assessment_quality"], ["Template", "tmpl_assessment@1.4.0"]],
    runtime_dispatches: [{ dispatched_at: "2026-04-02T10:01:00Z", dispatch_type: "worker", status: "completed", integration_id: "int_agent_codex", external_reference: "ext_001", detail: "queued" }],
    runtime_signals: [{ received_at: "2026-04-02T10:02:00Z", event_id: "sig_001", source: "worker", status: "completed", current_step: "review", detail: "signal received" }],
    started_at: "2026-04-02T10:00:00Z",
    completed_at: null,
    steps: [
      { id: "step_001", name: "Draft", status: "completed", actor: "system", started_at: "2026-04-02T10:00:00Z", completed_at: "2026-04-02T10:05:00Z", detail: "Drafted." },
      { id: "step_002", name: "Review", status: "running", actor: "reviewer_nina", started_at: "2026-04-02T10:06:00Z", completed_at: null, detail: "In review." }
    ],
    commands: [
      { name: "rerun", label: "Rerun", command: "rerun" }
    ],
    artifacts: [{ id: "art_001", name: "Assessment Draft" }],
    history: [{ timestamp: "2026-04-02T10:06:00Z", actor: "system", action: "entered review" }]
  };

  const team = {
    id: "team_assessment_quality",
    name: "Assessment Quality",
    kind: "delivery",
    status: "active",
    member_count: 2,
    members: [
      { user_id: "user_demo", display_name: "Demo User", email: "demo@example.com", role: "lead" },
      { user_id: "reviewer_nina", display_name: "Reviewer Nina", email: "nina@example.com", role: "reviewer" }
    ]
  };

  const user = { id: "user_demo", display_name: "Demo User", email: "demo@example.com", status: "active", roles: ["admin"], role_summary: ["admin"], team_ids: ["team_assessment_quality"] };
  const portfolio = { id: "port_assessment", name: "Assessment Portfolio", owner_team_id: "team_assessment_quality", scope_keys: ["team_assessment_quality"], status: "active" };
  const integration = {
    id: "int_agent_codex",
    name: "OpenAI Codex",
    type: "agent",
    status: "active",
    endpoint: "https://api.openai.com/v1",
    resolved_endpoint: "https://api.openai.com/v1/responses",
    supports_direct_assignment: true,
    supports_interactive_sessions: true,
    has_api_key: true,
    has_access_token: true,
    settings: { provider: "openai", base_url: "https://api.openai.com/v1", model: "gpt-5.4", workspace_id: "default" }
  };

  return {
    listRequests: vi.fn(async () => ({ items: [requestRecord], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    listRuns: vi.fn(async () => ({ items: [runRecord], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    getRun: vi.fn(async () => runDetail),
    listArtifacts: vi.fn(async () => ({
      items: [
        {
          id: "art_001",
          type: "document",
          name: "Assessment Draft",
          current_version: "v1",
          status: "approved",
          request_id: "req_001",
          updated_at: "2026-04-02T10:10:00Z",
          owner: "team_assessment_quality"
        }
      ]
    })),
    getArtifact: vi.fn(async () => ({
      artifact: {
        id: "art_001",
        name: "Assessment Draft",
        status: "approved",
        owner: "team_assessment_quality"
      },
      selected_version_id: "artv_001",
      versions: [
        {
          id: "artv_001",
          label: "v1",
          summary: "Initial approved artifact",
          status: "approved",
          content: "artifact body"
        }
      ],
      review_state: "approved",
      stale_review: false,
      lineage: [
        {
          from_version_id: null,
          to_version_id: "artv_001",
          relation: "created_from_request",
          created_at: "2026-04-02T10:00:00Z"
        }
      ],
      history: [
        {
          timestamp: "2026-04-02T10:10:00Z",
          actor: "reviewer_nina",
          action: "approved",
          detail: "Artifact approved"
        }
      ]
    })),
    listCapabilities: vi.fn(async () => ({
      items: [
        {
          id: "cap_001",
          name: "Assessment Review",
          type: "workflow",
          version: "1.0.0",
          status: "active",
          owner: "team_assessment_quality",
          updated_at: "2026-04-02T10:00:00Z",
          usage_count: 12
        }
      ]
    })),
    getCapability: vi.fn(async () => ({
      capability: {
        id: "cap_001",
        name: "Assessment Review",
        status: "active",
        owner: "team_assessment_quality"
      },
      usage: [
        ["Requests", "12"],
        ["Integrations", "1"]
      ],
      definition: "Reviews and refines governed assessment requests.",
      lineage: ["cap_000 -> cap_001"],
      history: [
        {
          timestamp: "2026-04-02T10:00:00Z",
          actor: "user_demo",
          action: "registered"
        }
      ]
    })),
    getRequest: vi.fn(async () => requestDetail),
    listRequestAgentIntegrations: vi.fn(async () => [integration]),
    getAgentSession: vi.fn(async () => agentSession),
    getRequestHistory: vi.fn(async () => [{ timestamp: "2026-04-02T10:00:00Z", actor: "user_demo", action: "submitted", object_type: "request", object_id: "req_001", reason_or_evidence: "Initial submission" }]),
    listWorkflowAnalytics: vi.fn(async () => [{ workflow: "tmpl_assessment", avg_cycle_time: "2.4h", p95_duration: "3.2h", failure_rate: "3%", review_delay: "1.1h", cost_per_execution: "$4.20", trend: "up" }]),
    listWorkflowTrends: vi.fn(async () => [{ period_start: "2026-04-01", request_count: 4, failed_count: 1, avg_cycle_time_hours: 2.4, review_stale_count: 1, cost_per_execution: 4.2 }]),
    listAgentAnalytics: vi.fn(async () => [{ agent: "OpenAI Codex", invocations: 8, success_rate: "95%", retry_rate: "5%", avg_duration: "3.2m", cost_per_invocation: "$1.50", quality_score: "4.7/5" }]),
    listAgentTrends: vi.fn(async () => [{ period_start: "2026-04-01", invocation_count: 8, retry_rate: 5, success_rate: 95, quality_score: 4.7, avg_duration_minutes: 3.2 }]),
    listDeliveryDoraScoped: vi.fn(async () => [{ scope_type: "team", scope_key: "team_assessment_quality", deployment_frequency: "daily", lead_time_hours: 4.2, change_failure_rate: "3%", mean_time_to_restore_hours: 1.2 }]),
    listDeliveryLifecycleScoped: vi.fn(async () => [{ scope_type: "team", scope_key: "team_assessment_quality", throughput_30d: 14, cycle_time_hours: 4.4, review_time_hours: 1.2, promotion_time_hours: 0.8 }]),
    listDeliveryTrends: vi.fn(async () => [{ period_start: "2026-04-01", throughput_count: 4, completed_count: 3, deployment_count: 2, lead_time_hours: 4.2, failed_count: 1 }]),
    getDeliveryForecast: vi.fn(async () => ({ forecast_days: 14, avg_daily_throughput: 2.1, avg_daily_deployments: 1.2, projected_total_throughput: 29.4, projected_total_deployments: 16.8, projected_lead_time_hours: 4.0 })),
    listDeliveryForecastPoints: vi.fn(async () => [{ period_start: "2026-04-03", projected_throughput_count: 2.1, projected_deployment_count: 1.2, projected_lead_time_hours: 4.0 }]),
    listPerformanceRouteSummaries: vi.fn(async () => ({ items: [{ route: "/api/v1/requests", method: "GET", request_count: 120, avg_duration_ms: 45, p95_duration_ms: 90, error_rate: "1%", apdex: "0.98" }], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    listPerformanceSloSummaries: vi.fn(async () => ({ items: [{ route: "/api/v1/requests", method: "GET", availability_actual: "99.9%", latency_slo_ms: 150, error_budget_remaining: "99%", status: "healthy" }], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    listPerformanceTrends: vi.fn(async () => ({ items: [{ period_start: "2026-04-01", avg_duration_ms: 45, p95_duration_ms: 90, request_count: 120, error_rate: "1%" }], page: 1, page_size: 100, total_count: 1, total_pages: 1 })),
    listPerformanceMetrics: vi.fn(async () => ({ items: [{ route: "/api/v1/requests", method: "GET", correlation_id: "corr_001", trace_id: "trace_001", span_id: "span_001", duration_ms: 45, created_at: "2026-04-02T10:00:00Z" }], page: 1, page_size: 25, total_count: 1, total_pages: 1 })),
    getPerformanceOperationsSummary: vi.fn(async () => ({ queued_checks: 1, running_checks: 1, waiting_runs: 2, failed_runs: 1, stale_reviews: 1, pending_promotions: 1, avg_check_queue_minutes: 2.5, avg_runtime_queue_minutes: 3.1 })),
    listPerformanceOperationsTrends: vi.fn(async () => [{ period_start: "2026-04-01", queued_checks: 1, running_checks: 1, waiting_runs: 2, failed_runs: 1, stale_reviews: 1, pending_promotions: 1 }]),
    listPortfolios: vi.fn(async () => [portfolio]),
    listTeams: vi.fn(async () => [team]),
    listUsers: vi.fn(async () => [user]),
    listPortfolioSummaries: vi.fn(async () => [{ portfolio_id: "port_assessment", portfolio_name: "Assessment Portfolio", request_count: 12, active_request_count: 3, completed_request_count: 9, deployment_count: 4 }]),
    listBottleneckAnalytics: vi.fn(async () => [{ bottleneck: "review", count: 3, average_delay: "1.2h", severity: "high" }]),
    listAdminUsers: vi.fn(async () => [user]),
    listAdminTeams: vi.fn(async () => [team]),
    listAdminPortfolios: vi.fn(async () => [portfolio]),
    listPolicies: vi.fn(async () => [{
      id: "pol_001",
      name: "Default Policy",
      status: "active",
      scope: "global",
      owner_team_id: "team_assessment_quality",
      rule_count: 3,
      updated_at: "2026-04-02T10:00:00Z",
      transition_gates: [{ transition_target: "submitted", required_check_name: "Intake Completeness" }],
      rules: ["submitted -> Intake Completeness"],
      review_rules: [{ rule: "required-review" }],
      sla_rules: [{ severity: "high" }]
    }]),
    listIntegrations: vi.fn(async () => [integration]),
    getPromotion: vi.fn(async () => ({
      id: "pro_001",
      target: "production",
      execution_readiness: "Ready",
      required_checks: [{ name: "policy_pack", state: "passed", severity: "low", detail: "ok", evidence: "evidence", evaluated_by: "system", id: "pchk_001" }],
      required_approvals: [{ reviewer: "ops_isaac", state: "pending", scope: "ops" }],
      check_results: [{ id: "pchk_001", name: "policy_pack", state: "passed", severity: "low", detail: "ok", evidence: "evidence", evaluated_by: "system" }],
      check_runs: [{ id: "pcr_001", scope: "promotion", status: "completed", trigger_reason: "authorize", enqueued_by: "system", queued_at: "2026-04-02T10:00:00Z" }],
      overrides: [{ check_result_id: "pchk_001", state: "approved", reason: "manual override", requested_by: "ops_isaac", decided_by: "ops_isaac", created_at: "2026-04-02T10:05:00Z" }],
      deployment_executions: [{ executed_at: "2026-04-02T10:10:00Z", target: "production", integration_id: "int_ms_foundry", status: "completed", external_reference: "dep_001", detail: "ok" }],
      promotion_history: [{ timestamp: "2026-04-02T10:10:00Z", actor: "ops_isaac", action: "executed" }]
    }))
  };
});

vi.mock("./requests/[requestId]/agents/[sessionId]/live-session", () => ({
  AgentSessionLiveView: ({ initialSession }: { initialSession: { summary: string } }) => <div>Live Session: {initialSession.summary}</div>
}));

describe("coverage smoke pages", () => {
  it("renders analytics pages", async () => {
    render(await AnalyticsPage());
    expect(screen.getByText("Analytics Overview")).toBeInTheDocument();
    expect(screen.getByText("Delivery and Workflow Volume")).toBeInTheDocument();

    render(await WorkflowAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Workflow Analytics")).toBeInTheDocument();
    expect(screen.getByText("Workflow Volume")).toBeInTheDocument();

    render(await AgentAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Agent Analytics")).toBeInTheDocument();
    expect(screen.getByText("Agent Invocation Trend")).toBeInTheDocument();

    render(await DeliveryAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Delivery Analytics")).toBeInTheDocument();
    expect(screen.getByText("Forecast Throughput and Deployments")).toBeInTheDocument();

    render(await PerformanceAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Performance Analytics")).toBeInTheDocument();
    expect(screen.getByText("Queue Pressure")).toBeInTheDocument();

    render(await AnalyticsCostPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Cost Analytics")).toBeInTheDocument();
    expect(screen.getByText("Estimated Spend Over Time")).toBeInTheDocument();

    render(await BottleneckAnalyticsPage({ searchParams: Promise.resolve({ days: "30" }) }));
    expect(screen.getByText("Bottleneck Analytics")).toBeInTheDocument();
  });

  it("renders help pages", async () => {
    render(await HelpOverviewPage());
    expect(screen.getByText("Help and User Guide")).toBeInTheDocument();
    expect(screen.getByText("Guide Map")).toBeInTheDocument();

    render(await HelpRequestsPage());
    expect(screen.getByText("Help: Requests")).toBeInTheDocument();
    expect(screen.getByText("Create Request Form")).toBeInTheDocument();

    render(await HelpOperationsPage());
    expect(screen.getByText("Help: Operations")).toBeInTheDocument();
    expect(screen.getByText("Operational Areas")).toBeInTheDocument();

    render(await HelpAdminPage());
    expect(screen.getByText("Help: Admin")).toBeInTheDocument();
    expect(screen.getByText("Admin Areas")).toBeInTheDocument();

    render(await HelpAnalyticsPage());
    expect(screen.getByText("Help: Analytics")).toBeInTheDocument();
    expect(screen.getByText("Analytics Pages")).toBeInTheDocument();

    render(await HelpJourneysPage());
    expect(screen.getByText("Help: User Journeys")).toBeInTheDocument();
    expect(screen.getByText("Supported User Journeys")).toBeInTheDocument();
  });

  it("renders request pages", async () => {
    render(await RequestDetailPage({ params: Promise.resolve({ requestId: "req_001" }), searchParams: Promise.resolve({}) }));
    expect(screen.getByText("Request Detail")).toBeInTheDocument();
    expect(screen.getByText("Assign to Agent")).toBeInTheDocument();

    render(await RequestAgentsPage({ params: Promise.resolve({ requestId: "req_001" }), searchParams: Promise.resolve({}) }));
    expect(screen.getAllByText("Agent Sessions").length).toBeGreaterThan(0);

    render(await RequestHistoryPage({ params: Promise.resolve({ requestId: "req_001" }) }));
    expect(screen.getByText("Audit History")).toBeInTheDocument();

    render(await RequestAgentSessionPage({ params: Promise.resolve({ requestId: "req_001", sessionId: "ags_001" }) }));
    expect(screen.getByText("Agent Session: Codex")).toBeInTheDocument();
    expect(screen.getByText("Live Session: Proposed an updated assessment outline.")).toBeInTheDocument();
  });

  it("renders admin pages", async () => {
    render(await AdminOrgPage());
    expect(screen.getByText("Admin Organization")).toBeInTheDocument();
    expect(screen.getByText("Teams and Members")).toBeInTheDocument();

    render(await AdminTeamDetailPage({ params: Promise.resolve({ teamId: "team_assessment_quality" }) }));
    expect(screen.getByText("Team Settings")).toBeInTheDocument();
    expect(screen.getByText("Create User In Team")).toBeInTheDocument();

    render(await AdminUserDetailPage({ params: Promise.resolve({ userId: "user_demo" }) }));
    expect(screen.getByText("User Settings")).toBeInTheDocument();

    render(await AdminIntegrationsPage());
    expect(screen.getByText("Admin Integrations")).toBeInTheDocument();

    render(await AdminIntegrationDetailPage({ params: Promise.resolve({ integrationId: "int_agent_codex" }) }));
    expect(screen.getByText("Integration Settings")).toBeInTheDocument();
    expect(screen.getByText("Provider Settings")).toBeInTheDocument();
    expect(screen.getByText("Clear stored API key")).toBeInTheDocument();
    expect(screen.queryByDisplayValue("sk-test")).not.toBeInTheDocument();

    render(await AdminPoliciesPage());
    expect(screen.getByText("Admin Policies")).toBeInTheDocument();
  });

  it("renders execution and governance pages", async () => {
    render(await RunsPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Runs" })).toBeInTheDocument();
    expect(screen.getByText("All Runs")).toBeInTheDocument();

    render(await FailedRunsPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Failed Runs" })).toBeInTheDocument();

    render(await RunDetailPage({ params: Promise.resolve({ runId: "run_001" }) }));
    expect(screen.getByText("Run Detail")).toBeInTheDocument();

    render(await PromotionPendingPage({ searchParams: Promise.resolve({}) }));
    expect(screen.getByRole("heading", { name: "Promotion Pending" })).toBeInTheDocument();

    render(await PromotionPage({ params: Promise.resolve({ promotionId: "pro_001" }) }));
    expect(screen.getByRole("heading", { level: 1, name: "Promotion Gate" })).toBeInTheDocument();
    expect(screen.queryByText("No promotion history.")).not.toBeInTheDocument();

    render(await ArtifactsPage());
    expect(screen.getByRole("heading", { name: "Artifacts" })).toBeInTheDocument();

    render(await ArtifactDetailPage({ params: Promise.resolve({ artifactId: "art_001" }) }));
    expect(screen.getByText("Artifact Detail")).toBeInTheDocument();

    render(await CapabilitiesPage());
    expect(screen.getByRole("heading", { name: "Capability Registry" })).toBeInTheDocument();

    render(await CapabilityDetailPage({ params: Promise.resolve({ capabilityId: "cap_001" }) }));
    expect(screen.getByText("Capability Detail")).toBeInTheDocument();
  });
});
