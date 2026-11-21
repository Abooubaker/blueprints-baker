"use client";

import { ArrowRight, Check, Circle } from "lucide-react";
import Link from "next/link";

import { PROJECT_MODULES } from "@/lib/constants";
import type { BuildArtifact } from "@/lib/types";
import { cn } from "@/lib/utils";

const READY: Record<string, (build: BuildArtifact) => boolean> = {
  components: (build) => Boolean(build.research),
  wiring: (build) => Boolean(build.electrical),
  programming: (build) => Boolean(build.programming),
  mechanical: (build) => Boolean(build.mechanical),
  cost: (build) => Boolean(build.cost),
  docs: (build) => build.documentation.files.length > 0,
};

export function moduleReady(build: BuildArtifact, slug: string): boolean {
  return READY[slug]?.(build) ?? false;
}

export function readySlugs(build: BuildArtifact): Set<string> {
  return new Set(
    PROJECT_MODULES.filter((module) => moduleReady(build, module.slug)).map((m) => m.slug),
  );
}

/** First artifact that still needs attention, or the first step when all are ready. */
export function nextStepSlug(build: BuildArtifact): string {
  return PROJECT_MODULES.find((module) => !moduleReady(build, module.slug))?.slug ?? "components";
}

export function adjacentSteps(slug?: string): { previous?: string; next?: string; index: number } {
  const index = PROJECT_MODULES.findIndex((module) => module.slug === slug);
  if (index < 0) return { index: 0, next: PROJECT_MODULES[0]?.slug };
  return {
    index,
    previous: PROJECT_MODULES[index - 1]?.slug,
    next: PROJECT_MODULES[index + 1]?.slug,
  };
}

/**
 * A compact, ordered view of the six build steps. Highlights where the user is
 * and what comes next so there is never any guesswork about the next action.
 */
export function BuildSteps({
  projectId,
  build,
  activeSlug,
  nextSlug,
}: {
  projectId: string;
  build: BuildArtifact;
  activeSlug?: string;
  nextSlug?: string;
}) {
  const ready = readySlugs(build);
  const stepNumber = activeSlug
    ? PROJECT_MODULES.findIndex((module) => module.slug === activeSlug) + 1
    : 0;

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-faint font-mono text-[10px] tracking-[0.14em] uppercase">Build steps</p>
        {stepNumber > 0 ? (
          <span className="text-faint font-mono text-[10px]">
            {stepNumber} / {PROJECT_MODULES.length}
          </span>
        ) : null}
      </div>
      <ol className="space-y-1.5">
        {PROJECT_MODULES.map((module, index) => {
          const isActive = module.slug === activeSlug;
          const isNext = module.slug === nextSlug;
          const isDone = ready.has(module.slug) && !isActive;

          return (
            <li key={module.slug}>
              <Link
                href={`/projects/${projectId}/${module.slug}`}
                className={cn(
                  "group border-line-soft flex items-center gap-3 rounded-lg border px-3 py-2.5 transition-colors",
                  isActive
                    ? "border-signal/50 bg-signal/[0.08]"
                    : isNext
                      ? "border-signal/30 bg-elevated/60 hover:border-signal/50"
                      : "bg-surface/60 hover:border-line hover:bg-elevated/40",
                )}
              >
                <span
                  className={cn(
                    "flex size-6 shrink-0 items-center justify-center rounded-full border font-mono text-[10px]",
                    isActive
                      ? "border-signal bg-signal text-signal-ink"
                      : isDone
                        ? "border-signal/40 bg-signal/10 text-signal"
                        : isNext
                          ? "border-signal/50 text-signal"
                          : "border-line text-faint",
                  )}
                >
                  {isDone ? <Check className="size-3" /> : index + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      "block text-[13px] font-medium",
                      isActive ? "text-signal" : isNext ? "text-ink" : "text-muted",
                    )}
                  >
                    {module.label}
                  </span>
                  {isNext ? (
                    <span className="text-faint mt-0.5 block truncate text-[11px]">Next step</span>
                  ) : null}
                </span>
                {(isActive || isNext) && !isDone ? (
                  <ArrowRight className="text-signal/70 size-3.5 shrink-0 rtl:rotate-180" />
                ) : null}
                {isDone && !isActive ? (
                  <Circle className="text-signal/30 size-2.5 shrink-0" />
                ) : null}
              </Link>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
