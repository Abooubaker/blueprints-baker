"""Cost Estimation Agent — budget roll-up and alternatives."""

from __future__ import annotations

from app.ai.base import PlaceholderAgent
from app.ai.contracts import CostEstimate, CostInput
from app.models.enums import AgentName


class CostEstimationAgent(PlaceholderAgent):
    """Calculates project cost and proposes budget scenarios.

    Responsibilities (M8):
    - roll up the bill of materials with quantities, shipping, and contingency;
    - state every assumption and mark estimated prices;
    - compare alternative components and quantify trade-offs;
    - classify the result as under/within/over budget.

    Downstream contract: ``CostEstimate`` is terminal. Currency conversion and
    live pricing are integration concerns and must be cached, timestamped, and
    clearly labelled as estimates.
    """

    name = AgentName.COST
    display_name = "Cost Estimation"
    description = (
        "Calculates total project cost, breaks it down by component, and "
        "compares budget alternatives."
    )
    depends_on = (AgentName.PLANNER, AgentName.COMPONENT_RESEARCH)
    input_model = CostInput
    output_model = CostEstimate
    milestone = "M8"
    owner_area = "AI Engineering / Integrations"
