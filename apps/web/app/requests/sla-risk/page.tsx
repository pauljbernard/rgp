import { listRequestEscalations, listRequests, listSlaBreaches } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, QueueTabs, SectionHeading, appShellProps, formatDate, statusTone } from "../../../components/ui-helpers";
import { executeEscalationFromRiskQueueAction, remediateSlaBreachFromRiskQueueAction } from "./actions";

const requestQueueTabs = [
  { key: "all", label: "All Requests", href: "/requests" },
  { key: "blocked", label: "Blocked Requests", href: "/requests/blocked" },
  { key: "federated-conflicts", label: "Federated Conflicts", href: "/requests/federated-conflicts" },
  { key: "promotion", label: "Promotion Pending", href: "/promotions/pending" },
  { key: "sla-risk", label: "SLA Risk", href: "/requests/sla-risk" }
];

function isSlaRisk(item: {
  sla_risk_level?: string | null;
}) {
  return Boolean(item.sla_risk_level);
}

export default async function SlaRiskRequestsPage() {
  const [data, breaches] = await Promise.all([listRequests({ page_size: 100 }), listSlaBreaches()]);
  const riskItems = data.items.filter(isSlaRisk);
  const escalationEntries = await Promise.all(
    riskItems.map(async (item) => [item.id, await listRequestEscalations(item.id)] as const)
  );
  const escalationsByRequest = new Map(escalationEntries);
  const latestBreachByRequest = new Map<string, (typeof breaches)[number]>();
  for (const breach of breaches) {
    if (!latestBreachByRequest.has(breach.request_id)) {
      latestBreachByRequest.set(breach.request_id, breach);
    }
  }
  const requestsWithRecordedBreaches = riskItems.filter((item) => latestBreachByRequest.has(item.id));
  const unremediatedBreaches = breaches.filter((breach) => !breach.remediation_action).length;

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
              { label: "Recorded Breaches", value: requestsWithRecordedBreaches.length },
              { label: "Unremediated Breaches", value: unremediatedBreaches }
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
            { label: "Signals", value: "policy-derived execution, review, promotion, and urgent thresholds" },
            { label: "Recorded Breaches", value: `${requestsWithRecordedBreaches.length} requests`, active: requestsWithRecordedBreaches.length > 0 }
          ]}
          actions={
            <Link href="/queues" className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
              Queue Controls
            </Link>
          }
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
            {
              key: "breach",
              header: "Latest Breach",
              render: (row) => {
                const breach = latestBreachByRequest.get(row.id);
                if (!breach) {
                  return "No recorded breach";
                }
                return `${breach.breach_type} • ${breach.actual_hours}h / ${breach.target_hours}h`;
              }
            },
            {
              key: "severity",
              header: "Severity",
              render: (row) => {
                const breach = latestBreachByRequest.get(row.id);
                return breach ? breach.severity : "Observed";
              }
            },
            {
              key: "escalation",
              header: "Triggered Escalations",
              render: (row) => {
                const rules = escalationsByRequest.get(row.id) ?? [];
                return rules.length ? rules.map((rule) => rule.name).join(", ") : "No triggered escalation";
              }
            },
            {
              key: "remediation",
              header: "Remediation",
              render: (row) => {
                const breach = latestBreachByRequest.get(row.id);
                return breach?.remediation_action ?? "Pending operator action";
              }
            },
            {
              key: "actions",
              header: "Actions",
              render: (row) => {
                const breach = latestBreachByRequest.get(row.id);
                const escalationRules = escalationsByRequest.get(row.id) ?? [];
                return (
                  <div className="flex flex-wrap gap-2">
                    {!breach || breach.remediation_action ? null : (
                      <form action={remediateSlaBreachFromRiskQueueAction}>
                        <input type="hidden" name="breachId" value={breach.id} />
                        <input type="hidden" name="remediationAction" value="queue_lead_notified" />
                        <button type="submit" className="rounded-md border border-chrome bg-white px-3 py-1 text-xs font-medium text-slate-700">
                          Notify Queue Lead
                        </button>
                      </form>
                    )}
                    {escalationRules[0] ? (
                      <form action={executeEscalationFromRiskQueueAction}>
                        <input type="hidden" name="requestId" value={row.id} />
                        <input type="hidden" name="ruleId" value={escalationRules[0].id} />
                        <button type="submit" className="rounded-md border border-slate-300 bg-slate-950 px-3 py-1 text-xs font-medium text-white">
                          Execute Escalation
                        </button>
                      </form>
                    ) : null}
                    {!breach && !escalationRules[0] ? "No action required" : null}
                  </div>
                );
              }
            },
            { key: "updated", header: "Updated At", render: (row) => formatDate(row.updated_at) }
          ]}
        />
      </div>
    </PageShell>
  );
}
