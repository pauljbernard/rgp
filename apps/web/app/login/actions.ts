"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const sessionCookieName = "rgp_access_token";
const authStateCookieName = "rgp_auth_state";
const apiBaseUrl = process.env.RGP_API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
const webBaseUrl = process.env.NEXT_PUBLIC_WEB_BASE_URL ?? "http://localhost:3000";

function secureCookies() {
  const hostname = new URL(webBaseUrl).hostname;
  return !["localhost", "127.0.0.1"].includes(hostname);
}

export async function logoutAction() {
  const store = await cookies();
  store.delete(sessionCookieName);
  store.delete(authStateCookieName);
  redirect("/login");
}

export async function loginWithPasswordAction(formData: FormData) {
  const response = await fetch(`${apiBaseUrl}/api/v1/auth/local-login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
    body: JSON.stringify({
      email: String(formData.get("email") ?? ""),
      password: String(formData.get("password") ?? ""),
      tenant_id: String(formData.get("tenantId") ?? "tenant_demo"),
    }),
  });

  if (!response.ok) {
    redirect("/login?error=exchange_failed");
  }

  const token = (await response.json()) as { access_token: string };
  const store = await cookies();
  store.set(sessionCookieName, token.access_token, {
    path: "/",
    sameSite: "lax",
    secure: secureCookies(),
    httpOnly: true,
    maxAge: 3600,
  });
  redirect("/requests");
}
