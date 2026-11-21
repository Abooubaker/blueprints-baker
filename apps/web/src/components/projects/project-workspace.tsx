"use client";

import {
  ArrowRight,
  CheckCircle2,
  FileText,
  Loader2,
  Play,
  RefreshCw,
  TriangleAlert,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { BuildSteps, nextStepSlug, readySlugs } from "@/components/projects/build-steps";
import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
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
        <div className="bg-raised h-3 w-32 animate-pulse" />
        <div className="border-line-soft h-28 animate-pulse border-y" />
        <div className="grid gap-4 sm:grid-cols-3">
          {[0, 1, 2].map((key) => (
            <div key={key} className="bg-raised h-20 animate-pulse" />
          ))}
        </div>
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
        className="text-faint hover:text-ink mb-6 inline-flex items-center gap-1.5 font-mono text-[10px] tracking-[0.12em] uppercase transition-colors"
      >
        ← index / all projects
      </Link>

      <div className="mb-7 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div className="min-w-0">
          <div className="mb-3 flex flex-wrap items-center gap-2 font-mono text-[10px] uppercase">
            <Badge variant={status.variant}>{status.label}</Badge>
            <Badge variant="outline">{titleCase(project.robot_type)}</Badge>
            {build?.identification ? (
              <span className="text-faint">
                confidence {Math.round(build.identification.confidence * 100)}%
              </span>
            ) : null}
            <span className="text-faint">rev {formatRelative(project.updated_at)}</span>
          </div>
          <h1 className="text-ink truncate text-[30px] leading-tight font-semibold tracking-[-0.03em] sm:text-[36px]">
            {project.name}
          </h1>
          <p className="text-muted mt-2 max-w-2xl text-sm leading-relaxed">
            {project.description || build?.specification?.summary || "No description yet."}
          </p>
        </div>
      </div>

      {buildError ? (
        <div className="border-danger/30 bg-danger/[0.04] text-danger mb-6 flex items-start gap-2.5 border-l-2 px-4 py-3 text-xs">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          {buildError}
        </div>
      ) : null}

      {!build || build.status === "empty" ? (
        <section className="border-line-soft border-y py-9">
          <p className="text-signal font-mono text-[10px] tracking-[0.18em] uppercase">
            {"// build not generated"}
          </p>
          <div className="mt-4 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-xl">
              <h2 className="text-ink text-2xl font-medium tracking-tight">
                {DEMO_MODE ? "This is the demo build" : "Ready to generate"}
              </h2>
              <p className="text-muted mt-2 text-[13px] leading-relaxed">
                {DEMO_MODE
                  ? "Explore the six steps using real engine output. Nothing here can be changed."
                  : "One click produces parts priced at your stores, a schematic, code, a 3D print price, a budget, and documentation."}
              </p>
            </div>
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
        </section>
      ) : (
        <div className="grid items-start gap-10 xl:grid-cols-[1fr_270px]">
          <div className="space-y-10">
            <section className="border-line-soft border-y py-8">
              <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
                <div className="min-w-0">
                  <p className="text-signal font-mono text-[10px] tracking-[0.18em] uppercase">
                    {"// next · "}
                    {readyCount} of {PROJECT_MODULES.length} ready
                  </p>
                  <h2 className="text-ink mt-3 text-2xl font-medium tracking-tight">
                    {nextModule?.label ?? "Review your build"}
                  </h2>
                  <p className="text-muted mt-2 max-w-lg text-[13px] leading-relaxed">
                    {nextModule?.description ?? "Everything is ready. Review the artifacts."}
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

            <div className="border-line-soft divide-line-soft grid grid-cols-3 divide-x border-t pt-5">
              {[
                {
                  label: "Total estimate",
                  value: formatJod(cost?.total_jod),
                  hint: "parts + print",
                },
                {
                  label: "Parts",
                  value: String(research?.bill_of_materials.length ?? 0),
                  hint: research?.selected_shops?.length
                    ? `${research.selected_shops.length} stores`
                    : "no stores",
                },
                {
                  label: "Cheapest print",
                  value: cheapestPrint ? formatJod(cheapestPrint.total_jod) : "—",
                  hint: cheapestPrint ? `${cheapestPrint.material}` : "not generated",
                },
              ].map((item) => (
                <div key={item.label} className="px-4 first:pl-0">
                  <p className="text-faint font-mono text-[8px] tracking-[0.14em] uppercase">
                    {item.label}
                  </p>
                  <p className="text-ink mt-2 font-mono text-lg tracking-tight">{item.value}</p>
                  <p className="text-faint mt-1 truncate font-mono text-[9px]">{item.hint}</p>
                </div>
              ))}
            </div>

            <section className="border-line-soft border-t pt-6">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="text-ink flex items-center gap-2 font-mono text-[11px] tracking-[0.14em] uppercase">
                  <FileText className="text-signal size-3.5" /> specification
                </h2>
                <Badge
                  variant={project.specification?.status === "approved" ? "signal" : "outline"}
                >
                  {project.specification?.status ?? "draft"} · v
                  {project.specification?.version ?? 1}
                </Badge>
              </div>
              <p className="text-muted max-w-3xl text-[13px] leading-relaxed">
                {build.specification?.summary ||
                  project.specification?.summary ||
                  project.description ||
                  "No specification summary yet."}
              </p>
              <dl className="divide-line-soft border-line-soft mt-5 grid grid-cols-3 divide-x border-t pt-4 font-mono">
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
                  <div key={label} className="px-4 first:pl-0">
                    <dt className="text-faint text-[8px] tracking-[0.14em] uppercase">{label}</dt>
                    <dd className="text-ink mt-1 truncate text-[11px]">{value}</dd>
                  </div>
                ))}
              </dl>
              {build.specification?.requirements.length ? (
                <div className="border-line-soft mt-5 border-t pt-4">
                  <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
                    Requirements
                  </p>
                  <ul className="grid gap-1.5 sm:grid-cols-2">
                    {build.specification.requirements.map((requirement) => (
                      <li key={requirement} className="text-muted flex items-start gap-2 text-xs">
                        <CheckCircle2 className="text-signal/70 mt-0.5 size-3 shrink-0" />
                        {requirement}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </section>
          </div>

          <aside className="space-y-6">
            <BuildSteps projectId={projectId} build={build} nextSlug={nextSlug} />

            <div className="border-line-soft border-t pt-4">
              <div className="mb-2 flex items-center justify-between font-mono text-[10px] uppercase">
                <span className="text-faint">progress</span>
                <span className="text-muted">
                  {readyCount} / {PROJECT_MODULES.length}
                </span>
              </div>
              <Progress value={(readyCount / PROJECT_MODULES.length) * 100} />
              <p className="text-faint mt-3 font-mono text-[9px] leading-relaxed">
                built {formatRelative(build.generated_at)}
              </p>
              {build.missing.length ? (
                <p className="text-warn mt-2 font-mono text-[9px] leading-relaxed">
                  missing: {build.missing.join(", ")}
                </p>
              ) : null}
            </div>

            {!DEMO_MODE ? (
              <button
                type="button"
                onClick={() => void generate()}
                disabled={building}
                className="text-faint hover:text-signal inline-flex items-center gap-1.5 font-mono text-[10px] tracking-[0.12em] uppercase transition-colors disabled:opacity-50"
              >
                {building ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="size-3.5" />
                )}
                regenerate build
              </button>
            ) : null}
          </aside>
        </div>
      )}
    </div>
  );
}
