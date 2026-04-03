import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const sessionCookieName = "rgp_access_token";
const authStateCookieName = "rgp_auth_state";
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
const webBaseUrl = process.env.NEXT_PUBLIC_WEB_BASE_URL ?? "http://localhost:3000";

function publicAppUrl(path: string) {
  return new URL(path, webBaseUrl);
}

function secureCookies() {
  const hostname = new URL(webBaseUrl).hostname;
  return !["localhost", "127.0.0.1"].includes(hostname);
}

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const state = request.nextUrl.searchParams.get("state");
  const storedState = request.cookies.get(authStateCookieName)?.value;

  if (!code || !state || !storedState || state !== storedState) {
    return NextResponse.redirect(publicAppUrl("/login?error=state_mismatch"));
  }

  const exchangeResponse = await fetch(`${apiBaseUrl}/api/v1/auth/dev-exchange`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    cache: "no-store",
    body: JSON.stringify({
      code,
      redirect_uri: `${webBaseUrl}/login/callback`,
    }),
  });

  if (!exchangeResponse.ok) {
    return NextResponse.redirect(publicAppUrl("/login?error=exchange_failed"));
  }

  const token = (await exchangeResponse.json()) as { access_token: string };
  const response = NextResponse.redirect(publicAppUrl("/requests"));
  response.cookies.set(sessionCookieName, token.access_token, {
    path: "/",
    sameSite: "lax",
    secure: secureCookies(),
    httpOnly: true,
    maxAge: 3600,
  });
  response.cookies.delete(authStateCookieName);
  return response;
}
