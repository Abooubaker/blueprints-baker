from __future__ import annotations

from decimal import Decimal

from app.models.enums import PrintMaterial
from app.pricing import material_fraction_for_infill, price_print


def test_material_fraction_scales_with_infill() -> None:
    assert material_fraction_for_infill(0) == Decimal("0.080")
    assert material_fraction_for_infill(35) == Decimal("0.402")
    assert material_fraction_for_infill(100) == Decimal("1.000")


def test_print_price_uses_selected_material_and_custom_rate() -> None:
    quotes = price_print(
        Decimal("88"),
        infill_percent=60,
        price_overrides={PrintMaterial.PETG: Decimal("0.15")},
        selected_material=PrintMaterial.PETG,
    )

    selected = next(quote for quote in quotes if quote["is_selected"])
    assert selected["material"] == PrintMaterial.PETG.value
    assert selected["price_per_gram_jod"] == Decimal("0.15")
    assert selected["weight_g"] > Decimal("0")

    chart_petg = next(
        quote
        for quote in price_print(Decimal("88"), infill_percent=60)
        if quote["material"] == PrintMaterial.PETG.value
    )
    assert selected["weight_g"] == chart_petg["weight_g"]
    assert selected["total_jod"] > chart_petg["total_jod"]


def test_lower_infill_weighs_less() -> None:
    dense = price_print(Decimal("88"), infill_percent=80)
    light = price_print(Decimal("88"), infill_percent=20)

    dense_weight = next(quote["weight_g"] for quote in dense if quote["material"] == "PLA")
    light_weight = next(quote["weight_g"] for quote in light if quote["material"] == "PLA")
    assert light_weight < dense_weight
