import type { ComponentProps, ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Separator({ className, ...props }: ComponentProps<"div">) {
  return <div role="separator" className={cn("bg-line-soft h-px w-full", className)} {...props} />;
}

export function Progress({
  value,
  className,
  indicatorClassName,
}: {
  value: number;
  className?: string;
  indicatorClassName?: string;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("bg-raised h-1.5 w-full overflow-hidden rounded-full", className)}>
      <div
        className={cn("bg-signal h-full rounded-full transition-all", indicatorClassName)}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("bg-raised animate-pulse rounded-lg", className)} />;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-panel border-line flex flex-col items-center justify-center border border-dashed px-6 py-14 text-center">
      <div className="border-line bg-elevated text-signal mb-4 flex size-11 items-center justify-center rounded-xl border">
        {icon}
      </div>
      <h3 className="text-ink text-sm font-medium">{title}</h3>
      <p className="text-muted mt-1.5 max-w-sm text-sm leading-relaxed">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={cn("max-w-2xl", className)}>
      {eyebrow ? (
        <p className="text-signal mb-3 font-mono text-[11px] tracking-[0.2em] uppercase">
          {eyebrow}
        </p>
      ) : null}
      <h2 className="text-ink text-2xl font-medium tracking-tight sm:text-3xl">{title}</h2>
      {description ? (
        <p className="text-muted mt-3 text-sm leading-relaxed sm:text-base">{description}</p>
      ) : null}
    </div>
  );
}
