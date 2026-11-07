"use client";

import { useQuery } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import Link from "next/link";

import { clientApi } from "@/shared/api/client";
import type { Order, Paginated } from "@/shared/api/contracts";
import { ApiError } from "@/shared/api/errors";
import { formatEgp } from "@/shared/lib/money";
import { buttonVariants } from "@/shared/ui/button";

export function OrdersView() {
  const query = useQuery({ queryKey: ["orders"], queryFn: () => clientApi<Paginated<Order>>("/api/backend/orders"), retry: false });
  if (query.isPending) return <div className="grid place-items-center py-24"><LoaderCircle className="animate-spin"/></div>;
  if (query.error instanceof ApiError && query.error.status === 401) return <div className="surface p-10 text-center"><h2 className="font-display text-4xl">Sign in to see your orders.</h2><Link href="/login?next=/orders" className={`${buttonVariants()} mt-6`}>Sign in</Link></div>;
  if (!query.data?.results.length) return <div className="surface p-10 text-center"><h2 className="font-display text-4xl">No orders yet.</h2><Link href="/products" className={`${buttonVariants()} mt-6`}>Start shopping</Link></div>;
  return <div className="grid gap-3">{query.data.results.map((order) => <Link key={order.id} href={`/orders/${order.id}`} className="surface grid gap-5 p-6 transition hover:-translate-y-0.5 sm:grid-cols-[1fr_auto_auto] sm:items-center"><div><p className="eyebrow">{order.reference}</p><h2 className="mt-2 font-display text-2xl">{order.items.length} {order.items.length === 1 ? "piece" : "pieces"}</h2><p className="mt-1 text-xs text-ink/45">{new Date(order.created_at).toLocaleDateString("en-EG", { dateStyle: "medium" })}</p></div><span className="w-fit rounded-full bg-ink/6 px-3 py-1.5 text-xs font-semibold capitalize">{order.status}</span><strong>{formatEgp(order.total)}</strong></Link>)}</div>;
}
