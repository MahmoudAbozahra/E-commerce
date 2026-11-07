import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { ProductCard } from "@/features/catalog/product-card";
import { ProductRail } from "@/features/showcase/product-rail";
import { getCategories, getProducts } from "@/shared/api/server";
import { buttonVariants } from "@/shared/ui/button";

export default async function HomePage() {
  const [apparel, allProducts, categories] = await Promise.all([
    getProducts({ category: "apparel", available: true, ordering: "name", page_size: 24 }),
    getProducts({ available: true, ordering: "-created_at" }),
    getCategories(),
  ]);
  const featuredRail = apparel.results.filter((product) => product.featured);
  const railProducts = [
    ...featuredRail,
    ...apparel.results.filter((product) => !product.featured),
    ...(apparel.results.length ? [] : allProducts.results),
  ].slice(0, 10);
  const featured = allProducts.results.slice(0, 8);

  return (
    <>
      <ProductRail products={railProducts} />

      <section className="page-shell py-20 md:py-32" aria-labelledby="collection-title">
        <div className="mb-10 flex items-end justify-between gap-5 md:mb-14">
          <div><p className="eyebrow">Shop without the theatre</p><h2 id="collection-title" className="section-title mt-4">The full collection.</h2></div>
          <Link href="/products" className={`${buttonVariants({ variant: "secondary" })} hidden sm:inline-flex`}>See everything <ArrowRight size={16} /></Link>
        </div>
        {featured.length ? <div className="grid grid-cols-2 gap-x-3 gap-y-10 md:grid-cols-3 md:gap-x-6 lg:grid-cols-4">{featured.map((product, index) => <ProductCard key={product.id} product={product} priority={index < 2} />)}</div> : <p className="surface p-8 text-ink/60">No active products are available yet.</p>}
      </section>

      <section id="categories" className="scroll-mt-24 bg-ink py-20 text-canvas md:py-28" aria-labelledby="category-title">
        <div className="page-shell">
          <p className="eyebrow !text-canvas/50">Find your pace</p><h2 id="category-title" className="section-title mt-4 max-w-3xl">Browse by the way you live.</h2>
          <div className="mt-12 grid gap-px overflow-hidden rounded-[2rem] bg-canvas/15 md:grid-cols-3">
            {categories.results.slice(0, 6).map((category, index) => <Link href={`/categories/${category.slug}`} key={category.id} className="group min-h-48 bg-ink p-7 transition hover:bg-canvas/7"><span className="text-xs text-canvas/35">0{index + 1}</span><h3 className="mt-16 font-display text-3xl">{category.name}</h3><p className="mt-2 line-clamp-2 text-sm text-canvas/48">{category.description || "Explore the current edit."}</p></Link>)}
          </div>
        </div>
      </section>
    </>
  );
}
