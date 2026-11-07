import type { Metadata } from "next";

import { CheckoutView } from "@/features/checkout/checkout-view";

export const metadata: Metadata = { title: "Checkout", robots: { index: false, follow: false } };
export default function CheckoutPage() { return <div className="page-shell py-14 md:py-20"><p className="eyebrow">Secure store session</p><h1 className="section-title mb-10 mt-4">Checkout.</h1><CheckoutView/></div>; }
