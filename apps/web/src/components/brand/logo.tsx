import Link from "next/link";

import { assetPath } from "@/lib/constants";
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
      <image
        href={assetPath("/brand/albayraq-mark.png")}
        x="3.6"
        y="9.6"
        width="24.8"
        height="12.8"
        preserveAspectRatio="xMidYMid meet"
      />
    </svg>
  );
}

export function Logo({ className, markClassName }: { className?: string; markClassName?: string }) {
  return (
    <Link
      href="/"
      className={cn("group flex items-center gap-2.5", className)}
      aria-label="Albayraq home"
    >
      <LogoMark
        className={cn(
          "transition-transform duration-300 group-hover:rotate-[-4deg]",
          markClassName,
        )}
      />
      <span className="flex items-baseline gap-2">
        <span className="text-ink text-[16px] font-semibold tracking-[-0.02em]">Albayraq</span>
        <span className="border-line text-faint hidden rounded border px-1.5 py-0.5 font-mono text-[9px] tracking-[0.14em] uppercase sm:inline">
          beta
        </span>
      </span>
    </Link>
  );
}
