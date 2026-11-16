import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn("mb-7 flex flex-col justify-between gap-5 sm:flex-row sm:items-end", className)}
    >
      <div className="min-w-0">
        {eyebrow ? (
          <p className="text-signal mb-2 font-mono text-[10px] tracking-[0.2em] uppercase">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="text-ink text-[26px] leading-tight font-medium tracking-[-0.02em] sm:text-[30px]">
          {title}
        </h1>
        {description ? (
          <p className="text-muted mt-2 max-w-2xl text-sm leading-relaxed">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}
