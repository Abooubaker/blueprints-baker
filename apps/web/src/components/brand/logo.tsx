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
        d="M9 25V15.5C9 10.8 12 8.2 15.8 8.2c3.4 0 5.9 1.6 7.1 4l3.9.9c.7.2.8 1 .2 1.3l-2.6 1.1c-1 3.5-4 5.9-8.2 5.9L9 25Z"
        fill="#eaf6ff"
      />
      <path
        d="M26.4 14.4c-1.6-.2-3.1-.3-4.4-.2"
        stroke="#0b2f4f"
        strokeWidth="1.1"
        strokeLinecap="round"
      />
      <circle cx="17.4" cy="13.4" r="1.2" fill="#6fd6ff" />
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
