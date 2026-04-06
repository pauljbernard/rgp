import { render, screen } from "@testing-library/react";
import React from "react";
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
    matched_skills: ["review"],
    route_basis: ["skill overlap: review", "capacity: 2/6"],
    current_load: 2,
    max_capacity: 6,
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
    expect(screen.getByText("SLA status: yellow")).toBeInTheDocument();
  });
});
