"use server";

import { executeRequestEscalation, remediateSlaBreach } from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function remediateSlaBreachFromRiskQueueAction(formData: FormData) {
  const breachId = String(formData.get("breachId") ?? "").trim();
  const remediationAction = String(formData.get("remediationAction") ?? "").trim();
  if (!breachId || !remediationAction) {
    throw new Error("Missing SLA breach remediation fields");
  }

  await remediateSlaBreach(breachId, {
    remediation_action: remediationAction,
  });

  revalidatePath("/requests/sla-risk");
  revalidatePath("/queues");
  revalidatePath("/requests");
  redirect("/requests/sla-risk");
}

export async function executeEscalationFromRiskQueueAction(formData: FormData) {
  const requestId = String(formData.get("requestId") ?? "").trim();
  const ruleId = String(formData.get("ruleId") ?? "").trim();
  if (!requestId || !ruleId) {
    throw new Error("Missing escalation execution fields");
  }

  await executeRequestEscalation(requestId, ruleId);

  revalidatePath("/requests/sla-risk");
  revalidatePath("/requests");
  revalidatePath("/queues");
  redirect("/requests/sla-risk");
}
