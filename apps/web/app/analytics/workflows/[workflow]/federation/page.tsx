import { listRequests, listRuns, listWorkflowAnalytics, listWorkflowTrends } from "@/lib/server-api";
import Link from "next/link";
import { Badge, DataTable, FilterPanel, MetricStack, PageShell, SectionHeading, TimeSeriesChart, appShellProps, formatDate, statusTone } from "../../../../../components/ui-helpers";

function decodeWorkflow(value: string) {
  return decodeURIComponent(value);
}

export default async function WorkflowFederationPage({
  params,
  searchParams
}: {
  params: Promise<{ workflow: string }>;
  searchParams: Promise<{ days?: string; federation?: string }>;
}) {
  const { workflow: encodedWorkflow } = await params;
  const { days: daysParam, federation } = await searchParams;
  const workflow = decodeWorkflow(encodedWorkflow);
  const days = [7, 30, 90].includes(Number(daysParam)) ? Number(daysParam) : 30;
  const effectiveFederation = federation === "with_conflict" ? "with_conflict" : "with_projection";

  const [analyticsRows, trendRows, requestData, runData] = await Promise.all([
    listWorkflowAnalytics({ days }),
    listWorkflowTrends({ days, workflow }),
    listRequests({ page_size: 25, workflow, federation: effectiveFederation }),
    listRuns({ page_size: 25, workflow, federation: effectiveFederation })
  ]);

  const workflowRow = analyticsRows.find((row) => row.workflow === workflow);
  const requests = requestData.items;
  const runs = runData.items;

  return (
    <PageShell
      {...appShellProps(
        "/analytics/workflows",
        `${workflow} Federation`,
        "Workflow-scoped federated governance view across requests, runs, projections, and conflict signals."
      )}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Federation Summary" />
          <MetricStack
            items={[
              { label: "Workflow", value: workflow },
              { label: "Projected Requests", value: workflowRow?.federated_projection_count ?? 0 },
              { label: "Conflicts", value: workflowRow?.federated_conflict_count ?? 0 },
              { label: "Coverage", value: workflowRow?.federated_coverage ?? "0%" }
            ]}
          />
        </div>
      }
    >
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/analytics/workflows" className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
            Back to Workflows
          </Link>
          <Link href={`/analytics/workflows/${encodeURIComponent(workflow)}/history`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
            Open Workflow History
          </Link>
          <Link
            href={`/analytics/workflows/${encodeURIComponent(workflow)}/federation?days=${days}&federation=with_projection`}
            className={`rounded-md px-3 py-2 text-sm font-medium ${effectiveFederation === "with_projection" ? "bg-slate-950 text-white" : "border border-chrome bg-white text-slate-700"}`}
          >
            Projected Work
          </Link>
          <Link
            href={`/analytics/workflows/${encodeURIComponent(workflow)}/federation?days=${days}&federation=with_conflict`}
            className={`rounded-md px-3 py-2 text-sm font-medium ${effectiveFederation === "with_conflict" ? "bg-slate-950 text-white" : "border border-chrome bg-white text-slate-700"}`}
          >
            Conflict Focus
          </Link>
          <Link href={`/runs?workflow=${encodeURIComponent(workflow)}&federation=${effectiveFederation}`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
            Open Run Queue
          </Link>
          <Link href={`/requests?workflow=${encodeURIComponent(workflow)}&federation=${effectiveFederation}`} className="rounded-md border border-chrome bg-white px-3 py-2 text-sm font-medium text-slate-700">
            Open Request Queue
          </Link>
        </div>

        <FilterPanel
          items={[
            { label: "Workflow", value: workflow },
            { label: "Time Window", value: `${days}d` },
            { label: "View Mode", value: effectiveFederation === "with_conflict" ? "Conflict Focus" : "Projected Work" },
            { label: "Coverage", value: workflowRow?.federated_coverage ?? "0%" }
          ]}
          actions={
            <>
              <Link href={`/analytics/workflows/${encodeURIComponent(workflow)}/federation?days=7&federation=${effectiveFederation}`} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Last 7d
              </Link>
              <Link href={`/analytics/workflows/${encodeURIComponent(workflow)}/federation?days=30&federation=${effectiveFederation}`} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Last 30d
              </Link>
              <Link href={`/analytics/workflows/${encodeURIComponent(workflow)}/federation?days=90&federation=${effectiveFederation}`} className="rounded-md border border-chrome bg-white px-3 py-1.5 text-xs font-medium text-slate-700">
                Last 90d
              </Link>
            </>
          }
        />

        <TimeSeriesChart
          title="Workflow Trend"
          subtitle="Request volume and failures for the selected workflow."
          series={[
            {
              key: "requests",
              label: "Requests",
              color: "#0f172a",
              points: trendRows.map((point) => ({ label: point.period_start, value: point.request_count }))
            },
            {
              key: "failures",
              label: "Failures",
              color: "#dc2626",
              points: trendRows.map((point) => ({ label: point.period_start, value: point.failed_count }))
            }
          ]}
        />

        <div className="grid gap-4 xl:grid-cols-2">
          <div className="space-y-4">
            <div className="rounded-xl border border-chrome bg-panel px-5 py-4 shadow-panel">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">Affected Requests</h2>
                  <p className="text-sm text-slate-600">Workflow-scoped request records with federated projections.</p>
                </div>
                <Badge tone={requests.length > 0 ? "warning" : "neutral"}>{requests.length}</Badge>
              </div>
            </div>
            <DataTable
              data={requests}
              emptyMessage="No requests matched this workflow federation view."
              columns={[
                { key: "id", header: "ID", render: (row) => <Link href={`/requests/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
                { key: "title", header: "Title", render: (row) => <Link href={`/requests/${row.id}`} className="font-medium text-slate-900 hover:text-accent hover:underline">{row.title}</Link> },
                { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
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
                { key: "updated", header: "Updated", render: (row) => formatDate(row.updated_at) }
              ]}
            />
          </div>

          <div className="space-y-4">
            <div className="rounded-xl border border-chrome bg-panel px-5 py-4 shadow-panel">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">Affected Runs</h2>
                  <p className="text-sm text-slate-600">Run-level execution records participating in this federated workflow.</p>
                </div>
                <Badge tone={runs.length > 0 ? "info" : "neutral"}>{runs.length}</Badge>
              </div>
            </div>
            <DataTable
              data={runs}
              emptyMessage="No runs matched this workflow federation view."
              columns={[
                { key: "id", header: "ID", render: (row) => <Link href={`/runs/${row.id}`} className="font-mono text-xs text-accent">{row.id}</Link> },
                { key: "status", header: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status}</Badge> },
                { key: "step", header: "Current Step", render: (row) => row.current_step },
                {
                  key: "federation",
                  header: "Federation",
                  render: (row) => `${row.federated_projection_count} projection${row.federated_projection_count === 1 ? "" : "s"} • ${row.federated_conflict_count} conflict${row.federated_conflict_count === 1 ? "" : "s"}`
                },
                { key: "updated", header: "Updated", render: (row) => formatDate(row.updated_at) }
              ]}
            />
          </div>
        </div>
      </div>
    </PageShell>
  );
}
