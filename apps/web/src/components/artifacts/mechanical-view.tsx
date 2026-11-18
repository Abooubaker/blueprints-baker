"use client";

import {
  Box,
  Download,
  Printer,
  RotateCcw,
  Scale,
  SlidersHorizontal,
  TriangleAlert,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { MissingArtifacts, ModuleShell } from "@/components/artifacts/module-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBuild } from "@/hooks/use-build";
import { api, ApiError } from "@/lib/api";
import { DEMO_MODE, PRINT_CHART } from "@/lib/constants";
import { chartPriceFor, materialFractionForInfill, recalculatePrintQuotes } from "@/lib/print";
import type { PrintMaterial, PrintSettings } from "@/lib/types";
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

function demoStorageKey(projectId: string): string {
  return `blueprints-baker:print:${projectId}`;
}

function readDemoSettings(projectId: string): PrintSettings | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(demoStorageKey(projectId));
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<PrintSettings>;
    const validMaterial = PRINT_CHART.some((entry) => entry.material === parsed.material);
    const validInfill =
      typeof parsed.infill_percent === "number" &&
      parsed.infill_percent >= 0 &&
      parsed.infill_percent <= 100;
    const validPrice =
      parsed.price_per_gram_jod === null ||
      (typeof parsed.price_per_gram_jod === "number" && parsed.price_per_gram_jod >= 0);
    if (!validMaterial || !validInfill || !validPrice) {
      return null;
    }
    return parsed as PrintSettings;
  } catch {
    return null;
  }
}

function Slider({
  label,
  value,
  min,
  max,
  step,
  suffix,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  suffix: string;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <label className="text-faint font-mono text-[9px] tracking-[0.16em] uppercase">
          {label}
        </label>
        <span className="text-ink font-mono text-xs">
          {value.toFixed(step < 0.01 ? 3 : 0)}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        aria-label={label}
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="accent-aqua w-full cursor-pointer"
      />
    </div>
  );
}

export function MechanicalView({ projectId }: { projectId: string }) {
  const { build, loading, error, setBuild } = useBuild(projectId);
  const mechanical = build?.mechanical ?? null;
  const [settings, setSettings] = useState<PrintSettings | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const initialized = useRef<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!mechanical || !build || initialized.current === projectId) return;
    initialized.current = projectId;
    const stored = DEMO_MODE ? readDemoSettings(projectId) : null;
    setSettings(
      stored ?? {
        material: mechanical.selected_material ?? build.preferences.print_settings.material,
        infill_percent: mechanical.infill_percent,
        price_per_gram_jod: mechanical.custom_price_per_gram_jod,
      },
    );
  }, [build, mechanical, projectId]);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );

  const recalculated = useMemo(
    () => (mechanical && settings ? recalculatePrintQuotes(mechanical, settings) : null),
    [mechanical, settings],
  );
  const selected = recalculated?.selected ?? null;

  async function persist(next: PrintSettings) {
    if (DEMO_MODE) {
      try {
        window.localStorage.setItem(demoStorageKey(projectId), JSON.stringify(next));
        setSaveState("saved");
      } catch {
        setSaveState("error");
        setSaveError("This browser blocked local storage, so the demo change is temporary.");
      }
      return;
    }
    setSaveState("saving");
    setSaveError(null);
    try {
      const updated = await api.savePrintSettings(projectId, next);
      setBuild(updated);
      setSaveState("saved");
    } catch (caught) {
      setSaveState("error");
      setSaveError(
        caught instanceof ApiError ? caught.message : "Could not save the print settings.",
      );
    }
  }

  function update(next: Partial<PrintSettings>) {
    if (!settings) return;
    const merged = { ...settings, ...next };
    setSettings(merged);
    setSaveState("idle");
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => void persist(merged), 650);
  }

  const chartPrice = settings ? chartPriceFor(settings.material) : 0;
  const customPrice =
    settings && settings.price_per_gram_jod !== null && settings.price_per_gram_jod !== ""
      ? Number(settings.price_per_gram_jod)
      : null;
  const activePrice = customPrice ?? chartPrice;
  const priceMax = Math.max(
    0.5,
    Math.ceil(chartPrice * 5 * 100) / 100,
    Math.ceil(activePrice * 100) / 100,
  );
  const fraction = settings
    ? materialFractionForInfill(settings.infill_percent) * 100
    : mechanical
      ? Number(mechanical.material_fraction) * 100
      : 0;
  const dynamicWarnings = useMemo(() => {
    if (!mechanical || !settings) return [];
    const warnings = mechanical.warnings.filter(
      (warning) =>
        !warning.startsWith("Weigh the actual print;") && !warning.startsWith("Your custom "),
    );
    const effective = materialFractionForInfill(settings.infill_percent) * 100;
    warnings.push(
      `Weigh the actual print; the estimate uses a ${effective.toFixed(1)}% effective ` +
        `material fraction for ${settings.infill_percent}% infill.`,
    );
    if (customPrice !== null) {
      warnings.push(
        `Your custom ${settings.material} price of ${customPrice.toFixed(3)} JOD/g replaces ` +
          "the chart rate for the selected material only.",
      );
    }
    return warnings;
  }, [customPrice, mechanical, settings]);

  return (
    <ModuleShell
      projectId={projectId}
      title="3D model & print price"
      description="A basic parametric chassis exported as STL. Change the filament, infill, and per-gram price so the weight and total match what you can actually print for."
      loading={loading}
      error={error}
      build={build}
      requirement={(value) => Boolean(value.mechanical?.stl_ascii)}
    >
      {build && mechanical && settings ? (
        <div className="space-y-5">
          <MissingArtifacts build={build} />

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                label: "Dimensions",
                value: `${mechanical.dimensions_mm.length_mm ?? "—"} × ${mechanical.dimensions_mm.width_mm ?? "—"} × ${mechanical.dimensions_mm.height_mm ?? "—"} mm`,
              },
              { label: "Volume", value: `${Number(mechanical.volume_cm3).toFixed(2)} cm³` },
              { label: "Infill", value: `${settings.infill_percent}%` },
              {
                label: "Your print",
                value: formatJod(selected?.total_jod),
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

          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <SlidersHorizontal className="text-signal size-4" /> Print settings
              </CardTitle>
              <Badge variant={customPrice !== null ? "aqua" : "outline"}>
                {customPrice !== null ? "Your price" : "Chart price"}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <p className="text-faint mb-2 font-mono text-[9px] tracking-[0.16em] uppercase">
                  Filament type
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {PRINT_CHART.map((entry) => {
                    const active = settings.material === entry.material;
                    return (
                      <button
                        key={entry.material}
                        type="button"
                        aria-pressed={active}
                        onClick={() =>
                          update({
                            material: entry.material as PrintMaterial,
                            price_per_gram_jod: null,
                          })
                        }
                        className={
                          active
                            ? "border-signal/40 bg-signal/10 text-ink rounded-lg border px-3 py-1.5 text-xs font-medium"
                            : "border-line bg-canvas/40 text-muted rounded-lg border px-3 py-1.5 text-xs transition-colors hover:border-[#2d6894]"
                        }
                      >
                        {entry.material}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <Slider
                    label="Infill"
                    value={settings.infill_percent}
                    min={0}
                    max={100}
                    step={5}
                    suffix="%"
                    onChange={(value) => update({ infill_percent: value })}
                  />
                  <p className="text-faint mt-2 text-[10px]">
                    {fraction.toFixed(1)}% effective material after walls and top/bottom layers.
                  </p>
                </div>

                <div>
                  <Slider
                    label="Your filament price"
                    value={activePrice}
                    min={0.01}
                    max={priceMax}
                    step={0.005}
                    suffix=" JOD/g"
                    onChange={(value) => update({ price_per_gram_jod: value })}
                  />
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <p className="text-faint text-[10px]">Chart: {chartPrice.toFixed(3)} JOD/g</p>
                    {customPrice !== null ? (
                      <button
                        type="button"
                        onClick={() => update({ price_per_gram_jod: null })}
                        className="text-faint hover:text-ink inline-flex items-center gap-1 text-[10px] transition-colors"
                      >
                        <RotateCcw className="size-2.5" /> Use chart price
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="border-line-soft flex flex-wrap items-center justify-between gap-2 border-t pt-3">
                <p className="text-muted text-[11px]">
                  {settings.material} · {settings.infill_percent}% infill ·{" "}
                  {Number(selected?.weight_g ?? 0).toFixed(1)} g
                </p>
                <p className="text-faint text-[10px]">
                  {saveState === "saving"
                    ? "Saving estimate…"
                    : saveState === "saved"
                      ? DEMO_MODE
                        ? "Preview kept in this browser; the demo Budget stays on the shipped build."
                        : "Saved to this project and reflected in the Budget."
                      : saveState === "error"
                        ? (saveError ?? "Could not save.")
                        : "Changes update the weight, total, and budget."}
                </p>
              </div>
            </CardContent>
          </Card>

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
                      {recalculated?.quotes.map((quote) => (
                        <tr
                          key={quote.material}
                          className={
                            quote.is_selected
                              ? "border-line-soft bg-signal/[0.08] border-t"
                              : quote.is_cheapest
                                ? "border-line-soft bg-canvas/40 border-t"
                                : "border-line-soft border-t"
                          }
                        >
                          <td className="text-ink px-3 py-2">
                            {quote.material}
                            {quote.is_selected ? (
                              <span className="text-signal ml-1.5 font-mono text-[8px] uppercase">
                                your pick
                              </span>
                            ) : null}
                            {quote.is_cheapest && !quote.is_selected ? (
                              <span className="text-faint ml-1.5 font-mono text-[8px] uppercase">
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
                  Weight uses an 8% shell fraction plus the selected infill. Change the sliders to
                  match a real spool or print-shop quote.
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

          {dynamicWarnings.length ? (
            <div className="rounded-panel border-warn/20 bg-warn/[0.05] border px-4 py-3">
              <p className="text-warn flex items-center gap-2 text-xs font-medium">
                <TriangleAlert className="size-3.5" /> Honest limits
              </p>
              <ul className="text-muted mt-2 space-y-1 text-[11px]">
                {dynamicWarnings.map((warning) => (
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
