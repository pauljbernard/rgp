"use server";

import { addAdminTeamMembership, createAdminPortfolio, createAdminTeam, createAdminTenant, createAdminUser, updateAdminTeam, updateAdminTenant, updateAdminUser } from "@/lib/server-api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

export async function createUserAction(formData: FormData) {
  const roles = String(formData.get("roles") ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  await createAdminUser({
    id: String(formData.get("id") ?? ""),
    display_name: String(formData.get("displayName") ?? ""),
    email: String(formData.get("email") ?? ""),
    role_summary: roles,
    status: String(formData.get("status") ?? "active"),
    password: String(formData.get("password") ?? "").trim() || undefined,
    password_reset_required: formData.get("requirePasswordReset") === "on"
  });
  revalidatePath("/admin/org");
  revalidatePath("/admin/org/users/new");
}

export async function createTenantAction(formData: FormData) {
  await createAdminTenant({
    id: String(formData.get("id") ?? ""),
    name: String(formData.get("name") ?? ""),
    status: String(formData.get("status") ?? "active")
  });
  revalidatePath("/admin/org");
  revalidatePath("/admin/org/tenants/new");
}

export async function updateTenantAction(formData: FormData) {
  const tenantId = String(formData.get("tenantId") ?? "");
  await updateAdminTenant(tenantId, {
    name: String(formData.get("name") ?? ""),
    status: String(formData.get("status") ?? "active")
  });
  revalidatePath("/admin/org");
  revalidatePath(`/admin/org/tenants/${tenantId}`);
  redirect(`/admin/org/tenants/${tenantId}`);
}

export async function updateUserAction(formData: FormData) {
  const userId = String(formData.get("userId") ?? "");
  const roles = String(formData.get("roles") ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  await updateAdminUser(userId, {
    display_name: String(formData.get("displayName") ?? ""),
    email: String(formData.get("email") ?? ""),
    role_summary: roles,
    status: String(formData.get("status") ?? "active"),
    password: String(formData.get("password") ?? "").trim() || undefined,
    password_reset_required: formData.get("requirePasswordReset") === "on",
    reset_password: formData.get("resetPassword") === "on"
  });
  revalidatePath("/admin/org");
  revalidatePath(`/admin/org/users/${userId}`);
  redirect(`/admin/org/users/${userId}`);
}

export async function createTeamAction(formData: FormData) {
  await createAdminTeam({
    id: String(formData.get("id") ?? ""),
    organization_id: String(formData.get("organizationId") ?? ""),
    name: String(formData.get("name") ?? ""),
    kind: String(formData.get("kind") ?? "delivery"),
    status: String(formData.get("status") ?? "active")
  });
  revalidatePath("/admin/org");
}

export async function updateTeamAction(formData: FormData) {
  const teamId = String(formData.get("teamId") ?? "");
  await updateAdminTeam(teamId, {
    organization_id: String(formData.get("organizationId") ?? ""),
    name: String(formData.get("name") ?? ""),
    kind: String(formData.get("kind") ?? "delivery"),
    status: String(formData.get("status") ?? "active")
  });
  revalidatePath("/admin/org");
  revalidatePath(`/admin/org/teams/${teamId}`);
  redirect(`/admin/org/teams/${teamId}`);
}

export async function addTeamMembershipAction(formData: FormData) {
  const teamId = String(formData.get("teamId") ?? "");
  await addAdminTeamMembership({
    team_id: teamId,
    user_id: String(formData.get("userId") ?? ""),
    role: String(formData.get("role") ?? "member")
  });
  revalidatePath("/admin/org");
  revalidatePath(`/admin/org/teams/${teamId}`);
}

export async function createUserAndAddTeamMembershipAction(formData: FormData) {
  const userId = String(formData.get("id") ?? "");
  const teamId = String(formData.get("teamId") ?? "");
  const roles = String(formData.get("roles") ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  await createAdminUser({
    id: userId,
    display_name: String(formData.get("displayName") ?? ""),
    email: String(formData.get("email") ?? ""),
    role_summary: roles,
    status: String(formData.get("status") ?? "active"),
    password: String(formData.get("password") ?? "").trim() || undefined,
    password_reset_required: formData.get("requirePasswordReset") === "on"
  });
  await addAdminTeamMembership({
    team_id: teamId,
    user_id: userId,
    role: String(formData.get("membershipRole") ?? "member")
  });
  revalidatePath("/admin/org");
  revalidatePath(`/admin/org/teams/${teamId}`);
  redirect(`/admin/org/teams/${teamId}`);
}

export async function createPortfolioAction(formData: FormData) {
  const scopeKeys = String(formData.get("scopeKeys") ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  await createAdminPortfolio({
    id: String(formData.get("id") ?? ""),
    name: String(formData.get("name") ?? ""),
    owner_team_id: String(formData.get("ownerTeamId") ?? ""),
    scope_keys: scopeKeys,
    status: String(formData.get("status") ?? "active")
  });
  revalidatePath("/admin/org");
}
