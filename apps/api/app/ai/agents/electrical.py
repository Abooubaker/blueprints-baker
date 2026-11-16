"""Electrical Engineering Agent — wiring plan and electrical validation."""

from __future__ import annotations

from app.ai.base import PlaceholderAgent
from app.ai.contracts import ElectricalInput, ElectricalPlan
from app.models.enums import AgentName


class ElectricalEngineeringAgent(PlaceholderAgent):
    """Produces a safe, explainable wiring plan.

    Responsibilities (M5):
    - map component pins and communication buses;
    - build a power budget and check voltage/current compatibility;
    - detect missing level shifting, shared grounds, or driver requirements;
    - emit ordered wiring steps and safety warnings.

    Downstream contract: ``ElectricalPlan`` feeds the Programming Agent. Safety
    rules must be deterministic code, not only LLM prose, and must be unit
    tested against known-good and known-bad fixtures.
    """

    name = AgentName.ELECTRICAL
    display_name = "Electrical Engineering"
    description = (
        "Creates wiring plans, pin maps, and power budgets, then validates "
        "electrical compatibility and safety."
    )
    depends_on = (AgentName.PLANNER, AgentName.COMPONENT_RESEARCH)
    input_model = ElectricalInput
    output_model = ElectricalPlan
    milestone = "M5"
    owner_area = "Robotics / Electrical Engineering"
