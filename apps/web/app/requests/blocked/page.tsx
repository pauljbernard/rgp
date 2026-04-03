import { listRequests } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, QueueTabs, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";

const requestQueueTabs = [
  { key: "all", label: "All Requests", href: "/requests" },
  { key: "blocked", label: "Blocked Requests", href: "/requests/blocked" },
  { key: "promotion", label: "Promotion Pending", href: "/promotions/pending" },
  { key: "sla-risk", label: "SLA Risk", href: "/requests/sla-risk" }
];

export default async function BlockedRequestsPage({
  searchParams
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  await searchParams;
  const data = await listRequests({ page_size: 100 });
  const blockedItems = data.items.filter((item) => ["changes_requested", "awaiting_input", "validation_failed"].includes(item.status));

  return (
    <PageShell
      {...appShellProps("/requests", "Blocked Requests", "Actionable queue of requests that cannot progress until an explicit human or authoring intervention occurs.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Queue Status" />
          <MetricStack
            items={[
              { label: "Blocked Requests", value: blockedItems.length },
              { label: "Changes Requested", value: blockedItems.filter((item) => item.status === "changes_requested").length },
              { label: "Awaiting Input", value: blockedItems.filter((item) => item.status === "awaiting_input").length }
            ]}
          />
        </div>
      }
    >
      <div className="space-y-4">
        <QueueTabs activeKey="blocked" items={requestQueueTabs} />
        <FilterPanel
          title="Queue Filters"
          items={[
            { label: "Queue", value: "Blocked Requests" },
            { label: "Included Statuses", value: "changes_requested, awaiting_input, validation_failed" }
          ]}
        />
        <DataTable
          data={blockedItems}
          emptyMessage="No blocked requests."
          columns={[
            { key: "id", header: "ID", render: (row) => <Link href={`/requests/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
            {
              key: "title",
              header: "Title",
              render: (row) => (
                <Link href={`/requests/${row.id}`} className="font-medium text-slate-900 hover:text-accent hover:underline">
                  {row.title}
                </Link>
              )
            },
            { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
            { key: "owner", header: "Owner", render: (row) => row.owner_team_id ?? "Unassigned" },
            { key: "priority", header: "Priority", render: (row) => row.priority },
            { key: "workflow", header: "Workflow", render: (row) => row.workflow_binding_id ?? row.template_id },
            { key: "updated", header: "Updated At", render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
