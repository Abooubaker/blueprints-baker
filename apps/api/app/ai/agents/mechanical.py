"""Mechanical Design Agent — structure, layout, and assembly planning."""

from __future__ import annotations

from app.ai.base import PlaceholderAgent
from app.ai.contracts import MechanicalInput, MechanicalOutput
from app.models.enums import AgentName


class MechanicalDesignAgent(PlaceholderAgent):
    """Turns electronics choices into a buildable mechanical plan.

    Responsibilities (M7):
    - propose chassis, mounting, wheel, and actuator arrangements;
    - produce ordered assembly steps with tools and safety notes;
    - check mass, clearance, and fastener compatibility;
    - reference drawings/models without embedding CAD payloads in JSON.

    Downstream contract: ``MechanicalOutput`` feeds assembly docs and, later,
    parametric CAD generation. 3D model generation is explicitly out of scope
    for M7 and belongs to a future milestone.
    """

    name = AgentName.MECHANICAL
    display_name = "Mechanical Design"
    description = (
        "Plans the chassis and structure, recommends mechanical parts, and "
        "produces assembly instructions."
    )
    depends_on = (AgentName.PLANNER, AgentName.COMPONENT_RESEARCH)
    input_model = MechanicalInput
    output_model = MechanicalOutput
    milestone = "M7"
    owner_area = "Mechanical Design"
