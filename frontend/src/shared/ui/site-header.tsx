import { Heart, Search, ShoppingBag } from "lucide-react";
import Link from "next/link";

import { SessionControls } from "@/features/auth/session-controls";
import { siteConfig } from "@/shared/config/site";
import { MobileNavigation } from "@/shared/ui/mobile-navigation";

const nav = [
  ["Home", "/"],
  ["New arrivals", "/products?ordering=-created_at"],
  ["All products", "/products"],
  ["Categories", "/#categories"],
] as const;

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-ink/8 bg-canvas/88 backdrop-blur-xl">
      <div className="page-shell grid h-18 grid-cols-[1fr_auto_1fr] items-center gap-3">
        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
          {nav.map(([label, href]) => <Link key={href} className="nav-pill" href={href}>{label}</Link>)}
        </nav>
        <MobileNavigation items={nav} />

        <Link href="/" className="brand-mark" aria-label={`${siteConfig.name} home`} title="Back to the storefront home">{siteConfig.name}</Link>

        <div className="flex items-center justify-end gap-1">
          <Link href="/products" className="icon-button" aria-label="Search products" title="Search products"><Search size={18} /></Link>
          <Link href="/account#wishlist" className="icon-button hidden sm:inline-flex" aria-label="Wishlist" title="Wishlist"><Heart size={18} /></Link>
          <Link href="/cart" className="icon-button" aria-label="Shopping bag" title="Shopping bag"><ShoppingBag size={18} /></Link>
          <SessionControls />
        </div>
      </div>
    </header>
  );
}
