import { listRequests } from "@/lib/server-api";
import Link from "next/link";
import React from "react";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, QueueTabs, SectionHeading, appShellProps, statusTone, formatDate } from "../../components/ui-helpers";

const requestQueueTabs = [
  { key: "all", label: "All Requests", href: "/requests" },
  { key: "blocked", label: "Blocked Requests", href: "/requests/blocked" },
  { key: "federated-conflicts", label: "Federated Conflicts", href: "/requests/federated-conflicts" },
  { key: "promotion", label: "Promotion Pending", href: "/promotions/pending" },
  { key: "sla-risk", label: "SLA Risk", href: "/requests/sla-risk" }
];

export default async function RequestsPage({
  searchParams
}: {
  searchParams: Promise<{ status?: string; owner_team_id?: string; workflow?: string; request_id?: string; federation?: string; page?: string; sort?: string; order?: string; selected?: string; cols?: string }>;
}) {
  const filters = await searchParams;
  const page = Number(filters.page ?? "1") || 1;
  const data = await listRequests({ ...filters, page });
  const sort = filters.sort ?? "updated_at";
  const order = filters.order === "asc" ? "asc" : "desc";
  const selectedKeys = (filters.selected ?? "").split(",").filter(Boolean);
  const defaultColumns = ["id", "type", "title", "status", "owner", "priority", "workflow", "federation", "phase", "blocking", "sla", "updated"];
  const visibleColumnKeys = new Set((filters.cols ?? defaultColumns.join(",")).split(",").filter(Boolean));
  const sortedItems = [...data.items].sort((left, right) => {
    const direction = order === "asc" ? 1 : -1;
    switch (sort) {
      case "title":
        return direction * left.title.localeCompare(right.title);
      case "status":
        return direction * left.status.localeCompare(right.status);
      case "priority":
        return direction * left.priority.localeCompare(right.priority);
      case "owner_team_id":
        return direction * (left.owner_team_id ?? "").localeCompare(right.owner_team_id ?? "");
      default:
        return direction * (new Date(left.updated_at).getTime() - new Date(right.updated_at).getTime());
    }
  });
  const active = data.items.filter((item) => ["submitted", "in_execution", "awaiting_review", "under_review"].includes(item.status)).length;
  const blocked = data.items.filter((item) => item.status === "changes_requested").length;
  const withPage = (nextPage: number, overrides: Record<string, string | undefined> = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries({ ...filters, ...overrides, page: String(nextPage) })) {
      if (value) {
        params.set(key, value);
      }
    }
    return `/requests?${params.toString()}`;
  };
  const sortHref = (column: string) => withPage(1, { sort: column, order: sort === column && order === "asc" ? "desc" : "asc" });
  const toggleSelectedHref = (requestId: string) => {
    const nextSelected = selectedKeys.includes(requestId)
      ? selectedKeys.filter((key) => key !== requestId)
      : [...selectedKeys, requestId];
    return withPage(1, { selected: nextSelected.length > 0 ? nextSelected.join(",") : undefined });
  };
  const toggleColumnHref = (columnKey: string) => {
    const nextColumns = new Set(visibleColumnKeys);
    if (nextColumns.has(columnKey)) {
      if (nextColumns.size === 1) {
        return withPage(1);
      }
      nextColumns.delete(columnKey);
    } else {
      nextColumns.add(columnKey);
    }
    return withPage(1, { cols: Array.from(nextColumns).join(",") });
  };
  const columnVisibility = [
    { key: "type", label: "Type" },
    { key: "owner", label: "Owner" },
    { key: "priority", label: "Priority" },
    { key: "workflow", label: "Workflow" },
    { key: "federation", label: "Federation" },
    { key: "phase", label: "Phase" },
    { key: "blocking", label: "Blocking" },
    { key: "sla", label: "SLA Risk" },
    { key: "updated", label: "Updated" }
  ].map((column) => ({
    ...column,
    visible: visibleColumnKeys.has(column.key),
    toggleHref: toggleColumnHref(column.key)
  }));

  return (
    <PageShell
      {...appShellProps("/requests", "Requests", "Primary navigation surface for governed work across submitters, reviewers, and operators.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Queue Status" />
          <MetricStack items={[{ label: "Total Requests", value: data.total_count }, { label: "Active", value: active }, { label: "Blocked", value: blocked }]} />
        </div>
      }
    >
      <div className="space-y-4">
        <QueueTabs activeKey="all" items={requestQueueTabs} />
        <FilterPanel
          items={[
            { label: "Status", value: filters.status ?? "All", active: Boolean(filters.status) },
            { label: "Priority", value: "Use table sorting", active: false },
            { label: "Owner", value: filters.owner_team_id ?? "All teams", active: Boolean(filters.owner_team_id) },
            { label: "Workflow", value: filters.workflow ?? "All workflows", active: Boolean(filters.workflow) },
            { label: "Federation", value: filters.federation ?? "All requests", active: Boolean(filters.federation) }
          ]}
          actions={
            <>
              <Link href={withPage(1, { status: undefined, federation: undefined })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Clear
              </Link>
              <Link href={withPage(1, { status: "awaiting_review" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Awaiting Review
              </Link>
              <Link href={withPage(1, { status: "promotion_pending" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Promotion Pending
              </Link>
              <Link href={withPage(1, { federation: "with_conflict" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Federated Conflicts
              </Link>
            </>
          }
        />
        <form method="get" className="grid gap-3 rounded-xl border border-chrome bg-panel px-5 py-4 shadow-panel md:grid-cols-5">
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="text-xs font-medium text-slate-500">Status</span>
            <select name="status" defaultValue={filters.status ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2">
              <option value="">All statuses</option>
              <option value="draft">Draft</option>
              <option value="submitted">Submitted</option>
              <option value="awaiting_review">Awaiting Review</option>
              <option value="under_review">Under Review</option>
              <option value="changes_requested">Changes Requested</option>
              <option value="promotion_pending">Promotion Pending</option>
              <option value="failed">Failed</option>
              <option value="completed">Completed</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="text-xs font-medium text-slate-500">Owner Team</span>
            <input name="owner_team_id" defaultValue={filters.owner_team_id ?? ""} placeholder="team_curriculum_science" className="rounded-md border border-chrome bg-white px-3 py-2" />
          </label>
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="text-xs font-medium text-slate-500">Workflow</span>
            <input name="workflow" defaultValue={filters.workflow ?? ""} placeholder="wf_curriculum_v3" className="rounded-md border border-chrome bg-white px-3 py-2" />
          </label>
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="text-xs font-medium text-slate-500">Federation</span>
            <select name="federation" defaultValue={filters.federation ?? ""} className="rounded-md border border-chrome bg-white px-3 py-2">
              <option value="">All requests</option>
              <option value="with_projection">Projected to external systems</option>
              <option value="with_conflict">Federated conflicts</option>
            </select>
          </label>
          <div className="flex items-end gap-2 md:col-span-4">
            <button type="submit" className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white">Apply Filters</button>
            <Link href="/requests" className="rounded-md border border-chrome bg-white px-4 py-2 text-sm font-medium text-slate-700">Reset</Link>
          </div>
        </form>
        <div className="flex items-center justify-between rounded-xl border border-chrome bg-panel px-5 py-4 shadow-panel">
          <div>
            <h2 className="text-lg font-semibold">Request List</h2>
            <p className="text-sm text-slate-600">Create, review, and route governed requests from the canonical queue.</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/requests/blocked" className="rounded-md border border-chrome bg-white px-4 py-2 text-sm font-semibold text-slate-700">
              Blocked Queue
            </Link>
            <Link href="/requests/new" className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white">
              Create Request
            </Link>
          </div>
        </div>
        <DataTable
          data={sortedItems}
          emptyMessage="No requests yet."
          selection={{
            rowKey: (row) => row.id,
            selectedKeys,
            toggleHref: toggleSelectedHref,
            clearHref: selectedKeys.length > 0 ? withPage(1, { selected: undefined }) : undefined
          }}
          columnVisibility={columnVisibility}
          pagination={{
            page: data.page,
            pageSize: data.page_size,
            totalCount: data.total_count,
            totalPages: data.total_pages,
            previousHref: data.page > 1 ? withPage(data.page - 1) : undefined,
            nextHref: data.page < data.total_pages ? withPage(data.page + 1) : undefined
          }}
          columns={[
            { key: "id", header: "ID", render: (row) => <Link href={`/requests/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
            { key: "type", header: "Type", render: (row) => row.request_type },
            {
              key: "title",
              header: "Title",
              sortHref: sortHref("title"),
              sortDirection: sort === "title" ? order : undefined,
              render: (row) => (
                <Link href={`/requests/${row.id}`} className="font-medium text-slate-900 hover:text-accent hover:underline">
                  {row.title}
                </Link>
              )
            },
            { key: "status", header: "Status", sortHref: sortHref("status"), sortDirection: sort === "status" ? order : undefined, render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "owner", header: "Owner", sortHref: sortHref("owner_team_id"), sortDirection: sort === "owner_team_id" ? order : undefined, render: (row) => row.owner_team_id ?? "Unassigned" },
            { key: "priority", header: "Priority", sortHref: sortHref("priority"), sortDirection: sort === "priority" ? order : undefined, render: (row) => row.priority },
            { key: "workflow", header: "Workflow", render: (row) => row.workflow_binding_id ?? row.template_id },
            {
              key: "federation",
              header: "Federation",
              render: (row) =>
                row.federated_projection_count > 0
                  ? `${row.federated_projection_count} projection${row.federated_projection_count === 1 ? "" : "s"}${row.federated_conflict_count > 0 ? ` • ${row.federated_conflict_count} conflict${row.federated_conflict_count === 1 ? "" : "s"}` : ""}`
                  : "None"
            },
            { key: "phase", header: "Current Phase", render: (row) => (["in_execution", "awaiting_input"].includes(row.status) ? "Execution" : ["awaiting_review", "under_review", "changes_requested"].includes(row.status) ? "Review" : "Intake") },
            { key: "blocking", header: "Blocking Status", render: (row) => (row.status === "changes_requested" ? "Blocked" : row.status === "promotion_pending" ? "Promotion Pending" : "Clear") },
            { key: "sla", header: "SLA Risk", render: (row) => row.sla_risk_level ? `${row.sla_risk_level}: ${row.sla_risk_reason}` : "Normal" },
            { key: "updated", header: "Updated At", sortHref: sortHref("updated_at"), sortDirection: sort === "updated_at" ? order : undefined, render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
