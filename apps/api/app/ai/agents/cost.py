"""Cost Estimation Agent — BOM, print material, and budget roll-up."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from app.ai.base import BaseAgent
from app.ai.contracts import (
    AgentRequest,
    BudgetAlternative,
    CostEstimate,
    CostInput,
    CostLineItem,
)
from app.models.enums import AgentName
from app.pricing import JOD_PER_USD, cheapest_print_quote


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CostEstimationAgent(BaseAgent):
    """Rolls up selected parts and the cheapest print material."""

    name = AgentName.COST
    display_name = "Cost Estimation"
    description = (
        "Rolls up the bill of materials and 3D-print material into a transparent "
        "estimate in USD and JOD, with budget alternatives."
    )
    depends_on = (AgentName.PLANNER, AgentName.COMPONENT_RESEARCH)
    input_model = CostInput
    output_model = CostEstimate
    status = "available"
    milestone = "M8"
    owner_area = "AI Engineering / Integrations"

    async def execute(self, request: AgentRequest) -> CostEstimate:
        research = request.context.shared.component_research
        if research is None:
            raise ValueError("Cost Estimation requires a component bill of materials.")

        line_items: list[CostLineItem] = []
        subtotal_usd = Decimal("0")
        subtotal_jod = Decimal("0")
        for item in research.bill_of_materials:
            selection = item.selection
            if selection is None:
                continue
            unit_usd = selection.price_usd or Decimal("0")
            unit_jod = selection.cheapest_price_jod or _money(unit_usd * JOD_PER_USD)
            line_usd = unit_usd * item.quantity
            line_jod = unit_jod * item.quantity
            subtotal_usd += line_usd
            subtotal_jod += line_jod
            line_items.append(
                CostLineItem(
                    label=selection.name,
                    category=item.category,
                    quantity=item.quantity,
                    unit_price_usd=unit_usd,
                    line_total_usd=line_usd,
                    unit_price_jod=unit_jod,
                    line_total_jod=line_jod,
                    supplier=selection.cheapest_store.value
                    if selection.cheapest_store is not None
                    else "estimate",
                    is_estimate=True,
                )
            )

        mechanical = request.context.shared.mechanical
        print_cost: Decimal | None = None
        if mechanical is not None and mechanical.material_quotes:
            print_cost = cheapest_print_quote(mechanical.material_quotes)
            if print_cost is not None:
                line_items.append(
                    CostLineItem(
                        label="3D-printed chassis (cheapest material)",
                        category="mechanical",
                        quantity=1,
                        unit_price_jod=print_cost,
                        line_total_jod=print_cost,
                        supplier="local 3D print",
                        is_estimate=True,
                    )
                )

        subtotal_usd = _money(subtotal_usd)
        subtotal_jod = _money(subtotal_jod)
        shipping_usd = Decimal("0")
        contingency_usd = _money(subtotal_usd * Decimal("0.05"))
        total_usd = _money(subtotal_usd + shipping_usd + contingency_usd)
        print_jod = _money(print_cost or Decimal("0"))
        total_jod = _money(subtotal_jod + print_jod)

        budget_max = request.context.budget.max_usd
        if budget_max is None:
            budget_status = "unknown"
        elif total_usd <= budget_max:
            budget_status = "within"
        else:
            budget_status = "over"

        alternatives = [
            BudgetAlternative(
                description="Use the cheapest selected store for every part.",
                tradeoffs=["Longer shipping and less predictable stock."],
            ),
            BudgetAlternative(
                description="Print the chassis in PLA instead of resin.",
                savings_usd=_money(print_jod * Decimal("0.45") * JOD_PER_USD),
                tradeoffs=["Lower heat resistance and a less smooth finish."],
            ),
        ]

        return CostEstimate(
            line_items=line_items,
            subtotal_usd=subtotal_usd,
            subtotal_jod=subtotal_jod,
            shipping_usd=shipping_usd,
            contingency_usd=contingency_usd,
            print_cost_jod=print_jod if print_cost is not None else None,
            total_usd=total_usd,
            total_jod=total_jod,
            currency="JOD",
            budget=request.context.budget,
            budget_status=budget_status,
            alternatives=alternatives,
            assumptions=[
                "Component prices are curated planning estimates in JOD, not live quotes.",
                "Shipping is excluded because the selected stores ship differently.",
                "A 5% contingency is added to the component subtotal.",
                "Print pricing uses the required PLA/PETG/ABS/Resin/TPU chart.",
            ],
        )


__all__ = ["CostEstimationAgent"]
