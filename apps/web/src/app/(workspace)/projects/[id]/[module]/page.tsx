import type { Metadata } from "next";
import { ArrowLeft, Construction } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { CodeView } from "@/components/artifacts/code-view";
import { CostView } from "@/components/artifacts/cost-view";
import { DocsView } from "@/components/artifacts/docs-view";
import { MechanicalView } from "@/components/artifacts/mechanical-view";
import { PartsView } from "@/components/artifacts/parts-view";
import { WiringWorkspace } from "@/components/projects/wiring-workspace";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DEMO_MODE, DEMO_PROJECT_ID, PROJECT_MODULES } from "@/lib/constants";

export function generateStaticParams() {
  if (!DEMO_MODE) return [];
  return PROJECT_MODULES.map((moduleInfo) => ({
    id: DEMO_PROJECT_ID,
    module: moduleInfo.slug,
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string; module: string }>;
}): Promise<Metadata> {
  const { module: moduleSlug } = await params;
  const moduleInfo = PROJECT_MODULES.find((item) => item.slug === moduleSlug);
  return { title: moduleInfo?.label ?? "Module" };
}

export default async function ModulePage({
  params,
}: {
  params: Promise<{ id: string; module: string }>;
}) {
  const { id, module: moduleSlug } = await params;
  const moduleInfo = PROJECT_MODULES.find((item) => item.slug === moduleSlug);
  if (!moduleInfo) notFound();

  switch (moduleSlug) {
    case "components":
      return <PartsView projectId={id} />;
    case "wiring":
      return <WiringWorkspace projectId={id} />;
    case "programming":
      return <CodeView projectId={id} />;
    case "mechanical":
      return <MechanicalView projectId={id} />;
    case "cost":
      return <CostView projectId={id} />;
    case "docs":
      return <DocsView projectId={id} />;
    default:
      break;
  }

  const Icon = moduleInfo.icon;
  return (
    <div className="mx-auto max-w-3xl">
      <Link
        href={`/projects/${id}`}
        className="text-faint hover:text-ink mb-5 inline-flex items-center gap-1.5 text-xs transition-colors"
      >
        <ArrowLeft className="size-3.5" /> Back to project
      </Link>
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="border-line bg-elevated text-signal flex size-10 items-center justify-center rounded-lg border">
              <Icon className="size-5" strokeWidth={1.6} />
            </div>
            <div>
              <CardTitle>{moduleInfo.label}</CardTitle>
              <Badge variant="warn" className="mt-1">
                In development
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border-line bg-canvas/40 rounded-lg border border-dashed p-5">
            <div className="text-ink flex items-center gap-2 text-sm">
              <Construction className="text-warn size-4" /> This route is intentionally a scaffold.
            </div>
            <p className="text-muted mt-2 text-xs leading-relaxed">{moduleInfo.description}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
