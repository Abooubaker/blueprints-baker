"use client";

import {
  Armchair,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Bot,
  CheckCircle2,
  CircuitBoard,
  Clock3,
  Compass,
  FileText,
  FolderGit2,
  Gauge,
  Loader2,
  Plane,
  Play,
  RefreshCw,
  Route,
  Scan,
  Sparkles,
  TriangleAlert,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, Progress, Separator } from "@/components/ui/misc";
import { AGENTS, DEMO_MODE, PROJECT_MODULES, PROJECT_STATUS_STYLES } from "@/lib/constants";
import { api, ApiError } from "@/lib/api";
import type {
  AgentName,
  AgentRun,
  AgentRunStatus,
  OrchestrationResult,
  Project,
} from "@/lib/types";
import { cn, formatDate, formatMoney, formatRelative, titleCase } from "@/lib/utils";

const RUN_STYLES: Record<
  AgentRunStatus,
  {
    label: string;
    variant: "default" | "signal" | "aqua" | "warn" | "danger" | "outline";
    text: string;
  }
> = {
  succeeded: { label: "Complete", variant: "signal", text: "text-signal" },
  running: { label: "Running", variant: "aqua", text: "text-aqua" },
  queued: { label: "Queued", variant: "default", text: "text-muted" },
  not_implemented: { label: "Placeholder", variant: "warn", text: "text-warn" },
  skipped: { label: "Blocked", variant: "outline", text: "text-faint" },
  failed: { label: "Failed", variant: "danger", text: "text-danger" },
  cancelled: { label: "Cancelled", variant: "outline", text: "text-faint" },
};

function RobotTypeGlyph({ type, className }: { type: string; className?: string }) {
  switch (type) {
    case "line_follower":
      return <Route className={className} strokeWidth={1.6} />;
    case "obstacle_avoider":
      return <Scan className={className} strokeWidth={1.6} />;
    case "rover":
      return <Compass className={className} strokeWidth={1.6} />;
    case "robot_arm":
      return <Armchair className={className} strokeWidth={1.6} />;
    case "balancing_bot":
      return <Gauge className={className} strokeWidth={1.6} />;
    case "drone":
      return <Plane className={className} strokeWidth={1.6} />;
    default:
      return <Bot className={className} strokeWidth={1.6} />;
  }
}

function RunIcon({ status }: { status: AgentRunStatus }) {
  if (status === "succeeded") return <CheckCircle2 className="text-signal size-3.5" />;
  if (status === "failed") return <XCircle className="text-danger size-3.5" />;
  if (status === "running") return <Loader2 className="text-aqua size-3.5 animate-spin" />;
  if (status === "not_implemented") return <Sparkles className="text-warn size-3.5" />;
  return <Clock3 className="text-faint size-3.5" />;
}

export function ProjectWorkspace({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState<AgentName[] | "all" | null>(null);
  const [runResult, setRunResult] = useState<OrchestrationResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getProject(projectId), api.listAgentRuns(projectId, { limit: 50 })])
      .then(([loadedProject, runPage]) => {
        if (cancelled) return;
        setProject(loadedProject);
        setRuns(runPage.items);
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

  function reloadProject() {
    setLoading(true);
    setRefreshKey((key) => key + 1);
  }

  const latestByAgent = useMemo(() => {
    const map = new Map<AgentName, AgentRun>();
    for (const run of runs) {
      if (!map.has(run.agent)) map.set(run.agent, run);
    }
    return map;
  }, [runs]);

  async function runAgents(selection: AgentName[] | "all") {
    if (!project) return;
    setRunning(selection);
    setRunError(null);
    setRunResult(null);
    try {
      const result = await api.runAgents(project.id, {
        agents: selection === "all" ? undefined : selection,
      });
      setRunResult(result);
      const page = await api.listAgentRuns(project.id, { limit: 50 });
      setRuns(page.items);
    } catch (caught) {
      setRunError(
        caught instanceof ApiError ? caught.message : "The agent run could not be started.",
      );
    } finally {
      setRunning(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-raised h-4 w-32 animate-pulse rounded" />
        <div className="rounded-panel bg-raised h-24 animate-pulse" />
        <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
          <div className="rounded-panel bg-raised h-96 animate-pulse" />
          <div className="rounded-panel bg-raised h-96 animate-pulse" />
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
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={reloadProject}>
              <RefreshCw className="size-3.5" /> Retry
            </Button>
            <Button variant="ghost" size="sm" onClick={() => history.back()}>
              Go back
            </Button>
          </div>
        }
      />
    );
  }

  const status = PROJECT_STATUS_STYLES[project.status] ?? PROJECT_STATUS_STYLES.draft!;
  const spec = project.specification;
  const completedStages = AGENTS.filter(
    (agent) => latestByAgent.get(agent.name)?.status === "succeeded",
  ).length;
  const pipelineProgress = (completedStages / AGENTS.length) * 100;

  return (
    <div>
      <Link
        href="/dashboard"
        className="text-faint hover:text-ink mb-5 inline-flex items-center gap-1.5 text-xs transition-colors"
      >
        <ArrowLeft className="size-3.5" /> All projects
      </Link>

      <div className="mb-7 flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
        <div className="flex min-w-0 items-start gap-4">
          <div className="border-line bg-elevated text-signal flex size-12 shrink-0 items-center justify-center rounded-xl border">
            <RobotTypeGlyph type={project.robot_type} className="size-5" />
          </div>
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <Badge variant={status.variant}>{status.label}</Badge>
              <Badge variant="outline">{titleCase(project.robot_type)}</Badge>
              <span className="text-faint font-mono text-[10px]">
                updated {formatRelative(project.updated_at)}
              </span>
            </div>
            <h1 className="text-ink truncate text-[26px] leading-tight font-medium tracking-[-0.02em] sm:text-[30px]">
              {project.name}
            </h1>
            <p className="text-muted mt-1.5 max-w-2xl text-sm leading-relaxed">
              {project.description || "No description yet."}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <ButtonLink href={`/projects/${project.id}/wiring`} size="md">
            <CircuitBoard className="size-4" /> Open schematic
          </ButtonLink>
          {DEMO_MODE ? <Badge variant="outline">Precomputed · read-only</Badge> : null}
        </div>
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Budget cap",
            value: project.budget_max_usd ? formatMoney(project.budget_max_usd) : "Not set",
            hint: project.budget_min_usd
              ? `Floor ${formatMoney(project.budget_min_usd)}`
              : "Add a range when planning",
          },
          {
            label: "Specification",
            value: spec ? `v${spec.version}` : "—",
            hint: spec?.status ? titleCase(spec.status) : "No spec",
          },
          {
            label: "Agent runs",
            value: String(runs.length),
            hint: runs.length === 0 ? "Pipeline not started" : "Audited executions",
          },
          {
            label: "Pipeline",
            value: `${completedStages}/${AGENTS.length}`,
            hint: "Agents completed successfully",
          },
        ].map((item) => (
          <Card key={item.label} className="p-4">
            <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
              {item.label}
            </p>
            <p className="text-ink mt-2.5 text-xl font-medium tracking-tight">{item.value}</p>
            <p className="text-faint mt-1 text-[10px]">{item.hint}</p>
          </Card>
        ))}
      </div>

      {runResult ? (
        <div
          className={cn(
            "rounded-panel mb-5 flex items-start gap-3 border px-4 py-3",
            runResult.status === "succeeded"
              ? "border-signal/20 bg-signal/[0.05]"
              : runResult.status === "failed"
                ? "border-danger/20 bg-danger/[0.05]"
                : "border-warn/20 bg-warn/[0.05]",
          )}
        >
          <Sparkles className="text-warn mt-0.5 size-4 shrink-0" />
          <div className="min-w-0 flex-1 text-xs">
            <p className="text-ink font-medium">
              Outline complete — {runResult.runs.length} execution
              {runResult.runs.length === 1 ? "" : "s"} recorded.
            </p>
            <p className="text-muted mt-1 leading-relaxed">
              {runResult.status === "not_implemented"
                ? "The planner, component research, and electrical agents completed and stored validated artifacts. Programming, mechanical, and cost agents are still placeholders; open Schematic & pinout to inspect every connection."
                : "Agent results are stored in the project audit trail below."}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setRunResult(null)}
            className="text-faint hover:text-ink"
            aria-label="Dismiss result"
          >
            <XCircle className="size-4" />
          </button>
        </div>
      ) : null}

      {runError ? (
        <div className="rounded-panel border-danger/20 bg-danger/[0.05] text-danger mb-5 flex items-start gap-2.5 border px-4 py-3 text-xs">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          {runError}
        </div>
      ) : null}

      <div className="grid items-start gap-6 xl:grid-cols-[1fr_330px]">
        <div className="space-y-6">
          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-ink text-sm font-medium">Build modules</h2>
              <span className="text-faint font-mono text-[9px] tracking-wider uppercase">
                same specification · five disciplines
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {PROJECT_MODULES.map((module) => {
                const href =
                  module.slug === "specification"
                    ? "#specification"
                    : `/projects/${project.id}/${module.slug}`;
                return (
                  <Link
                    key={module.slug}
                    href={href}
                    className={cn(
                      "group rounded-panel flex flex-col border p-4 transition-colors",
                      module.available
                        ? "border-signal/20 bg-signal/[0.03] hover:border-signal/35"
                        : "border-line-soft bg-surface hover:border-line",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div
                        className={cn(
                          "flex size-8 items-center justify-center rounded-md border",
                          module.available
                            ? "border-signal/25 bg-signal/10 text-signal"
                            : "border-line bg-elevated text-faint",
                        )}
                      >
                        <module.icon className="size-4" strokeWidth={1.7} />
                      </div>
                      <Badge variant={module.available ? "signal" : "outline"}>
                        {module.available ? "Ready" : module.milestone}
                      </Badge>
                    </div>
                    <h3 className="text-ink mt-3 flex items-center gap-1.5 text-[13px] font-medium">
                      {module.label}
                      <ArrowUpRight className="text-faint size-3 opacity-0 transition-opacity group-hover:opacity-100" />
                    </h3>
                    <p className="text-faint mt-1 text-[11px] leading-relaxed">
                      {module.description}
                    </p>
                  </Link>
                );
              })}
            </div>
          </section>

          <Card id="specification" className="scroll-mt-24">
            <CardHeader className="flex-row items-start justify-between space-y-0">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="text-signal/80 size-4" /> Specification
                </CardTitle>
                <p className="text-muted mt-1 text-xs">
                  Structured intent created with the project. Editing lands in M2.
                </p>
              </div>
              <Badge variant={spec?.status === "approved" ? "signal" : "outline"}>
                {spec?.status ?? "draft"} · v{spec?.version ?? 1}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="border-line-soft bg-canvas/30 rounded-lg border p-4">
                <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                  Summary
                </p>
                <p className="text-muted mt-2 text-[13px] leading-relaxed">
                  {spec?.summary || project.description || "No specification summary yet."}
                </p>
              </div>

              <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {[
                  [
                    "Platform",
                    spec?.target_platform ? titleCase(spec.target_platform) : "Undecided",
                  ],
                  ["Drive type", spec?.drive_type ? titleCase(spec.drive_type) : "Not set"],
                  ["Environment", spec?.environment ? titleCase(spec.environment) : "Indoor"],
                  ["Power source", spec?.power_source || "Planner decides"],
                  [
                    "Payload",
                    spec?.payload_capacity_kg ? `${spec.payload_capacity_kg} kg` : "Not set",
                  ],
                  ["Difficulty", titleCase(project.difficulty)],
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

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
                    Requirements
                  </p>
                  {spec?.requirements?.length ? (
                    <ul className="space-y-1.5">
                      {spec.requirements.map((requirement) => (
                        <li key={requirement} className="text-muted flex items-start gap-2 text-xs">
                          <span className="bg-signal/70 mt-1.5 size-1 shrink-0 rounded-full" />
                          {requirement}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-faint text-xs">No explicit requirements recorded.</p>
                  )}
                </div>
                <div>
                  <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
                    Constraints
                  </p>
                  {spec?.constraints?.length ? (
                    <ul className="space-y-1.5">
                      {spec.constraints.map((constraint) => (
                        <li key={constraint} className="text-muted flex items-start gap-2 text-xs">
                          <span className="bg-aqua/70 mt-1.5 size-1 shrink-0 rounded-full" />
                          {constraint}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-faint text-xs">No constraints recorded.</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-start justify-between space-y-0">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="text-signal/80 size-4" /> Agent pipeline
                </CardTitle>
                <p className="text-muted mt-1 text-xs">
                  Typed contracts, deterministic dependency order, audited runs.
                </p>
              </div>
              {DEMO_MODE ? (
                <Badge variant="outline">read-only</Badge>
              ) : (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => void runAgents("all")}
                  disabled={running !== null}
                >
                  {running !== null ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : runs.length ? (
                    <RefreshCw className="size-3.5" />
                  ) : (
                    <Play className="size-3.5" />
                  )}
                  {runs.length ? "Run again" : "Run pipeline"}
                </Button>
              )}
            </CardHeader>
            <CardContent>
              <div className="mb-5">
                <div className="text-faint mb-2 flex items-center justify-between text-[10px]">
                  <span>Pipeline completion</span>
                  <span className="font-mono">
                    {completedStages}/{AGENTS.length}
                  </span>
                </div>
                <Progress value={pipelineProgress} />
              </div>
              <div className="space-y-1.5">
                {AGENTS.map((agent, index) => {
                  const run = latestByAgent.get(agent.name);
                  const runStyle = run ? RUN_STYLES[run.status] : null;
                  return (
                    <div
                      key={agent.name}
                      className="border-line-soft bg-canvas/30 flex items-center gap-3 rounded-lg border px-3 py-2.5"
                    >
                      <span className="text-faint w-4 font-mono text-[9px]">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <agent.icon className="text-faint size-3.5 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-ink truncate text-xs">{agent.label}</p>
                        <p className="text-faint truncate text-[10px]">{agent.short}</p>
                      </div>
                      {run ? (
                        <div className="flex shrink-0 items-center gap-1.5">
                          <RunIcon status={run.status} />
                          <span className={cn("font-mono text-[9px] uppercase", runStyle?.text)}>
                            {runStyle?.label}
                          </span>
                        </div>
                      ) : (
                        <Badge variant="outline" className="shrink-0">
                          not run
                        </Badge>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        <aside className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Project details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs">
              {[
                ["Created", formatDate(project.created_at)],
                ["Updated", formatDate(project.updated_at)],
                ["Slug", project.slug],
                ["Project ID", `${project.id.slice(0, 8)}…`],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between gap-3">
                  <span className="text-faint">{label}</span>
                  <span className="text-muted truncate font-mono text-[10px]">{value}</span>
                </div>
              ))}
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-faint">Budget</span>
                <span className="text-muted">
                  {project.budget_min_usd ? `${formatMoney(project.budget_min_usd)} – ` : ""}
                  {formatMoney(project.budget_max_usd)}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm">Execution log</CardTitle>
              <Badge variant="outline">{runs.length}</Badge>
            </CardHeader>
            <CardContent>
              {runs.length === 0 ? (
                <div className="border-line rounded-lg border border-dashed px-3 py-5 text-center">
                  <Bot className="text-faint mx-auto size-4" />
                  <p className="text-faint mt-2 text-[11px]">
                    No agent runs yet. Execute the pipeline to inspect the contract.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {runs.slice(0, 8).map((run) => {
                    const runStyle = RUN_STYLES[run.status];
                    return (
                      <div key={run.id} className="flex items-start gap-2">
                        <RunIcon status={run.status} />
                        <div className="min-w-0 flex-1">
                          <p className="text-muted truncate text-[11px]">
                            {AGENTS.find((agent) => agent.name === run.agent)?.label ?? run.agent}
                          </p>
                          <p className="text-faint mt-0.5 flex items-center gap-1.5 text-[9px]">
                            <span className={runStyle.text}>{runStyle.label}</span>
                            <span>·</span>
                            <span>{formatRelative(run.created_at)}</span>
                            <span>·</span>
                            <span className="font-mono">{run.latency_ms}ms</span>
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="rounded-panel border-line-soft bg-surface border p-4">
            <div className="text-aqua flex items-center gap-2 text-[11px]">
              <FolderGit2 className="size-3.5" /> Foundation scope
            </div>
            <p className="text-faint mt-2 text-[11px] leading-relaxed">
              Project CRUD, specification persistence, and orchestration audit are implemented.
              Product capabilities are delivered through milestones M2–M10.
            </p>
            <a
              href="https://github.com/Abooubaker/blueprints-baker"
              target="_blank"
              rel="noreferrer"
              className="text-muted hover:text-signal mt-3 flex items-center gap-1 text-[11px]"
            >
              Follow the roadmap <ArrowRight className="size-3" />
            </a>
          </div>
        </aside>
      </div>
    </div>
  );
}
