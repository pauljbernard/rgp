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
      searchParams: Promise.resolve({ blocking_only: "true" })
    });
    render(ui);

    expect(screen.getByRole("button", { name: "Apply Filters" })).toBeInTheDocument();
    expect(screen.getAllByText("Assigned Reviewer").length).toBeGreaterThan(0);
    expect(screen.getByDisplayValue("reviewer_nina")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reassign" })).toBeInTheDocument();
  });
});
