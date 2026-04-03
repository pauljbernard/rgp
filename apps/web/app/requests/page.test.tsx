import { render, screen } from "@testing-library/react";
import React from "react";
import RequestsPage from "./page";

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
        request_type: "custom",
        template_id: "tmpl_curriculum",
        template_version: "3.2.0",
        title: "Science Unit",
        summary: "Test request",
        status: "awaiting_review",
        priority: "high",
        sla_policy_id: null,
        submitter_id: "user_demo",
        owner_team_id: "team_curriculum_science",
        owner_user_id: null,
        workflow_binding_id: "wf_curriculum_science_v3",
        current_run_id: null,
        policy_context: {},
        input_payload: {},
        tags: [],
        created_at: "2026-03-31T22:00:00Z",
        created_by: "user_demo",
        updated_at: "2026-03-31T22:00:00Z",
        updated_by: "user_demo",
        version: 1,
        is_archived: false,
        sla_risk_level: "high",
        sla_risk_reason: "Review delay"
      }
    ],
    page: 1,
    page_size: 25,
    total_count: 1,
    total_pages: 1
  }))
}));

describe("RequestsPage", () => {
  it("renders interactive filter controls and policy-derived SLA risk", async () => {
    const ui = await RequestsPage({
      searchParams: Promise.resolve({ status: "awaiting_review" })
    });
    render(ui);

    expect(screen.getByRole("button", { name: "Apply Filters" })).toBeInTheDocument();
    expect(screen.getByText("Owner Team")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /team_curriculum_science/ })).toBeInTheDocument();
    expect(screen.getByText("high: Review delay")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create Request" })).toHaveAttribute("href", "/requests/new");
  });
});
