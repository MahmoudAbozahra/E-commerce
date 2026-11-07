import type { NormalizedApiError } from "@/shared/api/contracts";

export class ApiError extends Error {
  constructor(
    public status: number,
    public normalized: NormalizedApiError,
  ) {
    super(normalized.message);
    this.name = "ApiError";
  }
}

function collectFields(value: unknown) {
  if (!value || typeof value !== "object") return {};
  const fields: Record<string, string[]> = {};
  Object.entries(value as Record<string, unknown>).forEach(([key, messages]) => {
    fields[key] = Array.isArray(messages)
      ? messages.map(String)
      : [typeof messages === "string" ? messages : JSON.stringify(messages)];
  });
  return fields;
}

export function normalizeApiError(payload: unknown, fallback = "Something went wrong. Please try again."): NormalizedApiError {
  const wrapper = payload && typeof payload === "object" ? (payload as Record<string, unknown>).error : null;
  const error = wrapper && typeof wrapper === "object" ? (wrapper as Record<string, unknown>) : null;
  const detail = error?.detail ?? payload;
  const fields = collectFields(detail);
  const message =
    typeof detail === "string"
      ? detail
      : Object.values(fields).flat()[0] ?? fallback;
  return { code: typeof error?.code === "string" ? error.code : "request_failed", message, fields };
}
