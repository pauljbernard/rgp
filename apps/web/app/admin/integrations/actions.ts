"use server";

import {
  createIntegration,
  createIntegrationProjection,
  deleteIntegration,
  reconcileIntegration,
  resolveIntegrationProjection,
  syncIntegrationProjection,
  updateIntegrationProjectionExternalState,
  updateIntegration
} from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

function readSettings(formData: FormData) {
  const entries = {
    provider: String(formData.get("provider") ?? "").trim(),
    base_url: String(formData.get("baseUrl") ?? "").trim(),
    model: String(formData.get("model") ?? "").trim(),
    api_key: String(formData.get("apiKey") ?? "").trim(),
    access_token: String(formData.get("accessToken") ?? "").trim(),
    workspace_id: String(formData.get("workspaceId") ?? "").trim(),
  };
  return Object.fromEntries(Object.entries(entries).filter(([, value]) => value));
}

export async function createIntegrationAction(formData: FormData) {
  const created = await createIntegration({
    id: String(formData.get("id") ?? ""),
    name: String(formData.get("name") ?? ""),
    type: String(formData.get("type") ?? ""),
    status: String(formData.get("status") ?? "connected"),
    endpoint: String(formData.get("endpoint") ?? ""),
    settings: readSettings(formData),
  });
  revalidatePath("/admin/integrations");
  redirect(`/admin/integrations/${created.id}`);
}

export async function updateIntegrationAction(formData: FormData) {
  const integrationId = String(formData.get("integrationId") ?? "");
  await updateIntegration(integrationId, {
    name: String(formData.get("name") ?? ""),
    type: String(formData.get("type") ?? ""),
    status: String(formData.get("status") ?? "connected"),
    endpoint: String(formData.get("endpoint") ?? ""),
    settings: readSettings(formData),
    clear_api_key: formData.get("clearApiKey") === "on",
    clear_access_token: formData.get("clearAccessToken") === "on",
  });
  revalidatePath("/admin/integrations");
  revalidatePath(`/admin/integrations/${integrationId}`);
  redirect(`/admin/integrations/${integrationId}`);
}

export async function deleteIntegrationAction(formData: FormData) {
  const integrationId = String(formData.get("integrationId") ?? "");
  await deleteIntegration(integrationId);
  revalidatePath("/admin/integrations");
  redirect("/admin/integrations");
}

export async function createIntegrationProjectionAction(formData: FormData) {
  const integrationId = String(formData.get("integrationId") ?? "");
  await createIntegrationProjection(integrationId, {
    entity_type: String(formData.get("entityType") ?? ""),
    entity_id: String(formData.get("entityId") ?? ""),
  });
  revalidatePath(`/admin/integrations/${integrationId}`);
  redirect(`/admin/integrations/${integrationId}`);
}

export async function syncIntegrationProjectionAction(formData: FormData) {
  const integrationId = String(formData.get("integrationId") ?? "");
  const projectionId = String(formData.get("projectionId") ?? "");
  await syncIntegrationProjection(projectionId);
  revalidatePath(`/admin/integrations/${integrationId}`);
  redirect(`/admin/integrations/${integrationId}`);
}

export async function reconcileIntegrationAction(formData: FormData) {
  const integrationId = String(formData.get("integrationId") ?? "");
  await reconcileIntegration(integrationId);
  revalidatePath(`/admin/integrations/${integrationId}`);
  redirect(`/admin/integrations/${integrationId}`);
}

export async function updateIntegrationProjectionExternalStateAction(formData: FormData) {
  const integrationId = String(formData.get("integrationId") ?? "");
  const projectionId = String(formData.get("projectionId") ?? "");
  await updateIntegrationProjectionExternalState(projectionId, {
    external_status: String(formData.get("externalStatus") ?? "").trim() || undefined,
    external_title: String(formData.get("externalTitle") ?? "").trim() || undefined,
    external_ref: String(formData.get("externalRef") ?? "").trim() || undefined,
  });
  revalidatePath(`/admin/integrations/${integrationId}`);
  redirect(`/admin/integrations/${integrationId}`);
}

export async function resolveIntegrationProjectionAction(formData: FormData) {
  const integrationId = String(formData.get("integrationId") ?? "");
  const projectionId = String(formData.get("projectionId") ?? "");
  await resolveIntegrationProjection(projectionId, {
    action: String(formData.get("action") ?? "accept_internal"),
  });
  revalidatePath(`/admin/integrations/${integrationId}`);
  redirect(`/admin/integrations/${integrationId}`);
}
