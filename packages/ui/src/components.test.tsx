import { render, screen } from "@testing-library/react";
import React from "react";
import {
  Badge,
  Button,
  ConversationDock,
  DataTable,
  EntityHeader,
  FilterPanel,
  KeyValueGrid,
  PageShell,
  PromotionGate,
  ReviewPanel,
  Tabs,
  TimeSeriesChart,
  Timeline
} from "./components";
import * as uiIndex from "./index";

describe("DataTable", () => {
  it("renders selection and column visibility controls", () => {
    render(
      <DataTable
        data={[
          { id: "req_001", title: "First request", owner: "team_alpha" },
          { id: "req_002", title: "Second request", owner: "team_beta" }
        ]}
        emptyMessage="Empty"
        selection={{
          rowKey: (row) => row.id,
          selectedKeys: ["req_001"],
          toggleHref: (key) => `/requests?selected=${key}`,
          clearHref: "/requests"
        }}
        columnVisibility={[
          { key: "title", label: "Title", visible: true, toggleHref: "/requests?cols=title" },
          { key: "owner", label: "Owner", visible: false, toggleHref: "/requests?cols=owner" }
        ]}
        columns={[
          { key: "title", header: "Title", render: (row) => row.title },
          { key: "owner", header: "Owner", render: (row) => row.owner }
        ]}
      />
    );

    expect(screen.getByText("1 selected")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Clear Selection" })).toHaveAttribute("href", "/requests");
    expect(screen.getByRole("link", { name: "Title" })).toHaveAttribute("href", "/requests?cols=title");
    expect(screen.getByRole("link", { name: "Owner" })).toHaveAttribute("href", "/requests?cols=owner");
    expect(screen.getByLabelText("Toggle selection for req_001")).toBeInTheDocument();
    expect(screen.queryByText("team_alpha")).not.toBeInTheDocument();
  });

  it("renders sortable headers and pagination controls", () => {
    render(
      <DataTable
        data={[{ id: "req_001", title: "First request" }]}
        emptyMessage="Empty"
        pagination={{
          page: 2,
          pageSize: 25,
          totalCount: 60,
          totalPages: 3,
          previousHref: "/requests?page=1",
          nextHref: "/requests?page=3"
        }}
        columns={[
          { key: "id", header: "ID", render: (row) => row.id },
          { key: "title", header: "Title", sortHref: "/requests?sort=title&order=asc", sortDirection: "asc", render: (row) => row.title }
        ]}
      />
    );

    expect(screen.getByRole("link", { name: /Title/ })).toHaveAttribute("href", "/requests?sort=title&order=asc");
    expect(screen.getByText("Page 2 of 3 · 60 total records")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Previous" })).toHaveAttribute("href", "/requests?page=1");
    expect(screen.getByRole("link", { name: "Next" })).toHaveAttribute("href", "/requests?page=3");
  });

  it("keeps columns visible when they are not explicitly managed by column visibility controls", () => {
    render(
      <DataTable
        data={[{ id: "req_001", title: "First request", owner: "team_alpha" }]}
        emptyMessage="Empty"
        columnVisibility={[
          { key: "owner", label: "Owner", visible: false, toggleHref: "/requests?cols=owner" }
        ]}
        columns={[
          { key: "id", header: "ID", render: (row) => row.id },
          { key: "title", header: "Title", render: (row) => row.title },
          { key: "owner", header: "Owner", render: (row) => row.owner }
        ]}
      />
    );

    expect(screen.getByText("req_001")).toBeInTheDocument();
    expect(screen.getByText("First request")).toBeInTheDocument();
    expect(screen.queryByText("team_alpha")).not.toBeInTheDocument();
  });

  it("renders time-series chart legends and empty-state labels", () => {
    render(
      <TimeSeriesChart
        title="Workflow Volume"
        subtitle="Daily volume and failures"
        series={[
          {
            key: "requests",
            label: "Requests",
            color: "#0f172a",
            points: [
              { label: "2026-03-29", value: 3 },
              { label: "2026-03-30", value: 5 }
            ]
          },
          {
            key: "failures",
            label: "Failures",
            color: "#dc2626",
            points: [
              { label: "2026-03-29", value: 1 },
              { label: "2026-03-30", value: 0 }
            ]
          }
        ]}
      />
    );

    expect(screen.getByText("Workflow Volume")).toBeInTheDocument();
    expect(screen.getByText("Requests")).toBeInTheDocument();
    expect(screen.getByText("Failures")).toBeInTheDocument();
    expect(screen.getByText("Latest: 5")).toBeInTheDocument();
  });

  it("renders loading, error, and empty states", () => {
    const { rerender } = render(
      <DataTable
        data={[]}
        emptyMessage="Empty state"
        loading
        columns={[{ key: "title", header: "Title", render: (row: { title: string }) => row.title }]}
      />
    );

    expect(screen.getByText("Loading table data…")).toBeInTheDocument();

    rerender(
      <DataTable
        data={[]}
        emptyMessage="Empty state"
        errorMessage="Broken table"
        columns={[{ key: "title", header: "Title", render: (row: { title: string }) => row.title }]}
      />
    );

    expect(screen.getByText("Broken table")).toBeInTheDocument();

    rerender(
      <DataTable
        data={[]}
        emptyMessage="Empty state"
        columns={[{ key: "title", header: "Title", render: (row: { title: string }) => row.title }]}
      />
    );

    expect(screen.getByText("Empty state")).toBeInTheDocument();
  });
});

describe("shared ui components", () => {
  it("renders page shell, entity header, filter panel, tabs, and key value content", () => {
    render(
      <PageShell
        title="Requests"
        subtitle="Track work."
        currentPath="/requests"
        navItems={[
          { label: "Requests", href: "/requests" },
          { label: "Runs", href: "/runs" }
        ]}
        headerActions={<Button label="Log Out" />}
        contextPanel={<div>Context Panel</div>}
      >
        <EntityHeader
          id="req_001"
          title="Assessment Refresh"
          status={<Badge tone="info">awaiting_review</Badge>}
          ownership="team_assessment_quality"
          blocking="Awaiting reviewer"
          primaryActions={<Button label="Resume" tone="primary" />}
        />
        <FilterPanel
          title="Queue Filters"
          items={[
            { label: "Status", value: "awaiting_review", active: true },
            { label: "Owner", value: "team_assessment_quality", href: "/requests?owner=team_assessment_quality" }
          ]}
        />
        <Tabs
          activeKey="overview"
          tabs={[
            { key: "overview", label: "Overview", href: "/requests/req_001" },
            { key: "history", label: "History" }
          ]}
        />
        <KeyValueGrid
          items={[
            { label: "Owner", value: "team_assessment_quality" },
            { label: "Request", value: <a href="/requests/req_001">req_001</a> }
          ]}
        />
      </PageShell>
    );

    expect(screen.getByRole("heading", { level: 1, name: "Requests" })).toBeInTheDocument();
    expect(screen.getByText("Track work.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Requests" })).toHaveClass("bg-slate-200");
    expect(screen.getByText("Context Panel")).toBeInTheDocument();
    expect(screen.getByText("Owner: team_assessment_quality")).toBeInTheDocument();
    expect(screen.getByText("Blocking: Awaiting reviewer")).toBeInTheDocument();
    expect(screen.getByText("Queue Filters")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Owner:/ })).toHaveAttribute("href", "/requests?owner=team_assessment_quality");
    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute("href", "/requests/req_001");
    expect(screen.getAllByText("team_assessment_quality").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "req_001" })).toHaveAttribute("href", "/requests/req_001");
  });

  it("renders timeline, review panel, promotion gate, and conversation dock states", () => {
    render(
      <>
        <Timeline
          currentStepId="step_002"
          steps={[
            { id: "step_001", name: "Draft", status: "completed", owner: "system" },
            { id: "step_002", name: "Review", status: "running", owner: "reviewer_nina" },
            { id: "step_003", name: "Publish", status: "blocked" }
          ]}
        />
        <ReviewPanel state="changes_requested" scopeLabel="Assessment Draft v1" />
        <PromotionGate
          target="production"
          readiness="Ready once approval completes."
          checks={[
            { name: "policy_pack", state: "passed", detail: "All checks passed" },
            { name: "security_scan", state: "pending", detail: "Awaiting execution" }
          ]}
          approvals={[
            { reviewer: "ops_isaac", state: "approved", scope: "ops" },
            { reviewer: "governance_lee", state: "pending", scope: "governance" }
          ]}
        />
        <ConversationDock
          title="Conversation Dock"
          messages={[
            { actor: "system", text: "Run entered review." },
            { actor: "operator", text: "Monitoring for escalation." }
          ]}
        />
      </>
    );

    expect(screen.getByText("Run Steps")).toBeInTheDocument();
    expect(screen.getByText("completed · system")).toBeInTheDocument();
    expect(screen.getByText("running · reviewer_nina")).toBeInTheDocument();
    expect(screen.getByText("Review Panel")).toBeInTheDocument();
    expect(screen.getByText("Scope: Assessment Draft v1")).toBeInTheDocument();
    expect(screen.getByText("changes_requested")).toBeInTheDocument();
    expect(screen.getByText("Promotion Gate")).toBeInTheDocument();
    expect(screen.getByText("Target: production")).toBeInTheDocument();
    expect(screen.getByText("Ready once approval completes.")).toBeInTheDocument();
    expect(screen.getByText("Conversation Dock")).toBeInTheDocument();
    expect(screen.getByText("Monitoring for escalation.")).toBeInTheDocument();
  });

  it("renders chart empty state, button states, badges, and index exports", () => {
    render(
      <>
        <TimeSeriesChart title="Empty Chart" series={[]} />
        <Button label="Disabled" disabled />
        <Badge tone="success">done</Badge>
        <Badge tone="danger">failed</Badge>
      </>
    );

    expect(screen.getByText("No time-series data available for the selected filters.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Disabled" })).toBeDisabled();
    expect(screen.getByText("done")).toBeInTheDocument();
    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(uiIndex.DataTable).toBe(DataTable);
    expect(uiIndex.PageShell).toBe(PageShell);
  });
});
