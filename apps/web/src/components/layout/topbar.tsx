"use client";

import { usePathname } from "next/navigation";

import { MobileNav } from "@/components/layout/sidebar";
import { PROJECT_MODULES } from "@/lib/constants";

function crumbs(pathname: string): string[] {
  if (pathname === "/dashboard") return ["Workspace", "Dashboard"];
  if (pathname === "/projects/new") return ["Workspace", "New project"];
  if (pathname.startsWith("/projects/")) {
    const [, , moduleSlug] = pathname.split("/");
    if (moduleSlug) {
      const moduleInfo = PROJECT_MODULES.find((item) => item.slug === moduleSlug);
      return ["Workspace", "Projects", moduleInfo?.label ?? "Module"];
    }
    return ["Workspace", "Projects", "Overview"];
  }
  return ["Workspace"];
}

export function Topbar() {
  const pathname = usePathname();
  const trail = crumbs(pathname);

  return (
    <header className="border-line-soft bg-canvas/80 sticky top-0 z-20 flex h-16 items-center gap-4 border-b px-4 backdrop-blur-xl sm:px-6">
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
      <span className="text-faint ml-auto hidden font-mono text-[9px] tracking-[0.18em] uppercase sm:block">
        Albayraq · Drafting table
      </span>
    </header>
  );
}
