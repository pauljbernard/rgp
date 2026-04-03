import { randomUUID } from "crypto";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const authStateCookieName = "rgp_auth_state";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
const webBaseUrl = process.env.NEXT_PUBLIC_WEB_BASE_URL ?? "http://localhost:3000";

function secureCookies() {
  const hostname = new URL(webBaseUrl).hostname;
  return !["localhost", "127.0.0.1"].includes(hostname);
}

const profiles = {
  admin: {
    userId: "admin_demo",
    tenantId: "tenant_demo",
    roles: ["admin", "operator", "reviewer", "submitter"],
  },
  reviewer: {
    userId: "reviewer_demo",
    tenantId: "tenant_demo",
    roles: ["reviewer", "observer"],
  },
  submitter: {
    userId: "submitter_demo",
    tenantId: "tenant_demo",
    roles: ["submitter", "observer"],
  },
  observer: {
    userId: "observer_demo",
    tenantId: "tenant_demo",
    roles: ["observer"],
  },
  other_admin: {
    userId: "tenant_other_admin",
    tenantId: "tenant_other",
    roles: ["admin", "operator", "reviewer", "submitter"],
  },
} as const;

export function GET(request: NextRequest) {
  const profileId = request.nextUrl.searchParams.get("profile") ?? "admin";
  const profile = profiles[profileId as keyof typeof profiles] ?? profiles.admin;
  const state = randomUUID();
  const redirectUri = `${webBaseUrl}/login/callback`;
  const authorizeUrl = new URL(`${apiBaseUrl}/api/v1/auth/dev-authorize`);
  authorizeUrl.searchParams.set("redirect_uri", redirectUri);
  authorizeUrl.searchParams.set("state", state);
  authorizeUrl.searchParams.set("user_id", profile.userId);
  authorizeUrl.searchParams.set("tenant_id", profile.tenantId);
  for (const role of profile.roles) {
    authorizeUrl.searchParams.append("roles", role);
  }

  const response = NextResponse.redirect(authorizeUrl);
  response.cookies.set(authStateCookieName, state, {
    path: "/",
    sameSite: "lax",
    secure: secureCookies(),
    httpOnly: true,
    maxAge: 300,
  });
  return response;
}
