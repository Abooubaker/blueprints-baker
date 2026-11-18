"use client";

import { CircleDollarSign, Info, TriangleAlert } from "lucide-react";

import { MissingArtifacts, ModuleShell } from "@/components/artifacts/module-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/misc";
import { useBuild } from "@/hooks/use-build";
import { formatJod, formatMoney, titleCase } from "@/lib/utils";

const STATUS: Record<string, { label: string; variant: "signal" | "warn" | "danger" | "outline" }> =
  {
    within: { label: "Within budget", variant: "signal" },
    over: { label: "Over budget", variant: "danger" },
    under: { label: "Under budget", variant: "signal" },
    unknown: { label: "Budget not set", variant: "outline" },
  };

export function CostView({ projectId }: { projectId: string }) {
  const { build, loading, error } = useBuild(projectId);
  const cost = build?.cost ?? null;
  const status = STATUS[cost?.budget_status ?? "unknown"] ?? STATUS.unknown!;
  const budgetMax = cost?.budget.max_usd ? Number(cost.budget.max_usd) : null;
  const totalUsd = cost?.total_usd ? Number(cost.total_usd) : null;
  const usedPercent =
    budgetMax && totalUsd ? Math.min(100, Math.round((totalUsd / budgetMax) * 100)) : 0;

  return (
    <ModuleShell
      projectId={projectId}
      title="Budget"
      description="A transparent roll-up of parts at the cheapest selected store, the printed chassis, and a contingency. Estimates in JOD, with USD kept for the original budget."
      loading={loading}
      error={error}
      build={build}
      requirement={(value) => Boolean(value.cost)}
    >
      {build && cost ? (
        <div className="space-y-5">
          <MissingArtifacts build={build} />

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="p-4">
              <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                Components
              </p>
              <p className="text-ink mt-2 text-xl font-medium">{formatJod(cost.subtotal_jod)}</p>
            </Card>
            <Card className="p-4">
              <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                3D print
              </p>
              <p className="text-ink mt-2 text-xl font-medium">{formatJod(cost.print_cost_jod)}</p>
              {build.mechanical ? (
                <p className="text-faint mt-1 text-[10px]">
                  {build.mechanical.selected_material} · {build.mechanical.infill_percent}% infill
                </p>
              ) : null}
            </Card>
            <Card className="p-4">
              <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">Total</p>
              <p className="text-ink mt-2 text-xl font-medium">{formatJod(cost.total_jod)}</p>
              <p className="text-faint mt-1 text-[10px]">{formatMoney(totalUsd)} USD</p>
            </Card>
            <Card className="p-4">
              <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">Budget</p>
              <div className="mt-2">
                <Badge variant={status.variant}>{status.label}</Badge>
              </div>
              <p className="text-faint mt-1 text-[10px]">
                {budgetMax ? `Cap ${formatMoney(budgetMax)}` : "No cap set"}
              </p>
            </Card>
          </div>

          {budgetMax ? (
            <Card className="p-4">
              <div className="text-faint mb-2 flex items-center justify-between text-[10px]">
                <span>Budget used</span>
                <span className="font-mono">{usedPercent}%</span>
              </div>
              <Progress
                value={usedPercent}
                indicatorClassName={usedPercent > 100 ? "bg-danger" : undefined}
              />
            </Card>
          ) : null}

          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <CircleDollarSign className="text-signal size-4" /> Line items
              </CardTitle>
              <Badge variant="outline">JOD estimates</Badge>
            </CardHeader>
            <CardContent>
              <div className="border-line-soft overflow-x-auto rounded-lg border">
                <table className="w-full min-w-[540px] text-left text-xs">
                  <thead className="bg-canvas/50 text-faint font-mono text-[9px] tracking-wider uppercase">
                    <tr>
                      <th className="px-3 py-2 font-normal">Item</th>
                      <th className="px-3 py-2 font-normal">Store</th>
                      <th className="px-3 py-2 text-right font-normal">Qty</th>
                      <th className="px-3 py-2 text-right font-normal">Unit</th>
                      <th className="px-3 py-2 text-right font-normal">Line</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cost.line_items.map((item, index) => (
                      <tr key={`${item.label}-${index}`} className="border-line-soft border-t">
                        <td className="text-ink px-3 py-2">
                          {item.label}
                          <span className="text-faint ml-1.5 font-mono text-[9px]">
                            {titleCase(item.category)}
                          </span>
                        </td>
                        <td className="text-muted px-3 py-2">{titleCase(item.supplier)}</td>
                        <td className="text-muted px-3 py-2 text-right font-mono">
                          {item.quantity}
                        </td>
                        <td className="text-muted px-3 py-2 text-right font-mono">
                          {formatJod(item.unit_price_jod ?? item.unit_price_usd)}
                        </td>
                        <td className="text-ink px-3 py-2 text-right font-mono">
                          {formatJod(item.line_total_jod ?? item.line_total_usd)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-line-soft border-t">
                      <td className="text-muted px-3 py-2" colSpan={4}>
                        Components subtotal
                      </td>
                      <td className="text-ink px-3 py-2 text-right font-mono">
                        {formatJod(cost.subtotal_jod)}
                      </td>
                    </tr>
                    <tr className="border-line-soft border-t">
                      <td className="text-muted px-3 py-2" colSpan={4}>
                        3D print ({build.mechanical?.selected_material ?? "selected material"})
                      </td>
                      <td className="text-ink px-3 py-2 text-right font-mono">
                        {formatJod(cost.print_cost_jod)}
                      </td>
                    </tr>
                    <tr className="border-line-soft bg-signal/[0.04] border-t">
                      <td className="text-ink px-3 py-2 font-medium" colSpan={4}>
                        Total
                      </td>
                      <td className="text-signal px-3 py-2 text-right font-mono">
                        {formatJod(cost.total_jod)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              <p className="text-faint mt-2 text-[10px]">
                Contingency {formatMoney(Number(cost.contingency_usd ?? 0))} USD · shipping excluded
                because selected stores ship differently.
              </p>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Ways to save</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2.5">
                  {cost.alternatives.map((alternative) => (
                    <li
                      key={alternative.description}
                      className="border-line-soft bg-canvas/30 rounded-lg border px-3 py-2"
                    >
                      <p className="text-ink text-xs">{alternative.description}</p>
                      <p className="text-faint mt-1 text-[10px]">
                        {alternative.tradeoffs.join(" · ")}
                      </p>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Info className="text-aqua size-4" /> Assumptions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="text-muted space-y-1.5 text-[11px] leading-relaxed">
                  {cost.assumptions.map((assumption) => (
                    <li key={assumption}>• {assumption}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          <div className="rounded-panel border-warn/20 bg-warn/[0.05] flex items-start gap-2 border px-4 py-3">
            <TriangleAlert className="text-warn mt-0.5 size-3.5 shrink-0" />
            <p className="text-muted text-[11px] leading-relaxed">
              These are planning estimates. Confirm live price, stock, and shipping at each store
              before ordering.
            </p>
          </div>
        </div>
      ) : null}
    </ModuleShell>
  );
}
