"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createAssignmentGroup, createEscalationRule, createSlaDefinition, remediateSlaBreach } from "@/lib/server-api";

export async function createAssignmentGroupAction(formData: FormData) {
  const name = String(formData.get("name") ?? "").trim();
  const skillTags = String(formData.get("skillTags") ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const maxCapacityRaw = String(formData.get("maxCapacity") ?? "").trim();

  await createAssignmentGroup({
    name,
    skill_tags: skillTags,
    max_capacity: maxCapacityRaw ? Number(maxCapacityRaw) : undefined,
  });

  revalidatePath("/queues");
  redirect("/queues");
}

export async function createEscalationRuleAction(formData: FormData) {
  const name = String(formData.get("name") ?? "").trim();
  const escalationTarget = String(formData.get("escalationTarget") ?? "").trim();
  const escalationType = String(formData.get("escalationType") ?? "reassign");
  const delayMinutes = Number(formData.get("delayMinutes") ?? 60);
  const statusValue = String(formData.get("statusValue") ?? "").trim();

  await createEscalationRule({
    name,
    escalation_target: escalationTarget,
    escalation_type: escalationType,
    delay_minutes: delayMinutes,
    condition: statusValue ? { field: "status", equals: statusValue } : {},
  });

  revalidatePath("/queues");
  redirect("/queues");
}

export async function createSlaDefinitionAction(formData: FormData) {
  const name = String(formData.get("name") ?? "").trim();
  const scopeType = String(formData.get("scopeType") ?? "request_type");
  const scopeId = String(formData.get("scopeId") ?? "").trim();
  const responseTarget = String(formData.get("responseTargetHours") ?? "").trim();
  const resolutionTarget = String(formData.get("resolutionTargetHours") ?? "").trim();
  const reviewTarget = String(formData.get("reviewDeadlineHours") ?? "").trim();

  await createSlaDefinition({
    name,
    scope_type: scopeType,
    scope_id: scopeId || undefined,
    response_target_hours: responseTarget ? Number(responseTarget) : undefined,
    resolution_target_hours: resolutionTarget ? Number(resolutionTarget) : undefined,
    review_deadline_hours: reviewTarget ? Number(reviewTarget) : undefined,
  });

  revalidatePath("/queues");
  redirect("/queues");
}

export async function remediateSlaBreachAction(formData: FormData) {
  const breachId = String(formData.get("breachId") ?? "").trim();
  const remediationAction = String(formData.get("remediationAction") ?? "").trim();
  if (!breachId || !remediationAction) {
    throw new Error("Missing SLA breach remediation fields");
  }

  await remediateSlaBreach(breachId, {
    remediation_action: remediationAction,
  });

  revalidatePath("/queues");
  revalidatePath("/requests/sla-risk");
  revalidatePath("/requests");
  redirect("/queues");
}
