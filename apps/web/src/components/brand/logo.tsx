import Link from "next/link";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={cn("size-8", className)} fill="none">
      <rect x="1" y="1" width="30" height="30" rx="7" fill="#0b2f4f" stroke="#7fa8c8" />
      <path
        d="M6 6h6M6 6v6M26 6h-6M26 6v6M6 26h6M6 26v-6M26 26h-6M26 26v-6"
        stroke="#eaf6ff"
        strokeWidth="1.2"
      />
      <path
        d="M11 22V11h5.2a3.7 3.7 0 0 1 .2 7.4H11"
        stroke="#eaf6ff"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="m16.6 18.5 4.4 3.5" stroke="#eaf6ff" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="22.6" cy="10.4" r="1.6" fill="#6fd6ff" />
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
