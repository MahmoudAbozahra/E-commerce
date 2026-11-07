"use client";

import { motion, type PanInfo, useReducedMotion } from "motion/react";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { circularIndex, circularOffset } from "@/shared/lib/circular-carousel";
import { orbitSpring } from "@/shared/lib/motion";

const NAMED_COLORS: Record<string, string> = {
  black: "#171918",
  blush: "#d8a49f",
  camel: "#b8895c",
  charcoal: "#4a4d4d",
  clay: "#a6513c",
  cobalt: "#2457a7",
  cocoa: "#6f4e3d",
  grey: "#9a9b98",
  indigo: "#30456a",
  ink: "#252d32",
  ivory: "#eee8d8",
  midnight: "#172131",
  moss: "#65704b",
  navy: "#24334f",
  oat: "#d8cbb2",
  olive: "#73704a",
  rose: "#b96f78",
  rust: "#a35435",
  sage: "#81927c",
  sand: "#c9b58c",
  sky: "#9fc2d6",
  stone: "#aaa397",
  taupe: "#9b8778",
  white: "#f7f5ef",
};

function visualBackground(value: string) {
  const normalized = value.trim().toLowerCase();
  if (NAMED_COLORS[normalized]) return NAMED_COLORS[normalized];
  const parts = normalized.split(/\s+(?:and|&)\s+|\//).map((part) => NAMED_COLORS[part.trim()]).filter(Boolean);
  if (parts.length > 1) return `conic-gradient(${parts.map((color, index) => `${color} ${index * (100 / parts.length)}% ${(index + 1) * (100 / parts.length)}%`).join(", ")})`;
  const hue = [...normalized].reduce((total, character) => total + character.charCodeAt(0), 0) % 360;
  return `hsl(${hue} 24% 58%)`;
}

export function VariantOptionOrbit({ name, values, selected, onSelect }: { name: string; values: string[]; selected: string; onSelect: (value: string) => void }) {
  const reducedMotion = useReducedMotion();
  const active = Math.max(0, values.indexOf(selected));
  const rotate = (direction: number) => onSelect(values[circularIndex(active + direction, values.length)]);
  const onDragEnd = (_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (Math.abs(info.offset.x) < 28 || values.length < 2) return;
    rotate(info.offset.x < 0 ? 1 : -1);
  };

  return (
    <div className="relative max-w-[390px] pt-1" aria-label={`${name} options orbit`}>
      <div className="pointer-events-none absolute left-7 right-7 top-6 h-14 rounded-[50%] border border-ink/12" aria-hidden="true" />
      <motion.div className="relative h-24 cursor-grab touch-pan-y [perspective:900px] active:cursor-grabbing" drag={values.length > 1 && !reducedMotion ? "x" : false} dragConstraints={{ left: 0, right: 0 }} dragElastic={0.12} onDragEnd={onDragEnd}>
        {values.map((value, index) => {
          const offset = circularOffset(index, active, values.length);
          const distance = Math.abs(offset);
          const isActive = offset === 0;
          const visible = distance <= 2;
          const angle = offset * (Math.PI / 4.8);
          return (
            <motion.button
              key={value}
              type="button"
              aria-label={`Select ${name} ${value}`}
              aria-pressed={isActive}
              tabIndex={visible ? 0 : -1}
              onClick={() => onSelect(value)}
              className="absolute left-1/2 top-0 grid w-20 -translate-x-1/2 justify-items-center gap-1 border-0 bg-transparent p-0 text-center focus:outline-none focus-visible:ring-2 focus-visible:ring-ink"
              style={{ zIndex: 10 - distance, pointerEvents: visible ? "auto" : "none" }}
              initial={false}
              animate={{
                x: Math.sin(angle) * 132,
                y: (1 - Math.cos(angle)) * 22,
                scale: isActive ? 1 : 0.76,
                rotateY: offset * -20,
                opacity: visible ? (isActive ? 1 : 0.52) : 0,
              }}
              transition={reducedMotion ? { duration: 0 } : orbitSpring}
            >
              <span className={`grid h-12 w-12 place-items-center rounded-full border-[3px] bg-canvas shadow-[0_8px_22px_rgba(31,36,33,.14)] ${isActive ? "border-ink" : "border-white/80"}`}>
                <span className="h-8 w-8 rounded-full border border-ink/10" style={{ background: visualBackground(value) }} aria-hidden="true" />
              </span>
              <span className={`max-w-24 text-[.66rem] font-bold capitalize leading-3 ${isActive ? "text-ink" : "text-ink/52"}`}>{value}</span>
            </motion.button>
          );
        })}
      </motion.div>
      {values.length > 1 && (
        <div className="mt-1 flex items-center justify-center gap-3">
          <button type="button" className="icon-button h-8! w-8! border border-ink/12" aria-label={`Previous ${name}`} onClick={() => rotate(-1)}><ArrowLeft size={14} /></button>
          <span className="min-w-14 text-center text-[.64rem] font-bold tracking-[.14em] text-ink/42">{active + 1} / {values.length}</span>
          <button type="button" className="icon-button h-8! w-8! border border-ink/12" aria-label={`Next ${name}`} onClick={() => rotate(1)}><ArrowRight size={14} /></button>
        </div>
      )}
    </div>
  );
}
