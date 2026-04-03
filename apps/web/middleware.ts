import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const sessionCookieName = "rgp_access_token";
const publicPaths = new Set(["/login", "/login/start", "/login/callback"]);
const webBaseUrl = process.env.NEXT_PUBLIC_WEB_BASE_URL ?? "http://localhost:3000";

function publicAppUrl(path: string) {
  return new URL(path, webBaseUrl);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname === "/favicon.ico" ||
    pathname.match(/\.[^/]+$/)
  ) {
    return NextResponse.next();
  }

  const hasSession = Boolean(request.cookies.get(sessionCookieName)?.value);
  const isPublic = publicPaths.has(pathname);

  if (!hasSession && !isPublic) {
    return NextResponse.redirect(publicAppUrl("/login"));
  }

  if (hasSession && pathname === "/login") {
    return NextResponse.redirect(publicAppUrl("/requests"));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image).*)"],
};
