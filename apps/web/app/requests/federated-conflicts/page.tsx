import { listRequests } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, QueueTabs, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";

const requestQueueTabs = [
  { key: "all", label: "All Requests", href: "/requests" },
  { key: "blocked", label: "Blocked Requests", href: "/requests/blocked" },
  { key: "federated-conflicts", label: "Federated Conflicts", href: "/requests/federated-conflicts" },
  { key: "promotion", label: "Promotion Pending", href: "/promotions/pending" },
  { key: "sla-risk", label: "SLA Risk", href: "/requests/sla-risk" }
];

export default async function FederatedConflictRequestsPage() {
  const data = await listRequests({ page_size: 25, federation: "with_conflict" });
  const conflictItems = data.items.filter((item) => item.federated_conflict_count > 0);

  return (
    <PageShell
      {...appShellProps("/requests", "Federated Conflicts", "Requests whose canonical governance state diverges from one or more external-system projections.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Conflict Summary" />
          <MetricStack
            items={[
              { label: "Requests in Conflict", value: conflictItems.length },
              { label: "Projected Requests", value: conflictItems.filter((item) => item.federated_projection_count > 0).length },
              { label: "Total Conflicts", value: conflictItems.reduce((sum, item) => sum + item.federated_conflict_count, 0) }
            ]}
          />
        </div>
      }
    >
      <div className="space-y-4">
        <QueueTabs activeKey="federated-conflicts" items={requestQueueTabs} />
        <FilterPanel
          title="Queue Filters"
          items={[
            { label: "Queue", value: "Federated Conflicts" },
            { label: "Signals", value: "request projections with canonical vs external divergence" }
          ]}
          actions={
            <>
              <Link href="/requests" className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                All Requests
              </Link>
              <Link href="/runs?federation=with_conflict" className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Run View
              </Link>
            </>
          }
        />
        <DataTable
          data={conflictItems}
          emptyMessage="No requests currently have federated conflicts."
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
            { key: "workflow", header: "Workflow", render: (row) => row.workflow_binding_id ?? row.template_id },
            {
              key: "federation",
              header: "Federation",
              render: (row) => `${row.federated_projection_count} projection${row.federated_projection_count === 1 ? "" : "s"} • ${row.federated_conflict_count} conflict${row.federated_conflict_count === 1 ? "" : "s"}`
            },
            {
              key: "remediate",
              header: "Remediate",
              render: (row) => (
                <div className="space-y-1">
                  <Link href={`/requests/${row.id}`} className="block text-xs font-medium text-accent">
                    Open request
                  </Link>
                  <Link href={`/requests/${row.id}/history`} className="block text-xs font-medium text-slate-600 hover:text-accent">
                    Open history
                  </Link>
                </div>
              )
            },
            { key: "updated", header: "Updated At", render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
