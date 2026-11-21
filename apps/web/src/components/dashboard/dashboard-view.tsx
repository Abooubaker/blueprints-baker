"use client";

import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  DollarSign,
  FolderKanban,
  Plus,
  Search,
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

function ProjectRow({ project }: { project: ProjectSummary }) {
  const meta = robotMeta(project.robot_type);
  const status = PROJECT_STATUS_STYLES[project.status] ?? PROJECT_STATUS_STYLES.draft!;
  const Icon = meta.icon;

  return (
    <Link
      href={`/projects/${project.id}`}
      className="group grid gap-3 py-5 sm:grid-cols-[auto_1fr_auto] sm:items-center sm:gap-5"
    >
      <div className="flex items-center gap-4">
        <Icon className="text-signal size-5" strokeWidth={1.5} />
        <div className="sm:hidden">
          <Badge variant={status.variant}>{status.label}</Badge>
        </div>
      </div>

      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2.5">
          <h3 className="text-ink group-hover:text-signal text-[15px] font-medium transition-colors">
            {project.name}
          </h3>
          <span className="hidden sm:inline">
            <Badge variant={status.variant}>{status.label}</Badge>
          </span>
        </div>
        <p className="text-muted mt-1 line-clamp-1 text-[13px] leading-relaxed">
          {project.description || "No description yet."}
        </p>
      </div>

      <div className="text-faint flex items-center justify-between gap-6 font-mono text-[10px] tracking-wide sm:justify-end">
        <span>{titleCase(project.robot_type)}</span>
        <span>{project.budget_max_usd ? formatMoney(project.budget_max_usd) : "no budget"}</span>
        <span className="hidden lg:inline">{formatRelative(project.updated_at)}</span>
        <ArrowUpRight className="text-signal size-4 opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
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
    <div className="space-y-8">
      {loading ? (
        <div className="border-line-soft border-y py-10">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="mt-4 h-7 w-72" />
          <Skeleton className="mt-3 h-3 w-full max-w-lg" />
        </div>
      ) : projects.length > 0 && latest ? (
        <section className="bg-blueprint border-line-soft relative border-y py-9">
          <div className="relative flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
            <div className="min-w-0">
              <p className="text-signal font-mono text-[10px] tracking-[0.18em] uppercase">
                {"// resume build"}
              </p>
              <h1 className="text-ink mt-4 truncate text-3xl font-semibold tracking-[-0.03em]">
                {latest.name}
              </h1>
              <p className="text-muted mt-2 max-w-xl text-[13px] leading-relaxed">
                {latest.description || "Pick up your build from the last step you were on."}
              </p>
            </div>
            <ButtonLink href={`/projects/${latest.id}`} size="md" className="shrink-0">
              Open build <ArrowRight className="size-4 rtl:rotate-180" />
            </ButtonLink>
          </div>
        </section>
      ) : (
        <section className="border-line-soft border-y py-10">
          <p className="text-signal font-mono text-[10px] tracking-[0.18em] uppercase">
            {"// new project"}
          </p>
          <h1 className="text-ink mt-4 text-3xl font-semibold tracking-[-0.03em]">
            Describe your first robot
          </h1>
          <p className="text-muted mt-3 max-w-xl text-[13px] leading-relaxed">
            Albayraq starts with a sentence, not a parts list. Tell us what you want to build and
            get a full, documented plan.
          </p>
          <ButtonLink href="/projects/new" size="md" className="mt-6">
            <Plus className="size-4" /> New robot project
          </ButtonLink>
        </section>
      )}

      {!loading && total > 0 ? (
        <div className="text-faint flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[10px] tracking-[0.1em] uppercase">
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
          <div className="flex items-baseline gap-3 font-mono text-[10px] tracking-[0.16em] uppercase">
            <span className="text-signal">{"// index"}</span>
            <h2 className="text-ink font-medium">All projects</h2>
            {!loading && total > 0 ? <span className="text-faint">[{total}]</span> : null}
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="text-faint absolute top-1/2 left-3 size-3.5 -translate-y-1/2" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Filter projects…"
                className="h-9 w-[190px] pl-8 font-mono text-xs"
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
          <div className="border-warn/30 bg-warn/[0.04] flex flex-col items-start gap-3 border-l-2 p-5">
            <div className="text-warn flex items-center gap-2 font-mono text-xs uppercase">
              <TriangleAlert className="size-4" />
              Backend unavailable
            </div>
            <p className="text-muted max-w-lg text-xs leading-relaxed">{error}</p>
            <code className="border-line bg-canvas text-muted rounded-sm border px-2 py-1 font-mono text-[10px]">
              cd apps/api && uv run uvicorn app.main:app --reload
            </code>
            <Button variant="secondary" size="sm" onClick={() => void reload()}>
              Try again
            </Button>
          </div>
        ) : loading ? (
          <div className="space-y-4">
            {[0, 1, 2].map((item) => (
              <div key={item} className="border-line-soft border-b pb-4">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="mt-3 h-3 w-full max-w-xl" />
              </div>
            ))}
          </div>
        ) : filtered.length > 0 ? (
          <div className="divide-line-soft border-line-soft divide-y border-t">
            {filtered.map((project) => (
              <ProjectRow key={project.id} project={project} />
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
