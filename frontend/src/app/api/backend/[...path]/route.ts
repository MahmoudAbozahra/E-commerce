import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  authenticatedDjangoRequest,
  clearSessionCookies,
  sameOriginMutation,
  setSessionCookies,
} from "@/shared/api/auth-session";

const allowedPrefixes = [
  "cart",
  "wishlist",
  "users/addresses",
  "users/me",
  "shipping/methods",
  "checkout",
  "coupons/validate",
  "orders",
  "loyalty",
  "notifications",
  "catalog/products",
];

type Context = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, context: Context) {
  const { path } = await context.params;
  const joined = path.join("/");
  if (!allowedPrefixes.some((prefix) => joined === prefix || joined.startsWith(`${prefix}/`))) {
    return NextResponse.json({ error: { detail: "Route is not available through the storefront." } }, { status: 404 });
  }
  if (!new Set(["GET", "HEAD", "OPTIONS"]).has(request.method) && !sameOriginMutation(request)) {
    return NextResponse.json({ error: { detail: "Cross-site request rejected." } }, { status: 403 });
  }

  const jar = await cookies();
  const access = jar.get(ACCESS_COOKIE)?.value;
  const refresh = jar.get(REFRESH_COOKIE)?.value;
  const target = `/api/v1/${joined.replace(/\/+$/, "")}/${new URL(request.url).search}`;
  const body = new Set(["GET", "HEAD"]).has(request.method) ? undefined : await request.arrayBuffer();
  const { response: upstream, rotated } = await authenticatedDjangoRequest(
    target,
    {
      method: request.method,
      body,
      headers: {
        ...(request.headers.get("content-type") ? { "Content-Type": request.headers.get("content-type") as string } : {}),
        ...(request.headers.get("idempotency-key") ? { "Idempotency-Key": request.headers.get("idempotency-key") as string } : {}),
      },
    },
    access,
    refresh,
  );
  const response = new NextResponse(upstream.status === 204 ? null : await upstream.arrayBuffer(), {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json", "Cache-Control": "no-store" },
  });
  if (rotated) setSessionCookies(response, rotated);
  if (upstream.status === 401) clearSessionCookies(response);
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
