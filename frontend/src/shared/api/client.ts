import { ApiError, normalizeApiError } from "@/shared/api/errors";

export async function clientApi<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, {
    ...init,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", Accept: "application/json", ...init.headers },
  });
  const payload = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, normalizeApiError(payload));
  return payload as T;
}
