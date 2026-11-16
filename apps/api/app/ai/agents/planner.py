"""Robot Planner — the central orchestrator-facing requirements analyst."""

from __future__ import annotations

from app.ai.base import PlaceholderAgent
from app.ai.contracts import PlannerInput, RobotSpecificationDraft
from app.models.enums import AgentName


class RobotPlannerAgent(PlaceholderAgent):
    """Turns free-form intent into a reviewable robot specification.

    Responsibilities (M3):
    - classify the robot type, platform, drive system, and environment;
    - extract functional and non-functional requirements;
    - surface ambiguities as ``open_questions`` instead of guessing;
    - produce a specification the user can approve before spending money.

    Downstream contract: ``RobotSpecificationDraft`` becomes
    ``context.shared.specification`` and is a hard dependency for every other
    agent. This agent must never select concrete products.
    """

    name = AgentName.PLANNER
    display_name = "Robot Planner"
    description = (
        "Converts the user's goal into a structured, buildable robot specification "
        "and coordinates the specialized agents."
    )
    depends_on = ()
    input_model = PlannerInput
    output_model = RobotSpecificationDraft
    milestone = "M3"
    owner_area = "AI Engineering"
    requires_specification = False
