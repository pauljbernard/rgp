import { getRequest, listRequestAgentIntegrations } from "@/lib/server-api";
import { Badge, Button, KeyValueGrid, PageShell, SectionHeading, Tabs, appShellProps, statusTone } from "../../../../components/ui-helpers";
import { assignAgentSessionAction } from "../actions";

export default async function RequestAgentsPage({
  params,
  searchParams
}: {
  params: Promise<{ requestId: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { requestId } = await params;
  const resolvedSearchParams = await searchParams;
  const errorMessage = typeof resolvedSearchParams.error === "string" && resolvedSearchParams.error ? resolvedSearchParams.error : "";
  const [data, integrations] = await Promise.all([getRequest(requestId), listRequestAgentIntegrations(requestId)]);
  const request = data.request;
  const agentIntegrations = integrations.filter((item) => item.supports_direct_assignment && item.supports_interactive_sessions);

  return (
    <PageShell
      {...appShellProps("/requests", "Request Agents", "Native interactive agent sessions attached directly to the governed request.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Request Context" />
          <KeyValueGrid
            items={[
              { label: "Request", value: request.id },
              { label: "Title", value: request.title },
              { label: "Status", value: <Badge tone={statusTone(request.status)}>{request.status}</Badge> },
              { label: "Owner", value: request.owner_team_id ?? "Unassigned" }
            ]}
          />
        </div>
      }
    >
      <div className="space-y-4">
        {errorMessage ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {errorMessage}
          </div>
        ) : null}
        <Tabs
          activeKey="agents"
          tabs={[
            { key: "overview", label: "Overview", href: `/requests/${request.id}` },
            { key: "runs", label: "Runs", href: request.current_run_id ? `/runs/${request.current_run_id}` : "/runs" },
            { key: "artifacts", label: "Artifacts", href: data.latest_artifact_ids[0] ? `/artifacts/${data.latest_artifact_ids[0]}` : "/artifacts" },
            { key: "reviews", label: "Reviews", href: "/reviews/queue" },
            { key: "agents", label: "Agents", href: `/requests/${request.id}/agents` },
            { key: "history", label: "History", href: `/requests/${request.id}/history` }
          ]}
        />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <SectionHeading title="Agent Sessions" />
            <div className="space-y-2">
              {data.agent_sessions.map((session) => (
                <a
                  key={session.id}
                  href={`/requests/${request.id}/agents/${session.id}`}
                  className="block rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">{session.agent_label}</div>
                    <Badge tone={statusTone(session.status)}>{session.status}</Badge>
                  </div>
                  <div className="mt-1 text-slate-600">{session.summary}</div>
                  <div className="mt-2 text-xs text-slate-500">
                    {session.integration_name} · {session.message_count} messages · {session.awaiting_human ? "awaiting human" : "agent active"}
                  </div>
                </a>
              ))}
              {!data.agent_sessions.length ? (
                <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-500">
                  No interactive agent sessions assigned yet.
                </div>
              ) : null}
            </div>
          </div>
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <SectionHeading title="Assign to Agent" />
            <form action={assignAgentSessionAction} className="space-y-3 rounded-lg border border-chrome bg-slate-50 p-4">
              <input type="hidden" name="requestId" value={request.id} />
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Agent Integration</span>
                <select name="integrationId" className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700">
                  {agentIntegrations.map((integration) => (
                    <option key={integration.id} value={integration.id}>
                      {integration.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Agent Label</span>
                <input
                  name="agentLabel"
                  defaultValue={request.title}
                  className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700"
                />
              </label>
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Initial Prompt</span>
                <textarea
                  name="initialPrompt"
                  rows={4}
                  defaultValue={`Work this governed request interactively. Request: ${request.title}. Summary: ${request.summary}.`}
                  className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700"
                />
              </label>
              <Button label="Assign Agent Session" tone="secondary" type="submit" disabled={!agentIntegrations.length} />
            </form>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
