"use client";

import { Box, Download, Printer, Scale, TriangleAlert } from "lucide-react";

import { MissingArtifacts, ModuleShell } from "@/components/artifacts/module-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBuild } from "@/hooks/use-build";
import { formatJod, titleCase } from "@/lib/utils";

function downloadStl(name: string, content: string) {
  const blob = new Blob([content], { type: "model/stl" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function MechanicalView({ projectId }: { projectId: string }) {
  const { build, loading, error } = useBuild(projectId);
  const mechanical = build?.mechanical ?? null;

  return (
    <ModuleShell
      projectId={projectId}
      title="3D model & print price"
      description="A basic parametric chassis exported as STL. It exists to estimate printed weight and price with the required JOD material chart — not as a production enclosure."
      loading={loading}
      error={error}
      build={build}
      requirement={(value) => Boolean(value.mechanical?.stl_ascii)}
    >
      {build && mechanical ? (
        <div className="space-y-5">
          <MissingArtifacts build={build} />

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                label: "Dimensions",
                value: `${mechanical.dimensions_mm.length_mm ?? "—"} × ${mechanical.dimensions_mm.width_mm ?? "—"} × ${mechanical.dimensions_mm.height_mm ?? "—"} mm`,
              },
              { label: "Volume", value: `${Number(mechanical.volume_cm3).toFixed(2)} cm³` },
              { label: "Infill", value: `${mechanical.infill_percent}%` },
              {
                label: "Cheapest print",
                value: formatJod(
                  mechanical.material_quotes.find((quote) => quote.is_cheapest)?.total_jod,
                ),
              },
            ].map((item) => (
              <Card key={item.label} className="p-4">
                <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                  {item.label}
                </p>
                <p className="text-ink mt-2 text-sm font-medium">{item.value}</p>
              </Card>
            ))}
          </div>

          <div className="grid items-start gap-4 lg:grid-cols-[1fr_1.15fr]">
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Box className="text-signal size-4" /> Reference model
                </CardTitle>
                <Badge variant="outline">STL · mm</Badge>
              </CardHeader>
              <CardContent>
                <div className="bg-blueprint border-line-soft relative flex h-52 items-center justify-center overflow-hidden rounded-lg border">
                  <svg viewBox="0 0 240 150" className="h-full w-full max-w-[280px]">
                    <g stroke="#7dd3fc" strokeOpacity="0.8" fill="none" strokeWidth="1.2">
                      <path d="M40 105 L150 105 L190 80 L80 80 Z" />
                      <path d="M40 105 L40 65 L80 40 L80 80" />
                      <path d="M80 80 L190 80 L190 40 L80 40 Z" />
                      <path d="M40 65 L150 65 L190 40" strokeDasharray="3 3" />
                      <path d="M150 105 L150 65" strokeDasharray="3 3" />
                    </g>
                    <text x="95" y="128" fill="#94a29c" fontSize="7" fontFamily="monospace">
                      {mechanical.dimensions_mm.length_mm} mm
                    </text>
                    <text x="196" y="70" fill="#94a29c" fontSize="7" fontFamily="monospace">
                      {mechanical.dimensions_mm.width_mm} mm
                    </text>
                    <text x="8" y="90" fill="#94a29c" fontSize="7" fontFamily="monospace">
                      {mechanical.dimensions_mm.height_mm} mm
                    </text>
                  </svg>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-3 w-full"
                  onClick={() => downloadStl(mechanical.stl_filename, mechanical.stl_ascii)}
                >
                  <Download className="size-3.5" /> Download {mechanical.stl_filename}
                </Button>
                <p className="text-faint mt-2 text-[10px] leading-relaxed">
                  {mechanical.manufacturing_notes[0]}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Printer className="text-signal size-4" /> Material price chart
                </CardTitle>
                <p className="text-muted text-[11px]">
                  total = max(minimum, base + price per gram × weight)
                </p>
              </CardHeader>
              <CardContent>
                <div className="border-line-soft overflow-hidden rounded-lg border">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-canvas/50 text-faint font-mono text-[9px] tracking-wider uppercase">
                      <tr>
                        <th className="px-3 py-2 font-normal">Material</th>
                        <th className="px-3 py-2 text-right font-normal">JOD/g</th>
                        <th className="px-3 py-2 text-right font-normal">Weight</th>
                        <th className="px-3 py-2 text-right font-normal">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mechanical.material_quotes.map((quote) => (
                        <tr
                          key={quote.material}
                          className={
                            quote.is_cheapest
                              ? "border-line-soft bg-signal/[0.06] border-t"
                              : "border-line-soft border-t"
                          }
                        >
                          <td className="text-ink px-3 py-2">
                            {quote.material}
                            {quote.is_cheapest ? (
                              <span className="text-signal ml-1.5 font-mono text-[8px] uppercase">
                                cheapest
                              </span>
                            ) : null}
                          </td>
                          <td className="text-muted px-3 py-2 text-right font-mono">
                            {Number(quote.price_per_gram_jod).toFixed(3)}
                          </td>
                          <td className="text-muted px-3 py-2 text-right font-mono">
                            {Number(quote.weight_g).toFixed(1)} g
                          </td>
                          <td className="text-ink px-3 py-2 text-right font-mono">
                            {formatJod(quote.total_jod)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="text-faint mt-2 flex items-start gap-1.5 text-[10px] leading-relaxed">
                  <Scale className="mt-0.5 size-3 shrink-0" />
                  Weight uses a 40% effective material fraction for a 35% infill print.
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Mechanical parts</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {mechanical.parts.map((part) => (
                    <li
                      key={part.name}
                      className="border-line-soft bg-canvas/30 rounded-lg border px-3 py-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-ink text-xs">{part.name}</span>
                        <Badge variant="outline">×{part.quantity}</Badge>
                      </div>
                      <p className="text-faint mt-1 text-[10px]">
                        {titleCase(part.category)} · {part.material}
                      </p>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Assembly</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-3">
                  {mechanical.assembly_steps.map((step) => (
                    <li key={step.order} className="flex gap-2.5">
                      <span className="border-signal/25 bg-signal/10 text-signal flex size-5 shrink-0 items-center justify-center rounded-full border font-mono text-[9px]">
                        {step.order}
                      </span>
                      <div>
                        <p className="text-ink text-xs font-medium">{step.title}</p>
                        <p className="text-muted mt-0.5 text-[11px] leading-relaxed">
                          {step.instructions}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          </div>

          {mechanical.warnings.length ? (
            <div className="rounded-panel border-warn/20 bg-warn/[0.05] border px-4 py-3">
              <p className="text-warn flex items-center gap-2 text-xs font-medium">
                <TriangleAlert className="size-3.5" /> Honest limits
              </p>
              <ul className="text-muted mt-2 space-y-1 text-[11px]">
                {mechanical.warnings.map((warning) => (
                  <li key={warning}>• {warning}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </ModuleShell>
  );
}
