import { getRun } from "@/lib/server-api";
import Link from "next/link";
import { Badge, Button, ConversationDock, DataTable, EntityHeader, KeyValueGrid, PageShell, Timeline, appShellProps, statusTone } from "../../../components/ui-helpers";
import { commandRunAction } from "./actions";

export default async function RunDetailPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const run = await getRun(runId);

  return (
    <PageShell {...appShellProps("/runs", "Run Detail", "Execution monitoring and intervention surface.")}>
      <div className="space-y-4">
        <EntityHeader
          id={run.id}
          title={run.workflow}
          status={<Badge tone={statusTone(run.status)}>{run.status}</Badge>}
          ownership={run.owner_team}
          blocking={run.waiting_reason ?? run.failure_reason ?? undefined}
          primaryActions={
            <>
              <Link href={`/runs/${run.id}/history`} className="rounded-md px-4 py-2 text-sm font-semibold bg-slate-100 text-slate-800">
                History
              </Link>
              {run.command_surface.map((action) => (
                <form key={action} action={commandRunAction}>
                  <input type="hidden" name="runId" value={run.id} />
                  <input type="hidden" name="command" value={action} />
                  <Button label={action} tone={action === "Cancel Run" ? "danger" : action === "Resume" || action === "Retry Step" ? "primary" : "secondary"} type="submit" />
                </form>
              ))}
            </>
          }
        />
        <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)_320px]">
          <Timeline steps={run.steps} currentStepId={run.steps.find((step) => step.name === run.current_step)?.id ?? run.steps[0].id} />
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <KeyValueGrid
              items={[
                { label: "Request", value: <Link href={`/requests/${run.request_id}`} className="text-accent">{run.request_id}</Link> },
                { label: "Workflow Identity", value: run.workflow_identity },
                { label: "Progress", value: `${run.progress_percent}%` },
                { label: "Current Step", value: run.current_step }
              ]}
            />
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Current Step Input</div>
              <div className="mt-2 text-sm text-slate-700">{run.current_step_input_summary}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 p-4">
              <div className="text-xs font-medium text-slate-500">Current Step Output</div>
              <div className="mt-2 text-sm text-slate-700">{run.current_step_output_summary}</div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
              <div className="text-xs font-medium text-slate-500">Run Context</div>
              <div className="mt-4 space-y-2">
                {run.run_context.map(([label, value]) => (
                  <div key={label} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm">
                    <div className="font-medium">{label}</div>
                    <div className="text-slate-600">{value}</div>
                  </div>
                ))}
              </div>
            </div>
            <DataTable
              data={run.runtime_dispatches}
              emptyMessage="No runtime dispatches recorded."
              columns={[
                { key: "time", header: "Dispatched At", render: (row) => new Date(row.dispatched_at).toLocaleString() },
                { key: "type", header: "Type", render: (row) => row.dispatch_type },
                { key: "status", header: "Status", render: (row) => row.status },
                { key: "integration", header: "Integration", render: (row) => row.integration_id },
                { key: "reference", header: "External Ref", render: (row) => row.external_reference ?? "None" },
                { key: "detail", header: "Detail", render: (row) => row.detail }
              ]}
            />
            <DataTable
              data={run.runtime_signals}
              emptyMessage="No runtime signals recorded."
              columns={[
                { key: "time", header: "Received At", render: (row) => new Date(row.received_at).toLocaleString() },
                { key: "event", header: "Event ID", render: (row) => row.event_id },
                { key: "source", header: "Source", render: (row) => row.source },
                { key: "status", header: "Status", render: (row) => row.status },
                { key: "step", header: "Current Step", render: (row) => row.current_step ?? "None" },
                { key: "detail", header: "Detail", render: (row) => row.detail }
              ]}
            />
            <div className="rounded-xl border border-chrome bg-panel p-5 shadow-panel">
              <div className="text-xs font-medium text-slate-500">Federated Execution</div>
              <div className="mt-4 space-y-3">
                {run.federated_projections.length ? (
                  run.federated_projections.map((projection) => (
                    <div key={projection.id} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-medium text-slate-900">{projection.external_system}</div>
                        <Badge tone={projection.conflicts.length ? "warning" : statusTone("completed")}>
                          {projection.conflicts.length ? `${projection.conflicts.length} conflict${projection.conflicts.length === 1 ? "" : "s"}` : projection.projection_status}
                        </Badge>
                      </div>
                      <div className="mt-1 text-slate-600">{projection.external_ref ?? "No external reference recorded"}</div>
                      <div className="mt-2 text-xs text-slate-500">
                        Adapter {projection.adapter_type ?? "unknown"} via {projection.sync_source ?? "unspecified source"}
                      </div>
                      <div className="mt-1 text-xs text-slate-500">
                        Capabilities {projection.adapter_capabilities.length ? projection.adapter_capabilities.join(", ") : "none declared"}
                      </div>
                      <div className="mt-2">
                        <Link href={`/requests/${run.request_id}/projections/${projection.id}`} className="text-xs font-medium text-accent">
                          Open projection drilldown
                        </Link>
                      </div>
                      {projection.conflicts.length ? (
                        <div className="mt-2 space-y-1 text-xs text-amber-700">
                          {projection.conflicts.map((conflict) => (
                            <div key={`${projection.id}-${String(conflict.field)}`}>
                              {String(conflict.field)}: canonical {String(conflict.internal)} / external {String(conflict.external)}
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    No federated projections are currently linked to this run's request.
                  </div>
                )}
              </div>
            </div>
            <ConversationDock
              title="Conversation Dock"
              messages={[
                { actor: "system", text: "Run waiting for reviewer decision." },
                { actor: "operator", text: "Monitoring for escalation and retry conditions." }
              ]}
            />
          </div>
        </div>
      </div>
    </PageShell>
  );
}
