import type { Metadata } from "next";

import { CatalogFilters } from "@/features/catalog/catalog-filters";
import { Pagination } from "@/features/catalog/pagination";
import { ProductCard } from "@/features/catalog/product-card";
import { getBrands, getCategories, getProducts } from "@/shared/api/server";

type Params = Promise<Record<string, string | string[] | undefined>>;
const first = (value: string | string[] | undefined) => Array.isArray(value) ? value[0] : value;

export async function generateMetadata({ searchParams }: { searchParams: Params }): Promise<Metadata> {
  const params = await searchParams;
  const hasFacet = ["search", "category", "brand", "min_price", "max_price", "ordering"].some((key) => first(params[key]));
  return { title: "Shop the collection", description: "Browse active products, live prices and availability from Atelier Cairo.", alternates: { canonical: "/products" }, robots: hasFacet ? { index: false, follow: true } : undefined };
}

export default async function ProductsPage({ searchParams }: { searchParams: Params }) {
  const raw = await searchParams;
  const values = Object.fromEntries(Object.entries(raw).map(([key, value]) => [key, first(value)]));
  const page = Math.max(1, Number(values.page) || 1);
  const [products, categories, brands] = await Promise.all([getProducts({ search: values.search, category: values.category, brand: values.brand, min_price: values.min_price, max_price: values.max_price, ordering: values.ordering, available: true, page }), getCategories(), getBrands()]);
  return <div className="page-shell py-14 md:py-20"><p className="eyebrow">Live catalog</p><div className="mb-10 mt-4 flex flex-wrap items-end justify-between gap-4"><h1 className="section-title">Shop the collection.</h1><p className="text-sm text-ink/50">{products.count} pieces</p></div><CatalogFilters categories={categories.results} brands={brands.results} values={values}/>{products.results.length ? <div className="grid grid-cols-2 gap-x-3 gap-y-10 md:grid-cols-3 md:gap-x-6 lg:grid-cols-4">{products.results.map((product, index) => <ProductCard key={product.id} product={product} priority={index < 4}/>)}</div> : <div className="surface p-12 text-center"><h2 className="font-display text-3xl">Nothing matched that edit.</h2><p className="mt-3 text-sm text-ink/55">Try removing a filter or using a broader search.</p></div>}<Pagination page={page} count={products.count} searchParams={values}/></div>;
}
