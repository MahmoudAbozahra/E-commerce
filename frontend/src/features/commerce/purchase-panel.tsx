"use client";

import { Heart, LoaderCircle, ShoppingBag } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import type { Product, ProductDetail, ProductVariant } from "@/shared/api/contracts";
import { ApiError } from "@/shared/api/errors";
import { clientApi } from "@/shared/api/client";
import { cn } from "@/shared/lib/cn";
import { formatEgp } from "@/shared/lib/money";
import { Button, buttonVariants } from "@/shared/ui/button";

import { VariantOptionOrbit } from "./variant-option-orbit";

function optionsFor(variants: ProductVariant[]) {
  const groups = new Map<string, Set<string>>();
  variants.forEach((variant) => Object.entries(variant.option_values ?? {}).forEach(([key, value]) => {
    if (!groups.has(key)) groups.set(key, new Set());
    groups.get(key)?.add(String(value));
  }));
  return [...groups].map(([name, values]) => ({ name, values: [...values] }));
}

export function PurchasePanel({ product, compact = false, onComplete }: { product: Product | ProductDetail; compact?: boolean; onComplete?: () => void }) {
  const router = useRouter();
  const variants = useMemo(() => [...(product.variants ?? [])], [product.variants]);
  const availableVariants = variants.filter((variant) => variant.is_active && variant.stock > 0);
  const initial = availableVariants[0] ?? variants[0];
  const [selection, setSelection] = useState<Record<string, string>>(() =>
    Object.fromEntries(Object.entries(initial?.option_values ?? {}).map(([key, value]) => [key, String(value)])),
  );
  const [status, setStatus] = useState<"idle" | "adding" | "added">("idle");
  const [message, setMessage] = useState("");
  const groups = useMemo(() => optionsFor(variants), [variants]);
  const selected = variants.find((variant) =>
    Object.entries(selection).every(([key, value]) => String((variant.option_values as Record<string, unknown> | undefined)?.[key]) === value),
  );
  const canBuy = Boolean(selected?.is_active && selected.stock > 0);

  function selectOption(name: string, value: string) {
    const nextSelection = { ...selection, [name]: value };
    const exactVariant = variants.find((variant) =>
      Object.entries(nextSelection).every(([key, option]) => String((variant.option_values as Record<string, unknown> | undefined)?.[key]) === option),
    );
    if (exactVariant) {
      setSelection(Object.fromEntries(Object.entries(exactVariant.option_values ?? {}).map(([key, option]) => [key, String(option)])));
      return;
    }
    setSelection(nextSelection);
  }

  async function addToCart() {
    if (!selected || !canBuy) return;
    setStatus("adding");
    setMessage("");
    try {
      await clientApi("/api/backend/cart/items", { method: "POST", body: JSON.stringify({ variant_id: selected.id, quantity: 1 }) });
      setStatus("added");
      setMessage("Added to your bag.");
      onComplete?.();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        router.push(`/login?next=${encodeURIComponent(`/products/${product.slug}`)}`);
        return;
      }
      setStatus("idle");
      setMessage(error instanceof Error ? error.message : "Could not add this item.");
    }
  }

  async function addToWishlist() {
    try {
      await clientApi("/api/backend/wishlist", { method: "POST", body: JSON.stringify({ product_id: product.id }) });
      setMessage("Saved to your wishlist.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) router.push(`/login?next=${encodeURIComponent(`/products/${product.slug}`)}`);
      else setMessage(error instanceof Error ? error.message : "Could not save this item.");
    }
  }

  return (
    <div className={cn("grid gap-5", compact && "gap-4")}>
      <div>
        <p className="eyebrow">{product.brand.name}</p>
        <h2 className={cn("mt-2 break-words font-display text-4xl leading-none tracking-[-.04em]", !compact && "md:text-5xl 2xl:text-6xl")}>{product.name}</h2>
        <div className="mt-4 flex items-center gap-3"><p className="text-lg font-semibold">{formatEgp(selected?.price ?? product.min_price)}</p><span className={cn("rounded-full px-3 py-1 text-xs", canBuy ? "bg-sage/12 text-sage" : "bg-clay/10 text-clay")}>{canBuy ? `${selected?.stock} in stock` : "Unavailable"}</span></div>
      </div>

      {groups.map((group) => (
        <fieldset key={group.name} className="grid gap-2">
          <legend className="text-xs font-bold uppercase tracking-[.14em] text-ink/50">{group.name}</legend>
          {group.name.toLowerCase() === "size" ? (
            <div className="flex flex-wrap gap-2">
              {group.values.map((value) => {
                const chosen = selection[group.name] === value;
                return <button key={value} type="button" aria-pressed={chosen} className={cn("min-h-10 rounded-full border px-4 text-sm capitalize transition", chosen ? "border-ink bg-ink text-canvas" : "border-ink/14 bg-white/50 hover:border-ink/45")} onClick={() => selectOption(group.name, value)}>{value}</button>;
              })}
            </div>
          ) : <VariantOptionOrbit name={group.name} values={group.values} selected={selection[group.name] ?? group.values[0]} onSelect={(value) => selectOption(group.name, value)} />}
        </fieldset>
      ))}

      <div className="flex flex-wrap gap-2">
        <Button onClick={addToCart} disabled={!canBuy || status === "adding"} className="flex-1">
          {status === "adding" ? <LoaderCircle className="animate-spin" size={17} /> : <ShoppingBag size={17} />}
          {status === "added" ? "Added" : "Add to bag"}
        </Button>
        <Button type="button" variant="secondary" aria-label="Add to wishlist" onClick={addToWishlist}><Heart size={17} /></Button>
      </div>
      {message && <p role="status" className="text-sm text-ink/62">{message}</p>}
      {compact && <Link href={`/products/${product.slug}`} className={buttonVariants({ variant: "ghost" })}>View full product details</Link>}
    </div>
  );
}
