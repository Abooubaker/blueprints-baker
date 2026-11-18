"use client";

import { Check, Copy, Download, FileCode2, FolderTree } from "lucide-react";
import { useState } from "react";

import { MissingArtifacts, ModuleShell } from "@/components/artifacts/module-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBuild } from "@/hooks/use-build";
import type { CodeLanguage } from "@/lib/types";
import { cn } from "@/lib/utils";

function languageBadge(language: CodeLanguage): string {
  switch (language) {
    case "python":
      return "PY";
    case "cpp":
      return "C++";
    case "c":
      return "C";
    case "stm32_assembly":
      return "ASM";
    case "verilog":
      return "V";
    case "vhdl":
      return "VHD";
    default:
      return "TXT";
  }
}

function extensionColor(path: string): string {
  if (path.endsWith(".py")) return "text-[#7dd3fc]";
  if (path.endsWith(".c") || path.endsWith(".h") || path.endsWith(".cpp")) return "text-[#93c5fd]";
  if (path.endsWith(".v") || path.endsWith(".vhd")) return "text-[#f0abfc]";
  if (path.endsWith(".s")) return "text-[#fcd34d]";
  if (path.endsWith(".md")) return "text-[#a7f3d0]";
  if (path.endsWith(".ini")) return "text-[#fdba74]";
  return "text-faint";
}

function downloadFile(name: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function CodeView({ projectId }: { projectId: string }) {
  const { build, loading, error } = useBuild(projectId);
  const bundles = build?.programming?.bundles ?? [];
  const [activeLanguage, setActiveLanguage] = useState<CodeLanguage | null>(null);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const bundle = bundles.find((item) => item.language === activeLanguage) ?? bundles[0] ?? null;
  const file = bundle?.files.find((item) => item.path === activeFile) ?? bundle?.files[0] ?? null;

  async function copy() {
    if (!file) return;
    await navigator.clipboard.writeText(file.content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <ModuleShell
      projectId={projectId}
      title="Generated code"
      description="Multi-file starter bundles for every language you selected, generated from the validated controller pin map. Complete the TODO blocks and verify on hardware."
      loading={loading}
      error={error}
      build={build}
      requirement={(value) => Boolean(value.programming?.bundles.length)}
    >
      {build && bundle && file ? (
        <div className="space-y-4">
          <MissingArtifacts build={build} />

          <div className="flex flex-wrap items-center gap-1.5">
            {bundles.map((item) => (
              <button
                key={item.language}
                type="button"
                onClick={() => {
                  setActiveLanguage(item.language);
                  setActiveFile(item.files[0]?.path ?? null);
                }}
                className={cn(
                  "flex items-center gap-2 rounded-lg border px-3 py-2 text-xs transition-colors",
                  item.language === bundle.language
                    ? "border-signal/35 bg-signal/[0.08] text-ink"
                    : "border-line bg-canvas/40 text-muted hover:border-[#2d6894]",
                )}
              >
                <span className="text-signal font-mono text-[9px]">
                  {languageBadge(item.language)}
                </span>
                {item.display_name}
              </button>
            ))}
          </div>

          <div className="rounded-panel border-line overflow-hidden border bg-[#0b1116]">
            <div className="border-line-soft flex items-center justify-between border-b bg-[#0e151b] px-4 py-2">
              <div className="flex items-center gap-2">
                <span className="size-2.5 rounded-full bg-[#ff5f57]" />
                <span className="size-2.5 rounded-full bg-[#febc2e]" />
                <span className="size-2.5 rounded-full bg-[#28c840]" />
                <span className="text-faint ml-2 font-mono text-[10px]">
                  {build.project_name.toLowerCase().replaceAll(" ", "-")} — {file.path}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => void copy()}>
                  {copied ? (
                    <>
                      <Check className="size-3" /> Copied
                    </>
                  ) : (
                    <>
                      <Copy className="size-3" /> Copy
                    </>
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    downloadFile(file.path.split("/").at(-1) ?? "file.txt", file.content)
                  }
                >
                  <Download className="size-3" /> Download
                </Button>
              </div>
            </div>

            <div className="grid min-h-[420px] md:grid-cols-[220px_1fr]">
              <aside className="border-line-soft border-b bg-[#0c1318] md:border-r md:border-b-0">
                <p className="text-faint flex items-center gap-1.5 px-3 py-2 font-mono text-[9px] tracking-[0.14em] uppercase">
                  <FolderTree className="size-3" /> Explorer
                </p>
                <ul>
                  {bundle.files.map((item) => (
                    <li key={item.path}>
                      <button
                        type="button"
                        onClick={() => setActiveFile(item.path)}
                        className={cn(
                          "flex w-full items-center gap-2 px-3 py-1.5 text-left font-mono text-[11px] transition-colors",
                          item.path === file.path
                            ? "text-ink bg-white/[0.06]"
                            : "text-muted hover:bg-white/[0.03]",
                        )}
                      >
                        <FileCode2 className={cn("size-3 shrink-0", extensionColor(item.path))} />
                        <span className="truncate">{item.path}</span>
                      </button>
                    </li>
                  ))}
                </ul>
                <div className="border-line-soft mt-3 border-t px-3 py-2">
                  <p className="text-faint text-[10px]">Libraries</p>
                  <p className="text-muted mt-1 text-[10px] leading-relaxed">
                    {bundle.libraries.length ? bundle.libraries.join(", ") : "None"}
                  </p>
                </div>
              </aside>

              <div className="min-w-0">
                <div className="border-line-soft flex items-center gap-2 border-b bg-[#0e151b] px-3 py-1.5">
                  <span className="text-muted border-line-soft rounded-t border-b-2 border-b-[#7dd3fc] px-2 py-1 font-mono text-[10px]">
                    {file.path.split("/").at(-1)}
                  </span>
                </div>
                <pre className="text-ink/85 overflow-auto p-4 font-mono text-[11.5px] leading-[1.65]">
                  <code>
                    {file.content.split("\n").map((line, index) => (
                      <div key={index} className="flex">
                        <span className="text-faint/60 w-8 shrink-0 text-right select-none">
                          {index + 1}
                        </span>
                        <span className="pl-4 whitespace-pre-wrap">{line || " "}</span>
                      </div>
                    ))}
                  </code>
                </pre>
              </div>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Setup</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="text-muted space-y-1.5 text-[11px] leading-relaxed">
                  {build.programming?.setup_steps.map((step, index) => (
                    <li key={step} className="flex gap-2">
                      <span className="text-signal font-mono">{index + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Upload & verify</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="text-muted space-y-1.5 text-[11px] leading-relaxed">
                  {build.programming?.upload_steps.map((step, index) => (
                    <li key={step} className="flex gap-2">
                      <span className="text-signal font-mono">{index + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          </div>

          {bundle.notes.length ? (
            <div className="rounded-panel border-warn/20 bg-warn/[0.05] border px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="warn">Scaffold</Badge>
                <span className="text-faint text-[10px]">
                  Status: {bundle.status} · framework: {bundle.framework || "toolchain-neutral"}
                </span>
              </div>
              <ul className="text-muted mt-2 space-y-1 text-[11px]">
                {bundle.notes.map((note) => (
                  <li key={note}>• {note}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </ModuleShell>
  );
}
