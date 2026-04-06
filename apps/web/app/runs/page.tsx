import { listRequestProjections, listRuns } from "@/lib/server-api";
import Link from "next/link";
import { Badge, Button, DataTable, FilterPanel, PageShell, QueueTabs, appShellProps, formatDate, statusTone } from "../../components/ui-helpers";
import { resolveRequestProjectionAction, syncRequestProjectionAction } from "../requests/[requestId]/projections/[projectionId]/actions";

const runQueueTabs = [
  { key: "all", label: "All Runs", href: "/runs" },
  { key: "failed", label: "Failed Runs", href: "/runs/failed" }
];

function primaryResolutionAction(adapterType: string | null | undefined, supportedActions: string[]) {
  if (supportedActions.includes("resume_session")) {
    return { action: "resume_session", label: "Resume Session" };
  }
  if (supportedActions.includes("retry_sync")) {
    return { action: "retry_sync", label: "Retry Sync" };
  }
  if (supportedActions.includes("reprovision")) {
    return { action: "reprovision", label: "Reprovision" };
  }
  if (supportedActions.includes("merge")) {
    return { action: "merge", label: "Merge" };
  }
  if (supportedActions.includes("accept_internal")) {
    return {
      action: "accept_internal",
      label:
        adapterType === "repository_projection"
          ? "Accept Canonical"
          : adapterType === "runtime_projection"
            ? "Accept Governed State"
            : "Accept Internal",
    };
  }
  return { action: supportedActions[0] ?? "accept_internal", label: "Resolve" };
}

export default async function RunsPage({
  searchParams
}: {
  searchParams: Promise<{ status?: string; workflow?: string; owner?: string; request_id?: string; federation?: string; page?: string; sort?: string; order?: string; selected?: string; cols?: string }>;
}) {
  const filters = await searchParams;
  const page = Number(filters.page ?? "1") || 1;
  const data = await listRuns({ ...filters, page });
  const sort = filters.sort ?? "updated_at";
  const order = filters.order === "asc" ? "asc" : "desc";
  const selectedKeys = (filters.selected ?? "").split(",").filter(Boolean);
  const defaultColumns = ["id", "request", "workflow", "status", "federation", "step", "elapsed", "waiting", "updated"];
  const visibleColumnKeys = new Set((filters.cols ?? defaultColumns.join(",")).split(",").filter(Boolean));
  const sortedItems = [...data.items].sort((left, right) => {
    const direction = order === "asc" ? 1 : -1;
    switch (sort) {
      case "workflow":
        return direction * left.workflow.localeCompare(right.workflow);
      case "status":
        return direction * left.status.localeCompare(right.status);
      case "current_step":
        return direction * left.current_step.localeCompare(right.current_step);
      default:
        return direction * (new Date(left.updated_at).getTime() - new Date(right.updated_at).getTime());
    }
  });
  const withPage = (nextPage: number, overrides: Record<string, string | undefined> = {}) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries({ ...filters, ...overrides, page: String(nextPage) })) {
      if (value) {
        params.set(key, value);
      }
    }
    return `/runs?${params.toString()}`;
  };
  const sortHref = (column: string) => withPage(1, { sort: column, order: sort === column && order === "asc" ? "desc" : "asc" });
  const toggleSelectedHref = (runId: string) => {
    const nextSelected = selectedKeys.includes(runId)
      ? selectedKeys.filter((key) => key !== runId)
      : [...selectedKeys, runId];
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
    { key: "request", label: "Request" },
    { key: "workflow", label: "Workflow" },
    { key: "federation", label: "Federation" },
    { key: "step", label: "Step" },
    { key: "elapsed", label: "Elapsed" },
    { key: "waiting", label: "Waiting" },
    { key: "updated", label: "Updated" }
  ].map((column) => ({
    ...column,
    visible: visibleColumnKeys.has(column.key),
    toggleHref: toggleColumnHref(column.key)
  }));
  const projectionRows = await Promise.all(
    sortedItems
      .filter((item) => item.federated_projection_count > 0)
      .map(async (item) => [item.request_id, await listRequestProjections(item.request_id)] as const)
  );
  const remediationProjectionByRequest = new Map(
    projectionRows.map(([requestId, projections]) => [
      requestId,
      projections.find((projection) => projection.conflicts.length > 0) ?? projections[0] ?? null,
    ])
  );
  const returnTo = withPage(data.page);

  return (
    <PageShell {...appShellProps("/runs", "Runs", "Operational run management for active, waiting, failed, and completed execution instances.")}>
      <div className="space-y-4">
        <QueueTabs activeKey="all" items={runQueueTabs} />
        <FilterPanel
          items={[
            { label: "Status", value: filters.status ?? "All", active: Boolean(filters.status) },
            { label: "Workflow", value: filters.workflow ?? "All workflows", active: Boolean(filters.workflow) },
            { label: "Owner Team", value: filters.owner ?? "All teams", active: Boolean(filters.owner) },
            { label: "Request", value: filters.request_id ?? "All requests", active: Boolean(filters.request_id) },
            { label: "Federation", value: filters.federation ?? "All runs", active: Boolean(filters.federation) }
          ]}
          actions={
            <>
              <Link href={withPage(1, { status: undefined, federation: undefined })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Clear
              </Link>
              <Link href={withPage(1, { status: "waiting" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Waiting
              </Link>
              <Link href={withPage(1, { status: "failed" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Failed
              </Link>
              <Link href={withPage(1, { federation: "with_conflict" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Federated Conflicts
              </Link>
            </>
          }
        />
        <DataTable
          data={sortedItems}
          emptyMessage="No runs found."
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
            { key: "id", header: "Run ID", render: (row) => <Link href={`/runs/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
            { key: "request", header: "Request ID", render: (row) => <Link href={`/requests/${row.request_id}`} className="text-accent">{row.request_id}</Link> },
            { key: "workflow", header: "Workflow", sortHref: sortHref("workflow"), sortDirection: sort === "workflow" ? order : undefined, render: (row) => row.workflow },
            { key: "status", header: "Status", sortHref: sortHref("status"), sortDirection: sort === "status" ? order : undefined, render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            {
              key: "federation",
              header: "Federation",
              render: (row) =>
                row.federated_projection_count ? (
                  <div className="space-y-2">
                    <div>{row.federated_projection_count} projection{row.federated_projection_count === 1 ? "" : "s"}</div>
                    <Badge tone={row.federated_conflict_count ? "warning" : "success"}>
                      {row.federated_conflict_count ? `${row.federated_conflict_count} conflict${row.federated_conflict_count === 1 ? "" : "s"}` : "in sync"}
                    </Badge>
                    {(() => {
                      const projection = remediationProjectionByRequest.get(row.request_id);
                      if (!projection) {
                        return null;
                      }
                      const primaryAction = primaryResolutionAction(projection.adapter_type, projection.supported_resolution_actions);
                      return (
                        <div className="space-y-2">
                          <Link href={`/requests/${row.request_id}/projections/${projection.id}`} className="block text-xs font-medium text-accent">
                            Open remediation
                          </Link>
                          <div className="flex flex-wrap gap-2">
                            <form action={syncRequestProjectionAction}>
                              <input type="hidden" name="requestId" value={row.request_id} />
                              <input type="hidden" name="projectionId" value={projection.id} />
                              <input type="hidden" name="returnTo" value={returnTo} />
                              <Button label="Sync" tone="secondary" type="submit" />
                            </form>
                            <form action={resolveRequestProjectionAction}>
                              <input type="hidden" name="requestId" value={row.request_id} />
                              <input type="hidden" name="projectionId" value={projection.id} />
                              <input type="hidden" name="action" value={primaryAction.action} />
                              <input type="hidden" name="returnTo" value={returnTo} />
                              <Button label={primaryAction.label} tone="primary" type="submit" />
                            </form>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                ) : (
                  <span className="text-slate-500">No projections</span>
                )
            },
            { key: "step", header: "Current Step", sortHref: sortHref("current_step"), sortDirection: sort === "current_step" ? order : undefined, render: (row) => row.current_step },
            { key: "elapsed", header: "Elapsed Time", render: (row) => row.elapsed_time },
            { key: "waiting", header: "Waiting Reason", render: (row) => row.waiting_reason ?? "None" },
            { key: "updated", header: "Updated At", sortHref: sortHref("updated_at"), sortDirection: sort === "updated_at" ? order : undefined, render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
