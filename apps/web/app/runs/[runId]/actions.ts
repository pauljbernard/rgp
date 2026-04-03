"use server";

import { commandRun } from "@/lib/server-api";
import type { RunCommand } from "@rgp/domain";
import { revalidatePath } from "next/cache";

export async function commandRunAction(formData: FormData) {
  const runId = formData.get("runId");
  const command = formData.get("command");
  if (typeof runId !== "string" || typeof command !== "string") {
    throw new Error("Missing run command fields");
  }
  await commandRun(runId, {
    command: command as RunCommand,
    reason: `Run command submitted from run detail: ${command}`
  });
  revalidatePath(`/runs/${runId}`);
  revalidatePath("/runs");
}
