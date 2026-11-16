import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { CreateProjectForm } from "@/components/projects/create-project-form";

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
      <CreateProjectForm />
    </>
  );
}
