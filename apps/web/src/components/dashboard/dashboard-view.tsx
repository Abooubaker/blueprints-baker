"use client";

import {
  ArrowRight,
  ArrowUpRight,
  Activity,
  DollarSign,
  FolderKanban,
  Plus,
  Search,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink } from "@/components/ui/button";
import { Input } from "@/components/ui/form";
import { EmptyState, Skeleton } from "@/components/ui/misc";
import { PROJECT_STATUS_STYLES, ROBOT_TYPES } from "@/lib/constants";
import type { ProjectSummary } from "@/lib/types";
import { formatMoney, formatRelative, titleCase } from "@/lib/utils";
import { useProjects } from "@/hooks/use-projects";

function robotMeta(type: string) {
  return ROBOT_TYPES.find((item) => item.value === type) ?? ROBOT_TYPES[ROBOT_TYPES.length - 1]!;
}

function ProjectCard({ project }: { project: ProjectSummary }) {
  const meta = robotMeta(project.robot_type);
  const status = PROJECT_STATUS_STYLES[project.status] ?? PROJECT_STATUS_STYLES.draft!;
  const Icon = meta.icon;

  return (
    <Link
      href={`/projects/${project.id}`}
      className="group rounded-panel border-line-soft bg-surface hover:border-signal/40 hover:bg-elevated/40 flex flex-col border p-5 transition-all"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="border-line bg-elevated text-signal group-hover:border-signal/30 group-hover:bg-signal/5 flex size-10 items-center justify-center rounded-lg border transition-colors">
          <Icon className="size-4.5" strokeWidth={1.6} />
        </div>
        <Badge variant={status.variant}>{status.label}</Badge>
      </div>

      <h3 className="text-ink group-hover:text-signal mt-4 text-[15px] font-medium">
        {project.name}
      </h3>
      <p className="text-muted mt-1.5 line-clamp-2 min-h-10 text-[13px] leading-relaxed">
        {project.description || "No description yet."}
      </p>

      <div className="border-line-soft mt-5 flex items-center justify-between border-t pt-3.5">
        <div className="text-faint flex items-center gap-2.5 font-mono text-[10px] tracking-wide">
          <span>{titleCase(project.robot_type)}</span>
          <span className="bg-faint size-0.5 rounded-full" />
          <span>{project.budget_max_usd ? formatMoney(project.budget_max_usd) : "No budget"}</span>
        </div>
        <span className="text-faint text-[10px]">{formatRelative(project.updated_at)}</span>
      </div>
      <span className="text-signal/80 mt-3 inline-flex items-center gap-1.5 text-[11px] font-medium opacity-0 transition-opacity group-hover:opacity-100">
        Open build <ArrowUpRight className="size-3.5" />
      </span>
    </Link>
  );
}

export function DashboardView() {
  const { projects, total, loading, error, reload } = useProjects();
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return projects;
    return projects.filter(
      (project) =>
        project.name.toLowerCase().includes(query) ||
        project.description.toLowerCase().includes(query),
    );
  }, [projects, search]);

  const active = projects.filter((project) => project.status !== "archived").length;
  const planning = projects.filter(
    (project) => project.status === "planning" || project.status === "in_progress",
  ).length;
  const budget = projects.reduce((sum, project) => sum + (project.budget_max_usd ?? 0), 0);
  const latest = useMemo(
    () => [...projects].sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0],
    [projects],
  );

  return (
    <div className="space-y-7">
      {loading ? (
        <div className="rounded-panel border-line-soft bg-surface h-28 animate-pulse border" />
      ) : projects.length > 0 && latest ? (
        <section className="border-signal/25 bg-signal/[0.05] rounded-panel relative overflow-hidden border p-6">
          <div className="bg-dot-grid pointer-events-none absolute inset-0 opacity-30" />
          <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="text-signal font-mono text-[10px] tracking-[0.16em] uppercase">
                Continue where you left off
              </p>
              <h1 className="text-ink mt-2 truncate text-xl font-medium tracking-tight sm:text-2xl">
                {latest.name}
              </h1>
              <p className="text-muted mt-1.5 max-w-xl text-[13px] leading-relaxed">
                {latest.description || "Pick up your build from the last step you were on."}
              </p>
            </div>
            <ButtonLink href={`/projects/${latest.id}`} size="md" className="shrink-0">
              Open build <ArrowRight className="size-4 rtl:rotate-180" />
            </ButtonLink>
          </div>
        </section>
      ) : (
        <section className="panel-sheen rounded-panel border-line-soft border p-6">
          <div className="flex items-start gap-4">
            <div className="border-signal/25 bg-signal/10 text-signal flex size-11 shrink-0 items-center justify-center rounded-xl border">
              <Sparkles className="size-5" />
            </div>
            <div>
              <h1 className="text-ink text-xl font-medium tracking-tight sm:text-2xl">
                Describe your first robot
              </h1>
              <p className="text-muted mt-2 max-w-xl text-[13px] leading-relaxed">
                Albayraq starts with a sentence, not a parts list. Tell us what you want to build
                and get a full, documented plan.
              </p>
              <ButtonLink href="/projects/new" size="md" className="mt-5">
                <Plus className="size-4" /> New robot project
              </ButtonLink>
            </div>
          </div>
        </section>
      )}

      {!loading && total > 0 ? (
        <div className="text-faint flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px]">
          <span className="inline-flex items-center gap-1.5">
            <FolderKanban className="size-3.5" /> {active} active
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Activity className="size-3.5" /> {planning} in planning
          </span>
          <span className="inline-flex items-center gap-1.5">
            <DollarSign className="size-3.5" /> {formatMoney(budget)} planned
          </span>
        </div>
      ) : null}

      <section>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <h2 className="text-ink text-sm font-medium">All projects</h2>
            {!loading && total > 0 ? (
              <span className="text-faint font-mono text-[10px]">{total}</span>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="text-faint absolute top-1/2 left-3 size-3.5 -translate-y-1/2" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Filter projects…"
                className="h-9 w-[190px] pl-8 text-xs"
                aria-label="Filter projects"
              />
            </div>
            {projects.length > 0 ? (
              <ButtonLink href="/projects/new" size="sm" variant="secondary">
                <Plus className="size-3.5" /> New
              </ButtonLink>
            ) : null}
          </div>
        </div>

        {error ? (
          <div className="rounded-panel border-warn/20 bg-warn/[0.05] flex flex-col items-start gap-3 border p-5">
            <div className="text-warn flex items-center gap-2 text-sm">
              <TriangleAlert className="size-4" />
              Backend unavailable
            </div>
            <p className="text-muted max-w-lg text-xs leading-relaxed">{error}</p>
            <code className="border-line bg-canvas text-muted rounded border px-2 py-1 font-mono text-[10px]">
              cd apps/api && uv run uvicorn app.main:app --reload
            </code>
            <Button variant="secondary" size="sm" onClick={() => void reload()}>
              Try again
            </Button>
          </div>
        ) : loading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div key={item} className="rounded-panel border-line-soft bg-surface border p-5">
                <Skeleton className="size-10" />
                <Skeleton className="mt-4 h-4 w-40" />
                <Skeleton className="mt-2.5 h-3 w-full" />
                <Skeleton className="mt-1.5 h-3 w-2/3" />
                <Skeleton className="mt-5 h-3 w-1/2" />
              </div>
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filtered.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : projects.length > 0 ? (
          <EmptyState
            icon={<Search className="size-4" />}
            title="No matching projects"
            description="Try a different search term or clear the filter to see everything."
            action={
              <Button variant="secondary" size="sm" onClick={() => setSearch("")}>
                Clear filter
              </Button>
            }
          />
        ) : null}
      </section>
    </div>
  );
}
