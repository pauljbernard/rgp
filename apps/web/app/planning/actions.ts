"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { addPlanningMembership, createPlanningConstruct, removePlanningMembership, updatePlanningMembership } from "@/lib/server-api";

export async function createPlanningConstructAction(formData: FormData) {
  const created = await createPlanningConstruct({
    type: String(formData.get("type") ?? "initiative"),
    name: String(formData.get("name") ?? "").trim(),
    description: String(formData.get("description") ?? "").trim() || undefined,
    owner_team_id: String(formData.get("ownerTeamId") ?? "").trim() || undefined,
    priority: Number(formData.get("priority") ?? 0),
    target_date: String(formData.get("targetDate") ?? "").trim() || undefined,
    capacity_budget: String(formData.get("capacityBudget") ?? "").trim()
      ? Number(formData.get("capacityBudget"))
      : undefined,
  });

  revalidatePath("/planning");
  redirect(`/planning/${created.id}`);
}

export async function addPlanningMembershipAction(formData: FormData) {
  const constructId = String(formData.get("constructId") ?? "");
  await addPlanningMembership(constructId, {
    request_id: String(formData.get("requestId") ?? "").trim(),
    sequence: Number(formData.get("sequence") ?? 0),
    priority: Number(formData.get("priority") ?? 0),
  });

  revalidatePath(`/planning/${constructId}`);
  revalidatePath("/planning");
  redirect(`/planning/${constructId}`);
}

export async function updatePlanningMembershipAction(formData: FormData) {
  const constructId = String(formData.get("constructId") ?? "");
  const requestId = String(formData.get("requestId") ?? "");
  await updatePlanningMembership(constructId, requestId, {
    sequence: Number(formData.get("sequence") ?? 0),
    priority: Number(formData.get("priority") ?? 0),
  });

  revalidatePath(`/planning/${constructId}`);
  revalidatePath("/planning");
  redirect(`/planning/${constructId}`);
}

export async function removePlanningMembershipAction(formData: FormData) {
  const constructId = String(formData.get("constructId") ?? "");
  const requestId = String(formData.get("requestId") ?? "");
  await removePlanningMembership(constructId, requestId);

  revalidatePath(`/planning/${constructId}`);
  revalidatePath("/planning");
  redirect(`/planning/${constructId}`);
}

export async function nudgePlanningMembershipAction(formData: FormData) {
  const constructId = String(formData.get("constructId") ?? "");
  const requestId = String(formData.get("requestId") ?? "");
  const currentSequence = Number(formData.get("currentSequence") ?? 0);
  const priority = Number(formData.get("priority") ?? 0);
  const direction = String(formData.get("direction") ?? "later");
  const nextSequence = direction === "earlier" ? Math.max(0, currentSequence - 1) : currentSequence + 1;

  await updatePlanningMembership(constructId, requestId, {
    sequence: nextSequence,
    priority,
  });

  revalidatePath(`/planning/${constructId}`);
  revalidatePath("/planning");
  redirect(`/planning/${constructId}`);
}
