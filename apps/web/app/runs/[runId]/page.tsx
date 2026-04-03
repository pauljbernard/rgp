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
