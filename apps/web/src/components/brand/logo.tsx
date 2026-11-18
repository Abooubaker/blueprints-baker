import Link from "next/link";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={cn("size-8", className)} fill="none">
      <rect x="1" y="1" width="30" height="30" rx="7" fill="#0b2f4f" stroke="#7fa8c8" />
      <path
        d="M6 6h5M6 6v5M26 6h-5M26 6v5M6 26h5M6 26v-5M26 26h-5M26 26v-5"
        stroke="#eaf6ff"
        strokeWidth="1.1"
        strokeOpacity="0.7"
      />
      <path
        d="M10.4 22.6v-6.8c-2.1-.7-3-2.7-2.2-4.5.8-1.8 3-2.3 4.5-1.2.4-2.1 2.3-3.2 4-2.6 1.7-.9 3.9-.2 4.5 1.6 2-.2 3.5 1.3 3.5 3.3 0 1.5-1 2.8-2.4 3.3v6.9Z"
        fill="none"
        stroke="#eaf6ff"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M10.4 20.4h11.9" stroke="#eaf6ff" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="23.2" cy="9.2" r="1.4" fill="#6fd6ff" />
    </svg>
  );
}

export function Logo({ className, markClassName }: { className?: string; markClassName?: string }) {
  return (
    <Link
      href="/"
      className={cn("group flex items-center gap-2.5", className)}
      aria-label="Blueprints Baker home"
    >
      <LogoMark
        className={cn(
          "transition-transform duration-300 group-hover:rotate-[-4deg]",
          markClassName,
        )}
      />
      <span className="flex items-baseline gap-2">
        <span className="text-ink text-[16px] font-semibold tracking-[-0.02em]">
          Blueprints <span className="text-aqua">Baker</span>
        </span>
        <span className="border-line text-faint hidden rounded border px-1.5 py-0.5 font-mono text-[9px] tracking-[0.14em] uppercase sm:inline">
          beta
        </span>
      </span>
    </Link>
  );
}
