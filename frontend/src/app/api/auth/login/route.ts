import { NextResponse } from "next/server";

import { djangoRequest, sameOriginMutation, setSessionCookies, type TokenPair } from "@/shared/api/auth-session";

export async function POST(request: Request) {
  if (!sameOriginMutation(request)) return NextResponse.json({ error: { detail: "Cross-site request rejected." } }, { status: 403 });
  const body = await request.text();
  const upstream = await djangoRequest("/api/v1/auth/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  const payload = await upstream.json().catch(() => null);
  if (!upstream.ok) return NextResponse.json(payload, { status: upstream.status });

  const tokens = payload as TokenPair;
  const profile = await djangoRequest("/api/v1/users/me/", {
    headers: { Authorization: `Bearer ${tokens.access}` },
  });
  const response = NextResponse.json(await profile.json(), { status: 200 });
  response.headers.set("Cache-Control", "no-store");
  setSessionCookies(response, tokens);
  return response;
}
