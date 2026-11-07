/* eslint-disable @next/next/no-html-link-for-pages */
import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Pagination } from "@/features/catalog/pagination";
import { ProductCard } from "@/features/catalog/product-card";
import { ApiError } from "@/shared/api/errors";
import { getCategories, getProducts } from "@/shared/api/server";

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<{ page?: string }> };

async function categoryFor(slug: string) {
  const categories = await getCategories();
  return categories.results.find((category) => category.slug === slug);
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const category = await categoryFor(slug);
  if (!category) return { title: "Category not found" };
  return { title: category.name, description: category.description || `Shop ${category.name} at Atelier Cairo.`, alternates: { canonical: `/categories/${slug}` } };
}

export default async function CategoryPage({ params, searchParams }: Props) {
  const [{ slug }, query] = await Promise.all([params, searchParams]);
  const category = await categoryFor(slug);
  if (!category) notFound();
  const page = Math.max(1, Number(query.page) || 1);
  let products;
  try { products = await getProducts({ category: slug, available: true, page }); } catch (error) { if (error instanceof ApiError && error.status === 404) notFound(); throw error; }
  return <div className="page-shell py-14 md:py-20"><nav aria-label="Breadcrumb" className="text-xs text-ink/45"><a href="/">Home</a> / <a href="/products">Collection</a> / <span aria-current="page">{category.name}</span></nav><p className="eyebrow mt-12">Category edit</p><h1 className="display-title mt-5 max-w-5xl">{category.name}</h1><p className="mt-6 max-w-2xl text-base leading-7 text-ink/58">{category.description || `Explore every active ${category.name.toLowerCase()} piece in the current collection.`}</p><div className="mt-14 grid grid-cols-2 gap-x-3 gap-y-10 md:grid-cols-3 md:gap-x-6 lg:grid-cols-4">{products.results.map((product, index) => <ProductCard key={product.id} product={product} priority={index < 4}/>)}</div>{!products.results.length && <p className="surface mt-12 p-10 text-center text-ink/55">This category has no available pieces right now.</p>}<Pagination page={page} count={products.count} searchParams={{}}/><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({ "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: "Home", item: "/" }, { "@type": "ListItem", position: 2, name: category.name, item: `/categories/${slug}` }] }).replace(/</g, "\\u003c") }}/></div>;
}
