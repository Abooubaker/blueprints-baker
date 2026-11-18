"use client";

import { BookOpen, Cpu, Github, LayoutDashboard, Menu, Plus, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { Logo } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/projects/new", label: "New project", icon: Plus },
];

const LEARN = [
  {
    label: "Documentation",
    href: "https://github.com/Abooubaker/blueprints-baker/tree/main/docs",
    icon: BookOpen,
  },
  {
    label: "Source code",
    href: "https://github.com/Abooubaker/blueprints-baker",
    icon: Cpu,
  },
];

function isActive(pathname: string, href: string) {
  if (href === "/dashboard") return pathname === "/dashboard" || pathname.startsWith("/projects");
  return pathname === href;
}

function ApiStatus() {
  const [state, setState] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let cancelled = false;
    const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
    fetch(`${base}/health`, { cache: "no-store" })
      .then((response) => {
        if (!cancelled) setState(response.ok ? "online" : "offline");
      })
      .catch(() => {
        if (!cancelled) setState("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="text-faint flex items-center gap-2 font-mono text-[10px] tracking-[0.12em] uppercase">
      <span
        className={cn(
          "size-1.5 rounded-full",
          state === "online" && "bg-signal",
          state === "checking" && "bg-warn",
          state === "offline" && "bg-danger",
        )}
      />
      {state === "online" ? "API online" : state === "checking" ? "Checking API" : "API offline"}
    </div>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col">
      <div className="border-line-soft flex h-16 items-center border-b px-5">
        <Logo />
      </div>

      <nav className="flex-1 space-y-7 overflow-y-auto px-3 py-5">
        <div>
          <p className="text-faint mb-2 px-2.5 font-mono text-[10px] tracking-[0.16em] uppercase">
            Workspace
          </p>
          <ul className="space-y-0.5">
            {NAV.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={onNavigate}
                    className={cn(
                      "group flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] transition-colors",
                      active
                        ? "bg-signal/10 text-signal"
                        : "text-muted hover:text-ink hover:bg-white/[0.04]",
                    )}
                  >
                    <item.icon className="size-4" strokeWidth={1.7} />
                    {item.label}
                    {active ? (
                      <span className="bg-signal ml-auto size-1 rounded-full" aria-hidden />
                    ) : null}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>

        <div>
          <p className="text-faint mb-2 px-2.5 font-mono text-[10px] tracking-[0.16em] uppercase">
            Learn
          </p>
          <ul className="space-y-0.5">
            {LEARN.map((item) => (
              <li key={item.label}>
                <a
                  href={item.href}
                  target="_blank"
                  rel="noreferrer"
                  className="text-muted hover:text-ink flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] transition-colors hover:bg-white/[0.04]"
                >
                  <item.icon className="size-4" strokeWidth={1.7} />
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      <div className="border-line-soft space-y-3 border-t px-5 py-4">
        <ApiStatus />
        <div className="text-faint flex items-center justify-between text-[11px]">
          <span>Foundation v0.1</span>
          <a
            href="https://github.com/Abooubaker/blueprints-baker"
            target="_blank"
            rel="noreferrer"
            className="hover:text-ink transition-colors"
            aria-label="Blueprints Baker on GitHub"
          >
            <Github className="size-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="border-line-soft bg-surface/70 fixed inset-y-0 left-0 z-30 hidden w-[248px] border-r backdrop-blur-xl lg:block">
      <SidebarContent />
    </aside>
  );
}

export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="border-line text-muted hover:text-ink flex size-9 items-center justify-center rounded-lg border transition-colors lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="size-4" />
      </button>
      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="bg-canvas/80 absolute inset-0 backdrop-blur-sm"
            aria-label="Close navigation"
            onClick={() => setOpen(false)}
          />
          <div className="border-line bg-surface absolute inset-y-0 left-0 w-[280px] border-r">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-muted hover:text-ink absolute top-4 right-3 z-10 flex size-8 items-center justify-center rounded-md"
              aria-label="Close navigation"
            >
              <X className="size-4" />
            </button>
            <SidebarContent onNavigate={() => setOpen(false)} />
          </div>
        </div>
      ) : null}
    </>
  );
}
