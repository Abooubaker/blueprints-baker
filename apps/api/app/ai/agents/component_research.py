"""Component Research — deterministic reference bill of materials.

The agent chooses from the curated electrical library rather than inventing
parts. Every selection carries its ``library_key`` so the wiring agent can bind
real pins to it. Supplier lookup and live pricing remain a later milestone; the
prices here are planning estimates and are labelled as such.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.ai.base import BaseAgent
from app.ai.contracts import (
    AgentRequest,
    BillOfMaterialsItem,
    ComponentCandidate,
    ComponentResearchInput,
    ComponentResearchOutput,
)
from app.electrical.library import (
    COMPONENT_LIBRARY,
    build_reference_bom,
)
from app.models.enums import AgentName


def _candidate_specs(profile_key: str) -> dict[str, Any]:
    profile = COMPONENT_LIBRARY[profile_key]
    return {
        "library_key": profile.key,
        "logic_voltage_v": profile.logic_voltage_v,
        "supply_min_v": profile.supply_min_v,
        "supply_max_v": profile.supply_max_v,
        "typical_current_ma": profile.current_ma_typical,
        "peak_current_ma": profile.current_ma_peak,
        "interfaces": list(profile.interfaces),
        "pins": [pin.name for pin in profile.pins],
        "electrical_notes": profile.notes,
    }


class ComponentResearchAgent(BaseAgent):
    """Builds a compatible, priced reference BOM from the curated library."""

    name = AgentName.COMPONENT_RESEARCH
    display_name = "Component Research"
    description = (
        "Selects a compatible bill of materials for the robot archetype, "
        "including controllers, drivers, motors, sensors, and power."
    )
    depends_on = (AgentName.PLANNER,)
    input_model = ComponentResearchInput
    output_model = ComponentResearchOutput
    status = "available"
    milestone = "M4"
    owner_area = "Robotics / Hardware Engineering"

    async def execute(self, request: AgentRequest) -> ComponentResearchOutput:
        specification = request.context.shared.specification
        if specification is None:
            raise ValueError("Component Research requires a robot specification.")

        parts, unresolved = build_reference_bom(
            robot_type=specification.robot_type,
            target_platform=specification.target_platform.value,
            difficulty=specification.difficulty.value,
            drive_type=specification.drive_type.value,
            budget_max_usd=request.context.budget.max_usd,
        )

        items: list[BillOfMaterialsItem] = []
        total = Decimal("0")
        for part in parts:
            profile = part.profile
            candidate = ComponentCandidate(
                name=profile.name,
                manufacturer=profile.manufacturer,
                model_number=profile.model_number,
                category=profile.category.value,
                specs=_candidate_specs(profile.key),
                price_usd=profile.price_usd,
                supplier="RoboCraft curated library",
                supplier_url=None,
                availability="in_stock",
                compatibility_notes=[profile.notes] if profile.notes else [],
                score=0.9,
            )
            total += profile.price_usd * part.quantity
            items.append(
                BillOfMaterialsItem(
                    role=part.role,
                    category=profile.category.value,
                    quantity=part.quantity,
                    required=True,
                    selection=candidate,
                    rationale=part.rationale,
                )
            )

        controller_name = next(
            (part.profile.name for part in parts if part.profile.is_controller),
            "none selected",
        )
        compatibility_notes = [
            f"Controller: {controller_name}",
            "All selected parts are in the curated electrical library, so pin-level "
            "wiring can be generated.",
            "Prices are planning estimates in USD, not live supplier quotes.",
        ]
        if specification.target_platform.value == "undecided":
            compatibility_notes.append(
                "Platform was chosen from the robot archetype; set a target platform "
                "to constrain it."
            )

        return ComponentResearchOutput(
            bill_of_materials=items,
            unresolved_requirements=unresolved,
            compatibility_notes=compatibility_notes,
            total_estimated_usd=total,
            sources=["RoboCraft curated component library v1.0"],
        )


__all__ = ["ComponentResearchAgent"]
