"""Build use-cases: run the full guided pipeline and assemble one artifact."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.contracts import (
    BuildPreferences,
    ComponentResearchOutput,
    CostEstimate,
    ElectricalPlan,
    MechanicalOutput,
    ProgrammingOutput,
    RobotIdentification,
    RobotSpecificationDraft,
)
from app.ai.documentation import build_documentation
from app.ai.orchestrator import AgentOrchestrator
from app.ai.provider import LLMProvider
from app.core.errors import ValidationError
from app.models.agent_run import AgentRun
from app.models.enums import AgentName, AgentRunStatus, TargetPlatform
from app.schemas.agent import AgentRunRequest
from app.schemas.build import BuildArtifactRead
from app.services import agent_service, preferences_service
from app.services.project_service import get_project

_MODELS: dict[AgentName, type[BaseModel]] = {
    AgentName.COMPONENT_RESEARCH: ComponentResearchOutput,
    AgentName.ELECTRICAL: ElectricalPlan,
    AgentName.PROGRAMMING: ProgrammingOutput,
    AgentName.MECHANICAL: MechanicalOutput,
    AgentName.COST: CostEstimate,
}

_LABELS: dict[AgentName, str] = {
    AgentName.COMPONENT_RESEARCH: "component research",
    AgentName.ELECTRICAL: "electrical plan",
    AgentName.PROGRAMMING: "code bundles",
    AgentName.MECHANICAL: "3D model",
    AgentName.COST: "cost estimate",
}


def _parse[T: BaseModel](model: type[T], run: AgentRun | None) -> T | None:
    if run is None or run.output_payload is None:
        return None
    try:
        return model.model_validate(run.output_payload)
    except Exception:
        return None


def _identification(
    preferences: BuildPreferences, specification: RobotSpecificationDraft | None
) -> RobotIdentification | None:
    if not preferences.confirmed:
        return None
    return RobotIdentification(
        proposed_name=preferences.robot_name or "Robot project",
        robot_type=preferences.robot_type,
        confidence=preferences.identification_confidence or 0.8,
        rationale=preferences.identification_rationale or "Confirmed in the guided flow.",
        suggested_platform=(
            specification.target_platform if specification is not None else TargetPlatform.UNDECIDED
        ),
        suggested_difficulty=preferences.difficulty,
        key_requirements=list(preferences_service.preferences_requirements(preferences)),
        needs_confirmation=False,
    )


async def get_build_artifact(session: AsyncSession, project_id: uuid.UUID) -> BuildArtifactRead:
    project = await get_project(session, project_id)
    preferences = await preferences_service.get_preferences(session, project_id)
    latest = await agent_service.latest_agent_runs_by_agent(session, project_id)

    parsed: dict[AgentName, BaseModel | None] = {}
    missing: list[str] = []
    for agent, model in _MODELS.items():
        run = latest.get(agent)
        value = _parse(model, run)
        parsed[agent] = value
        if value is None:
            missing.append(_LABELS[agent])

    context = agent_service.build_project_context(project)
    specification = context.shared.specification
    research = parsed[AgentName.COMPONENT_RESEARCH]
    electrical = parsed[AgentName.ELECTRICAL]
    programming = parsed[AgentName.PROGRAMMING]
    mechanical = parsed[AgentName.MECHANICAL]
    cost = parsed[AgentName.COST]

    documentation = build_documentation(
        project_name=project.name,
        description=project.description,
        preferences=preferences,
        identification=_identification(preferences, specification),
        specification=specification,
        research=research if isinstance(research, ComponentResearchOutput) else None,
        electrical=electrical if isinstance(electrical, ElectricalPlan) else None,
        programming=programming,
        mechanical=mechanical if isinstance(mechanical, MechanicalOutput) else None,
        cost=cost if isinstance(cost, CostEstimate) else None,
    )

    present = sum(1 for value in parsed.values() if value is not None)
    status = "ready" if present == len(_MODELS) else "partial" if present else "empty"
    completed = [
        run.completed_at or run.created_at
        for run in latest.values()
        if run.status == AgentRunStatus.SUCCEEDED
    ]
    generated_at = max(completed) if completed else datetime.now(UTC)
    warnings = [f"{label.title()} is not available yet." for label in missing]

    return BuildArtifactRead(
        project_id=project.id,
        project_name=project.name,
        status=status,
        generated_at=generated_at,
        preferences=preferences,
        identification=_identification(preferences, specification),
        specification=specification,
        research=research if isinstance(research, ComponentResearchOutput) else None,
        electrical=electrical if isinstance(electrical, ElectricalPlan) else None,
        programming=programming if isinstance(programming, ProgrammingOutput) else None,
        mechanical=mechanical if isinstance(mechanical, MechanicalOutput) else None,
        cost=cost if isinstance(cost, CostEstimate) else None,
        documentation=documentation,
        missing=missing,
        warnings=warnings,
    )


async def generate_build(
    session: AsyncSession,
    project_id: uuid.UUID,
    orchestrator: AgentOrchestrator,
    provider: LLMProvider,
) -> BuildArtifactRead:
    """Run the full pipeline, then assemble the artifact for the UI."""

    preferences = await preferences_service.get_preferences(session, project_id)
    if not preferences.confirmed:
        raise ValidationError("Confirm the guided flow before generating a build.")

    result = await agent_service.run_agents(
        session,
        project_id,
        AgentRunRequest(parameters=preferences_service.preferences_parameters(preferences)),
        orchestrator,
        provider,
    )
    failed = [run for run in result.runs if run.status == AgentRunStatus.FAILED]
    if failed:
        raise ValidationError(
            "The build pipeline could not finish: "
            + "; ".join(run.error_message or run.agent.value for run in failed),
            details={"errors": [run.error_message for run in failed]},
        )
    return await get_build_artifact(session, project_id)


async def get_mechanical_stl(session: AsyncSession, project_id: uuid.UUID) -> tuple[str, str]:
    artifact = await get_build_artifact(session, project_id)
    if artifact.mechanical is None or not artifact.mechanical.stl_ascii:
        raise ValidationError("No 3D model exists for this project yet. Generate the build first.")
    return artifact.mechanical.stl_filename, artifact.mechanical.stl_ascii


__all__ = ["generate_build", "get_build_artifact", "get_mechanical_stl"]
