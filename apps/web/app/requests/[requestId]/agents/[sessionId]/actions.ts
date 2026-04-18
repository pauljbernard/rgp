"use server";

import {
  approveAgentSessionCheckpoint,
  completeAgentSession,
  importAgentSessionArtifact,
  postAgentSessionMessage,
  resumeAgentSessionRuntime,
  updateAgentSessionGovernance
} from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

function readValue(formData: FormData, key: string) {
  const value = formData.get(key);
  if (typeof value !== "string" || !value) {
    throw new Error(`Missing ${key}`);
  }
  return value;
}

export async function postAgentSessionMessageAction(formData: FormData) {
  const requestId = readValue(formData, "requestId");
  const sessionId = readValue(formData, "sessionId");
  const body = readValue(formData, "body");
  await postAgentSessionMessage(requestId, sessionId, {
    body,
    reason: "Interactive guidance sent from agent session page",
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/agents/${sessionId}`);
  redirect(`/requests/${requestId}/agents/${sessionId}`);
}

export async function completeAgentSessionAction(formData: FormData) {
  const requestId = readValue(formData, "requestId");
  const sessionId = readValue(formData, "sessionId");
  await completeAgentSession(requestId, sessionId, {
    reason: "Accepted agent response and resumed request workflow",
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/agents`);
  revalidatePath(`/requests/${requestId}/agents/${sessionId}`);
  redirect(`/requests/${requestId}`);
}

export async function resumeAgentSessionRuntimeAction(formData: FormData) {
  const requestId = readValue(formData, "requestId");
  const sessionId = readValue(formData, "sessionId");
  const workItemId = readValue(formData, "workItemId");
  const note = formData.get("note");
  await resumeAgentSessionRuntime(requestId, sessionId, {
    work_item_id: workItemId,
    note: typeof note === "string" && note ? note : null,
    reason: "Resumed governed runtime work from agent session page",
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/agents`);
  revalidatePath(`/requests/${requestId}/agents/${sessionId}`);
  redirect(`/requests/${requestId}/agents/${sessionId}`);
}

export async function approveAgentSessionCheckpointAction(formData: FormData) {
  const requestId = readValue(formData, "requestId");
  const sessionId = readValue(formData, "sessionId");
  const workItemId = readValue(formData, "workItemId");
  const policy = readValue(formData, "policy");
  await approveAgentSessionCheckpoint(requestId, sessionId, {
    work_item_id: workItemId,
    policy,
    reason: "Approved governed runtime checkpoint from agent session page",
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/agents`);
  revalidatePath(`/requests/${requestId}/agents/${sessionId}`);
  redirect(`/requests/${requestId}/agents/${sessionId}`);
}

export async function importAgentSessionArtifactAction(formData: FormData) {
  const requestId = readValue(formData, "requestId");
  const sessionId = readValue(formData, "sessionId");
  const artifactKey = readValue(formData, "artifactKey");
  const title = readValue(formData, "title");
  const artifactType = readValue(formData, "artifactType");
  const summary = readValue(formData, "summary");
  const sourceRef = readValue(formData, "sourceRef");
  const path = formData.get("path");
  await importAgentSessionArtifact(requestId, sessionId, {
    artifact_key: artifactKey,
    title,
    artifact_type: artifactType,
    summary,
    source_ref: sourceRef,
    path: typeof path === "string" && path ? path : null,
    reason: "Imported governed runtime artifact from agent session page",
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/agents`);
  revalidatePath(`/requests/${requestId}/agents/${sessionId}`);
  redirect(`/requests/${requestId}/agents/${sessionId}`);
}

export async function updateAgentSessionGovernanceAction(formData: FormData) {
  const requestId = readValue(formData, "requestId");
  const sessionId = readValue(formData, "sessionId");
  const collaborationMode = readValue(formData, "collaborationMode");
  const agentOperatingProfile = readValue(formData, "agentOperatingProfile");
  await updateAgentSessionGovernance(requestId, sessionId, {
    collaboration_mode: collaborationMode,
    agent_operating_profile: agentOperatingProfile,
    reason: "Updated session governance from agent session page",
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/agents`);
  revalidatePath(`/requests/${requestId}/agents/${sessionId}`);
  redirect(`/requests/${requestId}/agents/${sessionId}`);
}
