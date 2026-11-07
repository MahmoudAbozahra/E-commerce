import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE, clearSessionCookies, djangoRequest, sameOriginMutation } from "@/shared/api/auth-session";

export async function POST(request: Request) {
  if (!sameOriginMutation(request)) return NextResponse.json({ error: { detail: "Cross-site request rejected." } }, { status: 403 });
  const jar = await cookies();
  const access = jar.get(ACCESS_COOKIE)?.value;
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  if (refresh) {
    await djangoRequest("/api/v1/auth/logout/", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(access ? { Authorization: `Bearer ${access}` } : {}) },
      body: JSON.stringify({ refresh }),
    }).catch(() => null);
  }
  const response = new NextResponse(null, { status: 204 });
  clearSessionCookies(response);
  response.headers.set("Cache-Control", "no-store");
  return response;
}
