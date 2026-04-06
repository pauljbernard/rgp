import { getRequest, getRequestKnowledgeContext, getRoutingRecommendation, listRequestAgentIntegrations, listRequestProjections } from "@/lib/server-api";
import type { RequestStatus } from "@rgp/domain";
import { Badge, Button, EntityHeader, KeyValueGrid, PageShell, SectionHeading, Tabs, appShellProps, statusTone } from "../../../components/ui-helpers";
import { RefreshOnCheckRunEvents } from "../../../components/refresh-on-check-run-events";
import { assignAgentSessionAction, cancelRequestAction, cloneRequestAction, runRequestChecksAction, submitRequestAction, transitionRequestAction } from "./actions";

export default async function RequestDetailPage({
  params,
  searchParams
}: {
  params: Promise<{ requestId: string }>;
  searchParams: Promise<{ error?: string }>;
}) {
  const { requestId } = await params;
  const resolvedSearchParams = await searchParams;
  const errorMessage = typeof resolvedSearchParams.error === "string" && resolvedSearchParams.error ? resolvedSearchParams.error : "";
  const [data, integrations, projections, knowledge, routingRecommendation] = await Promise.all([
    getRequest(requestId),
    listRequestAgentIntegrations(requestId),
    listRequestProjections(requestId),
    getRequestKnowledgeContext(requestId, 4),
    getRoutingRecommendation(requestId)
  ]);
  const request = data.request;
  const agentIntegrations = integrations.filter((item) => item.supports_direct_assignment && item.supports_interactive_sessions);
  const canSubmit = ["draft", "changes_requested", "validation_failed", "awaiting_input"].includes(request.status);
  const canCancel = !["canceled", "completed", "archived"].includes(request.status);
  const transitionOptions: Partial<Record<RequestStatus, RequestStatus[]>> = {
    submitted: ["validated", "validation_failed"],
    validated: ["classified"],
    classified: ["ownership_resolved"],
    ownership_resolved: ["planned"],
    planned: ["queued"],
    queued: ["in_execution", "failed"],
    in_execution: ["awaiting_input", "awaiting_review", "failed"],
    awaiting_review: ["under_review", "changes_requested", "approved"],
    under_review: ["changes_requested", "approved", "rejected"],
    approved: ["promotion_pending", "completed"],
    promotion_pending: ["promoted", "failed"],
    promoted: ["completed"],
    failed: ["planned"]
  };
  const availableTransitions = transitionOptions[request.status] ?? [];
  const hasPendingChecks = data.check_runs.some((item) => item.status === "queued" || item.status === "running");

  return (
    <PageShell
      {...appShellProps("/requests", "Request Detail", "Canonical control plane for a single governed request.")}
      contextPanel={
        <div className="space-y-4">
          <SectionHeading title="Next Action" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">{data.next_required_action}</div>
          <SectionHeading title="Blockers" />
          <div className="space-y-2">
            {(data.active_blockers.length ? data.active_blockers : ["No active blockers."]).map((blocker) => (
              <div key={blocker} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-600">
                {blocker}
              </div>
            ))}
          </div>
        </div>
      }
    >
      <RefreshOnCheckRunEvents requestId={request.id} active={hasPendingChecks} />
      <div className="space-y-4">
        {errorMessage ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {errorMessage}
          </div>
        ) : null}
        <EntityHeader
          id={request.id}
          title={request.title}
          status={<Badge tone={statusTone(request.status)}>{request.status}</Badge>}
          ownership={request.owner_team_id ?? "Unassigned"}
          blocking={data.active_blockers[0]}
          primaryActions={
            <>
              <form action={cloneRequestAction}>
                <input type="hidden" name="requestId" value={request.id} />
                <Button label="Clone Request" tone="secondary" type="submit" />
              </form>
              <form action={cancelRequestAction}>
                <input type="hidden" name="requestId" value={request.id} />
                <Button label="Cancel Request" tone="danger" type="submit" disabled={!canCancel} />
              </form>
              <form action={submitRequestAction}>
                <input type="hidden" name="requestId" value={request.id} />
                <Button label="Submit Request" tone="primary" type="submit" disabled={!canSubmit} />
              </form>
            </>
          }
        />
        <Tabs
          activeKey="overview"
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
            <SectionHeading title="Overview" />
            <KeyValueGrid
              items={[
                { label: "Request Type", value: request.request_type },
                { label: "Template", value: `${request.template_id}@${request.template_version}` },
                { label: "Priority", value: request.priority },
                { label: "Status", value: request.status },
                { label: "Latest Run", value: data.latest_run_id ?? "None" },
                { label: "Latest Artifacts", value: data.latest_artifact_ids.join(", ") || "None" },
                {
                  label: "Predecessors",
                  value: data.predecessors.length
                    ? data.predecessors.map((item) => `${item.request_id} (${item.relationship_type})`).join(", ")
                    : "None"
                },
                {
                  label: "Successors",
                  value: data.successors.length
                    ? data.successors.map((item) => `${item.request_id} (${item.relationship_type})`).join(", ")
                    : "None"
                }
              ]}
            />
          </div>
          <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
            <SectionHeading title="Current Status" />
            <div className="text-sm text-slate-600">{request.summary}</div>
            <SectionHeading title="Lifecycle Actions" />
            <div className="flex flex-wrap gap-2">
              <form action={runRequestChecksAction}>
                <input type="hidden" name="requestId" value={request.id} />
                <Button label="Run Checks" tone="secondary" type="submit" />
              </form>
              {availableTransitions.length ? (
                availableTransitions.map((targetStatus: RequestStatus) => (
                  <form key={targetStatus} action={transitionRequestAction}>
                    <input type="hidden" name="requestId" value={request.id} />
                    <input type="hidden" name="targetStatus" value={targetStatus} />
                    <Button label={targetStatus.replaceAll("_", " ")} tone="secondary" type="submit" />
                  </form>
                ))
              ) : (
                <div className="text-sm text-slate-500">No additional lifecycle transitions available from the current status.</div>
              )}
            </div>
            <SectionHeading title="Active Blockers" />
            <div className="space-y-2">
              {(data.active_blockers.length ? data.active_blockers : ["No active blockers"]).map((item) => (
                <div key={item} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {item}
                </div>
              ))}
            </div>
            <SectionHeading title="Request Checks" />
            <div className="space-y-2">
              {(data.check_results.length ? data.check_results : []).map((item) => (
                <div key={item.id} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  <div className="font-medium">{item.name}: {item.state}</div>
                  <div className="text-slate-600">{item.detail}</div>
                </div>
              ))}
              {!data.check_results.length ? <div className="text-sm text-slate-500">No request checks recorded yet.</div> : null}
            </div>
            <SectionHeading title="Check Runs" />
            <div className="space-y-2">
              {(data.check_runs.length ? data.check_runs : []).map((item) => (
                <div key={item.id} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  <div className="font-medium">{item.scope} checks: {item.status}</div>
                  <div className="text-slate-600">{item.trigger_reason}</div>
                </div>
              ))}
              {!data.check_runs.length ? <div className="text-sm text-slate-500">No check runs queued yet.</div> : null}
            </div>
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
              {!data.agent_sessions.length ? <div className="text-sm text-slate-500">No interactive agent sessions assigned yet.</div> : null}
            </div>
            <SectionHeading title="Governed Knowledge" />
            <div className="space-y-2">
              {knowledge.map((artifact) => (
                <a
                  key={artifact.id}
                  href={`/knowledge/${artifact.id}`}
                  className="block rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700"
                >
                  <div className="font-medium">{artifact.name}</div>
                  <div className="mt-1 text-slate-600">{artifact.description || "Published governed knowledge artifact."}</div>
                  <div className="mt-2 text-xs text-slate-500">
                    v{artifact.version} · {artifact.tags?.length ? artifact.tags.join(", ") : "no tags"}
                  </div>
                </a>
              ))}
              {!knowledge.length ? <div className="text-sm text-slate-500">No governed knowledge suggestions were retrieved for this request.</div> : null}
            </div>
            <SectionHeading title="Routing Recommendation" />
            <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
              <div className="font-medium text-slate-900">
                {routingRecommendation.recommended_group_name ?? "No assignment group recommendation"}
              </div>
              <div className="mt-1 text-slate-600">SLA status: {routingRecommendation.sla_status}</div>
              <div className="mt-1 text-slate-600">
                Matched skills: {routingRecommendation.matched_skills.length ? routingRecommendation.matched_skills.join(", ") : "none"}
              </div>
              <div className="mt-1 text-slate-600">
                Basis: {routingRecommendation.route_basis.length ? routingRecommendation.route_basis.join(" · ") : "no basis recorded"}
              </div>
              {routingRecommendation.escalation_targets.length ? (
                <div className="mt-2 text-xs text-amber-700">
                  Escalations: {routingRecommendation.escalation_targets.join(", ")}
                </div>
              ) : null}
            </div>
            <SectionHeading title="Federated Projections" />
            <div className="space-y-2">
              {projections.map((projection) => (
                <div key={projection.id} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium">{projection.external_system}</div>
                    <Badge tone={projection.conflicts.length ? "warning" : statusTone("completed")}>
                      {projection.conflicts.length ? `${projection.conflicts.length} conflict${projection.conflicts.length === 1 ? "" : "s"}` : projection.projection_status}
                    </Badge>
                  </div>
                  <div className="mt-1 text-slate-600">
                    {projection.external_ref ?? "No external reference recorded"}
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    Adapter {projection.adapter_type ?? "unknown"} via {projection.sync_source ?? "unspecified source"}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">
                    Capabilities {(projection.adapter_capabilities.length ? projection.adapter_capabilities.join(", ") : "none declared")}
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    Last sync {projection.last_synced_at ? new Date(projection.last_synced_at).toLocaleString() : "not yet synced"}
                  </div>
                  <div className="mt-2">
                    <a href={`/requests/${request.id}/projections/${projection.id}`} className="text-xs font-medium text-accent">
                      Open projection drilldown
                    </a>
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
              ))}
              {!projections.length ? <div className="text-sm text-slate-500">No federated projections are currently bound to this request.</div> : null}
            </div>
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
