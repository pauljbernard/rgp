import { listRuns } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, QueueTabs, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";

const runQueueTabs = [
  { key: "all", label: "All Runs", href: "/runs" },
  { key: "failed", label: "Failed Runs", href: "/runs/failed" }
];

export default async function FailedRunsPage({
  searchParams
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const filters = await searchParams;
  const page = Number(filters.page ?? "1") || 1;
  const data = await listRuns({ status: "failed", page, page_size: 25 });
  const withPage = (nextPage: number) => `/runs/failed?page=${nextPage}`;

  return (
    <PageShell
      {...appShellProps("/runs", "Failed Runs", "Operator worklist for execution failures that need diagnosis, retry, cancellation review, or replanning.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Queue Status" />
          <MetricStack
            items={[
              { label: "Failed Runs", value: data.total_count },
              { label: "Cancelable", value: data.items.filter((item) => item.status === "failed").length },
              { label: "Requests Affected", value: new Set(data.items.map((item) => item.request_id)).size }
            ]}
          />
        </div>
      }
    >
      <div className="space-y-4">
        <QueueTabs activeKey="failed" items={runQueueTabs} />
        <FilterPanel
          title="Queue Filters"
          items={[
            { label: "Queue", value: "Failed Runs" },
            { label: "Status", value: "failed" }
          ]}
        />
        <DataTable
          data={data.items}
          emptyMessage="No failed runs."
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
            { key: "workflow", header: "Workflow", render: (row) => row.workflow },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "step", header: "Current Step", render: (row) => row.current_step },
            { key: "waiting", header: "Failure / Waiting", render: (row) => row.waiting_reason ?? "Failed" },
            { key: "updated", header: "Updated At", render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
