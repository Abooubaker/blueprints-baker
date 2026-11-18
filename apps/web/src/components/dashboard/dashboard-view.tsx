"use client";

import {
  Activity,
  ArrowUpRight,
  Bot,
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/form";
import { EmptyState, Progress, Skeleton } from "@/components/ui/misc";
import { AGENTS, PROJECT_STATUS_STYLES, ROBOT_TYPES } from "@/lib/constants";
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
      className="group rounded-panel border-line-soft bg-surface hover:border-line hover:bg-elevated/40 flex flex-col border p-5 transition-all"
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
        <div className="text-faint flex items-center gap-3 font-mono text-[10px] tracking-wide">
          <span>{titleCase(project.robot_type)}</span>
          <span className="bg-faint size-0.5 rounded-full" />
          <span>{project.budget_max_usd ? formatMoney(project.budget_max_usd) : "No budget"}</span>
        </div>
        <span className="text-faint text-[10px]">{formatRelative(project.updated_at)}</span>
      </div>
    </Link>
  );
}

function StatCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: typeof FolderKanban;
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">{label}</p>
        <Icon className="text-faint size-3.5" />
      </div>
      <p className="text-ink mt-3 text-2xl font-medium tracking-tight">{value}</p>
      <p className="text-faint mt-1 text-[11px]">{hint}</p>
    </Card>
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

  return (
    <div className="space-y-7">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Active projects"
          value={loading ? "—" : String(active)}
          hint={total === 0 ? "Create your first robot" : `${total} total in workspace`}
          icon={FolderKanban}
        />
        <StatCard
          label="In planning"
          value={loading ? "—" : String(planning)}
          hint="Specification or build in progress"
          icon={Activity}
        />
        <StatCard
          label="Planned budget"
          value={loading ? "—" : formatMoney(budget)}
          hint="Sum of project budget caps"
          icon={DollarSign}
        />
        <StatCard
          label="Agent pipeline"
          value="6"
          hint="Parts, wiring, code, 3D, cost + docs"
          icon={Bot}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
        <section>
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <h2 className="text-ink text-sm font-medium">Your projects</h2>
              {!loading && total > 0 ? (
                <span className="text-faint font-mono text-[10px]">{total}</span>
              ) : null}
            </div>
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
            <div className="grid gap-4 md:grid-cols-2">
              {[0, 1, 2, 3].map((item) => (
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
            <div className="grid gap-4 md:grid-cols-2">
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
          ) : (
            <EmptyState
              icon={<Sparkles className="size-4" />}
              title="Describe your first robot"
              description="Albayraq starts with a sentence, not a parts list. Create a project and tell us what you want to build."
              action={
                <ButtonLink href="/projects/new" size="sm">
                  <Plus className="size-3.5" /> New robot project
                </ButtonLink>
              }
            />
          )}
        </section>

        <aside className="space-y-4">
          <Card className="panel-sheen">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">What a build includes</CardTitle>
                <Badge variant="signal">Ready</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { label: "Parts priced at your stores", done: true },
                { label: "Schematic, nets & pinout", done: true },
                { label: "Multi-file code bundles", done: true },
                { label: "STL, weight & print price", done: true },
                { label: "Budget and documentation", done: true },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-2.5 text-xs">
                  <span className="border-signal/25 bg-signal/10 text-signal flex size-5 items-center justify-center rounded-full border">
                    <span className="bg-signal size-1.5 rounded-full" />
                  </span>
                  <span className="text-ink">{item.label}</span>
                </div>
              ))}
              <div className="pt-1">
                <Progress value={100} />
                <p className="text-faint mt-2 text-[10px]">
                  One confirmed flow produces all artifacts from the same validated pin map.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Agent roster</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {AGENTS.map((agent) => (
                <div
                  key={agent.name}
                  className="flex items-center gap-2.5 rounded-md px-1.5 py-1.5"
                >
                  <agent.icon className="text-faint size-3.5" />
                  <span className="text-muted text-[12px]">{agent.label}</span>
                  <span className="text-signal ml-auto font-mono text-[8px] tracking-wider uppercase">
                    ready
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>

          <a
            href="https://github.com/Abooubaker/blueprints-baker"
            target="_blank"
            rel="noreferrer"
            className="rounded-panel border-line-soft bg-surface text-muted hover:border-line hover:text-ink flex items-center justify-between border px-4 py-3 text-xs transition-colors"
          >
            <span>Roadmap & documentation</span>
            <ArrowUpRight className="size-3.5" />
          </a>
        </aside>
      </div>
    </div>
  );
}
