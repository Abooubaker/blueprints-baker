"""Robot project, specification, and agent-run endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import OrchestratorDep, PaginationDep, ProviderDep
from app.core.db import get_db
from app.models.enums import ProjectStatus, RobotType
from app.schemas.agent import AgentRunRead, AgentRunRequest, OrchestrationRead
from app.schemas.common import Page, PageMeta
from app.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
    SpecificationRead,
    SpecificationUpdate,
)
from app.services import agent_service, project_service

router = APIRouter(prefix="/projects", tags=["projects"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=Page[ProjectSummary], summary="List robot projects")
async def list_projects(
    session: SessionDep,
    pagination: PaginationDep,
    status_filter: Annotated[ProjectStatus | None, Query(alias="status")] = None,
    robot_type: Annotated[RobotType | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
) -> Page[ProjectSummary]:
    projects, total = await project_service.list_projects(
        session,
        limit=pagination.limit,
        offset=pagination.offset,
        status=status_filter,
        robot_type=robot_type,
        search=search,
    )
    return Page[ProjectSummary](
        items=[ProjectSummary.model_validate(project) for project in projects],
        meta=PageMeta(total=total, limit=pagination.limit, offset=pagination.offset),
    )


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a robot project",
)
async def create_project(payload: ProjectCreate, session: SessionDep) -> ProjectRead:
    project = await project_service.create_project(session, payload)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead, summary="Get a robot project")
async def get_project(project_id: uuid.UUID, session: SessionDep) -> ProjectRead:
    project = await project_service.get_project(session, project_id)
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead, summary="Update a robot project")
async def update_project(
    project_id: uuid.UUID, payload: ProjectUpdate, session: SessionDep
) -> ProjectRead:
    project = await project_service.update_project(session, project_id, payload)
    return ProjectRead.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a robot project",
)
async def delete_project(project_id: uuid.UUID, session: SessionDep) -> None:
    await project_service.delete_project(session, project_id)


@router.get(
    "/{project_id}/specification",
    response_model=SpecificationRead,
    summary="Get the robot specification",
)
async def get_specification(project_id: uuid.UUID, session: SessionDep) -> SpecificationRead:
    specification = await project_service.get_specification(session, project_id)
    return SpecificationRead.model_validate(specification)


@router.put(
    "/{project_id}/specification",
    response_model=SpecificationRead,
    summary="Update the robot specification (manual edit)",
)
async def update_specification(
    project_id: uuid.UUID, payload: SpecificationUpdate, session: SessionDep
) -> SpecificationRead:
    specification = await project_service.update_specification(session, project_id, payload)
    return SpecificationRead.model_validate(specification)


@router.post(
    "/{project_id}/agent-runs",
    response_model=OrchestrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Run AI agents for a project",
    description=(
        "Runs the requested agents in dependency order and records every execution. "
        "In the current foundation release specialized agents return "
        "`not_implemented`; this endpoint proves the orchestration contract."
    ),
)
async def run_agents(
    project_id: uuid.UUID,
    payload: AgentRunRequest,
    session: SessionDep,
    orchestrator: OrchestratorDep,
    provider: ProviderDep,
) -> OrchestrationRead:
    return await agent_service.run_agents(session, project_id, payload, orchestrator, provider)


@router.get(
    "/{project_id}/agent-runs",
    response_model=Page[AgentRunRead],
    summary="List agent execution records",
)
async def list_agent_runs(
    project_id: uuid.UUID, session: SessionDep, pagination: PaginationDep
) -> Page[AgentRunRead]:
    runs, total = await agent_service.list_agent_runs(
        session, project_id, limit=pagination.limit, offset=pagination.offset
    )
    return Page[AgentRunRead](
        items=[AgentRunRead.model_validate(run) for run in runs],
        meta=PageMeta(total=total, limit=pagination.limit, offset=pagination.offset),
    )
