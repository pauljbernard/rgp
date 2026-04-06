import { render, screen } from "@testing-library/react";
import React from "react";

import SlaRiskRequestsPage from "./page";

vi.mock("next/link", () => ({
  default: ({ href, children, prefetch: _prefetch, ...props }: { href: string; children: React.ReactNode; prefetch?: boolean }) => (
    <a href={href} {...props}>
      {children}
    </a>
  )
}));

vi.mock("@/lib/server-api", () => ({
  listRequests: vi.fn(async () => ({
    items: [
      {
        id: "req_001",
        tenant_id: "tenant_demo",
        request_type: "assessment",
        template_id: "tmpl_assessment",
        template_version: "1.0.0",
        title: "Assessment Refresh",
        summary: "Refresh benchmark assessment.",
        status: "awaiting_review",
        priority: "high",
        sla_policy_id: null,
        submitter_id: "user_demo",
        owner_team_id: "team_assessment_quality",
        owner_user_id: null,
        workflow_binding_id: "wf_assessment_revision_v1",
        current_run_id: null,
        policy_context: {},
        input_payload: {},
        tags: [],
        created_at: "2026-04-03T09:00:00Z",
        created_by: "user_demo",
        updated_at: "2026-04-03T11:00:00Z",
        updated_by: "user_demo",
        version: 1,
        is_archived: false,
        sla_risk_level: "critical",
        sla_risk_reason: "Review delay",
        federated_projection_count: 0,
        federated_conflict_count: 0,
      },
    ],
    page: 1,
    page_size: 100,
    total_count: 1,
    total_pages: 1,
  })),
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
  listRequestEscalations: vi.fn(async () => [
    {
      id: "er_001",
      tenant_id: "tenant_demo",
      name: "Stale Review Escalation",
      condition: { field: "status", equals: "awaiting_review" },
      escalation_target: "team_queue_lead",
      escalation_type: "reassign",
      delay_minutes: 60,
      status: "active",
      created_at: "2026-04-03T12:00:00Z",
    },
  ]),
}));

describe("SlaRiskRequestsPage", () => {
  it("renders recorded breach evidence and remediation state", async () => {
    render(await SlaRiskRequestsPage());

    expect(screen.getByRole("heading", { name: "SLA Risk" })).toBeInTheDocument();
    expect(screen.getByText("Recorded Breaches")).toBeInTheDocument();
    expect(screen.getByText("Assessment Refresh")).toBeInTheDocument();
    expect(screen.getByText("review • 11h / 8h")).toBeInTheDocument();
    expect(screen.getByText("Stale Review Escalation")).toBeInTheDocument();
    expect(screen.getByText("Pending operator action")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Notify Queue Lead" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Execute Escalation" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Queue Controls" })).toHaveAttribute("href", "/queues");
  });
});
