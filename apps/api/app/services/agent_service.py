"""Agent orchestration use-cases and audit persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.contracts import AgentResult, ProjectContext, RobotSpecificationDraft
from app.ai.orchestrator import AgentOrchestrator, OrchestrationError
from app.ai.provider import LLMProvider
from app.core.errors import ValidationError
from app.models.agent_run import AgentRun
from app.models.enums import AgentName, AgentResultStatus, AgentRunStatus
from app.models.project import RobotProject
from app.schemas.agent import AgentRunRequest, OrchestrationRead
from app.services import preferences_service
from app.services.project_service import get_project

_RUN_STATUS_MAP: dict[AgentResultStatus, AgentRunStatus] = {
    AgentResultStatus.SUCCEEDED: AgentRunStatus.SUCCEEDED,
    AgentResultStatus.FAILED: AgentRunStatus.FAILED,
    AgentResultStatus.SKIPPED: AgentRunStatus.SKIPPED,
    AgentResultStatus.NOT_IMPLEMENTED: AgentRunStatus.NOT_IMPLEMENTED,
}


def build_project_context(project: RobotProject) -> ProjectContext:
    """Translate the persistence model into the agent contract."""
    specification = None
    if project.specification is not None:
        spec = project.specification
        specification = RobotSpecificationDraft(
            summary=spec.summary or project.description or project.name,
            use_case=spec.use_case,
            robot_type=project.robot_type,
            difficulty=project.difficulty,
            target_platform=spec.target_platform,
            drive_type=spec.drive_type,
            environment=spec.environment,
            power_source=spec.power_source,
            dimensions=spec.dimensions,
            payload_capacity_kg=spec.payload_capacity_kg,
            requirements=spec.requirements,
            constraints=spec.constraints,
        )

    budget = {}
    if project.budget_min_usd is not None:
        budget["min_usd"] = project.budget_min_usd
    if project.budget_max_usd is not None:
        budget["max_usd"] = project.budget_max_usd

    return ProjectContext(
        project_id=project.id,
        project_name=project.name,
        robot_type=project.robot_type,
        description=project.description,
        budget=budget,
        shared={"specification": specification} if specification else {},
    )


def _persist_run(
    project_id: uuid.UUID,
    result: AgentResult,
    *,
    provider: str,
    model: str,
    parameters: dict[str, object],
) -> AgentRun:
    return AgentRun(
        project_id=project_id,
        agent=result.agent,
        status=_RUN_STATUS_MAP[result.status],
        provider=provider,
        model=model,
        summary=result.summary[:500],
        input_payload={"parameters": parameters},
        output_payload=result.output,
        error_message=result.error,
        prompt_tokens=result.usage.prompt_tokens,
        completion_tokens=result.usage.completion_tokens,
        latency_ms=result.usage.latency_ms,
        started_at=result.started_at,
        completed_at=result.completed_at,
    )


async def run_agents(
    session: AsyncSession,
    project_id: uuid.UUID,
    payload: AgentRunRequest,
    orchestrator: AgentOrchestrator,
    provider: LLMProvider,
) -> OrchestrationRead:
    project = await get_project(session, project_id)
    context = build_project_context(project)
    preferences = await preferences_service.get_preferences(session, project_id)
    parameters: dict[str, object] = {
        **preferences_service.preferences_parameters(preferences),
        **payload.parameters,
    }

    try:
        orchestration = await orchestrator.run(
            context, agents=payload.agents, parameters=parameters
        )
    except OrchestrationError as exc:
        raise ValidationError(str(exc)) from exc

    runs = [
        _persist_run(
            project.id,
            result,
            provider=provider.name,
            model=provider.default_model,
            parameters=parameters,
        )
        for result in orchestration.results
    ]
    session.add_all(runs)
    await session.commit()
    for run in runs:
        await session.refresh(run)

    return OrchestrationRead(
        project_id=project.id,
        status=orchestration.status,
        runs=runs,
        shared_context=orchestration.context,
        provider=provider.name,
        model=provider.default_model,
    )


async def list_agent_runs(
    session: AsyncSession, project_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> tuple[list[AgentRun], int]:
    await get_project(session, project_id)
    total = await session.scalar(
        select(func.count()).select_from(AgentRun).where(AgentRun.project_id == project_id)
    )
    rows = await session.scalars(
        select(AgentRun)
        .where(AgentRun.project_id == project_id)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(rows), int(total or 0)


async def latest_agent_runs_by_agent(
    session: AsyncSession, project_id: uuid.UUID
) -> dict[AgentName, AgentRun]:
    """Return the newest run per agent; used by the project overview API."""
    rows = await session.scalars(
        select(AgentRun)
        .where(AgentRun.project_id == project_id)
        .order_by(AgentRun.created_at.desc())
    )
    latest: dict[AgentName, AgentRun] = {}
    for run in rows:
        latest.setdefault(run.agent, run)
    return latest


__all__ = [
    "build_project_context",
    "latest_agent_runs_by_agent",
    "list_agent_runs",
    "run_agents",
]
