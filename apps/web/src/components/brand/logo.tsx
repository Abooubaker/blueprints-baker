import Link from "next/link";

import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={cn("size-8", className)} fill="none">
      <rect x="1" y="1" width="30" height="30" rx="9" fill="#10171a" stroke="#2a3a3e" />
      <path
        d="M10.5 23V9h6.1a4.4 4.4 0 0 1 .3 8.8h-6.4"
        stroke="#c9f75a"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="m17.4 17.8 5.4 5.2" stroke="#c9f75a" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="23" cy="9" r="1.7" fill="#5cdbd3" />
    </svg>
  );
}

export function Logo({ className, markClassName }: { className?: string; markClassName?: string }) {
  return (
    <Link
      href="/"
      className={cn("group flex items-center gap-2.5", className)}
      aria-label="RoboCraft home"
    >
      <LogoMark
        className={cn(
          "transition-transform duration-300 group-hover:rotate-[-4deg]",
          markClassName,
        )}
      />
      <span className="flex items-baseline gap-2">
        <span className="text-ink text-[17px] font-semibold tracking-[-0.02em]">
          Robo<span className="text-signal">Craft</span>
        </span>
        <span className="border-line text-faint hidden rounded border px-1.5 py-0.5 font-mono text-[9px] tracking-[0.14em] uppercase sm:inline">
          beta
        </span>
      </span>
    </Link>
  );
}
