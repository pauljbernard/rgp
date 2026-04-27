import { render, screen } from "@testing-library/react";
import React from "react";
import * as serverApi from "@/lib/server-api";
import ReviewQueuePage from "./page";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    prefetch: _prefetch,
    ...props
  }: {
    href: string;
    children: React.ReactNode;
    prefetch?: boolean;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  )
}));

vi.mock("@/lib/server-api", () => ({
  getRequestKnowledgeContext: vi.fn(async () => [
    {
      id: "ka_001",
      tenant_id: "tenant_demo",
      name: "Assessment Review Playbook",
      description: "Reusable review guidance.",
      content: "Use governed review criteria.",
      content_type: "markdown",
      version: 2,
      status: "published",
      policy_scope: null,
      provenance: [],
      tags: ["policy", "review"],
      created_by: "user_demo",
      created_at: "2026-04-02T10:00:00Z",
      updated_at: "2026-04-02T10:10:00Z"
    }
  ]),
  getRoutingRecommendation: vi.fn(async () => ({
    request_id: "req_001",
    recommended_group_id: "ag_001",
    recommended_group_name: "Assessment Reviewers",
    recommended_node_id: "node_001",
    recommended_node_name: "Trusted Employee Node",
    recommended_node_employment_model: "employee",
    recommended_node_trust_tier: "trusted",
    recommended_node_billing_profile: "organization_funded",
    recommended_node_readiness_state: "ready",
    recommended_node_drain_state: "active",
    matched_skills: ["review"],
    route_basis: ["skill overlap: review", "capacity: 2/6"],
    current_load: 2,
    max_capacity: 6,
    fleet_basis: ["node skill overlap: review", "preferred ready employee-capable node pool", "trust tier: trusted", "billing posture: organization_funded"],
    sla_status: "yellow",
    escalation_targets: []
  })),
  listReviewQueue: vi.fn(async () => ({
    items: [
      {
        id: "revq_001",
        request_id: "req_001",
        review_scope: "artifact_version",
        artifact_or_changeset: "Science Unit v2",
        type: "content_review",
        priority: "high",
        sla: "Due in 2h",
        blocking_status: "Blocking request progress",
        assigned_reviewer: "reviewer_nina",
        stale: false
      }
    ],
    page: 1,
    page_size: 25,
    total_count: 1,
    total_pages: 1
  }))
}));

describe("ReviewQueuePage", () => {
  it("renders interactive review filter controls and reassignment action", async () => {
    const ui = await ReviewQueuePage({
      searchParams: Promise.resolve({ blocking_only: "true", request_id: "req_001" })
    });
    render(ui);

    expect(screen.getByRole("button", { name: "Apply Filters" })).toBeInTheDocument();
    expect(screen.getAllByText("Assigned Reviewer").length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue("reviewer_nina")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reassign" })).toBeInTheDocument();
    expect(screen.getByText("Routing Recommendation for req_001")).toBeInTheDocument();
    expect(screen.getByText("Assessment Reviewers")).toBeInTheDocument();
    expect(screen.getByText("Recommended node: Trusted Employee Node")).toBeInTheDocument();
    expect(screen.getByText("Node posture: employee / trusted / organization_funded")).toBeInTheDocument();
    expect(screen.getByText("Node readiness: ready / active")).toBeInTheDocument();
    expect(screen.getByText("SLA status: yellow")).toBeInTheDocument();
  });

  it("shows governed empty states when a request has no knowledge suggestions or routing basis", async () => {
    vi.mocked(serverApi.getRequestKnowledgeContext).mockResolvedValueOnce([]);
    vi.mocked(serverApi.getRoutingRecommendation).mockResolvedValueOnce({
      request_id: "req_404",
      recommended_group_id: null,
      recommended_group_name: null,
      recommended_node_id: null,
      recommended_node_name: null,
      recommended_node_employment_model: null,
      recommended_node_trust_tier: null,
      recommended_node_billing_profile: null,
      recommended_node_readiness_state: null,
      recommended_node_drain_state: null,
      matched_skills: [],
      route_basis: [],
      current_load: 0,
      max_capacity: 0,
      fleet_basis: [],
      sla_status: "unknown",
      escalation_targets: []
    });

    const ui = await ReviewQueuePage({
      searchParams: Promise.resolve({ request_id: "req_404" })
    });
    render(ui);

    expect(screen.getByText("Routing Recommendation for req_404")).toBeInTheDocument();
    expect(screen.getByText("No assignment group recommendation")).toBeInTheDocument();
    expect(screen.getByText("Recommended node: No fleet node recommendation")).toBeInTheDocument();
    expect(screen.getByText("Queue basis: no basis recorded")).toBeInTheDocument();
    expect(screen.getByText("Fleet basis: no fleet basis recorded")).toBeInTheDocument();
    expect(screen.getByText("No governed knowledge suggestions were retrieved for this request.")).toBeInTheDocument();
  });
});
