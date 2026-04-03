import { listRequests } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, QueueTabs, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";

const requestQueueTabs = [
  { key: "all", label: "All Requests", href: "/requests" },
  { key: "blocked", label: "Blocked Requests", href: "/requests/blocked" },
  { key: "promotion", label: "Promotion Pending", href: "/promotions/pending" },
  { key: "sla-risk", label: "SLA Risk", href: "/requests/sla-risk" }
];

function isSlaRisk(item: {
  sla_risk_level?: string | null;
}) {
  return Boolean(item.sla_risk_level);
}

export default async function SlaRiskRequestsPage() {
  const data = await listRequests({ page_size: 100 });
  const riskItems = data.items.filter(isSlaRisk);

  return (
    <PageShell
      {...appShellProps("/requests", "SLA Risk", "Queue of requests with elevated delivery risk based on urgency, review blockage, failure state, or promotion delay.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Risk Summary" />
          <MetricStack
            items={[
              { label: "SLA-Risk Requests", value: riskItems.length },
              { label: "Critical Risk", value: riskItems.filter((item) => item.sla_risk_level === "critical").length },
              { label: "Review / Promotion Delays", value: riskItems.filter((item) => ["Review delay", "Promotion delay"].includes(item.sla_risk_reason ?? "")).length }
            ]}
          />
        </div>
      }
    >
      <div className="space-y-4">
        <QueueTabs activeKey="sla-risk" items={requestQueueTabs} />
        <FilterPanel
          title="Queue Filters"
          items={[
            { label: "Queue", value: "SLA Risk" },
            { label: "Signals", value: "policy-derived execution, review, promotion, and urgent thresholds" }
          ]}
        />
        <DataTable
          data={riskItems}
          emptyMessage="No requests currently flagged as SLA risk."
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
            { key: "priority", header: "Priority", render: (row) => row.priority },
            { key: "owner", header: "Owner", render: (row) => row.owner_team_id ?? "Unassigned" },
            {
              key: "risk",
              header: "Risk Signal",
              render: (row) => row.sla_risk_reason ?? "Normal"
            },
            { key: "updated", header: "Updated At", render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
