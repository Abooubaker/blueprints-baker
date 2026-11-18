"use client";

import { ArrowLeft, ArrowRight, Loader2, TriangleAlert } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { ButtonLink } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/misc";
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

  return (
    <div>
      <Link
        href={`/projects/${projectId}`}
        className="text-faint hover:text-ink mb-5 inline-flex items-center gap-1.5 text-xs transition-colors"
      >
        <ArrowLeft className="size-3.5" /> {build.project_name}
      </Link>
      <div className="mb-6">
        <h1 className="text-ink text-2xl font-medium tracking-[-0.02em] sm:text-[28px]">{title}</h1>
        <p className="text-muted mt-1.5 max-w-2xl text-sm leading-relaxed">{description}</p>
      </div>
      {children}
    </div>
  );
}

export function MissingArtifacts({ build }: { build: BuildArtifact }) {
  if (build.missing.length === 0) return null;
  return (
    <div className="rounded-panel border-warn/20 bg-warn/[0.05] text-warn mt-4 border px-4 py-3 text-xs">
      Missing artifacts: {build.missing.join(", ")}. Regenerate the build to fill them in.
    </div>
  );
}
