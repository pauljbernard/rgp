import { listReviewQueue } from "@/lib/server-api";
import Link from "next/link";
import React from "react";
import { Badge, Button, DataTable, FilterPanel, PageShell, appShellProps } from "../../../components/ui-helpers";
import { overrideReviewAssignmentAction, reviewDecisionAction } from "./actions";

export default async function ReviewQueuePage({
  searchParams
}: {
  searchParams: Promise<{ assigned_reviewer?: string; blocking_only?: string; stale_only?: string; request_id?: string; page?: string; sort?: string; order?: string; selected?: string; cols?: string }>;
}) {
  const filters = await searchParams;
  const page = Number(filters.page ?? "1") || 1;
  const data = await listReviewQueue({
    page,
    assigned_reviewer: filters.assigned_reviewer,
    blocking_only: filters.blocking_only === "true",
    stale_only: filters.stale_only === "true",
    request_id: filters.request_id
  });
  const sort = filters.sort ?? "priority";
  const order = filters.order === "asc" ? "asc" : "desc";
  const selectedKeys = (filters.selected ?? "").split(",").filter(Boolean);
  const defaultColumns = ["request", "scope", "artifact", "type", "priority", "sla", "blocking", "reviewer", "actions"];
  const visibleColumnKeys = new Set((filters.cols ?? defaultColumns.join(",")).split(",").filter(Boolean));
  const sortedItems = [...data.items].sort((left, right) => {
    const direction = order === "asc" ? 1 : -1;
    switch (sort) {
      case "assigned_reviewer":
        return direction * left.assigned_reviewer.localeCompare(right.assigned_reviewer);
      case "blocking_status":
        return direction * left.blocking_status.localeCompare(right.blocking_status);
      case "priority":
      default:
        return direction * left.priority.localeCompare(right.priority);
    }
  });
  const withPage = (nextPage: number, overrides: Record<string, string | undefined> = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries({ ...filters, ...overrides, page: String(nextPage) })) {
      if (value) {
        params.set(key, value);
      }
    }
    return `/reviews/queue?${params.toString()}`;
  };
  const sortHref = (column: string) => withPage(1, { sort: column, order: sort === column && order === "asc" ? "desc" : "asc" });
  const toggleSelectedHref = (reviewId: string) => {
    const nextSelected = selectedKeys.includes(reviewId)
      ? selectedKeys.filter((key) => key !== reviewId)
      : [...selectedKeys, reviewId];
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
    { key: "scope", label: "Scope" },
    { key: "artifact", label: "Artifact" },
    { key: "type", label: "Type" },
    { key: "priority", label: "Priority" },
    { key: "sla", label: "SLA" },
    { key: "blocking", label: "Blocking" },
    { key: "reviewer", label: "Reviewer" },
    { key: "actions", label: "Actions" }
  ].map((column) => ({
    ...column,
    visible: visibleColumnKeys.has(column.key),
    toggleHref: toggleColumnHref(column.key)
  }));

  return (
    <PageShell {...appShellProps("/reviews/queue", "Review Queue", "Actionable reviewer worklist with blocking state and SLA visibility.")}>
      <div className="space-y-4">
        <FilterPanel
          items={[
            { label: "Assigned To", value: filters.assigned_reviewer ?? "All reviewers", active: Boolean(filters.assigned_reviewer) },
            { label: "Blocking Only", value: filters.blocking_only === "true" ? "On" : "Off", active: filters.blocking_only === "true" },
            { label: "Stale Only", value: filters.stale_only === "true" ? "On" : "Off", active: filters.stale_only === "true" },
            { label: "Request", value: filters.request_id ?? "All", active: Boolean(filters.request_id) }
          ]}
          actions={
            <>
              <Link href={withPage(1, { assigned_reviewer: undefined, blocking_only: undefined, stale_only: undefined, request_id: undefined })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Clear
              </Link>
              <Link href={withPage(1, { blocking_only: "true", stale_only: undefined })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Blocking Only
              </Link>
              <Link href={withPage(1, { stale_only: "true", blocking_only: undefined })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Stale Only
              </Link>
            </>
          }
        />
        <form method="get" className="grid gap-3 rounded-xl border border-chrome bg-panel px-5 py-4 shadow-panel md:grid-cols-4">
          <label className="grid gap-1 text-sm text-slate-700">
            <span className="text-xs font-medium text-slate-500">Assigned Reviewer</span>
            <input name="assigned_reviewer" defaultValue={filters.assigned_reviewer ?? ""} placeholder="reviewer_nina" className="rounded-md border border-chrome bg-white px-3 py-2" />
          </label>
          <label className="flex items-center gap-2 rounded-md border border-chrome bg-white px-3 py-2 text-sm text-slate-700">
            <input type="checkbox" name="blocking_only" value="true" defaultChecked={filters.blocking_only === "true"} />
            Blocking only
          </label>
          <label className="flex items-center gap-2 rounded-md border border-chrome bg-white px-3 py-2 text-sm text-slate-700">
            <input type="checkbox" name="stale_only" value="true" defaultChecked={filters.stale_only === "true"} />
            Stale only
          </label>
          <div className="flex items-end gap-2">
            <button type="submit" className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white">Apply Filters</button>
            <Link href="/reviews/queue" className="rounded-md border border-chrome bg-white px-4 py-2 text-sm font-medium text-slate-700">Reset</Link>
          </div>
        </form>
        <DataTable
          data={sortedItems}
          emptyMessage="Review queue is empty."
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
            { key: "request", header: "Request", render: (row) => <Link href={`/requests/${row.request_id}`} className="text-accent">{row.request_id}</Link> },
            { key: "scope", header: "Review Scope", render: (row) => row.review_scope },
            { key: "artifact", header: "Artifact / Change Set", render: (row) => row.artifact_or_changeset },
            { key: "type", header: "Type", render: (row) => row.type },
            { key: "priority", header: "Priority", sortHref: sortHref("priority"), sortDirection: sort === "priority" ? order : undefined, render: (row) => row.priority },
            { key: "sla", header: "SLA", render: (row) => row.sla },
            { key: "blocking", header: "Blocking Status", sortHref: sortHref("blocking_status"), sortDirection: sort === "blocking_status" ? order : undefined, render: (row) => <Badge tone={row.stale ? "danger" : "warning"}>{row.blocking_status}</Badge> },
            { key: "reviewer", header: "Assigned Reviewer", sortHref: sortHref("assigned_reviewer"), sortDirection: sort === "assigned_reviewer" ? order : undefined, render: (row) => row.assigned_reviewer },
            {
              key: "actions",
              header: "Actions",
              render: (row) => (
                <div className="flex flex-wrap gap-2">
                  <form action={reviewDecisionAction}>
                    <input type="hidden" name="reviewId" value={row.id} />
                    <input type="hidden" name="decision" value="approve" />
                    <Button label="Approve" tone="primary" type="submit" />
                  </form>
                  <form action={reviewDecisionAction}>
                    <input type="hidden" name="reviewId" value={row.id} />
                    <input type="hidden" name="decision" value="changes_requested" />
                    <Button label="Request Changes" tone="secondary" type="submit" />
                  </form>
                  <form action={overrideReviewAssignmentAction} className="flex gap-2">
                    <input type="hidden" name="reviewId" value={row.id} />
                    <input
                      name="assignedReviewer"
                      defaultValue={row.assigned_reviewer}
                      className="w-36 rounded-md border border-chrome bg-white px-2 py-1 text-xs text-slate-700"
                    />
                    <Button label="Reassign" tone="secondary" type="submit" />
                  </form>
                </div>
              )
            }
          ]}
        />
      </div>
    </PageShell>
  );
}
