"use client";

import {
  ArrowRight,
  CheckCircle2,
  DollarSign,
  FileText,
  Layers,
  Loader2,
  Play,
  RefreshCw,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { BuildSteps, nextStepSlug, readySlugs } from "@/components/projects/build-steps";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, Progress } from "@/components/ui/misc";
import { api, ApiError } from "@/lib/api";
import { DEMO_MODE, PROJECT_MODULES, PROJECT_STATUS_STYLES } from "@/lib/constants";
import type { BuildArtifact, Project } from "@/lib/types";
import { formatJod, formatRelative, titleCase } from "@/lib/utils";

export function ProjectWorkspace({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [build, setBuild] = useState<BuildArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [building, setBuilding] = useState(false);
  const [buildError, setBuildError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getProject(projectId), api.getBuild(projectId).catch(() => null)])
      .then(([loadedProject, loadedBuild]) => {
        if (cancelled) return;
        setProject(loadedProject);
        setBuild(loadedBuild);
        setError(null);
      })
      .catch((caught: unknown) => {
        if (cancelled) return;
        setError(caught instanceof ApiError ? caught.message : "Could not load this project.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, refreshKey]);

  function reload() {
    setLoading(true);
    setRefreshKey((key) => key + 1);
  }

  async function generate() {
    if (!project) return;
    setBuilding(true);
    setBuildError(null);
    try {
      const result = await api.generateBuild(project.id);
      setBuild(result);
      setProject(await api.getProject(project.id));
    } catch (caught) {
      setBuildError(
        caught instanceof ApiError ? caught.message : "The build pipeline could not finish.",
      );
    } finally {
      setBuilding(false);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-raised h-4 w-32 animate-pulse rounded" />
        <div className="rounded-panel bg-raised h-28 animate-pulse" />
        <div className="grid gap-4 sm:grid-cols-3">
          {[0, 1, 2].map((key) => (
            <div key={key} className="rounded-panel bg-raised h-24 animate-pulse" />
          ))}
        </div>
        <div className="rounded-panel bg-raised h-72 animate-pulse" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <EmptyState
        icon={<TriangleAlert className="size-4" />}
        title="Project unavailable"
        description={error ?? "This project does not exist."}
        action={
          <Button variant="secondary" size="sm" onClick={reload}>
            <RefreshCw className="size-3.5" /> Retry
          </Button>
        }
      />
    );
  }

  const status = PROJECT_STATUS_STYLES[project.status] ?? PROJECT_STATUS_STYLES.draft!;
  const research = build?.research ?? null;
  const mechanical = build?.mechanical ?? null;
  const cost = build?.cost ?? null;
  const cheapestPrint = mechanical?.material_quotes.find((quote) => quote.is_cheapest);
  const nextSlug = build ? nextStepSlug(build) : undefined;
  const nextModule = PROJECT_MODULES.find((module) => module.slug === nextSlug);
  const readyCount = build ? readySlugs(build).size : 0;

  return (
    <div>
      <Link
        href="/dashboard"
        className="text-faint hover:text-ink mb-5 inline-flex items-center gap-1.5 text-xs transition-colors"
      >
        ← All projects
      </Link>

      <div className="mb-7 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div className="min-w-0">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant={status.variant}>{status.label}</Badge>
            <Badge variant="outline">{titleCase(project.robot_type)}</Badge>
            {build?.identification ? (
              <span className="text-faint font-mono text-[10px]">
                identified at {Math.round(build.identification.confidence * 100)}%
              </span>
            ) : null}
            <span className="text-faint font-mono text-[10px]">
              updated {formatRelative(project.updated_at)}
            </span>
          </div>
          <h1 className="text-ink truncate text-[28px] leading-tight font-medium tracking-[-0.02em] sm:text-[32px]">
            {project.name}
          </h1>
          <p className="text-muted mt-1.5 max-w-2xl text-sm leading-relaxed">
            {project.description || build?.specification?.summary || "No description yet."}
          </p>
        </div>
      </div>

      {buildError ? (
        <div className="rounded-panel border-danger/20 bg-danger/[0.05] text-danger mb-5 flex items-start gap-2.5 border px-4 py-3 text-xs">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          {buildError}
        </div>
      ) : null}

      {!build || build.status === "empty" ? (
        <Card className="panel-sheen">
          <CardContent className="flex flex-col items-start gap-5 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-4">
              <div className="border-signal/25 bg-signal/10 text-signal flex size-11 shrink-0 items-center justify-center rounded-xl border">
                <Sparkles className="size-5" />
              </div>
              <div>
                <p className="text-ink text-base font-medium">
                  {DEMO_MODE ? "This is the demo build" : "Your build is ready to generate"}
                </p>
                <p className="text-muted mt-1.5 max-w-xl text-[13px] leading-relaxed">
                  {DEMO_MODE
                    ? "Explore the six steps using real engine output. Nothing here can be changed."
                    : "One click produces parts priced at your stores, a schematic, code, a 3D print price, a budget, and documentation."}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {DEMO_MODE ? (
                <ButtonLink href={`/projects/${projectId}/components`} size="md">
                  Explore the build <ArrowRight className="size-4 rtl:rotate-180" />
                </ButtonLink>
              ) : (
                <Button size="md" onClick={() => void generate()} disabled={building}>
                  {building ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Play className="size-4" />
                  )}
                  {building ? "Building…" : "Generate build"}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid items-start gap-6 xl:grid-cols-[1fr_300px]">
          <div className="space-y-6">
            <section className="border-signal/30 bg-signal/[0.06] rounded-panel relative overflow-hidden border p-6">
              <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-30" />
              <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-signal font-mono text-[10px] tracking-[0.16em] uppercase">
                    Next step · {readyCount} of {PROJECT_MODULES.length} ready
                  </p>
                  <h2 className="text-ink mt-2 text-xl font-medium tracking-tight">
                    {nextModule?.label ?? "Review your build"}
                  </h2>
                  <p className="text-muted mt-1.5 max-w-lg text-[13px] leading-relaxed">
                    {nextModule?.description ?? "Everything is ready. Review the artifacts below."}
                  </p>
                </div>
                {nextModule ? (
                  <ButtonLink
                    href={`/projects/${projectId}/${nextModule.slug}`}
                    size="md"
                    className="shrink-0"
                  >
                    Continue <ArrowRight className="size-4 rtl:rotate-180" />
                  </ButtonLink>
                ) : null}
              </div>
            </section>

            <div className="grid gap-3 sm:grid-cols-3">
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                    Total estimate
                  </p>
                  <DollarSign className="text-faint size-3.5" />
                </div>
                <p className="text-ink mt-3 text-xl font-medium tracking-tight">
                  {formatJod(cost?.total_jod)}
                </p>
                <p className="text-faint mt-1 text-[10px]">parts + cheapest print</p>
              </Card>
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                    Parts compared
                  </p>
                  <Layers className="text-faint size-3.5" />
                </div>
                <p className="text-ink mt-3 text-xl font-medium tracking-tight">
                  {research?.bill_of_materials.length ?? 0}
                </p>
                <p className="text-faint mt-1 truncate text-[10px]">
                  {research?.selected_shops?.length
                    ? `across ${research.selected_shops.length} stores`
                    : "no stores selected"}
                </p>
              </Card>
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                    Cheapest print
                  </p>
                  <Sparkles className="text-faint size-3.5" />
                </div>
                <p className="text-ink mt-3 text-xl font-medium tracking-tight">
                  {cheapestPrint ? formatJod(cheapestPrint.total_jod) : "—"}
                </p>
                <p className="text-faint mt-1 truncate text-[10px]">
                  {cheapestPrint
                    ? `${cheapestPrint.material} · ${cheapestPrint.weight_g} g`
                    : "not generated"}
                </p>
              </Card>
            </div>

            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <FileText className="text-signal/80 size-4" /> Specification
                </CardTitle>
                <Badge
                  variant={project.specification?.status === "approved" ? "signal" : "outline"}
                >
                  {project.specification?.status ?? "draft"} · v
                  {project.specification?.version ?? 1}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted text-[13px] leading-relaxed">
                  {build.specification?.summary ||
                    project.specification?.summary ||
                    project.description ||
                    "No specification summary yet."}
                </p>
                <dl className="grid gap-2 sm:grid-cols-3">
                  {[
                    [
                      "Platform",
                      titleCase(
                        build.specification?.target_platform ??
                          project.specification?.target_platform ??
                          "undecided",
                      ),
                    ],
                    [
                      "Drive",
                      titleCase(
                        build.specification?.drive_type ??
                          project.specification?.drive_type ??
                          "none",
                      ),
                    ],
                    ["Custom PCB", build.preferences.custom_pcb ? "Yes" : "No"],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="border-line-soft bg-surface/60 rounded-lg border px-3 py-2.5"
                    >
                      <dt className="text-faint font-mono text-[8px] tracking-[0.14em] uppercase">
                        {label}
                      </dt>
                      <dd className="text-ink mt-1 truncate text-xs">{value}</dd>
                    </div>
                  ))}
                </dl>
                {build.specification?.requirements.length ? (
                  <div>
                    <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
                      Requirements
                    </p>
                    <ul className="space-y-1.5">
                      {build.specification.requirements.map((requirement) => (
                        <li key={requirement} className="text-muted flex items-start gap-2 text-xs">
                          <CheckCircle2 className="text-signal/70 mt-0.5 size-3 shrink-0" />
                          {requirement}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </div>

          <aside className="space-y-4">
            <Card className="panel-sheen p-4">
              <BuildSteps projectId={projectId} build={build} nextSlug={nextSlug} />
              <div className="border-line-soft mt-5 border-t pt-4">
                <div className="mb-2 flex items-center justify-between text-[10px]">
                  <span className="text-faint">Progress</span>
                  <span className="text-muted font-mono">
                    {readyCount}/{PROJECT_MODULES.length}
                  </span>
                </div>
                <Progress value={(readyCount / PROJECT_MODULES.length) * 100} />
                <p className="text-faint mt-3 text-[10px] leading-relaxed">
                  Built {formatRelative(build.generated_at)}. Prices are estimates, not live quotes.
                </p>
                {build.missing.length ? (
                  <p className="text-warn mt-2 text-[10px] leading-relaxed">
                    Missing: {build.missing.join(", ")}
                  </p>
                ) : null}
              </div>
            </Card>
            {!DEMO_MODE ? (
              <Button
                variant="ghost"
                size="sm"
                className="w-full"
                onClick={() => void generate()}
                disabled={building}
              >
                {building ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="size-3.5" />
                )}
                Regenerate build
              </Button>
            ) : null}
          </aside>
        </div>
      )}
    </div>
  );
}
