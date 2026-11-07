/* eslint-disable @next/next/no-html-link-for-pages */
import type { Metadata } from "next";
import { Star } from "lucide-react";
import { notFound } from "next/navigation";

import { ProductGallery } from "@/features/catalog/product-gallery";
import { PurchasePanel } from "@/features/commerce/purchase-panel";
import { ApiError } from "@/shared/api/errors";
import { getProduct, getReviews } from "@/shared/api/server";
import { siteConfig } from "@/shared/config/site";
import { absoluteMediaUrl } from "@/shared/lib/urls";

type Props = { params: Promise<{ slug: string }> };

async function productOr404(slug: string) {
  try { return await getProduct(slug); } catch (error) { if (error instanceof ApiError && error.status === 404) notFound(); throw error; }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const product = await productOr404(slug);
  const description = product.description.slice(0, 155);
  const image = absoluteMediaUrl(product.primary_image?.url, siteConfig.url);
  return {
    title: product.name,
    description,
    alternates: { canonical: `/products/${product.slug}` },
    openGraph: { type: "website", title: product.name, description, url: `/products/${product.slug}`, images: image ? [{ url: image, alt: product.primary_image?.alt_text || product.name }] : undefined },
    twitter: { card: image ? "summary_large_image" : "summary", title: product.name, description, images: image ? [image] : undefined },
  };
}

export default async function ProductPage({ params }: Props) {
  const { slug } = await params;
  const product = await productOr404(slug);
  const reviews = await getReviews(product.id);
  const availableVariants = product.variants.filter((variant) => variant.is_active && variant.stock > 0);
  const offer = [...(availableVariants.length ? availableVariants : product.variants)].sort((a, b) => Number(a.price) - Number(b.price))[0];
  const image = absoluteMediaUrl(product.primary_image?.url, siteConfig.url);
  const productJson: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name,
    description: product.description,
    image: image ? [image] : undefined,
    sku: offer?.sku,
    brand: { "@type": "Brand", name: product.brand.name },
    offers: offer ? { "@type": "Offer", url: `${siteConfig.url}/products/${product.slug}`, priceCurrency: "EGP", price: offer.price, availability: availableVariants.length ? "https://schema.org/InStock" : "https://schema.org/OutOfStock", itemCondition: "https://schema.org/NewCondition" } : undefined,
  };
  if (product.review_count && product.rating_average) productJson.aggregateRating = { "@type": "AggregateRating", ratingValue: product.rating_average, reviewCount: product.review_count };
  const breadcrumbJson = { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: "Home", item: siteConfig.url }, { "@type": "ListItem", position: 2, name: product.category.name, item: `${siteConfig.url}/categories/${product.category.slug}` }, { "@type": "ListItem", position: 3, name: product.name, item: `${siteConfig.url}/products/${product.slug}` }] };
  return (
    <article className="page-shell py-8 md:py-14">
      <nav aria-label="Breadcrumb" className="mb-8 text-xs text-ink/45"><a href="/">Home</a> / <a href={`/categories/${product.category.slug}`}>{product.category.name}</a> / <span aria-current="page">{product.name}</span></nav>
      <div className="grid gap-10 lg:grid-cols-[1.2fr_.8fr] lg:gap-16"><ProductGallery product={product}/><div className="min-w-0 lg:sticky lg:top-28 lg:self-start"><PurchasePanel product={product}/><div className="mt-8 border-t border-ink/10 pt-7"><h1 className="sr-only">{product.name}</h1><p className="leading-7 text-ink/62">{product.description}</p><dl className="mt-6 grid gap-3 text-sm"><div className="flex justify-between border-t border-ink/8 pt-3"><dt className="text-ink/45">Category</dt><dd>{product.category.name}</dd></div><div className="flex justify-between border-t border-ink/8 pt-3"><dt className="text-ink/45">Payment</dt><dd>Cash on Delivery</dd></div></dl></div></div></div>
      <section className="mt-24 border-t border-ink/10 pt-14" aria-labelledby="reviews-title"><div className="flex items-end justify-between"><div><p className="eyebrow">Verified voices only</p><h2 id="reviews-title" className="section-title mt-3">Customer notes.</h2></div>{product.review_count > 0 && <p className="flex items-center gap-2"><Star size={17} fill="currentColor"/> {product.rating_average} · {product.review_count}</p>}</div>{reviews.results.length ? <div className="mt-10 grid gap-4 md:grid-cols-2">{reviews.results.map((review) => <blockquote key={review.id} className="surface p-7"><div className="flex gap-1" aria-label={`${review.rating} out of 5 stars`}>{Array.from({ length: review.rating }, (_, index) => <Star key={index} size={14} fill="currentColor"/>)}</div><p className="mt-4 leading-7">“{review.comment}”</p><footer className="mt-5 text-xs text-ink/45">{review.username}</footer></blockquote>)}</div> : <p className="mt-8 text-sm text-ink/50">No approved reviews yet. Only customers with a delivered order can review this product.</p>}</section>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(productJson).replace(/</g, "\\u003c") }}/><script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbJson).replace(/</g, "\\u003c") }}/>
    </article>
  );
}
