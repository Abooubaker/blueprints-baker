"use client";

import {
  ArrowUpRight,
  CheckCircle2,
  CircuitBoard,
  Clock3,
  Code2,
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
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((key) => (
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
  const programming = build?.programming ?? null;
  const cost = build?.cost ?? null;
  const cheapestPrint = mechanical?.material_quotes.find((quote) => quote.is_cheapest);
  const completedSteps = [research, build?.electrical, programming, mechanical, cost].filter(
    Boolean,
  ).length;

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

        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {DEMO_MODE ? (
            <Badge variant="outline">Read-only demo · real engine output</Badge>
          ) : (
            <Button
              size="md"
              onClick={() => void generate()}
              disabled={building}
              variant={build ? "secondary" : "primary"}
            >
              {building ? (
                <>
                  <Loader2 className="size-4 animate-spin" /> Building…
                </>
              ) : build ? (
                <>
                  <RefreshCw className="size-4" /> Regenerate build
                </>
              ) : (
                <>
                  <Play className="size-4" /> Generate build
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {buildError ? (
        <div className="rounded-panel border-danger/20 bg-danger/[0.05] text-danger mb-5 flex items-start gap-2.5 border px-4 py-3 text-xs">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          {buildError}
        </div>
      ) : null}

      {!build || build.status === "empty" ? (
        <Card className="mb-6">
          <CardContent className="flex flex-col items-start gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <div className="border-signal/25 bg-signal/10 text-signal flex size-10 shrink-0 items-center justify-center rounded-lg border">
                <Sparkles className="size-4.5" />
              </div>
              <div>
                <p className="text-ink text-sm font-medium">
                  This build has not been generated yet.
                </p>
                <p className="text-muted mt-1 max-w-xl text-xs leading-relaxed">
                  Generate it to get parts priced at your stores, a schematic, code bundles, a 3D
                  print price, a budget, and documentation.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {DEMO_MODE ? (
                <Badge variant="outline">Read-only demo</Badge>
              ) : (
                <Button size="sm" onClick={() => void generate()} disabled={building}>
                  {building ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <Play className="size-3.5" />
                  )}
                  Generate
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Total estimate",
            value: formatJod(cost?.total_jod),
            hint: "parts + cheapest print",
          },
          {
            label: "Parts compared",
            value: String(research?.bill_of_materials.length ?? 0),
            hint: research?.selected_shops?.length
              ? `across ${research.selected_shops.length} stores`
              : "no stores selected",
          },
          {
            label: "Cheapest print",
            value: cheapestPrint ? formatJod(cheapestPrint.total_jod) : "—",
            hint: cheapestPrint
              ? `${cheapestPrint.material} · ${cheapestPrint.weight_g} g`
              : "not generated",
          },
          {
            label: "Code bundles",
            value: String(programming?.bundles.length ?? 0),
            hint:
              programming?.bundles.map((item) => item.display_name).join(", ") || "not generated",
          },
        ].map((item) => (
          <Card key={item.label} className="p-4">
            <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
              {item.label}
            </p>
            <p className="text-ink mt-2.5 text-xl font-medium tracking-tight">{item.value}</p>
            <p className="text-faint mt-1 truncate text-[10px]">{item.hint}</p>
          </Card>
        ))}
      </div>

      <div className="grid items-start gap-6 xl:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-ink text-sm font-medium">Your build</h2>
              <span className="text-faint font-mono text-[9px] tracking-wider uppercase">
                {completedSteps}/5 artifacts ready
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {PROJECT_MODULES.map((module) => (
                <Link
                  key={module.slug}
                  href={`/projects/${project.id}/${module.slug}`}
                  className="group rounded-panel border-line-soft bg-surface hover:border-signal/30 flex flex-col border p-4 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="border-signal/25 bg-signal/10 text-signal flex size-8 items-center justify-center rounded-md border">
                      <module.icon className="size-4" strokeWidth={1.7} />
                    </div>
                    <ArrowUpRight className="text-faint size-3.5 opacity-0 transition-opacity group-hover:opacity-100" />
                  </div>
                  <h3 className="text-ink mt-3 text-[13px] font-medium">{module.label}</h3>
                  <p className="text-faint mt-1 text-[11px] leading-relaxed">
                    {module.description}
                  </p>
                </Link>
              ))}
            </div>
          </section>

          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <FileText className="text-signal/80 size-4" /> Specification
              </CardTitle>
              <Badge variant={project.specification?.status === "approved" ? "signal" : "outline"}>
                {project.specification?.status ?? "draft"} · v{project.specification?.version ?? 1}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted text-[13px] leading-relaxed">
                {build?.specification?.summary ||
                  project.specification?.summary ||
                  project.description ||
                  "No specification summary yet."}
              </p>
              <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {[
                  [
                    "Platform",
                    titleCase(
                      build?.specification?.target_platform ??
                        project.specification?.target_platform ??
                        "undecided",
                    ),
                  ],
                  [
                    "Drive",
                    titleCase(
                      build?.specification?.drive_type ??
                        project.specification?.drive_type ??
                        "none",
                    ),
                  ],
                  ["Difficulty", titleCase(project.difficulty)],
                  ["Stores", String(research?.selected_shops?.length ?? 0)],
                  ["Languages", String(programming?.bundles.length ?? 0)],
                  ["Custom PCB", build?.preferences.custom_pcb ? "Yes" : "No"],
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
              {build?.specification?.requirements.length ? (
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
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="mb-3 flex items-center justify-between text-[10px]">
                <span className="text-faint">Build freshness</span>
                <span className="text-muted font-mono">
                  {build ? formatRelative(build.generated_at) : "not built"}
                </span>
              </div>
              <Progress value={(completedSteps / 5) * 100} />
              <div className="mt-4 space-y-1.5">
                {[
                  ["Parts & prices", Boolean(research)],
                  ["Schematic", Boolean(build?.electrical)],
                  ["Code", Boolean(programming)],
                  ["3D & print price", Boolean(mechanical)],
                  ["Documentation", Boolean(build?.documentation.files.length)],
                ].map(([label, done]) => (
                  <div
                    key={String(label)}
                    className="flex items-center justify-between gap-2 text-xs"
                  >
                    <span className="text-muted">{label}</span>
                    {done ? (
                      <CheckCircle2 className="text-signal size-3.5" />
                    ) : (
                      <Clock3 className="text-faint size-3.5" />
                    )}
                  </div>
                ))}
              </div>
              {build?.missing.length ? (
                <p className="text-warn mt-3 text-[10px] leading-relaxed">
                  Missing: {build.missing.join(", ")}
                </p>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Stores</CardTitle>
            </CardHeader>
            <CardContent>
              {research?.selected_shops?.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {research.selected_shops.map((store) => (
                    <Badge key={store} variant="outline">
                      {store}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-faint text-xs">No stores selected.</p>
              )}
              <p className="text-faint mt-3 text-[10px] leading-relaxed">
                Every part is sorted cheapest → most expensive per selected store. Prices are
                estimates, not live quotes.
              </p>
            </CardContent>
          </Card>

          <div className="rounded-panel border-line-soft bg-surface border p-4">
            <div className="text-aqua flex items-center gap-2 text-[11px]">
              <CircuitBoard className="size-3.5" /> Shared build artifact
            </div>
            <p className="text-faint mt-2 text-[11px] leading-relaxed">
              Prices, schematic, code, 3D pricing, budget, and documents are all derived from the
              same confirmed answers and validated pin map.
            </p>
          </div>
        </aside>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        <ButtonLink href={`/projects/${project.id}/components`} variant="secondary" size="sm">
          <Layers className="size-3.5" /> Parts & prices
        </ButtonLink>
        <ButtonLink href={`/projects/${project.id}/wiring`} variant="secondary" size="sm">
          <CircuitBoard className="size-3.5" /> Schematic
        </ButtonLink>
        <ButtonLink href={`/projects/${project.id}/programming`} variant="secondary" size="sm">
          <Code2 className="size-3.5" /> Code
        </ButtonLink>
      </div>
    </div>
  );
}
