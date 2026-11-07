import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  authenticatedDjangoRequest,
  clearSessionCookies,
  setSessionCookies,
} from "@/shared/api/auth-session";

export async function GET() {
  const jar = await cookies();
  const access = jar.get(ACCESS_COOKIE)?.value;
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  if (!access && !refresh) return NextResponse.json({ user: null }, { status: 200, headers: { "Cache-Control": "no-store" } });

  const { response: upstream, rotated } = await authenticatedDjangoRequest("/api/v1/users/me/", {}, access, refresh);
  const payload = await upstream.json().catch(() => null);
  const response = NextResponse.json(upstream.ok ? { user: payload } : payload, { status: upstream.status });
  response.headers.set("Cache-Control", "no-store");
  if (rotated) setSessionCookies(response, rotated);
  if (upstream.status === 401) clearSessionCookies(response);
  return response;
}
