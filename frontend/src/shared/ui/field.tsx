import type { InputHTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/lib/cn";

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  hint?: ReactNode;
};

export function Field({ label, error, hint, className, id, ...props }: FieldProps) {
  const inputId = id ?? props.name;
  return (
    <label className="grid gap-2 text-sm font-medium text-ink" htmlFor={inputId}>
      {label}
      <input
        id={inputId}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${inputId}-error` : undefined}
        className={cn(
          "h-12 rounded-2xl border border-ink/14 bg-white/70 px-4 text-base font-normal outline-none transition placeholder:text-ink/35 focus:border-ink focus:ring-3 focus:ring-ink/8",
          error && "border-clay",
          className,
        )}
        {...props}
      />
      {error ? <span id={`${inputId}-error`} className="text-xs font-normal text-clay">{error}</span> : hint}
    </label>
  );
}
