import type { MetadataRoute } from "next";

import { getCategories, getProducts } from "@/shared/api/server";
import { siteConfig } from "@/shared/config/site";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [categories, firstPage] = await Promise.all([getCategories(), getProducts({ page: 1 })]);
  const products = [...firstPage.results];
  const pages = Math.ceil(firstPage.count / 20);
  for (let page = 2; page <= pages; page += 1) products.push(...(await getProducts({ page })).results);
  return [
    { url: siteConfig.url, changeFrequency: "daily", priority: 1 },
    { url: `${siteConfig.url}/products`, changeFrequency: "daily", priority: .9 },
    ...categories.results.map((category) => ({ url: `${siteConfig.url}/categories/${category.slug}`, changeFrequency: "weekly" as const, priority: .7 })),
    ...products.map((product) => ({ url: `${siteConfig.url}/products/${product.slug}`, lastModified: new Date(), changeFrequency: "weekly" as const, priority: .8 })),
  ];
}
