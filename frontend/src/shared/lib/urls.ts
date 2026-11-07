export function mediaUrl(value: string | null | undefined) {
  if (!value) return null;
  try {
    const parsed = new URL(value, "http://internal.invalid");
    if (parsed.pathname.startsWith("/media/")) {
      const path = `${parsed.pathname}${parsed.search}`;
      const publicOrigin = process.env.NEXT_PUBLIC_MEDIA_ORIGIN;
      return publicOrigin ? new URL(path, publicOrigin).toString() : path;
    }
    return parsed.origin === "http://internal.invalid" ? null : parsed.toString();
  } catch {
    return null;
  }
}

export function absoluteMediaUrl(value: string | null | undefined, siteUrl: string) {
  const normalized = mediaUrl(value);
  if (!normalized) return null;
  return new URL(normalized, siteUrl).toString();
}

export function buildQuery(params: Record<string, string | number | boolean | undefined>) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}
