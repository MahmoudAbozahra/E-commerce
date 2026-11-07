import type { Metadata } from "next";

import { CartView } from "@/features/cart/cart-view";

export const metadata: Metadata = { title: "Your bag", robots: { index: false, follow: false } };
export default function CartPage() { return <div className="page-shell py-14 md:py-20"><p className="eyebrow">Saved to your account</p><h1 className="section-title mb-10 mt-4">Your bag.</h1><CartView/></div>; }
