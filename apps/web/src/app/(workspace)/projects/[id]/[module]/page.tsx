import type { Metadata } from "next";
import { ArrowLeft, ArrowRight, Construction, GitBranch } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PROJECT_MODULES } from "@/lib/constants";
import { titleCase } from "@/lib/utils";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string; module: string }>;
}): Promise<Metadata> {
  const { module: moduleSlug } = await params;
  const moduleInfo = PROJECT_MODULES.find((item) => item.slug === moduleSlug);
  return { title: moduleInfo?.label ?? "Module" };
}

export default async function ModulePlaceholderPage({
  params,
}: {
  params: Promise<{ id: string; module: string }>;
}) {
  const { id, module: moduleSlug } = await params;
  const moduleInfo = PROJECT_MODULES.find((item) => item.slug === moduleSlug);
  if (!moduleInfo) notFound();

  const index = PROJECT_MODULES.findIndex((item) => item.slug === moduleSlug);
  const next = PROJECT_MODULES[index + 1];
  const Icon = moduleInfo.icon;

  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href={`/projects/${id}`}
        className="text-faint hover:text-ink mb-5 inline-flex items-center gap-1.5 text-xs transition-colors"
      >
        <ArrowLeft className="size-3.5" /> Back to project
      </Link>

      <PageHeader
        eyebrow={`Module scaffold · ${moduleInfo.milestone}`}
        title={moduleInfo.label}
        description={moduleInfo.description}
        actions={<Badge variant="warn">In development</Badge>}
      />

      <Card className="panel-sheen">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="border-line bg-elevated text-signal flex size-10 items-center justify-center rounded-lg border">
              <Icon className="size-5" strokeWidth={1.6} />
            </div>
            <div>
              <CardTitle>{moduleInfo.label} workspace</CardTitle>
              <p className="text-faint mt-0.5 font-mono text-[10px] tracking-wider uppercase">
                {titleCase(moduleInfo.slug)} · scheduled {moduleInfo.milestone}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="border-line bg-canvas/40 rounded-lg border border-dashed p-5">
            <div className="text-ink flex items-center gap-2 text-sm">
              <Construction className="text-warn size-4" /> This route is intentionally a scaffold.
            </div>
            <p className="text-muted mt-2 text-xs leading-relaxed">
              The application shell, project context, navigation, and data contracts exist. The
              feature team implements this module in {moduleInfo.milestone}. The route exists so
              navigation, layout, and integration can be developed and reviewed before the feature
              lands — it does not claim that the capability works.
            </p>
          </div>

          <div>
            <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
              Implementation contract
            </p>
            <ul className="text-muted space-y-2 text-xs">
              <li className="flex items-start gap-2">
                <GitBranch className="text-signal/70 mt-0.5 size-3.5 shrink-0" />
                Consume the approved specification via the project API; never fork project state
                into a module-local store.
              </li>
              <li className="flex items-start gap-2">
                <GitBranch className="text-signal/70 mt-0.5 size-3.5 shrink-0" />
                Persist artifacts through the shared project configuration or agent-run records.
              </li>
              <li className="flex items-start gap-2">
                <GitBranch className="text-signal/70 mt-0.5 size-3.5 shrink-0" />
                Add loading, empty, and error states; the API may be offline during development.
              </li>
            </ul>
          </div>

          <div className="border-line-soft flex flex-wrap items-center gap-2 border-t pt-4">
            <ButtonLink href={`/projects/${id}`} variant="secondary" size="sm">
              Project overview
            </ButtonLink>
            <a
              href="https://github.com/Abooubaker/robocraft/issues"
              target="_blank"
              rel="noreferrer"
              className="text-faint hover:text-signal ml-auto flex items-center gap-1 text-[11px]"
            >
              Find the {moduleInfo.milestone} task <ArrowRight className="size-3" />
            </a>
          </div>
        </CardContent>
      </Card>

      {next ? (
        <div className="mt-4 flex justify-end">
          <Link
            href={`/projects/${id}/${next.slug}`}
            className="text-faint hover:text-ink flex items-center gap-1.5 text-xs transition-colors"
          >
            Next: {next.label} <ArrowRight className="size-3.5" />
          </Link>
        </div>
      ) : null}
    </div>
  );
}
