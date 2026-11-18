"use client";

import { BookOpen, Download, FileText } from "lucide-react";
import { useState } from "react";

import { MissingArtifacts, ModuleShell } from "@/components/artifacts/module-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useBuild } from "@/hooks/use-build";
import { cn } from "@/lib/utils";

function download(name: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name.split("/").at(-1) ?? "doc.md";
  anchor.click();
  URL.revokeObjectURL(url);
}

function Markdown({ content }: { content: string }) {
  const lines = content.split("\n");
  return (
    <div className="space-y-2 text-[12.5px] leading-relaxed">
      {lines.map((line, index) => {
        const key = `${index}-${line.slice(0, 12)}`;
        if (line.startsWith("# ")) {
          return (
            <h2 key={key} className="text-ink pt-1 text-lg font-medium">
              {line.slice(2)}
            </h2>
          );
        }
        if (line.startsWith("## ")) {
          return (
            <h3 key={key} className="text-ink pt-3 text-sm font-medium">
              {line.slice(3)}
            </h3>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <p key={key} className="text-muted flex gap-2 pl-1">
              <span className="text-signal mt-1.5 size-1 shrink-0 rounded-full bg-current" />
              {line.slice(2)}
            </p>
          );
        }
        if (line.startsWith("|")) {
          return (
            <p
              key={key}
              className="text-muted overflow-x-auto font-mono text-[10.5px] whitespace-pre"
            >
              {line}
            </p>
          );
        }
        if (!line.trim()) return <div key={key} className="h-1" />;
        return (
          <p key={key} className="text-muted">
            {line}
          </p>
        );
      })}
    </div>
  );
}

export function DocsView({ projectId }: { projectId: string }) {
  const { build, loading, error } = useBuild(projectId);
  const files = build?.documentation.files ?? [];
  const [active, setActive] = useState<string | null>(null);
  const file = files.find((item) => item.path === active) ?? files[0] ?? null;

  return (
    <ModuleShell
      projectId={projectId}
      title="Documentation"
      description="Everything generated for this build, written down: sourcing, wiring, firmware, mechanical pricing, safety, decisions, and budget."
      loading={loading}
      error={error}
      build={build}
      requirement={(value) => value.documentation.files.length > 0}
    >
      {build && file ? (
        <div className="space-y-4">
          <MissingArtifacts build={build} />

          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="signal">
              <BookOpen className="size-2.5" /> {files.length} documents
            </Badge>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => download(file.path, file.content)}
              className="ml-auto"
            >
              <Download className="size-3.5" /> Download this file
            </Button>
          </div>

          <div className="grid items-start gap-4 lg:grid-cols-[240px_1fr]">
            <Card className="overflow-hidden p-1.5">
              <ul>
                {files.map((item) => (
                  <li key={item.path}>
                    <button
                      type="button"
                      onClick={() => setActive(item.path)}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-[11px] transition-colors",
                        item.path === file.path
                          ? "bg-signal/[0.08] text-ink"
                          : "text-muted hover:bg-white/[0.04]",
                      )}
                    >
                      <FileText className="text-signal/70 size-3.5 shrink-0" />
                      <span className="min-w-0">
                        <span className="block truncate">{item.title}</span>
                        <span className="text-faint block truncate font-mono text-[9px]">
                          {item.path}
                        </span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="p-5">
              <Markdown content={file.content} />
            </Card>
          </div>
        </div>
      ) : null}
    </ModuleShell>
  );
}
