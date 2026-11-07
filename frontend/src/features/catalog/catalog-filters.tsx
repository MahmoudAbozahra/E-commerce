import { Search } from "lucide-react";

import type { Brand, Category } from "@/shared/api/contracts";
import { Button } from "@/shared/ui/button";

export function CatalogFilters({ categories, brands, values }: { categories: Category[]; brands: Brand[]; values: Record<string, string | undefined> }) {
  return (
    <form className="surface mb-10 grid gap-3 p-4 md:grid-cols-[2fr_1fr_1fr_1fr_auto]" action="/products" method="get">
      <label className="relative"><span className="sr-only">Search products</span><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-ink/40" size={17}/><input name="search" defaultValue={values.search} className="h-12 w-full rounded-2xl border border-ink/10 bg-white/55 pl-11 pr-4 outline-none focus:border-ink" placeholder="Search by product or SKU"/></label>
      <label><span className="sr-only">Category</span><select name="category" defaultValue={values.category ?? ""} className="h-12 w-full rounded-2xl border border-ink/10 bg-white/55 px-3"><option value="">All categories</option>{categories.map((category) => <option key={category.id} value={category.slug}>{category.name}</option>)}</select></label>
      <label><span className="sr-only">Brand</span><select name="brand" defaultValue={values.brand ?? ""} className="h-12 w-full rounded-2xl border border-ink/10 bg-white/55 px-3"><option value="">All brands</option>{brands.map((brand) => <option key={brand.id} value={brand.slug}>{brand.name}</option>)}</select></label>
      <label><span className="sr-only">Sort products</span><select name="ordering" defaultValue={values.ordering ?? "-created_at"} className="h-12 w-full rounded-2xl border border-ink/10 bg-white/55 px-3"><option value="-created_at">Newest</option><option value="name">Name A–Z</option><option value="min_price">Price low to high</option><option value="-min_price">Price high to low</option></select></label>
      <Button type="submit" className="h-12 rounded-2xl px-6">Apply filters</Button>
    </form>
  );
}
