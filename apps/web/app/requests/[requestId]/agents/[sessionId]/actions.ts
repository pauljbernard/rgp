"use server";

import { completeAgentSession, postAgentSessionMessage, updateAgentSessionGovernance } from "@/lib/server-api";
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
