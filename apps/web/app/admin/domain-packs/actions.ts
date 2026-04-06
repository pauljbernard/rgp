"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { activateDomainPack, createDomainPack, installDomainPack } from "@/lib/server-api";

function parseCsv(value: FormDataEntryValue | null) {
  return String(value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export async function createDomainPackAction(formData: FormData) {
  const created = await createDomainPack({
    name: String(formData.get("name") ?? "").trim(),
    version: String(formData.get("version") ?? "").trim(),
    description: String(formData.get("description") ?? "").trim() || undefined,
    contributed_templates: parseCsv(formData.get("contributedTemplates")),
    contributed_artifact_types: parseCsv(formData.get("contributedArtifactTypes")),
    contributed_workflows: parseCsv(formData.get("contributedWorkflows")),
    contributed_policies: parseCsv(formData.get("contributedPolicies")),
  });

  revalidatePath("/admin/domain-packs");
  redirect(`/admin/domain-packs/${created.id}`);
}

export async function activateDomainPackAction(formData: FormData) {
  const packId = String(formData.get("packId") ?? "");
  await activateDomainPack(packId);
  revalidatePath(`/admin/domain-packs/${packId}`);
  revalidatePath("/admin/domain-packs");
  redirect(`/admin/domain-packs/${packId}`);
}

export async function installDomainPackAction(formData: FormData) {
  const packId = String(formData.get("packId") ?? "");
  await installDomainPack(packId);
  revalidatePath(`/admin/domain-packs/${packId}`);
  revalidatePath("/admin/domain-packs");
  redirect(`/admin/domain-packs/${packId}`);
}
