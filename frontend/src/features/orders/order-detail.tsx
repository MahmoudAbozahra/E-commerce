"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { clientApi } from "@/shared/api/client";
import type { Order } from "@/shared/api/contracts";
import { formatEgp } from "@/shared/lib/money";
import { Button, buttonVariants } from "@/shared/ui/button";

export function OrderDetail({ id }: { id: string }) {
  const search = useSearchParams();
  const client = useQueryClient();
  const query = useQuery({ queryKey: ["order", id], queryFn: () => clientApi<Order>(`/api/backend/orders/${id}`), retry: false });
  if (query.isPending) return <div className="grid place-items-center py-24"><LoaderCircle className="animate-spin"/></div>;
  if (!query.data) return <div className="surface p-10 text-center"><h2 className="font-display text-4xl">Order not found.</h2><Link className={`${buttonVariants()} mt-6`} href="/orders">Back to orders</Link></div>;
  const order = query.data;
  const cancellable = ["pending", "confirmed"].includes(order.status);
  return <div>{search.get("placed") === "1" && <div className="mb-6 flex items-center gap-3 rounded-3xl bg-sage/10 p-5 text-sage"><CheckCircle2/><p><strong>Your order is placed.</strong><br/><span className="text-sm">Keep reference {order.reference} for your records.</span></p></div>}<div className="grid gap-7 lg:grid-cols-[1fr_340px]"><section className="surface p-6 md:p-8"><div className="flex flex-wrap justify-between gap-4"><div><p className="eyebrow">Order {order.reference}</p><h1 className="mt-3 font-display text-4xl capitalize">{order.status}</h1></div>{cancellable && <Button variant="secondary" onClick={async () => { await clientApi(`/api/backend/orders/${id}/cancel`, { method: "POST" }); await client.invalidateQueries({ queryKey: ["order", id] }); }}>Cancel order</Button>}</div><div className="mt-8 grid gap-3">{order.items.map((item) => <div key={item.id} className="flex justify-between gap-4 border-t border-ink/8 pt-4"><div><strong>{item.product_name}</strong><p className="mt-1 text-xs text-ink/45">{item.sku} · Qty {item.quantity}</p></div><span>{formatEgp(item.line_total)}</span></div>)}</div></section><aside className="surface h-fit p-6"><p className="eyebrow">Paid on delivery</p><dl className="mt-6 grid gap-3 text-sm"><div className="flex justify-between"><dt>Subtotal</dt><dd>{formatEgp(order.subtotal)}</dd></div><div className="flex justify-between"><dt>Coupon</dt><dd>−{formatEgp(order.coupon_discount)}</dd></div><div className="flex justify-between"><dt>Points</dt><dd>−{formatEgp(order.points_discount)}</dd></div><div className="flex justify-between"><dt>Shipping</dt><dd>{formatEgp(order.shipping_fee)}</dd></div><div className="flex justify-between border-t border-ink/10 pt-4 text-lg font-bold"><dt>Total</dt><dd>{formatEgp(order.total)}</dd></div></dl><p className="mt-6 text-xs leading-5 text-ink/45">Returns are available for delivered order items through the Django return workflow. The dedicated storefront return form remains a follow-up.</p></aside></div></div>;
}
