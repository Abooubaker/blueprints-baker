"""Component Research Agent — requirement-to-parts resolution and sourcing."""

from __future__ import annotations

from app.ai.base import PlaceholderAgent
from app.ai.contracts import (
    ComponentResearchInput,
    ComponentResearchOutput,
)
from app.models.enums import AgentName


class ComponentResearchAgent(PlaceholderAgent):
    """Resolves specification slots into compatible, priced components.

    Responsibilities (M4):
    - derive a role-based bill of materials from the specification;
    - search the component catalog and approved suppliers;
    - compare specifications, availability, and price;
    - attach alternatives and explain trade-offs;
    - refuse selections that violate electrical or mechanical constraints.

    Downstream contract: ``ComponentResearchOutput`` feeds Electrical,
    Programming, Mechanical, and Cost agents. Supplier integrations must be
    isolated behind a service adapter so tests never hit the network.
    """

    name = AgentName.COMPONENT_RESEARCH
    display_name = "Component Research"
    description = (
        "Builds a bill of materials, finds compatible components, and compares "
        "suppliers, specifications, availability, and prices."
    )
    depends_on = (AgentName.PLANNER,)
    input_model = ComponentResearchInput
    output_model = ComponentResearchOutput
    milestone = "M4"
    owner_area = "AI Engineering / Integrations"
