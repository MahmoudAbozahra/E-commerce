import "server-only";

import { NextResponse } from "next/server";

import { djangoApiUrl } from "@/shared/config/site";

export const ACCESS_COOKIE = "atelier_access";
export const REFRESH_COOKIE = "atelier_refresh";

export type TokenPair = { access: string; refresh?: string };

// Access expiry can make several browser requests refresh at the same time.
// Keep one short-lived refresh flight per token so refresh rotation cannot make
// sibling requests blacklist each other and clear an otherwise valid session.
const authRuntime = globalThis as typeof globalThis & {
  __atelierRefreshFlights?: Map<string, Promise<TokenPair | null>>;
};
const refreshFlights = authRuntime.__atelierRefreshFlights ?? new Map<string, Promise<TokenPair | null>>();
authRuntime.__atelierRefreshFlights = refreshFlights;
const REFRESH_FLIGHT_GRACE_MS = 10_000;

export function setSessionCookies(response: NextResponse, tokens: TokenPair) {
  const common = {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
  };
  response.cookies.set(ACCESS_COOKIE, tokens.access, { ...common, maxAge: 60 * 15 });
  if (tokens.refresh) response.cookies.set(REFRESH_COOKIE, tokens.refresh, { ...common, maxAge: 60 * 60 * 24 });
}

export function clearSessionCookies(response: NextResponse) {
  response.cookies.set(ACCESS_COOKIE, "", { path: "/", maxAge: 0 });
  response.cookies.set(REFRESH_COOKIE, "", { path: "/", maxAge: 0 });
}

export async function djangoRequest(path: string, init: RequestInit = {}) {
  return fetch(new URL(path, djangoApiUrl), {
    ...init,
    cache: "no-store",
    headers: { Accept: "application/json", ...init.headers },
  });
}

export async function refreshAccess(refresh: string): Promise<TokenPair | null> {
  const inFlight = refreshFlights.get(refresh);
  if (inFlight) return inFlight;

  const flight = (async () => {
    const response = await djangoRequest("/api/v1/auth/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!response.ok) return null;
    return response.json() as Promise<TokenPair>;
  })();
  refreshFlights.set(refresh, flight);
  setTimeout(() => {
    if (refreshFlights.get(refresh) === flight) refreshFlights.delete(refresh);
  }, REFRESH_FLIGHT_GRACE_MS).unref?.();
  return flight;
}

export async function authenticatedDjangoRequest(
  path: string,
  init: RequestInit,
  access: string | undefined,
  refresh: string | undefined,
) {
  const run = (token: string | undefined) =>
    djangoRequest(path, {
      ...init,
      headers: { ...init.headers, ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
  let response = await run(access);
  let rotated: TokenPair | null = null;
  if (response.status === 401 && refresh) {
    rotated = await refreshAccess(refresh);
    if (rotated) response = await run(rotated.access);
  }
  return { response, rotated };
}

export function sameOriginMutation(request: Request) {
  const origin = request.headers.get("origin");
  if (!origin) return request.headers.get("sec-fetch-site") !== "cross-site";
  const requestUrl = new URL(request.url);
  const forwardedHost = request.headers.get("x-forwarded-host")?.split(",")[0]?.trim();
  const host = forwardedHost || request.headers.get("host");
  const forwardedProtocol = request.headers.get("x-forwarded-proto")?.split(",")[0]?.trim();
  const publicOrigin = host ? `${forwardedProtocol || requestUrl.protocol.replace(":", "")}://${host}` : requestUrl.origin;
  return origin === requestUrl.origin || origin === publicOrigin;
}
