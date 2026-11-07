import "server-only";

import { djangoApiUrl } from "@/shared/config/site";
import type { Brand, Category, Paginated, Product, ProductDetail, Review } from "@/shared/api/contracts";
import { ApiError, normalizeApiError } from "@/shared/api/errors";
import { buildQuery } from "@/shared/lib/urls";

type PublicFetchOptions = {
  revalidate?: number;
  tags?: string[];
};

export async function publicApiFetch<T>(path: string, options: PublicFetchOptions = {}): Promise<T> {
  const response = await fetch(new URL(path, djangoApiUrl), {
    headers: { Accept: "application/json" },
    next: { revalidate: options.revalidate ?? 300, tags: options.tags },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new ApiError(response.status, normalizeApiError(payload));
  }
  return response.json() as Promise<T>;
}

export type CatalogQuery = {
  search?: string;
  category?: string;
  brand?: string;
  min_price?: string;
  max_price?: string;
  available?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
};

export function getProducts(query: CatalogQuery = {}) {
  const suffix = buildQuery(query);
  return publicApiFetch<Paginated<Product>>(`/api/v1/catalog/products/${suffix ? `?${suffix}` : ""}`, {
    tags: ["products"],
  });
}

export function getProduct(slug: string) {
  return publicApiFetch<ProductDetail>(`/api/v1/catalog/products/${encodeURIComponent(slug)}/`, {
    tags: ["products", `product:${slug}`],
  });
}

export function getCategories() {
  return publicApiFetch<Paginated<Category>>("/api/v1/catalog/categories/", { tags: ["categories"] });
}

export function getBrands() {
  return publicApiFetch<Paginated<Brand>>("/api/v1/catalog/brands/", { tags: ["brands"] });
}

export function getReviews(productId: number) {
  return publicApiFetch<Paginated<Review>>(`/api/v1/catalog/products/${productId}/reviews/`, {
    revalidate: 120,
    tags: [`reviews:${productId}`],
  });
}
