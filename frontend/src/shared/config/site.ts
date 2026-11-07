export const siteConfig = {
  name: process.env.NEXT_PUBLIC_STORE_NAME ?? "Atelier Cairo",
  description:
    process.env.NEXT_PUBLIC_STORE_DESCRIPTION ??
    "Considered essentials, made for everyday Cairo.",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  indexable: process.env.NEXT_PUBLIC_INDEX_SITE === "true",
} as const;

export const djangoApiUrl = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8000";
