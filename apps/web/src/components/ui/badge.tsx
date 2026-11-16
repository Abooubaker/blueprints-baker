import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[10px] tracking-[0.12em] uppercase",
  {
    variants: {
      variant: {
        default: "border-line bg-elevated text-muted",
        signal: "border-signal/25 bg-signal/10 text-signal",
        aqua: "border-aqua/25 bg-aqua/10 text-aqua",
        warn: "border-warn/25 bg-warn/10 text-warn",
        danger: "border-danger/25 bg-danger/10 text-danger",
        outline: "border-line bg-transparent text-muted",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export function Badge({
  className,
  variant,
  ...props
}: ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export function Dot({ className }: { className?: string }) {
  return <span className={cn("size-1.5 rounded-full bg-current", className)} aria-hidden />;
}
