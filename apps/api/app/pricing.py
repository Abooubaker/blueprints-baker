"""Curated pricing rules for store estimates and 3D printing.

Nothing in this module calls a supplier. The numbers are deterministic planning
estimates in Jordanian dinars (JOD) so the guided flow can rank each part from
the cheapest selected store to the most expensive one. Real supplier APIs or
feeds can replace :func:`build_store_offers` without changing the contract.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import quote_plus

from app.ai.contracts import StoreOffer
from app.electrical.library import ComponentProfile
from app.models.enums import PrintMaterial, StoreName

JOD_PER_USD = Decimal("0.709")

# Per-store price modifiers and search endpoints. The modifiers are planning
# assumptions, not scraped prices.
STORE_META: dict[StoreName, tuple[str, Decimal, str, str]] = {
    StoreName.TEMU: (
        "Temu",
        Decimal("0.62"),
        "https://www.temu.com/search_result.html?search_key={q}",
        "in_stock",
    ),
    StoreName.ALIEXPRESS: (
        "AliExpress",
        Decimal("0.68"),
        "https://www.aliexpress.com/w/wholesale-{slug}.html",
        "in_stock",
    ),
    StoreName.MIKROELECTRON: (
        "MikroElectron",
        Decimal("0.96"),
        "https://mikroelectron.com/search?q={q}",
        "in_stock",
    ),
    StoreName.WASLLEH: (
        "Waslleh",
        Decimal("1.03"),
        "https://waslleh.com/?s={q}",
        "low_stock",
    ),
    StoreName.GHANIMJO: (
        "Ghanim Jo",
        Decimal("1.12"),
        "https://ghanimjo.com/?s={q}",
        "in_stock",
    ),
    StoreName.AMAZON: (
        "Amazon",
        Decimal("1.24"),
        "https://www.amazon.com/s?k={q}",
        "in_stock",
    ),
}

STORE_ORDER: tuple[StoreName, ...] = (
    StoreName.TEMU,
    StoreName.MIKROELECTRON,
    StoreName.WASLLEH,
    StoreName.AMAZON,
    StoreName.ALIEXPRESS,
    StoreName.GHANIMJO,
)


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _part_variance(profile: ComponentProfile) -> Decimal:
    """A stable per-part adjustment so stores do not all rank identically."""

    seed = sum(ord(character) for character in profile.key)
    return Decimal((seed % 11) - 5) / Decimal("100")


def _search_url(template: str, profile: ComponentProfile) -> str:
    query = quote_plus(f"{profile.manufacturer} {profile.model_number}".strip())
    slug = quote_plus(profile.name.replace(" ", "-").lower())
    return template.format(q=query, slug=slug)


def build_store_offers(
    profile: ComponentProfile,
    shops: list[StoreName] | tuple[StoreName, ...] | None = None,
) -> list[StoreOffer]:
    """Return selected-store estimates sorted cheapest first."""

    selected = list(shops or STORE_ORDER)
    base = profile.price_usd * JOD_PER_USD
    variance = _part_variance(profile)
    offers: list[StoreOffer] = []
    for store in selected:
        label, multiplier, url_template, availability = STORE_META[store]
        price = max(Decimal("0.10"), _money(base * multiplier * (Decimal("1") + variance)))
        offers.append(
            StoreOffer(
                store=store,
                label=label,
                price_jod=price,
                product_url=_search_url(url_template, profile),
                availability=availability,
                is_estimate=True,
                note="Curated estimate; confirm live price and stock before ordering.",
            )
        )
    offers.sort(key=lambda offer: (offer.price_jod, STORE_ORDER.index(offer.store)))
    return offers


# ---------------------------------------------------------------------------
# 3D print price chart
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PrintMaterialRule:
    material: PrintMaterial
    density_g_cm3: Decimal
    price_per_gram_jod: Decimal
    base_jod: Decimal
    minimum_jod: Decimal


PRINT_MATERIAL_RULES: tuple[PrintMaterialRule, ...] = (
    PrintMaterialRule(
        PrintMaterial.PLA, Decimal("1.24"), Decimal("0.070"), Decimal("0.500"), Decimal("1.000")
    ),
    PrintMaterialRule(
        PrintMaterial.PETG, Decimal("1.27"), Decimal("0.120"), Decimal("0.500"), Decimal("1.200")
    ),
    PrintMaterialRule(
        PrintMaterial.ABS, Decimal("1.04"), Decimal("0.120"), Decimal("0.500"), Decimal("1.000")
    ),
    PrintMaterialRule(
        PrintMaterial.RESIN, Decimal("1.10"), Decimal("0.300"), Decimal("0.500"), Decimal("1.500")
    ),
    PrintMaterialRule(
        PrintMaterial.TPU, Decimal("1.21"), Decimal("0.200"), Decimal("2.000"), Decimal("1.200")
    ),
)


_SHELL_FRACTION = Decimal("0.08")


def material_fraction_for_infill(infill_percent: int) -> Decimal:
    """Effective printed material fraction for a given infill percentage.

    A printed plate is not solid at low infill: walls and top/bottom layers still
    consume material. ``8%`` approximates those shells, and the remainder scales
    with infill. The default 35% therefore lands near the previous 40% estimate.
    """

    clamped = max(0, min(100, infill_percent))
    infill = Decimal(clamped) / Decimal("100")
    fraction = _SHELL_FRACTION + (Decimal("1") - _SHELL_FRACTION) * infill
    return fraction.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def price_print(
    volume_cm3: Decimal,
    *,
    infill_percent: int = 35,
    material_fraction: Decimal | None = None,
    price_overrides: Mapping[PrintMaterial, Decimal] | None = None,
    selected_material: PrintMaterial = PrintMaterial.PLA,
) -> list[dict[str, Decimal | str | bool]]:
    """Price a printed part for every material in the required chart.

    ``material_fraction`` is derived from ``infill_percent`` unless supplied.
    ``price_overrides`` replaces a chart rate for a material, which lets a user
    match a known local spool or print-shop price. The selected material is
    marked so the cost agent can use it instead of the cheapest quote.
    """

    fraction = (
        material_fraction
        if material_fraction is not None
        else material_fraction_for_infill(infill_percent)
    )
    overrides = price_overrides or {}
    quotes: list[dict[str, Decimal | str | bool]] = []
    for rule in PRINT_MATERIAL_RULES:
        price_per_gram = overrides.get(rule.material, rule.price_per_gram_jod)
        weight = volume_cm3 * rule.density_g_cm3 * fraction
        weight = weight.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = max(rule.minimum_jod, rule.base_jod + price_per_gram * weight)
        quotes.append(
            {
                "material": rule.material.value,
                "price_per_gram_jod": price_per_gram,
                "base_jod": rule.base_jod,
                "minimum_jod": rule.minimum_jod,
                "weight_g": weight,
                "total_jod": total.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
                "is_cheapest": False,
                "is_selected": rule.material == selected_material,
            }
        )
    cheapest = min(quotes, key=lambda quote: quote["total_jod"])
    for quote in quotes:
        quote["is_cheapest"] = quote is cheapest
    return quotes


def cheapest_print_quote(quotes: Sequence[object]) -> Decimal | None:
    """Return the cheapest total from serialized print quotes."""

    totals: list[Decimal] = []
    for quote in quotes:
        total = getattr(quote, "total_jod", None)
        if total is None and isinstance(quote, dict):
            total = quote.get("total_jod")
        if total is not None:
            totals.append(Decimal(str(total)))
    return min(totals) if totals else None


__all__ = [
    "JOD_PER_USD",
    "PRINT_MATERIAL_RULES",
    "STORE_META",
    "STORE_ORDER",
    "build_store_offers",
    "cheapest_print_quote",
    "material_fraction_for_infill",
    "price_print",
]
