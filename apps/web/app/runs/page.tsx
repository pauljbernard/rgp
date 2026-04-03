import { listRuns } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, PageShell, QueueTabs, appShellProps, formatDate, statusTone } from "../../components/ui-helpers";

const runQueueTabs = [
  { key: "all", label: "All Runs", href: "/runs" },
  { key: "failed", label: "Failed Runs", href: "/runs/failed" }
];

export default async function RunsPage({
  searchParams
}: {
  searchParams: Promise<{ status?: string; workflow?: string; owner?: string; request_id?: string; page?: string; sort?: string; order?: string; selected?: string; cols?: string }>;
}) {
  const filters = await searchParams;
  const page = Number(filters.page ?? "1") || 1;
  const data = await listRuns({ ...filters, page });
  const sort = filters.sort ?? "updated_at";
  const order = filters.order === "asc" ? "asc" : "desc";
  const selectedKeys = (filters.selected ?? "").split(",").filter(Boolean);
  const defaultColumns = ["id", "request", "workflow", "status", "step", "elapsed", "waiting", "updated"];
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
    { key: "step", label: "Step" },
    { key: "elapsed", label: "Elapsed" },
    { key: "waiting", label: "Waiting" },
    { key: "updated", label: "Updated" }
  ].map((column) => ({
    ...column,
    visible: visibleColumnKeys.has(column.key),
    toggleHref: toggleColumnHref(column.key)
  }));

  return (
    <PageShell {...appShellProps("/runs", "Runs", "Operational run management for active, waiting, failed, and completed execution instances.")}>
      <div className="space-y-4">
        <QueueTabs activeKey="all" items={runQueueTabs} />
        <FilterPanel
          items={[
            { label: "Status", value: filters.status ?? "All", active: Boolean(filters.status) },
            { label: "Workflow", value: filters.workflow ?? "All workflows", active: Boolean(filters.workflow) },
            { label: "Owner Team", value: filters.owner ?? "All teams", active: Boolean(filters.owner) },
            { label: "Request", value: filters.request_id ?? "All requests", active: Boolean(filters.request_id) }
          ]}
          actions={
            <>
              <Link href={withPage(1, { status: undefined })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Clear
              </Link>
              <Link href={withPage(1, { status: "waiting" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Waiting
              </Link>
              <Link href={withPage(1, { status: "failed" })} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Failed
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
