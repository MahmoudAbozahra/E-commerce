import Link from "next/link";

import { buttonVariants } from "@/shared/ui/button";

export default function NotFound() {
  return <section className="narrow-shell py-28 text-center"><p className="eyebrow">404</p><h1 className="section-title mt-4">That piece is no longer on the rail.</h1><p className="mx-auto mt-5 max-w-lg text-ink/60">The product may have moved, been archived, or the address may be incorrect.</p><Link href="/products" className={`${buttonVariants()} mt-8`}>Explore the collection</Link></section>;
}
