"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, Minus, Plus, Trash2 } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { clientApi } from "@/shared/api/client";
import type { Cart } from "@/shared/api/contracts";
import { ApiError } from "@/shared/api/errors";
import { formatEgp } from "@/shared/lib/money";
import { mediaUrl } from "@/shared/lib/urls";
import { buttonVariants } from "@/shared/ui/button";

export function CartView() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["cart"], queryFn: () => clientApi<Cart>("/api/backend/cart"), retry: false });
  async function mutate(path: string, init: RequestInit) {
    await clientApi(path, init);
    await queryClient.invalidateQueries({ queryKey: ["cart"] });
  }
  if (query.isPending) return <div className="grid place-items-center py-28" role="status"><LoaderCircle className="animate-spin"/><span className="sr-only">Loading bag</span></div>;
  if (query.error instanceof ApiError && query.error.status === 401) return <div className="surface p-10 text-center"><h2 className="font-display text-4xl">Your bag follows your account.</h2><p className="mx-auto mt-4 max-w-md text-sm text-ink/55">The Django cart is customer-owned, so sign in to view or add pieces.</p><Link className={`${buttonVariants()} mt-7`} href="/login?next=/cart">Sign in to continue</Link></div>;
  if (query.isError || !query.data) return <p role="alert" className="surface p-8 text-clay">We could not load your bag.</p>;
  const cart = query.data;
  if (!cart.items.length) return <div className="surface p-12 text-center"><p className="eyebrow">Nothing tucked away</p><h2 className="mt-4 font-display text-5xl">Your bag is light.</h2><Link className={`${buttonVariants()} mt-7`} href="/products">Explore the collection</Link></div>;
  return <div className="grid gap-8 lg:grid-cols-[1fr_360px]"><div className="grid gap-3">{cart.items.map((item) => { const image = mediaUrl(item.variant.product_primary_image?.url); return <article className="surface grid grid-cols-[100px_1fr] gap-4 p-3 sm:grid-cols-[140px_1fr]" key={item.id}><Link href={`/products/${item.variant.product_slug}`} className="product-media relative aspect-[4/5] overflow-hidden rounded-2xl">{image && <Image src={image} alt={item.variant.product_primary_image?.alt_text || item.variant.product_name} fill sizes="140px" unoptimized={image.endsWith(".svg")}/>}</Link><div className="flex min-w-0 flex-col justify-between gap-4 py-2 pr-2"><div><p className="eyebrow">{item.variant.sku}</p><h2 className="mt-1 font-display text-2xl">{item.variant.product_name}</h2><p className="mt-2 text-xs capitalize text-ink/50">{Object.entries(item.variant.option_values ?? {}).map(([key, value]) => `${key}: ${value}`).join(" · ")}</p></div><div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center rounded-full border border-ink/12"><button className="icon-button" type="button" aria-label={`Decrease ${item.variant.product_name} quantity`} disabled={item.quantity <= 1} onClick={() => mutate(`/api/backend/cart/items/${item.id}`, { method: "PATCH", body: JSON.stringify({ quantity: item.quantity - 1 }) })}><Minus size={14}/></button><span className="w-7 text-center text-sm">{item.quantity}</span><button className="icon-button" type="button" aria-label={`Increase ${item.variant.product_name} quantity`} disabled={item.quantity >= item.variant.stock} onClick={() => mutate(`/api/backend/cart/items/${item.id}`, { method: "PATCH", body: JSON.stringify({ quantity: item.quantity + 1 }) })}><Plus size={14}/></button></div><div className="flex items-center gap-3"><strong>{formatEgp(item.line_total)}</strong><button type="button" className="icon-button text-clay" aria-label={`Remove ${item.variant.product_name}`} onClick={() => mutate(`/api/backend/cart/items/${item.id}`, { method: "DELETE" })}><Trash2 size={16}/></button></div></div></div></article>; })}</div><aside className="surface h-fit p-6 lg:sticky lg:top-28"><p className="eyebrow">Order summary</p><div className="mt-6 flex justify-between border-b border-ink/10 pb-5"><span>Subtotal</span><strong>{formatEgp(cart.subtotal)}</strong></div><p className="mt-4 text-xs leading-5 text-ink/50">Shipping, coupons and loyalty points are calculated authoritatively by Django at checkout.</p><Link href="/checkout" className={`${buttonVariants({ size: "lg" })} mt-6 w-full`}>Continue to checkout</Link></aside></div>;
}
