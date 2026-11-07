import type { Metadata } from "next";

import { OrdersView } from "@/features/orders/orders-view";

export const metadata: Metadata = { title: "Your orders" };
export default function OrdersPage() { return <div className="narrow-shell py-14 md:py-20"><p className="eyebrow">Account history</p><h1 className="section-title mb-10 mt-4">Your orders.</h1><OrdersView/></div>; }
