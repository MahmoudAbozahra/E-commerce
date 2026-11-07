import type { Metadata } from "next";
import { Suspense } from "react";

import { AuthForm } from "@/features/auth/auth-form";

export const metadata: Metadata = { title: "Sign in" };
export default function LoginPage() { return <div className="narrow-shell grid min-h-[70vh] place-items-center py-16"><section className="surface w-full max-w-lg p-7 md:p-10"><p className="eyebrow">Welcome back</p><h1 className="mt-3 font-display text-5xl tracking-[-.04em]">Your store, remembered.</h1><p className="mb-8 mt-4 text-sm leading-6 text-ink/55">Sign in to access your saved bag, wishlist and orders.</p><Suspense><AuthForm mode="login"/></Suspense></section></div>; }
