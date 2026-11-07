"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useState, type FormEvent } from "react";

import { clientApi } from "@/shared/api/client";
import type { Address, Paginated, User } from "@/shared/api/contracts";
import { ApiError } from "@/shared/api/errors";
import { Button, buttonVariants } from "@/shared/ui/button";

export function AccountDashboard() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState("");
  const sessionQuery = useQuery({ queryKey: ["session"], queryFn: () => clientApi<{ user: User }>("/api/auth/session"), retry: false });
  const addressesQuery = useQuery({ queryKey: ["account"], queryFn: () => clientApi<Paginated<Address>>("/api/backend/users/addresses"), retry: false });
  const query = {
    isPending: sessionQuery.isPending || addressesQuery.isPending,
    error: sessionQuery.error || addressesQuery.error,
    data: sessionQuery.data && addressesQuery.data ? { session: sessionQuery.data, addresses: addressesQuery.data } : undefined,
  };
  async function addAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("");
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    try { await clientApi("/api/backend/users/addresses", { method: "POST", body: JSON.stringify({ ...data, country: "EG", is_default: true }) }); form.reset(); await queryClient.invalidateQueries({ queryKey: ["account"] }); setMessage("Address saved."); } catch (error) { setMessage(error instanceof Error ? error.message : "Could not save address."); }
  }
  if (query.isPending) return <div className="grid place-items-center py-24"><LoaderCircle className="animate-spin"/></div>;
  if (query.error instanceof ApiError && query.error.status === 401) return <div className="surface p-10 text-center"><h2 className="font-display text-4xl">Sign in to open your account.</h2><Link href="/login?next=/account" className={`${buttonVariants()} mt-6`}>Sign in</Link></div>;
  if (!query.data) return <p className="surface p-8 text-clay">Account details are unavailable.</p>;
  const { user } = query.data.session;
  return <div className="grid gap-7 lg:grid-cols-[.7fr_1.3fr]"><aside className="surface h-fit p-7"><p className="eyebrow">Profile</p><h2 className="mt-4 font-display text-4xl">{user.first_name} {user.last_name}</h2><p className="mt-2 text-sm text-ink/50">@{user.username}<br/>{user.email}</p><Link href="/orders" className={`${buttonVariants({ variant: "secondary" })} mt-7 w-full`}>View orders</Link></aside><section id="addresses" className="surface p-7"><p className="eyebrow">Delivery book</p><h2 className="mt-3 font-display text-4xl">Saved addresses.</h2><div className="mt-6 grid gap-3">{query.data.addresses.results.map((address) => <div key={address.id} className="rounded-2xl border border-ink/10 p-4 text-sm"><div className="flex justify-between"><strong>{address.recipient}</strong>{address.is_default && <span className="text-xs text-sage">Default</span>}</div><p className="mt-2 leading-6 text-ink/55">{address.line1}{address.line2 ? `, ${address.line2}` : ""}<br/>{address.city}, {address.state} · {address.phone}</p></div>)}</div><form onSubmit={addAddress} className="mt-8 grid gap-3 border-t border-ink/10 pt-7 sm:grid-cols-2"><h3 className="font-display text-2xl sm:col-span-2">Add an Egyptian address</h3>{[["recipient","Recipient"],["phone","Phone"],["line1","Address line"],["line2","Apartment / floor"],["city","City"],["state","Governorate"],["postal_code","Postal code"]].map(([name,label]) => <label key={name} className="grid gap-1.5 text-xs font-bold uppercase tracking-[.1em]">{label}<input required={!new Set(["line2","postal_code"]).has(name)} name={name} className="h-11 rounded-xl border border-ink/12 bg-white/60 px-3 text-sm font-normal normal-case tracking-normal"/></label>)}<Button type="submit" className="mt-2 sm:col-span-2">Save address</Button>{message && <p role="status" className="text-sm text-ink/55 sm:col-span-2">{message}</p>}</form></section></div>;
}
