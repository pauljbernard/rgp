"use server";

import { applyPromotionAction, evaluatePromotionCheck, overridePromotionApproval, overridePromotionCheck, runPromotionChecks } from "@/lib/server-api";
import type { PromotionAction } from "@rgp/domain";
import { revalidatePath } from "next/cache";

export async function promotionAction(formData: FormData) {
  const promotionId = formData.get("promotionId");
  const action = formData.get("action");
  if (typeof promotionId !== "string" || typeof action !== "string") {
    throw new Error("Missing promotion mutation fields");
  }
  await applyPromotionAction(promotionId, {
    action: action as PromotionAction,
    reason: `Promotion action submitted from gate: ${action}`
  });
  revalidatePath(`/promotions/${promotionId}`);
  revalidatePath("/requests");
  revalidatePath("/artifacts");
}

export async function evaluatePromotionCheckAction(formData: FormData) {
  const promotionId = formData.get("promotionId");
  const checkId = formData.get("checkId");
  const state = formData.get("state");
  if (typeof promotionId !== "string" || typeof checkId !== "string" || typeof state !== "string") {
    throw new Error("Missing promotion check fields");
  }
  await evaluatePromotionCheck(promotionId, checkId, {
    state,
    detail: `Check evaluated as ${state} from promotion gate`,
    evidence: "Manual gate evaluation"
  });
  revalidatePath(`/promotions/${promotionId}`);
  revalidatePath("/requests");
}

export async function overridePromotionCheckAction(formData: FormData) {
  const promotionId = formData.get("promotionId");
  const checkId = formData.get("checkId");
  if (typeof promotionId !== "string" || typeof checkId !== "string") {
    throw new Error("Missing promotion override fields");
  }
  await overridePromotionCheck(promotionId, checkId, {
    reason: "Administrative override from promotion gate"
  });
  revalidatePath(`/promotions/${promotionId}`);
  revalidatePath("/requests");
}

export async function runPromotionChecksAction(formData: FormData) {
  const promotionId = formData.get("promotionId");
  if (typeof promotionId !== "string") {
    throw new Error("Missing promotion id");
  }
  await runPromotionChecks(promotionId, {
    reason: "Promotion checks re-run from gate"
  });
  revalidatePath(`/promotions/${promotionId}`);
  revalidatePath("/requests");
}

export async function overridePromotionApprovalAction(formData: FormData) {
  const promotionId = formData.get("promotionId");
  const reviewer = formData.get("reviewer");
  const replacementReviewer = formData.get("replacementReviewer");
  if (typeof promotionId !== "string" || typeof reviewer !== "string" || typeof replacementReviewer !== "string") {
    throw new Error("Missing promotion approval override fields");
  }
  await overridePromotionApproval(promotionId, {
    reviewer,
    replacement_reviewer: replacementReviewer,
    reason: `Promotion approval overridden from gate: ${reviewer} -> ${replacementReviewer}`
  });
  revalidatePath(`/promotions/${promotionId}`);
  revalidatePath("/requests");
}
