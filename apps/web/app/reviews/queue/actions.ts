"use server";

import { overrideReviewAssignment, recordReviewDecision } from "@/lib/server-api";
import type { ReviewDecision } from "@rgp/domain";
import { revalidatePath } from "next/cache";

export async function reviewDecisionAction(formData: FormData) {
  const reviewId = formData.get("reviewId");
  const decision = formData.get("decision");
  if (typeof reviewId !== "string" || typeof decision !== "string") {
    throw new Error("Missing review mutation fields");
  }
  await recordReviewDecision(reviewId, {
    decision: decision as ReviewDecision,
    reason: `Review decision submitted from queue: ${decision}`
  });
  revalidatePath("/reviews/queue");
  revalidatePath("/requests");
}

export async function overrideReviewAssignmentAction(formData: FormData) {
  const reviewId = formData.get("reviewId");
  const assignedReviewer = formData.get("assignedReviewer");
  if (typeof reviewId !== "string" || typeof assignedReviewer !== "string") {
    throw new Error("Missing review override fields");
  }
  await overrideReviewAssignment(reviewId, {
    assigned_reviewer: assignedReviewer,
    reason: `Review assignment overridden from queue: ${assignedReviewer}`
  });
  revalidatePath("/reviews/queue");
  revalidatePath("/requests");
}
