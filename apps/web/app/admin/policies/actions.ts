"use server";

import { updatePolicyRules } from "@/lib/server-api";
import { revalidatePath } from "next/cache";

export async function updatePolicyRulesAction(formData: FormData) {
  const policyId = formData.get("policyId");
  const transitionTargets = formData.getAll("transitionTarget");
  const requiredCheckNames = formData.getAll("requiredCheckName");
  if (typeof policyId !== "string") {
    throw new Error("Missing policy update fields");
  }
  const rules = transitionTargets
    .map((value, index) => {
      const transitionTarget = typeof value === "string" ? value.trim() : "";
      const requiredCheckName = typeof requiredCheckNames[index] === "string" ? String(requiredCheckNames[index]).trim() : "";
      if (!transitionTarget || !requiredCheckName) {
        return null;
      }
      return `${transitionTarget}: ${requiredCheckName}`;
    })
    .filter((value): value is string => Boolean(value));
  await updatePolicyRules(policyId, {
    rules
  });
  revalidatePath("/admin/policies");
}
