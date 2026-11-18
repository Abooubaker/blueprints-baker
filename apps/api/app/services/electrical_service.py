"""Electrical artifact retrieval and generation use-cases."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.contracts import ComponentResearchOutput, ElectricalPlan
from app.ai.orchestrator import AgentOrchestrator
from app.ai.provider import LLMProvider
from app.core.errors import NotFoundError, ValidationError
from app.electrical.exporters import EXPORT_SPECS
from app.models.agent_run import AgentRun
from app.models.enums import AgentName, AgentResultStatus, AgentRunStatus
from app.schemas.agent import AgentRunRequest
from app.schemas.electrical import ElectricalArtifactRead, ExportFormatRead
from app.services import agent_service
from app.services.project_service import get_project


def _export_formats() -> list[ExportFormatRead]:
    return [
        ExportFormatRead(
            format=spec.format,
            label=spec.label,
            filename=spec.filename,
            media_type=spec.media_type,
            description=spec.description,
        )
        for spec in EXPORT_SPECS.values()
    ]


async def _latest_run(
    session: AsyncSession, project_id: uuid.UUID, agent: AgentName
) -> AgentRun | None:
    run = await session.scalar(
        select(AgentRun)
        .where(
            AgentRun.project_id == project_id,
            AgentRun.agent == agent,
            AgentRun.status == AgentRunStatus.SUCCEEDED,
        )
        .order_by(AgentRun.created_at.desc(), AgentRun.id.desc())
        .limit(1)
    )
    return run


async def get_artifact(session: AsyncSession, project_id: uuid.UUID) -> ElectricalArtifactRead:
    project = await get_project(session, project_id)
    run = await _latest_run(session, project_id, AgentName.ELECTRICAL)
    if run is None or run.output_payload is None:
        raise NotFoundError(
            "No electrical plan exists for this project yet. Generate the wiring plan first."
        )
    try:
        plan = ElectricalPlan.model_validate(run.output_payload)
    except Exception as exc:  # pragma: no cover - corrupted historical payload
        raise ValidationError(
            "The stored electrical plan no longer matches the current contract. "
            "Regenerate the wiring plan."
        ) from exc

    bom_run = await _latest_run(session, project_id, AgentName.COMPONENT_RESEARCH)
    bom: ComponentResearchOutput | None = None
    if bom_run is not None and bom_run.output_payload is not None:
        try:
            bom = ComponentResearchOutput.model_validate(bom_run.output_payload)
        except Exception:  # pragma: no cover - corrupted historical payload
            bom = None

    return ElectricalArtifactRead(
        project_id=project.id,
        project_name=project.name,
        agent_run_id=run.id,
        generated_at=run.completed_at or run.created_at,
        plan=plan,
        bom=bom,
        total_estimated_usd=(
            float(bom.total_estimated_usd)
            if bom is not None and bom.total_estimated_usd is not None
            else None
        ),
        export_formats=_export_formats(),
    )


async def generate_artifact(
    session: AsyncSession,
    project_id: uuid.UUID,
    orchestrator: AgentOrchestrator,
    provider: LLMProvider,
) -> ElectricalArtifactRead:
    """Run planner → component research → electrical and return the plan."""

    result = await agent_service.run_agents(
        session,
        project_id,
        AgentRunRequest(
            agents=[
                AgentName.PLANNER,
                AgentName.COMPONENT_RESEARCH,
                AgentName.ELECTRICAL,
            ]
        ),
        orchestrator,
        provider,
    )
    electrical = next(
        (run for run in result.runs if run.agent == AgentName.ELECTRICAL),
        None,
    )
    if electrical is not None and electrical.status != AgentRunStatus.SUCCEEDED:
        raise ValidationError(
            electrical.error_message
            or "The electrical agent could not produce a plan. "
            "Check the component bill of materials.",
            details={
                "agent": electrical.agent.value,
                "status": electrical.status.value,
                "errors": [run.error_message for run in result.runs if run.error_message],
            },
        )
    if result.status not in {AgentResultStatus.SUCCEEDED, AgentResultStatus.NOT_IMPLEMENTED}:
        raise ValidationError(
            "The electrical pipeline did not complete.",
            details={"errors": [run.error_message for run in result.runs if run.error_message]},
        )
    return await get_artifact(session, project_id)


__all__ = ["generate_artifact", "get_artifact"]
