import { render, screen } from "@testing-library/react";
import React from "react";

import PlanningConstructDetailPage from "./[constructId]/page";
import PlanningPage from "./page";

vi.mock("next/link", () => ({
  default: ({ href, children, prefetch: _prefetch, ...props }: { href: string; children: React.ReactNode; prefetch?: boolean }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@/lib/server-api", () => ({
  listPlanningConstructs: vi.fn(async () => [
    {
      id: "pc_001",
      tenant_id: "tenant_demo",
      type: "initiative",
      name: "Assessment Quality Initiative",
      description: "Cross-request planning container",
      owner_team_id: "team_assessment_quality",
      status: "active",
      priority: 5,
      target_date: "2026-06-30T00:00:00Z",
      capacity_budget: 40,
      created_at: "2026-04-01T00:00:00Z",
      updated_at: "2026-04-02T00:00:00Z",
    },
  ]),
  getPlanningRoadmap: vi.fn(async () => [
    {
      id: "pc_001",
      type: "initiative",
      name: "Assessment Quality Initiative",
      status: "active",
      priority: 5,
      target_date: "2026-06-30T00:00:00Z",
      capacity_budget: 40,
      member_count: 2,
      completion_pct: 50,
      completed_count: 1,
      in_progress_count: 1,
      blocked_count: 0,
      schedule_state: "on_track",
      owner_team_id: "team_assessment_quality",
    },
  ]),
  getPlanningConstruct: vi.fn(async () => ({
    construct: {
      id: "pc_001",
      tenant_id: "tenant_demo",
      type: "initiative",
      name: "Assessment Quality Initiative",
      description: "Cross-request planning container",
      owner_team_id: "team_assessment_quality",
      status: "active",
      priority: 5,
      target_date: "2026-06-30T00:00:00Z",
      capacity_budget: 40,
      created_at: "2026-04-01T00:00:00Z",
      updated_at: "2026-04-02T00:00:00Z",
    },
    memberships: [
      {
        id: "pm_001",
        planning_construct_id: "pc_001",
        request_id: "req_001",
        sequence: 1,
        priority: 5,
        added_at: "2026-04-02T00:00:00Z",
      },
    ],
    progress: {
      construct_id: "pc_001",
      total: 1,
      status_counts: { submitted: 0, in_progress: 1, blocked: 0, completed: 0, closed: 0, awaiting_review: 0 },
      completion_pct: 0,
    },
  })),
}));

describe("Planning pages", () => {
  it("renders roadmap health and progress signals on the planning list", async () => {
    render(await PlanningPage({ searchParams: Promise.resolve({}) }));

    expect(screen.getByRole("heading", { name: "Planning" })).toBeInTheDocument();
    expect(screen.getByText("Roadmap Health")).toBeInTheDocument();
    expect(screen.getByText("Due Soon")).toBeInTheDocument();
    expect(screen.getByText("Overdue")).toBeInTheDocument();
    expect(screen.getByText("50% complete")).toBeInTheDocument();
    expect(screen.getByText("1 done · 1 active · 0 blocked")).toBeInTheDocument();
  });

  it("renders planning detail sequencing controls and progress breakdown", async () => {
    render(await PlanningConstructDetailPage({ params: Promise.resolve({ constructId: "pc_001" }) }));

    expect(screen.getByRole("heading", { name: "Assessment Quality Initiative" })).toBeInTheDocument();
    expect(screen.getByText("Progress Breakdown")).toBeInTheDocument();
    expect(screen.getByText("Move Earlier")).toBeInTheDocument();
    expect(screen.getByText("Move Later")).toBeInTheDocument();
    expect(screen.getByText("Remove")).toBeInTheDocument();
  });
});
