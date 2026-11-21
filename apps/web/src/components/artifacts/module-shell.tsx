"use client";

import { ArrowLeft, ArrowRight, Loader2, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { adjacentSteps } from "@/components/projects/build-steps";
import { ButtonLink } from "@/components/ui/button";
import { EmptyState, Progress } from "@/components/ui/misc";
import { PROJECT_MODULES } from "@/lib/constants";
import type { BuildArtifact } from "@/lib/types";

export function ModuleShell({
  projectId,
  title,
  description,
  loading,
  error,
  build,
  requirement,
  children,
}: {
  projectId: string;
  title: string;
  description: string;
  loading: boolean;
  error: string | null;
  build: BuildArtifact | null;
  requirement?: (build: BuildArtifact) => boolean;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const slug = pathname.split("/").filter(Boolean).pop();
  const { index, previous, next } = adjacentSteps(slug);
  const stepNumber = index + 1;

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-16 text-sm">
        <Loader2 className="text-signal size-4 animate-spin" />
        <span className="text-muted">Loading generated build…</span>
      </div>
    );
  }

  if (error || !build) {
    return (
      <EmptyState
        icon={<TriangleAlert className="size-4" />}
        title="Build unavailable"
        description={error ?? "Generate the build from the project overview first."}
        action={
          <ButtonLink href={`/projects/${projectId}`} size="sm" variant="secondary">
            <ArrowLeft className="size-3.5" /> Back to project
          </ButtonLink>
        }
      />
    );
  }

  if (requirement && !requirement(build)) {
    return (
      <EmptyState
        icon={<TriangleAlert className="size-4" />}
        title="Not generated yet"
        description="Run the build pipeline from the project overview to create this artifact."
        action={
          <ButtonLink href={`/projects/${projectId}`} size="sm">
            Back to project <ArrowRight className="size-3.5" />
          </ButtonLink>
        }
      />
    );
  }

  const previousModule = PROJECT_MODULES.find((module) => module.slug === previous);
  const nextModule = PROJECT_MODULES.find((module) => module.slug === next);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between gap-3 font-mono text-[10px] tracking-[0.12em] uppercase">
        <Link
          href={`/projects/${projectId}`}
          className="text-faint hover:text-ink inline-flex items-center gap-1.5 transition-colors"
        >
          <ArrowLeft className="size-3.5" /> {build.project_name}
        </Link>
        {stepNumber > 0 ? (
          <span className="text-faint">
            step {String(stepNumber).padStart(2, "0")} / {PROJECT_MODULES.length}
          </span>
        ) : null}
      </div>

      <div className="border-line-soft mb-8 border-b pb-6">
        <h1 className="text-ink text-2xl font-semibold tracking-[-0.03em] sm:text-[30px]">
          {title}
        </h1>
        <p className="text-muted mt-2 max-w-2xl text-sm leading-relaxed">{description}</p>
        {stepNumber > 0 ? (
          <Progress className="mt-5 max-w-xs" value={(stepNumber / PROJECT_MODULES.length) * 100} />
        ) : null}
      </div>

      {children}

      <nav className="border-line-soft mt-10 flex items-center justify-between border-t pt-5 font-mono text-[10px] tracking-[0.12em] uppercase">
        {previousModule ? (
          <Link
            href={`/projects/${projectId}/${previousModule.slug}`}
            className="text-faint hover:text-ink inline-flex items-center gap-2 transition-colors"
          >
            <ArrowLeft className="size-3.5" /> {previousModule.label}
          </Link>
        ) : (
          <Link
            href={`/projects/${projectId}`}
            className="text-faint hover:text-ink inline-flex items-center gap-2 transition-colors"
          >
            <ArrowLeft className="size-3.5" /> Project overview
          </Link>
        )}
        <Link
          href={nextModule ? `/projects/${projectId}/${nextModule.slug}` : `/projects/${projectId}`}
          className="text-signal hover:text-ink inline-flex items-center gap-2 transition-colors"
        >
          {nextModule ? `Next · ${nextModule.label}` : "Finish · overview"}
          <ArrowRight className="size-3.5 rtl:rotate-180" />
        </Link>
      </nav>
    </div>
  );
}

export function MissingArtifacts({ build }: { build: BuildArtifact }) {
  if (build.missing.length === 0) return null;
  return (
    <div className="border-warn/30 bg-warn/[0.04] text-warn mt-4 border-l-2 px-4 py-3 text-xs">
      Missing artifacts: {build.missing.join(", ")}. Regenerate the build to fill them in.
    </div>
  );
}
