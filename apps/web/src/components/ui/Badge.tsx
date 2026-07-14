import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

type Variant = "burgundy" | "success" | "warning" | "error" | "neutral";

const variantClasses: Record<Variant, string> = {
  burgundy: "bg-burgundy/10 text-burgundy",
  success: "bg-success/10 text-success",
  warning: "bg-warning/10 text-warning",
  error: "bg-error/10 text-error",
  neutral: "bg-taupe/25 text-ink-secondary",
};

export function Badge({ children, variant = "neutral", className }: { children: ReactNode; variant?: Variant; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wider",
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
