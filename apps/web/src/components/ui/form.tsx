import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const fieldBase =
  "w-full rounded-lg border border-line bg-canvas/70 px-3.5 text-sm text-ink placeholder:text-faint transition-colors hover:border-[#2d6894] focus:border-signal/50 focus:bg-canvas focus:outline-none focus:ring-2 focus:ring-signal/15 disabled:cursor-not-allowed disabled:opacity-50";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(fieldBase, "h-11", className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea className={cn(fieldBase, "min-h-28 py-3 leading-relaxed", className)} {...props} />
  );
}

export function Select({ className, ...props }: ComponentProps<"select">) {
  return (
    <select
      className={cn(fieldBase, "h-11 appearance-none bg-[right_0.9rem_center] pr-9", className)}
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='none' stroke='%2394a29c' stroke-width='1.5' d='m2.5 4.5 3.5 3 3.5-3'/%3E%3C/svg%3E\")",
        backgroundRepeat: "no-repeat",
      }}
      {...props}
    />
  );
}

export function Label({ className, ...props }: ComponentProps<"label">) {
  return (
    <label
      className={cn(
        "text-ink/90 [&_.optional]:text-faint flex items-center gap-1.5 text-[13px] font-medium",
        className,
      )}
      {...props}
    />
  );
}

export function FieldHint({ className, ...props }: ComponentProps<"p">) {
  return <p className={cn("text-faint text-xs leading-relaxed", className)} {...props} />;
}

export function FieldError({ children }: { children?: string }) {
  if (!children) return null;
  return <p className="text-danger text-xs">{children}</p>;
}

export function Field({ className, ...props }: ComponentProps<"div">) {
  return <div className={cn("flex flex-col gap-2", className)} {...props} />;
}
