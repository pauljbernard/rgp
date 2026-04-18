import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const apiBaseUrl = process.env.RGP_API_INTERNAL_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8001";
const sessionCookieName = "rgp_access_token";

export async function GET(
  _request: Request,
  context: { params: Promise<{ requestId: string; sessionId: string }> }
) {
  const { requestId, sessionId } = await context.params;
  const store = await cookies();
  const token = store.get(sessionCookieName)?.value;
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const upstream = await fetch(`${apiBaseUrl}/api/v1/requests/${requestId}/agent-sessions/${sessionId}/stream`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "text/event-stream",
    },
    cache: "no-store",
  });

  if (!upstream.ok || !upstream.body) {
    return NextResponse.json({ error: "Streaming unavailable" }, { status: upstream.status || 502 });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
