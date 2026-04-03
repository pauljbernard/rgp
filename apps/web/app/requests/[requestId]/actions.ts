"use server";

import { assignAgentSession, cancelRequest, cloneRequest, runRequestChecks, submitRequest, transitionRequest } from "@/lib/server-api";
import type { RequestStatus } from "@rgp/domain";
import { revalidatePath } from "next/cache";
import { isRedirectError } from "next/dist/client/components/redirect-error";
import { redirect } from "next/navigation";

function readRequestId(formData: FormData) {
  const requestId = formData.get("requestId");
  if (typeof requestId !== "string" || !requestId) {
    throw new Error("Missing requestId");
  }
  return requestId;
}

export async function submitRequestAction(formData: FormData) {
  const requestId = readRequestId(formData);
  await submitRequest(requestId, { reason: "Submitted from request detail" });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath("/requests");
}

export async function cancelRequestAction(formData: FormData) {
  const requestId = readRequestId(formData);
  await cancelRequest(requestId, { reason: "Canceled from request detail" });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath("/requests");
}

export async function cloneRequestAction(formData: FormData) {
  const requestId = readRequestId(formData);
  const cloned = await cloneRequest(requestId, { reason: "Cloned from request detail" });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath("/requests");
  redirect(`/requests/${cloned.id}`);
}

export async function transitionRequestAction(formData: FormData) {
  const requestId = readRequestId(formData);
  const targetStatus = formData.get("targetStatus");
  if (typeof targetStatus !== "string" || !targetStatus) {
    throw new Error("Missing targetStatus");
  }
  await transitionRequest(requestId, {
    target_status: targetStatus as RequestStatus,
    reason: `Transitioned from request detail to ${targetStatus}`
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath("/requests");
}

export async function runRequestChecksAction(formData: FormData) {
  const requestId = readRequestId(formData);
  await runRequestChecks(requestId, {
    reason: "Request checks re-run from request detail"
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath("/requests");
}

export async function assignAgentSessionAction(formData: FormData) {
  const requestId = readRequestId(formData);
  const integrationId = String(formData.get("integrationId") ?? "");
  const initialPrompt = String(formData.get("initialPrompt") ?? "");
  const agentLabel = String(formData.get("agentLabel") ?? "");
  if (!integrationId || !initialPrompt) {
    throw new Error("Missing integration or initial prompt");
  }
  try {
    const session = await assignAgentSession(requestId, {
      integration_id: integrationId,
      initial_prompt: initialPrompt,
      agent_label: agentLabel || undefined,
      reason: "Assigned from request detail"
    });
    revalidatePath(`/requests/${requestId}`);
    revalidatePath("/requests");
    redirect(`/requests/${requestId}/agents/${session.id}`);
  } catch (error) {
    if (isRedirectError(error)) {
      throw error;
    }
    const message = error instanceof Error ? error.message : "Agent assignment failed";
    redirect(`/requests/${requestId}?error=${encodeURIComponent(message)}`);
  }
}
