"""Agent registry and deterministic pipeline orchestration.

The orchestrator is intentionally a plain, testable class. It does not know
about HTTP or the database; persistence is handled by the service layer.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

from app.ai.agents.component_research import ComponentResearchAgent
from app.ai.agents.cost import CostEstimationAgent
from app.ai.agents.electrical import ElectricalEngineeringAgent
from app.ai.agents.mechanical import MechanicalDesignAgent
from app.ai.agents.planner import RobotPlannerAgent
from app.ai.agents.programming import ProgrammingAgent
from app.ai.base import BaseAgent
from app.ai.contracts import (
    AgentDescriptor,
    AgentRequest,
    AgentResult,
    OrchestrationResult,
    ProjectContext,
    SharedProjectContext,
)
from app.ai.provider import LLMProvider
from app.models.enums import AgentName, AgentResultStatus

logger = logging.getLogger(__name__)

AGENT_CLASSES: tuple[type[BaseAgent], ...] = (
    RobotPlannerAgent,
    ComponentResearchAgent,
    ElectricalEngineeringAgent,
    ProgrammingAgent,
    MechanicalDesignAgent,
    CostEstimationAgent,
)

# Deterministic execution order; dependencies are declared on each agent and
# re-validated at runtime so an independent agent can be added safely.
PIPELINE_ORDER: tuple[AgentName, ...] = tuple(cls.name for cls in AGENT_CLASSES)

# Which shared-context slot an agent owns.
ARTIFACT_SLOTS: dict[AgentName, str] = {
    AgentName.PLANNER: "specification",
    AgentName.COMPONENT_RESEARCH: "component_research",
    AgentName.ELECTRICAL: "electrical",
    AgentName.PROGRAMMING: "programming",
    AgentName.MECHANICAL: "mechanical",
    AgentName.COST: "cost",
}


def build_agent_registry(provider: LLMProvider) -> dict[AgentName, BaseAgent]:
    """Instantiate every agent. Placeholder agents ignore the provider today."""
    del provider  # reserved for LLM-backed agents in M3
    return {cls.name: cls() for cls in AGENT_CLASSES}


def get_agent_descriptors(provider: LLMProvider) -> list[AgentDescriptor]:
    registry = build_agent_registry(provider)
    return [registry[name].descriptor() for name in PIPELINE_ORDER]


class OrchestrationError(ValueError):
    """Raised for invalid agent selection or dependency graphs."""


class AgentOrchestrator:
    """Runs a requested subset of agents in dependency order."""

    def __init__(self, agents: dict[AgentName, BaseAgent]) -> None:
        self._agents = agents
        self._validate_registry()

    def _validate_registry(self) -> None:
        missing = set(PIPELINE_ORDER) - set(self._agents)
        if missing:
            raise OrchestrationError(f"Missing agent implementations: {sorted(missing)}")
        for name, agent in self._agents.items():
            unknown = set(agent.depends_on) - set(self._agents)
            if unknown:
                raise OrchestrationError(f"{name} declares unknown dependencies: {sorted(unknown)}")

    def order(self, selection: Iterable[AgentName] | None = None) -> list[AgentName]:
        """Return requested agents plus transitive dependencies, in pipeline order."""
        requested = set(selection or PIPELINE_ORDER)
        unknown = requested - set(PIPELINE_ORDER)
        if unknown:
            raise OrchestrationError(f"Unknown agents requested: {sorted(unknown)}")

        resolved: set[AgentName] = set()

        def add(name: AgentName) -> None:
            if name in resolved:
                return
            for dependency in self._agents[name].depends_on:
                add(dependency)
            resolved.add(name)

        for name in PIPELINE_ORDER:
            if name in requested:
                add(name)
        return [name for name in PIPELINE_ORDER if name in resolved]

    async def run(
        self,
        context: ProjectContext,
        *,
        agents: Sequence[AgentName] | None = None,
        parameters: dict[str, object] | None = None,
    ) -> OrchestrationResult:
        """Execute agents sequentially and accumulate their artifacts.

        Failure policy: a failed/skipped/not-implemented agent blocks its
        dependents but does not abort independent branches. This makes partial
        progress visible and keeps one team's stub from hiding another's work.
        """
        order = self.order(agents)
        shared = context.shared.model_copy(deep=True)
        results: list[AgentResult] = []
        completed: dict[AgentName, AgentResultStatus] = {}

        for name in order:
            agent = self._agents[name]
            blocked = [
                dependency
                for dependency in agent.depends_on
                if completed.get(dependency) != AgentResultStatus.SUCCEEDED
            ]
            if blocked:
                results.append(
                    AgentResult(
                        agent=name,
                        status=AgentResultStatus.SKIPPED,
                        summary=f"{agent.display_name} skipped: dependency not satisfied.",
                        error=f"Blocked by: {', '.join(sorted(blocked))}",
                    )
                )
                completed[name] = AgentResultStatus.SKIPPED
                continue

            request = AgentRequest(
                context=context.model_copy(update={"shared": shared}),
                parameters=dict(parameters or {}),
            )
            result = await agent.run(request)
            results.append(result)
            completed[name] = result.status

            if result.status == AgentResultStatus.SUCCEEDED and result.output is not None:
                slot = ARTIFACT_SLOTS[name]
                try:
                    shared = self._apply_artifact(shared, slot, result.output)
                except Exception as exc:
                    logger.exception("Agent %s produced an invalid artifact", name)
                    result.status = AgentResultStatus.FAILED
                    result.error = f"Invalid output contract: {exc}"
                    completed[name] = AgentResultStatus.FAILED

        status = self._overall_status(results)
        return OrchestrationResult(
            project_id=context.project_id,
            status=status,
            results=results,
            context=shared,
        )

    @staticmethod
    def _apply_artifact(
        shared: SharedProjectContext, slot: str, payload: dict[str, object]
    ) -> SharedProjectContext:
        data = shared.model_dump()
        data[slot] = payload
        # Re-validating through the model is the contract enforcement point.
        return SharedProjectContext.model_validate(data)

    @staticmethod
    def _overall_status(results: Sequence[AgentResult]) -> AgentResultStatus:
        if not results:
            return AgentResultStatus.SKIPPED
        if all(result.status == AgentResultStatus.SUCCEEDED for result in results):
            return AgentResultStatus.SUCCEEDED
        if any(result.status == AgentResultStatus.FAILED for result in results):
            return AgentResultStatus.FAILED
        if any(result.status == AgentResultStatus.NOT_IMPLEMENTED for result in results):
            return AgentResultStatus.NOT_IMPLEMENTED
        if all(result.status == AgentResultStatus.SKIPPED for result in results):
            return AgentResultStatus.SKIPPED
        return AgentResultStatus.FAILED
