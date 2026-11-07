import type { Metadata } from "next";
import { Suspense } from "react";

import { OrderDetail } from "@/features/orders/order-detail";

export const metadata: Metadata = { title: "Order details" };
export default async function OrderPage({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <div className="narrow-shell py-14 md:py-20"><Suspense><OrderDetail id={id}/></Suspense></div>; }
