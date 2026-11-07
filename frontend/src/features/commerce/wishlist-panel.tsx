"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Heart, Trash2 } from "lucide-react";
import Link from "next/link";

import { clientApi } from "@/shared/api/client";
import type { Paginated } from "@/shared/api/contracts";
import { formatEgp } from "@/shared/lib/money";

type WishlistItem = {
  id: number;
  product: { id: number; name: string; slug: string; min_price: string | null; available: boolean };
  created_at: string;
};

export function WishlistPanel() {
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["wishlist"], queryFn: () => clientApi<Paginated<WishlistItem>>("/api/backend/wishlist"), retry: false });
  if (query.isError) return null;
  return (
    <section id="wishlist" className="surface mt-7 p-7 md:p-9">
      <div className="flex items-end justify-between gap-4"><div><p className="eyebrow">Wishlist</p><h2 className="mt-3 font-display text-4xl">Saved pieces.</h2></div><Heart aria-hidden="true" className="text-ink/25"/></div>
      {query.data?.results.length ? <div className="mt-7 grid gap-3 sm:grid-cols-2">{query.data.results.map((item) => <article key={item.id} className="flex items-center justify-between gap-3 rounded-2xl border border-ink/10 p-4"><Link href={`/products/${item.product.slug}`} className="min-w-0"><h3 className="truncate font-semibold">{item.product.name}</h3><p className="mt-1 text-xs text-ink/48">{item.product.min_price ? formatEgp(item.product.min_price) : "Price unavailable"} · {item.product.available ? "Available" : "Unavailable"}</p></Link><button className="icon-button shrink-0 text-clay" type="button" aria-label={`Remove ${item.product.name} from wishlist`} onClick={async () => { await clientApi(`/api/backend/wishlist/${item.id}`, { method: "DELETE" }); await client.invalidateQueries({ queryKey: ["wishlist"] }); }}><Trash2 size={16}/></button></article>)}</div> : <p className="mt-6 text-sm text-ink/50">Pieces saved with the heart button appear here.</p>}
    </section>
  );
}
