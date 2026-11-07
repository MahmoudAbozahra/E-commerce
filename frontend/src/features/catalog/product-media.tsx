import type { Product, ProductDetail } from "@/shared/api/contracts";
import { cn } from "@/shared/lib/cn";
import { mediaUrl } from "@/shared/lib/urls";
import { ResilientImage } from "@/shared/ui/resilient-image";

export function ProductMedia({ product, className, priority = false, sizes = "(max-width: 768px) 80vw, 33vw" }: { product: Product | ProductDetail; className?: string; priority?: boolean; sizes?: string }) {
  const source = mediaUrl(product.primary_image?.url);
  return (
    <div className={cn("product-media", className)}>
      {source ? (
        <ResilientImage
          src={source}
          alt={product.primary_image?.alt_text || `${product.name} product view`}
          fallbackLabel={`Image unavailable for ${product.name}`}
          fill
          priority={priority}
          sizes={sizes}
          unoptimized={source.endsWith(".svg")}
        />
      ) : (
        <div className="absolute inset-0 grid place-items-center" aria-label={`Image not available for ${product.name}`}>
          <div className="grid aspect-[3/4] w-2/5 place-items-center rounded-[45%_45%_20%_20%] border border-ink/10 bg-ink/6 font-display text-4xl text-ink/25">{product.name.slice(0, 1)}</div>
        </div>
      )}
    </div>
  );
}
