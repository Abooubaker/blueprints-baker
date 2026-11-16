"use client";

import { BookOpen, Github, HelpCircle } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { MobileNav } from "@/components/layout/sidebar";

function crumbs(pathname: string): string[] {
  if (pathname === "/dashboard") return ["Workspace", "Dashboard"];
  if (pathname === "/projects/new") return ["Workspace", "New project"];
  if (pathname.startsWith("/projects/")) return ["Workspace", "Projects", "Overview"];
  return ["Workspace"];
}

export function Topbar() {
  const pathname = usePathname();
  const trail = crumbs(pathname);

  return (
    <header className="border-line-soft bg-canvas/80 sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b px-4 backdrop-blur-xl sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <MobileNav />
        <div className="text-faint flex min-w-0 items-center gap-2 font-mono text-[10px] tracking-[0.12em] uppercase">
          {trail.map((item, index) => (
            <span key={`${item}-${index}`} className="flex items-center gap-2">
              {index > 0 ? <span className="text-line">/</span> : null}
              <span className={index === trail.length - 1 ? "text-muted truncate" : "truncate"}>
                {item}
              </span>
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-1.5">
        <Link
          href="/dashboard"
          className="border-line bg-elevated/60 text-muted hover:border-signal/30 hover:text-ink hidden items-center gap-2 rounded-lg border px-3 py-1.5 text-xs transition-colors sm:flex"
        >
          <BookOpen className="size-3.5" />
          Docs
        </Link>
        <a
          href="https://github.com/Abooubaker/robocraft"
          target="_blank"
          rel="noreferrer"
          className="text-muted hover:text-ink hidden size-8 items-center justify-center rounded-lg transition-colors hover:bg-white/5 sm:flex"
          aria-label="GitHub repository"
        >
          <Github className="size-4" />
        </a>
        <span className="bg-line-soft mx-1 hidden h-5 w-px sm:block" />
        <button
          type="button"
          className="border-line bg-elevated text-signal flex size-8 items-center justify-center rounded-full border text-[11px] font-medium"
          aria-label="Help and shortcuts"
          title="Help and shortcuts"
        >
          <HelpCircle className="size-4" />
        </button>
        <div
          className="border-signal/25 bg-signal/10 text-signal flex size-8 items-center justify-center rounded-full border font-mono text-[10px]"
          title="Local workspace"
        >
          AB
        </div>
      </div>
    </header>
  );
}
