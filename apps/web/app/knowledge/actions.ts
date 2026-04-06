"use server";

import { createKnowledgeArtifact, publishKnowledgeArtifact } from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function createKnowledgeArtifactAction(formData: FormData) {
  const tags = String(formData.get("tags") ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const created = await createKnowledgeArtifact({
    name: String(formData.get("name") ?? ""),
    description: String(formData.get("description") ?? "") || undefined,
    content: String(formData.get("content") ?? "") || undefined,
    content_type: String(formData.get("contentType") ?? "text"),
    tags,
  });
  revalidatePath("/knowledge");
  revalidatePath("/knowledge/new");
  redirect(`/knowledge/${created.id}`);
}

export async function publishKnowledgeArtifactAction(formData: FormData) {
  const artifactId = String(formData.get("artifactId") ?? "");
  await publishKnowledgeArtifact(artifactId);
  revalidatePath("/knowledge");
  revalidatePath(`/knowledge/${artifactId}`);
  redirect(`/knowledge/${artifactId}`);
}
