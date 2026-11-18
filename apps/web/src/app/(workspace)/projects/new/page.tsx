import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, ArrowRight, FlaskConical } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { CreateProjectForm } from "@/components/projects/create-project-form";
import { ButtonLink } from "@/components/ui/button";
import { DEMO_MODE, DEMO_PROJECT_ID } from "@/lib/constants";

export const metadata: Metadata = { title: "New project" };

export default function NewProjectPage() {
  return (
    <>
      <Link
        href="/dashboard"
        className="text-faint hover:text-ink mb-5 inline-flex items-center gap-1.5 text-xs transition-colors"
      >
        <ArrowLeft className="size-3.5" /> Back to projects
      </Link>
      <PageHeader
        eyebrow="New robot project"
        title="What do you want to build?"
        description="Start with intent. RoboCraft will keep the specification, components, wiring, code, and budget aligned as the project grows."
      />
      {DEMO_MODE ? (
        <div className="rounded-panel border-signal/20 bg-signal/[0.05] max-w-2xl border px-5 py-4">
          <div className="text-ink flex items-center gap-2 text-sm font-medium">
            <FlaskConical className="text-signal size-4" /> Project creation needs the full API
          </div>
          <p className="text-muted mt-2 text-xs leading-relaxed">
            This GitHub Pages build is a read-only demo generated from precomputed engine output.
            Open the demo project to explore a real specification, bill of materials, and validated
            wiring plan, including the netlist and build-guide exports.
          </p>
          <ButtonLink href={`/projects/${DEMO_PROJECT_ID}/wiring`} size="sm" className="mt-4">
            Open the wiring demo <ArrowRight className="size-3.5" />
          </ButtonLink>
        </div>
      ) : (
        <CreateProjectForm />
      )}
    </>
  );
}
