"""Electrical Engineering Agent — deterministic wiring plan and validation."""

from __future__ import annotations

from app.ai.base import BaseAgent
from app.ai.contracts import (
    AgentRequest,
    ElectricalInput,
    ElectricalPlan,
)
from app.electrical.engine import build_electrical_plan
from app.models.enums import AgentName


class ElectricalEngineeringAgent(BaseAgent):
    """Produces a safe, explainable wiring plan.

    The engine maps component pins, allocates controller peripherals, builds the
    power tree, and runs deterministic voltage/logic/ground/current/pin checks.
    The LLM, when enabled later, may explain the result — it never decides
    whether a connection is safe.
    """

    name = AgentName.ELECTRICAL
    display_name = "Electrical Engineering"
    description = (
        "Creates pin maps, nets, power budgets, and wiring steps, then validates "
        "voltage, logic-level, grounding, current, and pin conflicts."
    )
    depends_on = (AgentName.PLANNER, AgentName.COMPONENT_RESEARCH)
    input_model = ElectricalInput
    output_model = ElectricalPlan
    status = "available"
    milestone = "M5"
    owner_area = "Robotics / Electrical Engineering"

    async def execute(self, request: AgentRequest) -> ElectricalPlan:
        specification = request.context.shared.specification
        research = request.context.shared.component_research
        if specification is None:
            raise ValueError("Electrical Engineering requires a robot specification.")
        if research is None:
            raise ValueError(
                "Electrical Engineering requires a component bill of materials. "
                "Run Component Research first."
            )
        return build_electrical_plan(specification, research)


__all__ = ["ElectricalEngineeringAgent"]
