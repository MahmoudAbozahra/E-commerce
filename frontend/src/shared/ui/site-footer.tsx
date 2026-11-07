import Link from "next/link";

import { siteConfig } from "@/shared/config/site";

export function SiteFooter() {
  return (
    <footer className="mt-24 border-t border-ink/10 bg-mist/55">
      <div className="page-shell grid gap-10 py-14 md:grid-cols-[1.4fr_1fr_1fr]">
        <div><p className="brand-mark mb-4">{siteConfig.name}</p><p className="max-w-sm text-sm leading-6 text-ink/58">{siteConfig.description} Demo catalog imagery is illustrative and replaceable from Django admin.</p></div>
        <div><p className="footer-title">Explore</p><div className="grid gap-2 text-sm text-ink/65"><Link href="/products">Shop all</Link><Link href="/categories/apparel">Apparel</Link><Link href="/orders">Your orders</Link></div></div>
        <div><p className="footer-title">Store notes</p><p className="text-sm leading-6 text-ink/58">Prices are shown in EGP. Checkout currently supports Cash on Delivery through the store API.</p></div>
      </div>
      <div className="page-shell flex flex-wrap justify-between gap-3 border-t border-ink/8 py-5 text-xs text-ink/45"><span>© {new Date().getFullYear()} {siteConfig.name}</span><span>Built for accessible, indexable shopping.</span></div>
    </footer>
  );
}
