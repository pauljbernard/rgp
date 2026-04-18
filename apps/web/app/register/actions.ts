"use server";

import { redirect } from "next/navigation";

const apiBaseUrl = process.env.RGP_API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";

export async function submitRegistrationAction(formData: FormData) {
  const roles = formData
    .getAll("requestedRoles")
    .map((value) => String(value))
    .filter(Boolean);
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
    body: JSON.stringify({
      display_name: String(formData.get("displayName") ?? ""),
      email: String(formData.get("email") ?? ""),
      organization_id: String(formData.get("organizationId") ?? ""),
      job_title: String(formData.get("jobTitle") ?? ""),
      requested_team_id: String(formData.get("requestedTeamId") ?? ""),
      requested_roles: roles.length ? roles : ["submitter"],
      business_justification: String(formData.get("businessJustification") ?? ""),
      tenant_id: String(formData.get("tenantId") ?? "tenant_demo"),
    }),
  });

  if (!response.ok) {
    redirect("/register?error=1");
  }

  redirect("/register?submitted=1");
}
