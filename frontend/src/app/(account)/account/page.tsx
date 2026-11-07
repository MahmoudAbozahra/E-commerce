import type { Metadata } from "next";

import { AccountDashboard } from "@/features/auth/account-dashboard";
import { WishlistPanel } from "@/features/commerce/wishlist-panel";

export const metadata: Metadata = { title: "Your account" };
export default function AccountPage() { return <div className="page-shell py-14 md:py-20"><p className="eyebrow">Private store space</p><h1 className="section-title mb-10 mt-4">Your account.</h1><AccountDashboard/><WishlistPanel/></div>; }
