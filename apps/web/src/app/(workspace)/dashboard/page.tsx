import type { Metadata } from "next";
import { Plus } from "lucide-react";

import { DashboardView } from "@/components/dashboard/dashboard-view";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button";

export const metadata: Metadata = { title: "Dashboard" };

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        eyebrow="Workspace"
        title="Robot projects"
        description="Every build starts with a specification. Create a project, describe the goal, and let the agent pipeline turn it into a plan."
        actions={
          <ButtonLink href="/projects/new">
            <Plus className="size-4" /> New project
          </ButtonLink>
        }
      />
      <DashboardView />
    </>
  );
}
