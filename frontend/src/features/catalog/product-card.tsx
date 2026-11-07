import { ArrowUpRight } from "lucide-react";
import Link from "next/link";

import { ProductMedia } from "@/features/catalog/product-media";
import type { Product } from "@/shared/api/contracts";
import { formatEgp } from "@/shared/lib/money";

export function ProductCard({ product, priority = false }: { product: Product; priority?: boolean }) {
  return (
    <article className="group min-w-0">
      <Link href={`/products/${product.slug}`} className="block rounded-[2rem] focus:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-4">
        <ProductMedia product={product} priority={priority} className="aspect-[4/5] rounded-[2rem] transition duration-500 group-hover:-translate-y-1 group-hover:shadow-soft" />
        <div className="flex items-start justify-between gap-4 px-1 pt-4">
          <div><h2 className="font-semibold tracking-tight">{product.name}</h2><p className="mt-1 text-xs text-ink/50">{product.brand.name}</p></div>
          <div className="text-right"><p className="text-sm font-semibold">{formatEgp(product.min_price)}</p><ArrowUpRight className="ml-auto mt-2 opacity-0 transition group-hover:opacity-60" size={15} aria-hidden="true" /></div>
        </div>
      </Link>
    </article>
  );
}
