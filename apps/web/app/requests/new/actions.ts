"use server";

import { createRequestDraft } from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { isRedirectError } from "next/dist/client/components/redirect-error";

export async function createRequestAction(formData: FormData) {
  const templateId = formData.get("templateId");
  const templateVersion = formData.get("templateVersion");
  const title = formData.get("title");
  const summary = formData.get("summary");
  const priority = formData.get("priority");

  if (
    typeof templateId !== "string" ||
    typeof templateVersion !== "string" ||
    typeof title !== "string" ||
    typeof summary !== "string" ||
    typeof priority !== "string"
  ) {
    throw new Error("Invalid request payload");
  }

  const inputPayload = Object.fromEntries(
    Array.from(formData.entries())
      .filter(([key, value]) => key.startsWith("input_") && typeof value === "string" && value !== "")
      .map(([key, value]) => [key.replace(/^input_/, ""), value])
  );

  try {
    const created = await createRequestDraft({
      template_id: templateId,
      template_version: templateVersion,
      title,
      summary,
      priority: priority as "low" | "medium" | "high" | "urgent",
      input_payload: inputPayload
    });

    revalidatePath("/requests");
    redirect(`/requests/${created.id}`);
  } catch (error) {
    if (isRedirectError(error)) {
      throw error;
    }
    const message = error instanceof Error ? error.message : "Request creation failed";
    redirect(`/requests/new?template=${encodeURIComponent(`${templateId}@${templateVersion}`)}&error=${encodeURIComponent(message)}`);
  }
}
