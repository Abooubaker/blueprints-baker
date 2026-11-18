"use client";

import { ArrowUpRight, Store, TriangleAlert } from "lucide-react";

import { MissingArtifacts, ModuleShell } from "@/components/artifacts/module-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBuild } from "@/hooks/use-build";
import { formatJod, titleCase } from "@/lib/utils";

export function PartsView({ projectId }: { projectId: string }) {
  const { build, loading, error } = useBuild(projectId);
  const research = build?.research ?? null;

  return (
    <ModuleShell
      projectId={projectId}
      title="Parts & prices"
      description="Each part priced at every store you selected, sorted from cheapest to most expensive. Prices are curated estimates in JOD, not live quotes."
      loading={loading}
      error={error}
      build={build}
      requirement={(value) => Boolean(value.research)}
    >
      {build && research ? (
        <div className="space-y-5">
          <MissingArtifacts build={build} />

          <div className="grid gap-3 sm:grid-cols-3">
            <Card className="p-4">
              <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">Parts</p>
              <p className="text-ink mt-2 text-2xl font-medium">
                {research.bill_of_materials.length}
              </p>
            </Card>
            <Card className="p-4">
              <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                Component subtotal
              </p>
              <p className="text-ink mt-2 text-2xl font-medium">
                {formatJod(research.total_estimated_jod)}
              </p>
              <p className="text-faint mt-1 text-[10px]">cheapest selected store per part</p>
            </Card>
            <Card className="p-4">
              <p className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
                Stores compared
              </p>
              <p className="text-ink mt-2 text-lg font-medium">
                {(research.selected_shops ?? []).length || "All"}
              </p>
              <p className="text-faint mt-1 truncate text-[10px]">
                {(research.selected_shops ?? []).map(titleCase).join(", ") || "—"}
              </p>
            </Card>
          </div>

          <div className="space-y-3">
            {research.bill_of_materials.map((item, index) => {
              const candidate = item.selection;
              const offers = candidate?.offers ?? [];
              return (
                <Card key={`${item.role}-${index}`}>
                  <CardHeader className="flex-row items-start justify-between gap-3 space-y-0 pb-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <CardTitle className="text-sm">{candidate?.name ?? item.role}</CardTitle>
                        <Badge variant="outline">×{item.quantity}</Badge>
                        <Badge>{titleCase(item.category)}</Badge>
                      </div>
                      <p className="text-faint mt-1 text-[11px]">
                        {candidate
                          ? `${candidate.manufacturer} ${candidate.model_number}`.trim()
                          : "Unresolved requirement"}
                        {candidate?.cheapest_store ? (
                          <>
                            {" · "}
                            <span className="text-signal">
                              Cheapest: {titleCase(candidate.cheapest_store)} at{" "}
                              {formatJod(candidate.cheapest_price_jod)}
                            </span>
                          </>
                        ) : null}
                      </p>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {offers.length ? (
                      <div className="border-line-soft overflow-hidden rounded-lg border">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-canvas/50 text-faint font-mono text-[9px] tracking-wider uppercase">
                            <tr>
                              <th className="px-3 py-2 font-normal">Rank</th>
                              <th className="px-3 py-2 font-normal">Store</th>
                              <th className="px-3 py-2 font-normal">Availability</th>
                              <th className="px-3 py-2 text-right font-normal">Estimate</th>
                              <th className="px-3 py-2" />
                            </tr>
                          </thead>
                          <tbody>
                            {offers.map((offer, offerIndex) => (
                              <tr
                                key={`${offer.store}-${offerIndex}`}
                                className="border-line-soft border-t"
                              >
                                <td className="text-faint px-3 py-2 font-mono">
                                  {offerIndex === 0 ? (
                                    <span className="text-signal">01</span>
                                  ) : (
                                    String(offerIndex + 1).padStart(2, "0")
                                  )}
                                </td>
                                <td className="text-ink px-3 py-2">{offer.label}</td>
                                <td className="text-muted px-3 py-2">
                                  {titleCase(offer.availability)}
                                </td>
                                <td className="text-ink px-3 py-2 text-right font-mono">
                                  {formatJod(offer.price_jod)}
                                </td>
                                <td className="px-3 py-2 text-right">
                                  {offer.product_url ? (
                                    <a
                                      href={offer.product_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-signal hover:text-ink inline-flex items-center gap-1 text-[10px]"
                                    >
                                      Search <ArrowUpRight className="size-3" />
                                    </a>
                                  ) : null}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-faint text-xs">
                        No store offers for this part. It will be resolved by the planner.
                      </p>
                    )}
                    {item.rationale ? (
                      <p className="text-faint mt-2.5 text-[11px] leading-relaxed">
                        {item.rationale}
                      </p>
                    ) : null}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {research.unresolved_requirements.length ? (
            <div className="rounded-panel border-warn/20 bg-warn/[0.05] border px-4 py-3">
              <p className="text-warn flex items-center gap-2 text-xs font-medium">
                <TriangleAlert className="size-3.5" /> Unresolved requirements
              </p>
              <ul className="text-muted mt-2 space-y-1 text-[11px]">
                {research.unresolved_requirements.map((item) => (
                  <li key={item}>• {item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="rounded-panel border-line-soft bg-surface/60 border px-4 py-3">
            <p className="text-faint flex items-center gap-2 text-[11px]">
              <Store className="size-3.5" /> How these prices work
            </p>
            <ul className="text-muted mt-2 space-y-1 text-[11px] leading-relaxed">
              {research.compatibility_notes.map((note) => (
                <li key={note}>• {note}</li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </ModuleShell>
  );
}
