import { render, screen } from "@testing-library/react";

import QueuesPage from "./page";

vi.mock("@/lib/server-api", () => ({
  listAssignmentGroups: vi.fn(async () => [
    {
      id: "ag_001",
      tenant_id: "tenant_demo",
      name: "Assessment Reviewers",
      skill_tags: ["review", "policy"],
      max_capacity: 6,
      current_load: 2,
      status: "active",
      created_at: "2026-04-03T10:00:00Z",
    },
  ]),
  listSlaDefinitions: vi.fn(async () => [
    {
      id: "sla_001",
      tenant_id: "tenant_demo",
      name: "Assessment Review SLA",
      scope_type: "request_type",
      scope_id: "assessment",
      response_target_hours: 4,
      resolution_target_hours: 24,
      review_deadline_hours: 8,
      warning_threshold_pct: 70,
      status: "active",
      created_at: "2026-04-03T10:00:00Z",
    },
  ]),
  listEscalationRules: vi.fn(async () => [
    {
      id: "er_001",
      tenant_id: "tenant_demo",
      name: "Stale Review Escalation",
      condition: { field: "status", equals: "awaiting_review" },
      escalation_target: "queue_lead",
      escalation_type: "reassign",
      delay_minutes: 60,
      status: "active",
      created_at: "2026-04-03T10:00:00Z",
    },
  ]),
  listSlaBreaches: vi.fn(async () => [
    {
      id: "sb_001",
      tenant_id: "tenant_demo",
      sla_definition_id: "sla_001",
      request_id: "req_001",
      breach_type: "review",
      target_hours: 8,
      actual_hours: 11,
      severity: "high",
      remediation_action: null,
      breached_at: "2026-04-03T12:00:00Z",
    },
  ]),
  listNodes: vi.fn(async () => [
    {
      id: "node_001",
      readiness_state: "ready",
      employment_model: "employee",
      drain_state: "active",
      trust_tier: "trusted",
      current_load: 4,
    },
    {
      id: "node_002",
      readiness_state: "ready",
      employment_model: "contractor",
      drain_state: "active",
      trust_tier: "elevated",
      current_load: 1,
    },
    {
      id: "node_003",
      readiness_state: "attention_required",
      employment_model: "employee",
      drain_state: "active",
      trust_tier: "standard",
      current_load: 0,
    },
    {
      id: "node_004",
      readiness_state: "ready",
      employment_model: "employee",
      drain_state: "draining",
      trust_tier: "restricted",
      current_load: 2,
    },
  ]),
}));

describe("QueuesPage", () => {
  it("renders assignment groups, SLA definitions, escalation controls, and breach audit", async () => {
    render(await QueuesPage());

    expect(screen.getByRole("heading", { name: "Queues" })).toBeInTheDocument();
    expect(screen.getByText("Queue Summary")).toBeInTheDocument();
    expect(screen.getByText("Assessment Reviewers")).toBeInTheDocument();
    expect(screen.getByText("review, policy")).toBeInTheDocument();
    expect(screen.getByText("2/6")).toBeInTheDocument();
    expect(screen.getByText("Assessment Review SLA")).toBeInTheDocument();
    expect(screen.getByText("request_type: assessment")).toBeInTheDocument();
    expect(screen.getByText("Stale Review Escalation")).toBeInTheDocument();
    expect(screen.getByText("req_001")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Notify Queue Lead" }).length).toBeGreaterThan(0);
    expect(screen.getByText("Create Escalation Rule")).toBeInTheDocument();
    expect(screen.getByText("Create SLA Definition")).toBeInTheDocument();
    expect(screen.getByText("Create Assignment Group")).toBeInTheDocument();
    expect(screen.getByText("Attention Nodes")).toBeInTheDocument();
    expect(screen.getByText("Saturated Employee Nodes")).toBeInTheDocument();
    expect(screen.getByText("Trusted or Elevated Ready Nodes")).toBeInTheDocument();
    expect(screen.getByText("Contractor Fallback Nodes")).toBeInTheDocument();
  });

  it("renders empty-state guidance when queue governance data is absent", async () => {
    const serverApi = await import("@/lib/server-api");
    vi.mocked(serverApi.listAssignmentGroups).mockResolvedValueOnce([]);
    vi.mocked(serverApi.listSlaDefinitions).mockResolvedValueOnce([]);
    vi.mocked(serverApi.listEscalationRules).mockResolvedValueOnce([]);
    vi.mocked(serverApi.listSlaBreaches).mockResolvedValueOnce([]);
    vi.mocked(serverApi.listNodes).mockResolvedValueOnce([]);

    render(await QueuesPage());

    expect(screen.getByText("No assignment groups are configured.")).toBeInTheDocument();
    expect(screen.getByText("No SLA definitions are configured.")).toBeInTheDocument();
    expect(screen.getByText("No escalation rules are configured.")).toBeInTheDocument();
    expect(screen.getByText("No SLA breaches have been recorded.")).toBeInTheDocument();
    expect(screen.getAllByText("0").length).toBeGreaterThan(4);
  });
});
