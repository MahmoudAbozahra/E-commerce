"use client";

import { motion, type PanInfo, useReducedMotion } from "motion/react";
import { ArrowLeft, ArrowRight, RotateCw } from "lucide-react";
import { useState } from "react";

import type { ProductDetail } from "@/shared/api/contracts";
import { circularIndex, circularOffset } from "@/shared/lib/circular-carousel";
import { orbitSpring } from "@/shared/lib/motion";
import { mediaUrl } from "@/shared/lib/urls";
import { ResilientImage } from "@/shared/ui/resilient-image";

export function ProductGallery({ product }: { product: ProductDetail }) {
  const images = product.images?.length
    ? product.images.map((image) => ({ url: mediaUrl(image.image), alt: image.alt_text || `${product.name} product view` })).filter((image): image is { url: string; alt: string } => Boolean(image.url))
    : product.primary_image?.url ? [{ url: mediaUrl(product.primary_image.url) as string, alt: product.primary_image.alt_text || `${product.name} product view` }] : [];
  const [active, setActive] = useState(0);
  const reducedMotion = useReducedMotion();
  const rotate = (direction: number) => setActive((current) => circularIndex(current + direction, images.length));
  const onDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (Math.abs(info.offset.x) < 35) return;
    rotate(info.offset.x < 0 ? 1 : -1);
  };

  if (!images.length) return <div className="product-media grid aspect-[4/5] place-items-center rounded-[2.5rem] text-sm text-ink/40">Product image coming soon</div>;

  const orbitItems = images.length === 2
    ? [
        { image: images[circularIndex(active - 1, images.length)], index: circularIndex(active - 1, images.length), offset: -1, key: "left" },
        { image: images[active], index: active, offset: 0, key: "centre" },
        { image: images[circularIndex(active + 1, images.length)], index: circularIndex(active + 1, images.length), offset: 1, key: "right" },
      ]
    : images.map((image, index) => ({ image, index, offset: circularOffset(index, active, images.length), key: String(index) }));

  return (
    <section aria-label={`${product.name} circular image gallery`} className="relative">
      <div className="relative h-[min(72vh,720px)] min-h-[500px] overflow-hidden rounded-[2.5rem] bg-[radial-gradient(circle_at_50%_42%,rgba(255,253,248,.98),rgba(232,228,219,.72)_72%)]">
        <div className="pointer-events-none absolute left-[8%] right-[8%] top-8 h-px bg-ink/18" aria-hidden="true" />
        <motion.div className="absolute inset-0 cursor-grab touch-pan-y active:cursor-grabbing" drag={images.length > 1 && !reducedMotion ? "x" : false} dragConstraints={{ left: 0, right: 0 }} dragElastic={0.12} onDragEnd={onDragEnd}>
          {orbitItems.map(({ image, index, offset, key }) => {
            const distance = Math.abs(offset);
            const visible = distance <= 2;
            const angle = offset * (Math.PI / 5.2);
            const x = Math.sin(angle) * 42;
            const y = (1 - Math.cos(angle)) * 48;
            const isActive = offset === 0;
            return (
              <motion.button
                type="button"
                key={`${key}-${image.url}`}
                aria-label={isActive ? `Current image ${index + 1} of ${images.length}` : `Rotate to image ${index + 1}`}
                aria-current={isActive ? "true" : undefined}
                tabIndex={visible ? 0 : -1}
                onClick={() => setActive(index)}
                className="absolute left-1/2 top-[8%] aspect-[4/5] w-[min(72%,520px)] -translate-x-1/2 overflow-hidden rounded-[2rem] border border-white/75 bg-paper p-0 shadow-soft [will-change:transform,opacity] focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
                style={{ zIndex: 10 - distance, pointerEvents: visible ? "auto" : "none" }}
                initial={false}
                animate={{ x: `${x}vw`, y, scale: isActive ? 1 : Math.max(0.56, 0.78 - distance * 0.08), rotateY: offset * -16, opacity: visible ? (isActive ? 1 : 0.36) : 0 }}
                transition={reducedMotion ? { duration: 0 } : orbitSpring}
              >
                <ResilientImage src={image.url} alt={isActive ? image.alt : ""} fallbackLabel={`Image ${index + 1} unavailable for ${product.name}`} fill priority={isActive} sizes="(max-width: 768px) 78vw, 46vw" unoptimized={image.url.endsWith(".svg")} />
              </motion.button>
            );
          })}
        </motion.div>
        {images.length > 1 && (
          <div className="absolute inset-x-0 bottom-6 z-30 flex items-center justify-center gap-3">
            <button type="button" className="icon-button border border-ink/12 bg-canvas/90 backdrop-blur" aria-label="Previous product image" onClick={() => rotate(-1)}><ArrowLeft size={18} /></button>
            <span className="inline-flex min-w-24 items-center justify-center gap-2 text-[.67rem] font-bold uppercase tracking-[.15em] text-ink/45"><RotateCw size={13} /> {active + 1} / {images.length}</span>
            <button type="button" className="icon-button border border-ink/12 bg-canvas/90 backdrop-blur" aria-label="Next product image" onClick={() => rotate(1)}><ArrowRight size={18} /></button>
          </div>
        )}
      </div>
      {images.length > 1 && <p className="mt-3 text-center text-xs text-ink/42">Drag or use the arrows to rotate through every view.</p>}
    </section>
  );
}
