import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/shared/lib/cn";

const buttonVariants = cva(
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-full px-5 text-sm font-semibold tracking-tight transition focus-visible:outline-2 focus-visible:outline-offset-3 focus-visible:outline-ink disabled:cursor-not-allowed disabled:opacity-45",
  {
    variants: {
      variant: {
        primary: "border border-ink bg-ink text-[#fffdf8] shadow-sm hover:bg-[#343a36]",
        secondary: "border border-ink/20 bg-white/75 text-ink hover:border-ink/35 hover:bg-white",
        ghost: "text-ink hover:bg-ink/6",
      },
      size: { default: "h-11", sm: "h-9 px-4 text-xs", lg: "h-13 px-7" },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}

export { buttonVariants };
