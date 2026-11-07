import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthForm } from "@/features/auth/auth-form";

export const metadata: Metadata = { title: "Create account" };
export default function RegisterPage() { return <div className="narrow-shell grid min-h-[70vh] place-items-center py-16"><section className="surface w-full max-w-2xl p-7 md:p-10"><p className="eyebrow">Join the studio</p><h1 className="mt-3 font-display text-5xl tracking-[-.04em]">Make the collection yours.</h1><p className="mb-8 mt-4 text-sm leading-6 text-ink/55">An account is required because the current Django cart is customer-owned.</p><Suspense><AuthForm mode="register"/></Suspense></section></div>; }
