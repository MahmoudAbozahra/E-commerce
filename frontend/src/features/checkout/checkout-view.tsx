"use client";

import { useQuery } from "@tanstack/react-query";
import { LoaderCircle, LockKeyhole } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { clientApi } from "@/shared/api/client";
import type { Address, Order, Paginated, ShippingMethod } from "@/shared/api/contracts";
import { ApiError } from "@/shared/api/errors";
import { formatEgp } from "@/shared/lib/money";
import { Button, buttonVariants } from "@/shared/ui/button";

type Quote = { subtotal: string; coupon_discount: string; points: number; points_discount: string; shipping_fee: string; tax: string; total: string; currency: string; disclaimer: string };
type FormValues = { address_id: number; shipping_method_id: number; coupon_code: string; points: number };

export function CheckoutView() {
  const router = useRouter();
  const [quote, setQuote] = useState<Quote | null>(null);
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const keyRef = useRef<string | null>(null);
  const [values, setValues] = useState<FormValues>({ address_id: 0, shipping_method_id: 0, coupon_code: "", points: 0 });
  const query = useQuery({
    queryKey: ["checkout-foundation"],
    queryFn: async () => {
      const [addresses, shipping] = await Promise.all([clientApi<Paginated<Address>>("/api/backend/users/addresses"), clientApi<Paginated<ShippingMethod>>("/api/backend/shipping/methods")]);
      return { addresses: addresses.results, shipping: shipping.results };
    },
    retry: false,
  });
  const effective = { ...values, address_id: values.address_id || query.data?.addresses[0]?.id || 0, shipping_method_id: values.shipping_method_id || query.data?.shipping[0]?.id || 0 };
  function change(patch: Partial<FormValues>) { setValues((current) => ({ ...current, ...patch })); setQuote(null); keyRef.current = null; }

  async function getQuote() {
    setMessage("");
    try { setQuote(await clientApi<Quote>("/api/backend/checkout/preview", { method: "POST", body: JSON.stringify(effective) })); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Could not calculate this order."); }
  }
  async function placeOrder() {
    setSubmitting(true); setMessage("");
    keyRef.current ??= crypto.randomUUID();
    try {
      const order = await clientApi<Order>("/api/backend/checkout", { method: "POST", headers: { "Idempotency-Key": keyRef.current }, body: JSON.stringify(effective) });
      router.replace(`/orders/${order.id}?placed=1`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Checkout could not be completed.");
      if (error instanceof ApiError && error.status < 500) keyRef.current = null;
      setSubmitting(false);
    }
  }

  if (query.isPending) return <div className="grid place-items-center py-24"><LoaderCircle className="animate-spin"/><span className="sr-only">Preparing checkout</span></div>;
  if (query.error instanceof ApiError && query.error.status === 401) return <div className="surface p-10 text-center"><h2 className="font-display text-4xl">Sign in before checkout.</h2><Link href="/login?next=/checkout" className={`${buttonVariants()} mt-6`}>Sign in</Link></div>;
  if (query.isError || !query.data) return <p className="surface p-8 text-clay">Checkout is unavailable right now.</p>;
  if (!query.data.addresses.length) return <div className="surface p-10 text-center"><h2 className="font-display text-4xl">Add a delivery address first.</h2><p className="mt-4 text-sm text-ink/55">Django validates the selected address belongs to your account.</p><Link href="/account#addresses" className={`${buttonVariants()} mt-6`}>Add an address</Link></div>;
  return <div className="grid gap-8 lg:grid-cols-[1fr_390px]"><section className="surface p-6 md:p-8"><h2 className="font-display text-3xl">Delivery details</h2><div className="mt-7 grid gap-5"><label className="grid gap-2 text-sm font-semibold">Saved address<select className="h-12 rounded-2xl border border-ink/12 bg-white/60 px-4 font-normal" value={effective.address_id} onChange={(event) => change({ address_id: Number(event.target.value) })}>{query.data.addresses.map((address) => <option key={address.id} value={address.id}>{address.recipient} — {address.line1}, {address.city}</option>)}</select></label><label className="grid gap-2 text-sm font-semibold">Shipping method<select className="h-12 rounded-2xl border border-ink/12 bg-white/60 px-4 font-normal" value={effective.shipping_method_id} onChange={(event) => change({ shipping_method_id: Number(event.target.value) })}>{query.data.shipping.map((method) => <option key={method.id} value={method.id}>{method.name} · {formatEgp(method.flat_fee)} · {method.estimated_days_min}–{method.estimated_days_max} days</option>)}</select></label><div className="grid gap-4 sm:grid-cols-2"><label className="grid gap-2 text-sm font-semibold">Coupon code<input className="h-12 rounded-2xl border border-ink/12 bg-white/60 px-4 font-normal uppercase" value={values.coupon_code} onChange={(event) => change({ coupon_code: event.target.value.toUpperCase() })} placeholder="Optional"/></label><label className="grid gap-2 text-sm font-semibold">Loyalty points<input type="number" min="0" className="h-12 rounded-2xl border border-ink/12 bg-white/60 px-4 font-normal" value={values.points} onChange={(event) => change({ points: Math.max(0, Number(event.target.value)) })}/></label></div><div className="rounded-2xl border border-sage/20 bg-sage/7 p-4 text-sm"><strong>Payment: Cash on Delivery</strong><p className="mt-1 text-ink/55">No card gateway is connected or implied.</p></div><Button type="button" variant="secondary" onClick={getQuote}>Review authoritative total</Button></div></section><aside className="surface h-fit p-6 lg:sticky lg:top-28"><p className="eyebrow">Django-calculated total</p>{quote ? <dl className="mt-6 grid gap-3 text-sm"><div className="flex justify-between"><dt>Subtotal</dt><dd>{formatEgp(quote.subtotal)}</dd></div><div className="flex justify-between text-sage"><dt>Coupon</dt><dd>−{formatEgp(quote.coupon_discount)}</dd></div><div className="flex justify-between text-sage"><dt>Points</dt><dd>−{formatEgp(quote.points_discount)}</dd></div><div className="flex justify-between"><dt>Shipping</dt><dd>{formatEgp(quote.shipping_fee)}</dd></div><div className="flex justify-between border-t border-ink/10 pt-4 text-lg font-bold"><dt>Total</dt><dd>{formatEgp(quote.total)}</dd></div><p className="pt-2 text-xs leading-5 text-ink/45">{quote.disclaimer}</p></dl> : <p className="mt-5 text-sm leading-6 text-ink/50">Review the total before placing your order. Stock and all discounts are revalidated on submit.</p>}{message && <p role="alert" className="mt-5 rounded-2xl bg-clay/8 p-4 text-sm text-clay">{message}</p>}<Button className="mt-6 w-full" size="lg" disabled={!quote || submitting} onClick={placeOrder}>{submitting ? <LoaderCircle className="animate-spin" size={17}/> : <LockKeyhole size={17}/>} Place COD order</Button><p className="mt-4 text-center text-xs text-ink/42">Duplicate clicks reuse one Idempotency-Key.</p></aside></div>;
}
