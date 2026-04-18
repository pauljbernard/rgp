"use client";

import { useEffect, useMemo, useState } from "react";
import type { AgentSessionContextDetail, AgentSessionDetail } from "@rgp/domain";
import { Badge, Button, KeyValueGrid, SectionHeading, Tabs, statusTone } from "../../../../../components/ui-helpers";
import {
  approveAgentSessionCheckpointAction,
  completeAgentSessionAction,
  importAgentSessionArtifactAction,
  postAgentSessionMessageAction,
  resumeAgentSessionRuntimeAction,
  updateAgentSessionGovernanceAction
} from "./actions";

function bundleKnowledgeEntries(bundle: { contents?: Record<string, unknown> | null } | null) {
  const raw = bundle?.contents && typeof bundle.contents === "object"
    ? (bundle.contents as Record<string, unknown>).knowledge_context
    : null;
  return Array.isArray(raw) ? raw.filter((item): item is Record<string, unknown> => !!item && typeof item === "object") : [];
}

function bundleRuntimeEntries(bundle: { contents?: Record<string, unknown> | null } | null, key: string) {
  const raw = bundle?.contents && typeof bundle.contents === "object"
    ? (bundle.contents as Record<string, unknown>)[key]
    : null;
  return Array.isArray(raw) ? raw.filter((item): item is Record<string, unknown> => !!item && typeof item === "object") : [];
}

function bundleRuntimeMap(bundle: { contents?: Record<string, unknown> | null } | null, key: string) {
  const raw = bundle?.contents && typeof bundle.contents === "object"
    ? (bundle.contents as Record<string, unknown>)[key]
    : null;
  return raw && typeof raw === "object" && !Array.isArray(raw) ? raw as Record<string, unknown> : {};
}

export function AgentSessionLiveView({
  requestId,
  initialSession,
  initialContext,
}: {
  requestId: string;
  initialSession: AgentSessionDetail;
  initialContext: AgentSessionContextDetail;
}) {
  const [session, setSession] = useState(initialSession);
  const [sessionContext, setSessionContext] = useState(initialContext);
  const [streamError, setStreamError] = useState("");

  useEffect(() => {
    setSession(initialSession);
    setSessionContext(initialContext);
    setStreamError("");
  }, [initialContext, initialSession]);

  useEffect(() => {
    if (session.status !== "streaming") {
      return;
    }
    const source = new EventSource(`/requests/${requestId}/agents/${session.id}/stream`);

    source.addEventListener("snapshot", (event) => {
      const payload = JSON.parse((event as MessageEvent).data) as AgentSessionDetail;
      setSession(payload);
    });

    source.addEventListener("delta", (event) => {
      const payload = JSON.parse((event as MessageEvent).data) as {
        message_id: string;
        body: string;
        done: boolean;
      };
      setSession((current) => ({
        ...current,
        messages: current.messages.map((message) =>
          message.id === payload.message_id ? { ...message, body: payload.body } : message
        ),
        latest_message:
          current.latest_message?.id === payload.message_id
            ? { ...current.latest_message, body: payload.body }
            : current.latest_message,
      }));
    });

    source.addEventListener("done", (event) => {
      const payload = JSON.parse((event as MessageEvent).data) as AgentSessionDetail;
      setSession(payload);
      source.close();
    });

    source.addEventListener("error", (event) => {
      const payload = (() => {
        try {
          return JSON.parse((event as MessageEvent).data);
        } catch {
          return null;
        }
      })() as { message?: string } | null;
      setStreamError(payload?.message ?? "Agent stream failed.");
      source.close();
    });

    return () => {
      source.close();
    };
  }, [requestId, session.id, session.status]);

  const latestAgentMessage = useMemo(
    () => [...session.messages].reverse().find((message) => message.sender_type === "agent"),
    [session.messages]
  );
  const latestHumanMessage = useMemo(
    () => [...session.messages].reverse().find((message) => message.sender_type === "human"),
    [session.messages]
  );
  const attachedKnowledge = useMemo(() => bundleKnowledgeEntries(sessionContext.bundle), [sessionContext.bundle]);
  const governedRuntime = useMemo(() => bundleRuntimeMap(sessionContext.bundle, "sbcl_agent_runtime"), [sessionContext.bundle]);
  const runtimeApprovals = useMemo(() => bundleRuntimeEntries(sessionContext.bundle, "sbcl_agent_approvals"), [sessionContext.bundle]);
  const runtimeArtifacts = useMemo(() => bundleRuntimeEntries(sessionContext.bundle, "sbcl_agent_artifacts"), [sessionContext.bundle]);
  const isGovernedRuntime = session.runtime_subtype === "sbcl_agent";

  return (
    <div className="space-y-4">
      <Tabs
        activeKey="agents"
        tabs={[
          { key: "overview", label: "Overview", href: `/requests/${requestId}` },
          { key: "agents", label: "Agents", href: `/requests/${requestId}/agents` },
          { key: "history", label: "History", href: `/requests/${requestId}/history` }
        ]}
      />
      {streamError ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {streamError}
        </div>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <SectionHeading title="Current State" />
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Session Status</div>
              <div className="mt-2"><Badge tone={statusTone(session.status)}>{session.status}</Badge></div>
              <div className="mt-2 text-slate-600">{session.summary}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">What Happens Next</div>
              <div className="mt-2 text-slate-600">
                {session.status === "streaming"
                  ? "The agent is actively generating a response now."
                  : session.awaiting_human
                    ? "The human needs to respond to the agent before the session can continue."
                    : "The agent is active and may produce another turn without waiting on human input."}
              </div>
            </div>
          </div>
          {latestAgentMessage ? (
            <>
              <SectionHeading title="Current Agent Response" />
              <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                <div className="whitespace-pre-wrap">{latestAgentMessage.body || "Streaming response..."}</div>
              </div>
            </>
          ) : null}
          <SectionHeading title="Governed Context" />
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Context Bundle</div>
              <div className="mt-2 font-medium text-slate-900">{sessionContext.bundle.id}</div>
              <div className="mt-2 text-slate-600">Version {sessionContext.bundle.version} • {sessionContext.bundle.bundle_type}</div>
              <div className="mt-2 text-slate-600">Assembled by {sessionContext.bundle.assembled_by}</div>
            </div>
            <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Bundle Coverage</div>
              <div className="mt-2 text-slate-600">
                {Object.keys((sessionContext.bundle.contents ?? {}) as Record<string, unknown>).join(", ") || "No governed context keys available."}
              </div>
            </div>
          </div>
          {isGovernedRuntime ? (
            <>
              <SectionHeading title="Governed Runtime" />
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                  <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Environment</div>
                  <div className="mt-2 break-all font-medium text-slate-900">
                    {session.governed_runtime?.environment_ref ?? session.external_session_ref ?? "Not bound"}
                  </div>
                </div>
                <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                  <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Thread</div>
                  <div className="mt-2 break-all font-medium text-slate-900">
                    {session.governed_runtime?.thread_ref ?? String(governedRuntime.thread_ref ?? "Unavailable")}
                  </div>
                </div>
                <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                  <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Pending Approvals</div>
                  <div className="mt-2 text-2xl font-semibold text-slate-900">
                    {session.governed_runtime?.pending_approval_count ?? runtimeApprovals.length}
                  </div>
                </div>
                <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                  <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Pending Artifacts</div>
                  <div className="mt-2 text-2xl font-semibold text-slate-900">
                    {session.governed_runtime?.pending_artifact_count ?? runtimeArtifacts.length}
                  </div>
                </div>
              </div>
            </>
          ) : null}
          <div className="space-y-2">
            <SectionHeading title="Reusable Governed Knowledge" />
            {attachedKnowledge.length ? (
              attachedKnowledge.map((entry) => (
                <div key={String(entry.artifact_id ?? entry.name)} className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                  <div className="font-medium text-slate-900">{String(entry.name ?? entry.artifact_id ?? "Knowledge Artifact")}</div>
                  {entry.description ? <div className="mt-1 text-slate-600">{String(entry.description)}</div> : null}
                  <div className="mt-2 text-xs text-slate-500">
                    v{String(entry.version ?? "—")} · {String(entry.content_type ?? "content")}
                    {Array.isArray(entry.tags) && entry.tags.length ? ` · ${entry.tags.join(", ")}` : ""}
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-600">
                No published governed knowledge artifacts are attached to this session yet.
              </div>
            )}
          </div>
          {isGovernedRuntime ? (
            <>
              <SectionHeading title="Runtime Approval Checkpoints" />
              <div className="space-y-3">
                {runtimeApprovals.length ? (
                  runtimeApprovals.map((approval) => {
                    const workItemId = String(approval.id ?? approval.work_item_id ?? "work-item");
                    return (
                      <div key={workItemId} className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">
                        <div className="flex items-center justify-between gap-3">
                          <div className="font-medium">{String(approval.title ?? workItemId)}</div>
                          <Badge tone="warning">{String(approval.status ?? approval.wait_reason ?? "pending")}</Badge>
                        </div>
                        <div className="mt-2 text-amber-900">
                          {String(approval.wait_reason ?? approval.summary ?? approval.prompt ?? "Awaiting governed runtime action.")}
                        </div>
                        <div className="mt-3 grid gap-3 lg:grid-cols-2">
                          <form action={approveAgentSessionCheckpointAction} className="space-y-3 rounded-lg border border-amber-300 bg-white p-3">
                            <input type="hidden" name="requestId" value={requestId} />
                            <input type="hidden" name="sessionId" value={session.id} />
                            <input type="hidden" name="workItemId" value={workItemId} />
                            <label className="block space-y-1 text-sm text-slate-700">
                              <span className="block text-xs font-medium text-slate-500">Approval Policy</span>
                              <input
                                name="policy"
                                defaultValue="process-run"
                                className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700"
                              />
                            </label>
                            <Button label="Approve Checkpoint" tone="primary" type="submit" />
                          </form>
                          <form action={resumeAgentSessionRuntimeAction} className="space-y-3 rounded-lg border border-amber-300 bg-white p-3">
                            <input type="hidden" name="requestId" value={requestId} />
                            <input type="hidden" name="sessionId" value={session.id} />
                            <input type="hidden" name="workItemId" value={workItemId} />
                            <label className="block space-y-1 text-sm text-slate-700">
                              <span className="block text-xs font-medium text-slate-500">Resume Note</span>
                              <input
                                name="note"
                                placeholder="Optional note for the governed runtime."
                                className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700"
                              />
                            </label>
                            <Button label="Resume Runtime" tone="secondary" type="submit" />
                          </form>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-600">
                    No governed runtime approvals are currently pending.
                  </div>
                )}
              </div>

              <SectionHeading title="Importable Runtime Artifacts" />
              <div className="space-y-3">
                {runtimeArtifacts.length ? (
                  runtimeArtifacts.map((artifact) => {
                    const artifactKey = String(artifact.artifact_key ?? artifact.id ?? artifact.path ?? "runtime-artifact");
                    const title = String(artifact.title ?? artifact.name ?? artifact.path ?? artifactKey);
                    const summary = String(artifact.summary ?? artifact.description ?? "Imported from governed sbcl-agent runtime");
                    const sourceRef = String(artifact.source_ref ?? artifact.id ?? artifact.path ?? artifactKey);
                    const pathValue = artifact.path ? String(artifact.path) : "";
                    const artifactType = String(artifact.artifact_type ?? "sbcl_agent.artifact");
                    return (
                      <div key={artifactKey} className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                        <div className="flex items-center justify-between gap-3">
                          <div className="font-medium text-slate-900">{title}</div>
                          <Badge tone="info">{artifactType}</Badge>
                        </div>
                        <div className="mt-2 text-slate-600">{summary}</div>
                        {pathValue ? <div className="mt-2 text-xs text-slate-500">{pathValue}</div> : null}
                        <form action={importAgentSessionArtifactAction} className="mt-3">
                          <input type="hidden" name="requestId" value={requestId} />
                          <input type="hidden" name="sessionId" value={session.id} />
                          <input type="hidden" name="artifactKey" value={artifactKey} />
                          <input type="hidden" name="title" value={title} />
                          <input type="hidden" name="artifactType" value={artifactType} />
                          <input type="hidden" name="summary" value={summary} />
                          <input type="hidden" name="sourceRef" value={sourceRef} />
                          <input type="hidden" name="path" value={pathValue} />
                          <Button label="Import into RGP" tone="secondary" type="submit" />
                        </form>
                      </div>
                    );
                  })
                ) : (
                  <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-600">
                    No governed runtime artifacts are available for import right now.
                  </div>
                )}
              </div>
            </>
          ) : null}
          {sessionContext.capability_warnings.length ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {sessionContext.capability_warnings.join(" ")}
            </div>
          ) : null}
          <form action={updateAgentSessionGovernanceAction} className="space-y-3 rounded-lg border border-chrome bg-white p-4">
            <input type="hidden" name="requestId" value={requestId} />
            <input type="hidden" name="sessionId" value={session.id} />
            <SectionHeading title="Session Governance" />
            <div className="grid gap-3 md:grid-cols-2">
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Collaboration Mode</span>
                <select
                  name="collaborationMode"
                  defaultValue={session.collaboration_mode}
                  className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700"
                >
                  <option value="human_led">Human-Led</option>
                  <option value="agent_assisted">Agent-Assisted</option>
                  <option value="agent_led">Agent-Led</option>
                </select>
              </label>
              <label className="block space-y-1 text-sm text-slate-700">
                <span className="block text-xs font-medium text-slate-500">Agent Operating Profile</span>
                <select
                  name="agentOperatingProfile"
                  defaultValue={session.agent_operating_profile}
                  className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700"
                >
                  <option value="general">General</option>
                  <option value="review">Review</option>
                  <option value="editorial">Editorial</option>
                  <option value="execution">Execution</option>
                </select>
              </label>
            </div>
            <Button label="Apply Governance" tone="secondary" type="submit" />
          </form>
          <SectionHeading title="Available MCP Capabilities" />
          <div className="space-y-3">
            {sessionContext.available_tools.length ? (
              sessionContext.available_tools.map((tool) => (
                <div key={tool.name} className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-700">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-medium text-slate-900">{tool.name}</div>
                    <div className="flex items-center gap-2">
                      <Badge tone="success">available</Badge>
                      <Badge tone="info">{tool.required_collaboration_mode ?? "agent_assisted"}</Badge>
                    </div>
                  </div>
                  <div className="mt-2 text-slate-600">{tool.description}</div>
                </div>
              ))
            ) : (
              <div className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm text-slate-600">
                No MCP capabilities are currently exposed to this agent session.
              </div>
            )}
            {sessionContext.degraded_tools.map((tool) => (
              <div key={tool.name} className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium">{tool.name}</div>
                  <Badge tone="warning">degraded</Badge>
                </div>
                <div className="mt-2">{tool.description}</div>
                {tool.availability_reason ? <div className="mt-2 text-xs">{tool.availability_reason}</div> : null}
              </div>
            ))}
            {sessionContext.restricted_tools.map((tool) => (
              <div key={tool.name} className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-900">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium">{tool.name}</div>
                  <Badge tone="danger">restricted</Badge>
                </div>
                <div className="mt-2">{tool.description}</div>
                {tool.availability_reason ? <div className="mt-2 text-xs">{tool.availability_reason}</div> : null}
              </div>
            ))}
          </div>
          {session.awaiting_human ? (
            <form action={completeAgentSessionAction} className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
              <input type="hidden" name="requestId" value={requestId} />
              <input type="hidden" name="sessionId" value={session.id} />
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="text-sm text-emerald-900">
                  Accept the current agent response and let the request continue through its workflow.
                </div>
                <Button label="Accept Response and Continue" tone="primary" type="submit" />
              </div>
            </form>
          ) : null}
          <SectionHeading title="Session Transcript" />
          <div className="space-y-3">
            {session.messages.map((message) => (
              <div key={message.id} className="rounded-lg border border-chrome bg-slate-50 p-4 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium text-slate-900">{message.sender_type === "agent" ? session.agent_label : message.sender_id}</div>
                  <div className="text-xs text-slate-500">{new Date(message.created_at).toLocaleString()}</div>
                </div>
                <div className="mt-2 whitespace-pre-wrap text-slate-700">{message.body || (message.sender_type === "agent" ? "Streaming response..." : "")}</div>
              </div>
            ))}
          </div>
          <form action={postAgentSessionMessageAction} className="space-y-3 rounded-lg border border-chrome bg-white p-4">
            <input type="hidden" name="requestId" value={requestId} />
            <input type="hidden" name="sessionId" value={session.id} />
            <label className="block space-y-1 text-sm text-slate-700">
              <span className="block text-xs font-medium text-slate-500">Reply to Agent</span>
              <textarea
                name="body"
                rows={5}
                placeholder="Provide context, constraints, references, or approval guidance for the assigned agent."
                className="w-full rounded-lg border border-chrome bg-slate-50 px-3 py-2 text-sm text-slate-700"
              />
            </label>
            <Button label="Send Guidance" tone="primary" type="submit" />
          </form>
        </div>
        <div className="space-y-4 rounded-xl border border-chrome bg-panel p-5 shadow-panel">
          <a href={`/requests/${requestId}`} className="inline-flex rounded-lg border border-chrome px-3 py-2 text-sm font-medium text-slate-700">
            Back to Request
          </a>
          <SectionHeading title="Session Status" />
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <div className="font-medium">{session.summary}</div>
            <div className="mt-2 text-slate-600">{session.integration_name}</div>
            <div className="mt-2">
              <Badge tone={statusTone(session.status)}>{session.status}</Badge>
            </div>
          </div>
          {latestAgentMessage ? (
            <>
              <SectionHeading title="Latest Agent Response" />
              <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <div className="whitespace-pre-wrap">{latestAgentMessage.body || "Streaming response..."}</div>
                <div className="mt-2 text-xs text-slate-500">{new Date(latestAgentMessage.created_at).toLocaleString()}</div>
              </div>
            </>
          ) : null}
          {session.awaiting_human ? (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              The agent is waiting on human guidance. Reply below to continue the session.
            </div>
          ) : null}
          {latestHumanMessage ? (
            <>
              <SectionHeading title="Latest Human Guidance" />
              <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <div className="whitespace-pre-wrap">{latestHumanMessage.body}</div>
                <div className="mt-2 text-xs text-slate-500">{new Date(latestHumanMessage.created_at).toLocaleString()}</div>
              </div>
            </>
          ) : null}
          <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <div className="font-medium text-slate-900">Session State</div>
            <div className="mt-2 text-slate-600">Messages: {session.message_count}</div>
            <div className="text-slate-600">Awaiting Human: {session.awaiting_human ? "Yes" : "No"}</div>
          </div>
          <SectionHeading title="Context Access Audit" />
          <div className="space-y-3">
            {sessionContext.access_log.length ? (
              sessionContext.access_log.map((entry) => (
                <div key={entry.id} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  <div className="font-medium text-slate-900">{entry.accessor_type}: {entry.accessor_id}</div>
                  <div className="mt-1 text-slate-600">{entry.accessed_resource} • {entry.access_result}</div>
                  {entry.policy_basis?.reason ? <div className="mt-1 text-xs text-slate-500">{String(entry.policy_basis.reason)}</div> : null}
                  <div className="mt-1 text-xs text-slate-500">{entry.accessed_at ? new Date(entry.accessed_at).toLocaleString() : "Timestamp unavailable"}</div>
                </div>
              ))
            ) : (
              <div className="rounded-lg border border-chrome bg-slate-50 px-4 py-3 text-sm text-slate-600">
                No context access has been logged for this session yet.
              </div>
            )}
          </div>
          <SectionHeading title="Session Overview" />
          <KeyValueGrid
            items={[
              { label: "Agent", value: session.agent_label },
              { label: "Mode", value: session.collaboration_mode },
              { label: "Profile", value: session.agent_operating_profile },
              { label: "Provider", value: session.provider ?? "Unspecified" },
              { label: "Integration", value: session.integration_name },
              { label: "Status", value: <Badge tone={statusTone(session.status)}>{session.status}</Badge> },
              { label: "Awaiting Human", value: session.awaiting_human ? "Yes" : "No" },
              { label: "Assigned By", value: session.assigned_by },
              { label: "Assigned At", value: new Date(session.assigned_at).toLocaleString() },
              { label: "External Ref", value: session.external_session_ref ?? "Not connected" },
              ...(isGovernedRuntime
                ? [
                    { label: "Runtime Kind", value: session.governed_runtime?.session_kind ?? "stateful_runtime" },
                    { label: "Turn Ref", value: session.governed_runtime?.turn_ref ?? String(governedRuntime.turn_ref ?? "Unavailable") },
                  ]
                : []),
            ]}
          />
        </div>
      </div>
    </div>
  );
}
