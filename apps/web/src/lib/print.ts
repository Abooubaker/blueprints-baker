import { PRINT_CHART } from "@/lib/constants";
import type {
  MechanicalOutput,
  PrintMaterial,
  PrintMaterialQuote,
  PrintSettings,
} from "@/lib/types";

/** Walls and top/bottom layers consume material even at 0% infill. */
const SHELL_FRACTION = 0.08;

export function materialFractionForInfill(infillPercent: number): number {
  const clamped = Math.max(0, Math.min(100, infillPercent));
  return SHELL_FRACTION + (1 - SHELL_FRACTION) * (clamped / 100);
}

export function printChartEntry(material: PrintMaterial) {
  return PRINT_CHART.find((entry) => entry.material === material) ?? PRINT_CHART[0];
}

export function chartPriceFor(material: PrintMaterial): number {
  return printChartEntry(material).perGram;
}

function numeric(value: number | string | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const parsed = typeof value === "string" ? Number(value) : value;
  return Number.isFinite(parsed) ? parsed : 0;
}

function round(value: number, digits: number): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

export interface PrintRecalculation {
  quotes: PrintMaterialQuote[];
  selected: PrintMaterialQuote | null;
  cheapest: PrintMaterialQuote | null;
}

/**
 * Recalculate every material quote for the current infill and selected price.
 *
 * The server quote stores the weight at the generated infill. Scaling that
 * weight by the ratio of material fractions keeps density differences between
 * materials intact while the controls move.
 */
export function recalculatePrintQuotes(
  mechanical: MechanicalOutput,
  settings: PrintSettings,
): PrintRecalculation {
  const baseFraction = materialFractionForInfill(mechanical.infill_percent);
  const nextFraction = materialFractionForInfill(settings.infill_percent);
  const ratio = baseFraction > 0 ? nextFraction / baseFraction : 1;
  const customPrice =
    settings.price_per_gram_jod === null || settings.price_per_gram_jod === ""
      ? null
      : numeric(settings.price_per_gram_jod);

  const quotes = mechanical.material_quotes.map((quote) => {
    const chart = printChartEntry(quote.material);
    const price =
      quote.material === settings.material ? (customPrice ?? chart.perGram) : chart.perGram;
    const weight = numeric(quote.weight_g) * ratio;
    const base = numeric(quote.base_jod);
    const minimum = numeric(quote.minimum_jod);
    return {
      ...quote,
      price_per_gram_jod: price,
      weight_g: round(weight, 2),
      total_jod: round(Math.max(minimum, base + price * weight), 3),
      is_cheapest: false,
      is_selected: quote.material === settings.material,
    };
  });

  const cheapest = quotes.reduce<PrintMaterialQuote | null>(
    (best, quote) =>
      best === null || numeric(quote.total_jod) < numeric(best.total_jod) ? quote : best,
    null,
  );
  if (cheapest) cheapest.is_cheapest = true;

  return {
    quotes,
    selected: quotes.find((quote) => quote.is_selected) ?? null,
    cheapest,
  };
}
