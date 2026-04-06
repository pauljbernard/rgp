import { getRequest, getRequestAgentAssignmentPreview, listRequestAgentIntegrations } from "@/lib/server-api";
import { Badge, Button, KeyValueGrid, PageShell, SectionHeading, Tabs, appShellProps, statusTone } from "../../../../components/ui-helpers";
import { assignAgentSessionAction } from "../actions";

function bundleKnowledgeEntries(bundle: { contents?: Record<string, unknown> | null } | null) {
  const raw = bundle?.contents && typeof bundle.contents === "object"
    ? (bundle.contents as Record<string, unknown>).knowledge_context
    : null;
  return Array.isArray(raw) ? raw.filter((item): item is Record<string, unknown> => !!item && typeof item === "object") : [];
}

export default async function RequestAgentsPage({
  params,
  searchParams
}: {
  params: Promise<{ requestId: string }>;
  searchParams: Promise<{ error?: string; integration?: string; collaboration_mode?: string; agent_operating_profile?: string }>;
}) {
  const { requestId } = await params;
  const resolvedSearchParams = await searchParams;
  const errorMessage = typeof resolvedSearchParams.error === "string" && resolvedSearchParams.error ? resolvedSearchParams.error : "";
  const [data, integrations] = await Promise.all([getRequest(requestId), listRequestAgentIntegrations(requestId)]);
  const request = data.request;
  const agentIntegrations = integrations.filter((item) => item.supports_direct_assignment && item.supports_interactive_sessions);
  const selectedCollaborationMode =
    typeof resolvedSearchParams.collaboration_mode === "string" && resolvedSearchParams.collaboration_mode
      ? resolvedSearchParams.collaboration_mode
      : "agent_assisted";
  const selectedOperatingProfile =
    typeof resolvedSearchParams.agent_operating_profile === "string" && resolvedSearchParams.agent_operating_profile
      ? resolvedSearchParams.agent_operating_profile
      : "general";
  const selectedIntegrationId =
    typeof resolvedSearchParams.integration === "string" && agentIntegrations.some((item) => item.id === resolvedSearchParams.integration)
      ? resolvedSearchParams.integration
      : agentIntegrations[0]?.id;
  const selectedIntegration = agentIntegrations.find((item) => item.id === selectedIntegrationId) ?? null;
  const assignmentPreview = selectedIntegrationId
    ? await getRequestAgentAssignmentPreview(requestId, selectedIntegrationId, {
        collaboration_mode: selectedCollaborationMode,
        agent_operating_profile: selectedOperatingProfile,
      })
    : null;
  const previewKnowledge = bundleKnowledgeEntries(assignmentPreview?.bundle ?? null);

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
            <form action="GET" className="space-y-3 rounded-lg border border-chrome bg-slate-50 p-4">
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Preview Integration</span>
                <select
                  name="integration"
                  defaultValue={selectedIntegrationId}
                  className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700"
                >
                  {agentIntegrations.map((integration) => (
                    <option key={integration.id} value={integration.id}>
                      {integration.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Collaboration Mode</span>
                <select
                  name="collaboration_mode"
                  defaultValue={selectedCollaborationMode}
                  className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700"
                >
                  <option value="human_led">Human-Led</option>
                  <option value="agent_assisted">Agent-Assisted</option>
                  <option value="agent_led">Agent-Led</option>
                </select>
              </label>
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Agent Operating Profile</span>
                <select
                  name="agent_operating_profile"
                  defaultValue={selectedOperatingProfile}
                  className="w-full rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700"
                >
                  <option value="general">General</option>
                  <option value="review">Review</option>
                  <option value="editorial">Editorial</option>
                  <option value="execution">Execution</option>
                </select>
              </label>
              <Button label="Refresh Preview" tone="secondary" type="submit" disabled={!agentIntegrations.length} />
            </form>
            <form action={assignAgentSessionAction} className="space-y-3 rounded-lg border border-chrome bg-slate-50 p-4">
              <input type="hidden" name="requestId" value={request.id} />
              <input type="hidden" name="integrationId" value={selectedIntegrationId ?? ""} />
              <input type="hidden" name="collaborationMode" value={selectedCollaborationMode} />
              <input type="hidden" name="agentOperatingProfile" value={selectedOperatingProfile} />
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Agent Integration</span>
                <div className="rounded-lg border border-chrome bg-white px-3 py-2 text-sm text-slate-700">
                  {selectedIntegration ? `${selectedIntegration.name} (${selectedIntegration.provider ?? "provider unspecified"})` : "No interactive integrations available"}
                </div>
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
            <div className="space-y-3 rounded-lg border border-chrome bg-slate-50 p-4">
              <SectionHeading title="Governed Assignment Preview" />
              {assignmentPreview ? (
                <>
                  <div className="rounded-lg border border-chrome bg-white px-4 py-3 text-sm text-slate-700">
                    <div className="font-medium text-slate-900">{assignmentPreview.bundle.bundle_type}</div>
                    <div className="mt-2 text-slate-600">
                      Context keys: {Object.keys((assignmentPreview.bundle.contents ?? {}) as Record<string, unknown>).join(", ")}
                    </div>
                    <div className="mt-2 text-slate-600">
                      Policy scope: {assignmentPreview.bundle.policy_scope ? JSON.stringify(assignmentPreview.bundle.policy_scope) : "No explicit scope"}
                    </div>
                    <div className="mt-2 text-slate-600">
                      Mode: {selectedCollaborationMode} · Profile: {selectedOperatingProfile}
                    </div>
                    <div className="mt-2 text-slate-600">
                      Governed knowledge attached: {previewKnowledge.length}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <SectionHeading title="Reusable Governed Knowledge" />
                    {previewKnowledge.length ? (
                      previewKnowledge.map((entry) => (
                        <div key={String(entry.artifact_id ?? entry.name)} className="rounded-lg border border-chrome bg-white px-4 py-3 text-sm text-slate-700">
                          <div className="font-medium text-slate-900">{String(entry.name ?? entry.artifact_id ?? "Knowledge Artifact")}</div>
                          {entry.description ? <div className="mt-1 text-slate-600">{String(entry.description)}</div> : null}
                          <div className="mt-2 text-xs text-slate-500">
                            v{String(entry.version ?? "—")} · {String(entry.content_type ?? "content")}
                            {Array.isArray(entry.tags) && entry.tags.length ? ` · ${entry.tags.join(", ")}` : ""}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-lg border border-chrome bg-white px-4 py-3 text-sm text-slate-600">
                        No published governed knowledge artifacts are currently attached to this assignment preview.
                      </div>
                    )}
                  </div>
                  {assignmentPreview.capability_warnings.length ? (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                      {assignmentPreview.capability_warnings.join(" ")}
                    </div>
                  ) : null}
                  <div className="space-y-2">
                    {assignmentPreview.available_tools.length ? (
                      assignmentPreview.available_tools.map((tool) => (
                        <div key={tool.name} className="rounded-lg border border-chrome bg-white px-4 py-3 text-sm text-slate-700">
                          <div className="flex items-center justify-between gap-3">
                            <div className="font-medium text-slate-900">{tool.name}</div>
                            <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800">Available</span>
                          </div>
                          <div className="mt-1 text-slate-600">{tool.description}</div>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-lg border border-chrome bg-white px-4 py-3 text-sm text-slate-600">
                        No MCP capabilities are currently available for the selected integration.
                      </div>
                    )}
                    {assignmentPreview.degraded_tools.map((tool) => (
                      <div key={tool.name} className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                        <div className="flex items-center justify-between gap-3">
                          <div className="font-medium">{tool.name}</div>
                          <span className="rounded-full bg-amber-200 px-2 py-1 text-xs font-medium text-amber-900">Degraded</span>
                        </div>
                        <div className="mt-1">{tool.description}</div>
                        {tool.availability_reason ? <div className="mt-2 text-xs">{tool.availability_reason}</div> : null}
                      </div>
                    ))}
                    {assignmentPreview.restricted_tools.map((tool) => (
                      <div key={tool.name} className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900">
                        <div className="flex items-center justify-between gap-3">
                          <div className="font-medium">{tool.name}</div>
                          <span className="rounded-full bg-rose-200 px-2 py-1 text-xs font-medium text-rose-900">Restricted</span>
                        </div>
                        <div className="mt-1">{tool.description}</div>
                        {tool.availability_reason ? <div className="mt-2 text-xs">{tool.availability_reason}</div> : null}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="rounded-lg border border-chrome bg-white px-4 py-3 text-sm text-slate-600">
                  No governed assignment preview is available because there are no interactive integrations for this request.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
