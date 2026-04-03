"use server";

import { createIntegration, deleteIntegration, updateIntegration } from "@/lib/server-api";
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
