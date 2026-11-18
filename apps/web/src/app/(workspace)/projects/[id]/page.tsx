import type { Metadata } from "next";

import { ProjectWorkspace } from "@/components/projects/project-workspace";
import { DEMO_MODE, DEMO_PROJECT_ID } from "@/lib/constants";

export const metadata: Metadata = { title: "Project overview" };

export function generateStaticParams() {
  return DEMO_MODE ? [{ id: DEMO_PROJECT_ID }] : [];
}

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ProjectWorkspace projectId={id} />;
}
