"use client";

import { AnimatePresence, LayoutGroup, motion, type PanInfo, useReducedMotion } from "motion/react";
import { ArrowLeft, ArrowRight, RotateCw, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { ProductMedia } from "@/features/catalog/product-media";
import { PurchasePanel } from "@/features/commerce/purchase-panel";
import type { Product } from "@/shared/api/contracts";
import { circularIndex, circularOffset } from "@/shared/lib/circular-carousel";
import { formatEgp } from "@/shared/lib/money";
import { orbitSpring } from "@/shared/lib/motion";

const ORBIT_STEP = Math.PI / 8.3;

export function ProductRail({ products }: { products: Product[] }) {
  const [active, setActive] = useState(() => Math.floor(products.length / 2));
  const [selected, setSelected] = useState<number | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const triggerRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const reducedMotion = useReducedMotion();

  const rotate = (direction: number) => setActive((current) => circularIndex(current + direction, products.length));
  const onDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (Math.abs(info.offset.x) < 35) return;
    rotate(info.offset.x < 0 ? 1 : -1);
  };

  useEffect(() => {
    if (selected === null) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        const previous = selected;
        setSelected(null);
        window.setTimeout(() => triggerRefs.current[previous]?.focus(), reducedMotion ? 0 : 240);
      }
      if (event.key === "ArrowRight") setSelected((current) => circularIndex((current ?? 0) + 1, products.length));
      if (event.key === "ArrowLeft") setSelected((current) => circularIndex((current ?? 0) - 1, products.length));
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKey);
    };
  }, [selected, products.length, reducedMotion]);

  function closePreview() {
    const previous = selected;
    setSelected(null);
    if (previous !== null) setActive(previous);
    window.setTimeout(() => {
      if (previous !== null) triggerRefs.current[previous]?.focus();
    }, reducedMotion ? 0 : 240);
  }

  if (!products.length) return null;
  const current = selected === null ? null : products[selected];

  return (
    <LayoutGroup id="home-rail">
      <section aria-labelledby="rail-title" className="relative min-h-[700px] overflow-hidden pt-14 md:min-h-[780px] md:pt-18">
        <div className="page-shell text-center">
          <p className="eyebrow">The studio rail · Cairo / 2026</p>
          <h1 id="rail-title" className="mx-auto mt-5 max-w-5xl font-display text-[clamp(3.1rem,7vw,7.6rem)] leading-[.86] tracking-[-.055em]">Choose the piece that moves with you.</h1>
          <p className="mx-auto mt-6 max-w-xl text-sm leading-6 text-ink/56 md:text-base">Drag the circular rail or use the arrows. The centred piece opens into a live product preview.</p>
        </div>

        <div className="relative mx-auto mt-8 h-[410px] max-w-[1380px] select-none md:mt-12 md:h-[450px]" aria-label="Circular product rail">
          <div className="pointer-events-none absolute left-[4%] right-[4%] top-7 h-px bg-ink/25 before:absolute before:-left-1 before:-top-1 before:h-2 before:w-2 before:rounded-full before:bg-ink/35 after:absolute after:-right-1 after:-top-1 after:h-2 after:w-2 after:rounded-full after:bg-ink/35" aria-hidden="true" />
          <motion.div className="absolute inset-0 cursor-grab touch-pan-y [perspective:1600px] active:cursor-grabbing" drag={reducedMotion ? false : "x"} dragConstraints={{ left: 0, right: 0 }} dragElastic={0.12} onDragEnd={onDragEnd}>
            {products.map((product, index) => {
              const offset = circularOffset(index, active, products.length);
              const distance = Math.abs(offset);
              const angle = offset * ORBIT_STEP;
              const visible = distance <= 4;
              const isActive = offset === 0;
              const x = Math.sin(angle) * 44;
              const y = (1 - Math.cos(angle)) * 92;
              const scale = Math.max(0.57, 1 - distance * 0.115);
              return (
                <motion.button
                  ref={(node) => { triggerRefs.current[index] = node; }}
                  key={product.id}
                  type="button"
                  layoutId={isActive ? `rail-card-${product.id}` : undefined}
                  aria-label={`${isActive ? "Preview" : "Bring forward"} ${product.name}, ${formatEgp(product.min_price)}`}
                  aria-haspopup={isActive ? "dialog" : undefined}
                  aria-current={isActive ? "true" : undefined}
                  tabIndex={visible ? 0 : -1}
                  className="absolute left-1/2 top-5 w-[clamp(150px,18vw,238px)] -translate-x-1/2 border-0 bg-transparent px-0 pt-8 text-center [will-change:transform,opacity] focus:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-4"
                  style={{ zIndex: 20 - distance, pointerEvents: visible ? "auto" : "none" }}
                  initial={false}
                  animate={{ x: `${x}vw`, y, scale, rotateY: offset * -17, opacity: visible ? Math.max(0.2, 1 - distance * 0.2) : 0 }}
                  transition={reducedMotion ? { duration: 0 } : orbitSpring}
                  onHoverStart={() => setActive(index)}
                  onFocus={() => setActive(index)}
                  onClick={() => isActive ? setSelected(index) : setActive(index)}
                >
                  <span className="absolute left-1/2 top-0 h-10 w-px -translate-x-1/2 bg-ink/35 before:absolute before:-left-[7px] before:top-6 before:h-4 before:w-4 before:rounded-full before:border before:border-ink/35 before:border-b-transparent" aria-hidden="true" />
                  <motion.div layoutId={isActive ? `rail-image-${product.id}` : undefined} className="relative mx-auto aspect-[3/4] w-full">
                    <ProductMedia product={product} priority={isActive} sizes="(max-width: 768px) 52vw, 20vw" className="h-full w-full rounded-[2rem] border border-white/70 bg-paper shadow-[0_24px_60px_rgba(31,36,33,.15)]" />
                  </motion.div>
                  <motion.div animate={{ opacity: isActive ? 1 : 0, y: isActive ? 0 : 8 }} className="mt-3" aria-hidden={!isActive}>
                    <p className="text-xs font-bold uppercase tracking-[.12em]">{product.name}</p>
                    <p className="mt-1 text-xs text-ink/52">{formatEgp(product.min_price)}</p>
                  </motion.div>
                </motion.button>
              );
            })}
          </motion.div>
          <div className="absolute inset-x-0 bottom-0 z-40 flex items-center justify-center gap-3">
            <button type="button" className="icon-button border border-ink/12 bg-canvas/90 backdrop-blur" aria-label="Previous product" onClick={() => rotate(-1)}><ArrowLeft size={18} /></button>
            <span className="inline-flex min-w-24 items-center justify-center gap-2 text-[.67rem] font-bold uppercase tracking-[.15em] text-ink/45"><RotateCw size={13} /> {active + 1} / {products.length}</span>
            <button type="button" className="icon-button border border-ink/12 bg-canvas/90 backdrop-blur" aria-label="Next product" onClick={() => rotate(1)}><ArrowRight size={18} /></button>
          </div>
        </div>
      </section>

      <AnimatePresence>
        {current && selected !== null && (
          <motion.div
            className="fixed inset-0 z-[80] grid overflow-y-auto bg-canvas/94 px-3 py-4 backdrop-blur-xl md:place-items-center md:px-8"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: reducedMotion ? 0 : .38 }}
            role="dialog" aria-modal="true" aria-labelledby="quick-view-title"
          >
            <button ref={closeRef} type="button" className="icon-button fixed right-4 top-4 z-20 border border-ink/12 bg-canvas md:right-8 md:top-7" onClick={closePreview} aria-label="Close product preview"><X size={19} /></button>
            <div className="mx-auto grid w-full max-w-6xl items-center gap-7 pt-14 md:grid-cols-[1.15fr_.85fr] md:gap-14 md:pt-0">
              <motion.div layoutId={`rail-card-${current.id}`} className="relative">
                <motion.div layoutId={`rail-image-${current.id}`} className="mx-auto aspect-[4/5] max-h-[72vh] w-full max-w-[620px]">
                  <ProductMedia product={current} priority sizes="(max-width: 768px) 92vw, 50vw" className="h-full w-full rounded-[2rem] bg-paper shadow-soft" />
                </motion.div>
              </motion.div>
              <div id="quick-view-title"><PurchasePanel product={current} compact /></div>
            </div>
            <div className="fixed inset-x-0 bottom-5 flex justify-center gap-2 md:bottom-8">
              <button type="button" className="icon-button border border-ink/12 bg-canvas" aria-label="Previous product" onClick={() => setSelected(circularIndex(selected - 1, products.length))}><ArrowLeft size={18} /></button>
              <button type="button" className="icon-button border border-ink/12 bg-canvas" aria-label="Next product" onClick={() => setSelected(circularIndex(selected + 1, products.length))}><ArrowRight size={18} /></button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </LayoutGroup>
  );
}
