import { NextResponse } from "next/server";

import { djangoRequest, sameOriginMutation, setSessionCookies, type TokenPair } from "@/shared/api/auth-session";

export async function POST(request: Request) {
  if (!sameOriginMutation(request)) return NextResponse.json({ error: { detail: "Cross-site request rejected." } }, { status: 403 });
  const values = await request.json();
  const register = await djangoRequest("/api/v1/auth/register/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(values),
  });
  const registered = await register.json().catch(() => null);
  if (!register.ok) return NextResponse.json(registered, { status: register.status });

  const login = await djangoRequest("/api/v1/auth/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: values.username, password: values.password }),
  });
  if (!login.ok) return NextResponse.json(registered, { status: 201 });
  const tokens = (await login.json()) as TokenPair;
  const response = NextResponse.json(registered, { status: 201 });
  response.headers.set("Cache-Control", "no-store");
  setSessionCookies(response, tokens);
  return response;
}
