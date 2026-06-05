import type { HTMLAttributes } from "react";

type Variant = "default" | "secondary" | "destructive";

const STYLES: Record<Variant, string> = {
  default: "bg-slate-900 text-white",
  secondary: "bg-amber-100 text-amber-800",
  destructive: "bg-red-100 text-red-700",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ variant = "default", className = "", ...props }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide ${STYLES[variant]} ${className}`}
      {...props}
    />
  );
}
