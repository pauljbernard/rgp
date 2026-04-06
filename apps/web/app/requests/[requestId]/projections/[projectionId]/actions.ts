"use server";

import {
  resolveIntegrationProjection,
  syncIntegrationProjection,
  updateIntegrationProjectionExternalState,
} from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function syncRequestProjectionAction(formData: FormData) {
  const requestId = String(formData.get("requestId") ?? "");
  const projectionId = String(formData.get("projectionId") ?? "");
  const returnTo = String(formData.get("returnTo") ?? "").trim();
  await syncIntegrationProjection(projectionId);
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/history`);
  revalidatePath(`/requests/${requestId}/projections/${projectionId}`);
  if (returnTo) {
    revalidatePath(returnTo);
    redirect(returnTo);
  }
  redirect(`/requests/${requestId}/projections/${projectionId}`);
}

export async function updateRequestProjectionExternalStateAction(formData: FormData) {
  const requestId = String(formData.get("requestId") ?? "");
  const projectionId = String(formData.get("projectionId") ?? "");
  const returnTo = String(formData.get("returnTo") ?? "").trim();
  await updateIntegrationProjectionExternalState(projectionId, {
    external_status: String(formData.get("externalStatus") ?? "").trim() || undefined,
    external_title: String(formData.get("externalTitle") ?? "").trim() || undefined,
    external_ref: String(formData.get("externalRef") ?? "").trim() || undefined,
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/history`);
  revalidatePath(`/requests/${requestId}/projections/${projectionId}`);
  if (returnTo) {
    revalidatePath(returnTo);
    redirect(returnTo);
  }
  redirect(`/requests/${requestId}/projections/${projectionId}`);
}

export async function resolveRequestProjectionAction(formData: FormData) {
  const requestId = String(formData.get("requestId") ?? "");
  const projectionId = String(formData.get("projectionId") ?? "");
  const returnTo = String(formData.get("returnTo") ?? "").trim();
  await resolveIntegrationProjection(projectionId, {
    action: String(formData.get("action") ?? "accept_internal"),
  });
  revalidatePath(`/requests/${requestId}`);
  revalidatePath(`/requests/${requestId}/history`);
  revalidatePath(`/requests/${requestId}/projections/${projectionId}`);
  if (returnTo) {
    revalidatePath(returnTo);
    redirect(returnTo);
  }
  redirect(`/requests/${requestId}/projections/${projectionId}`);
}
