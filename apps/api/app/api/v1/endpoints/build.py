"""Guided-flow identification, preferences, and full build endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.contracts import BuildPreferences, PrintSettings, RobotIdentification
from app.ai.intent import identify_robot
from app.api.deps import OrchestratorDep, ProviderDep
from app.core.db import get_db
from app.schemas.build import BuildArtifactRead, IdentifyRequest
from app.services import build_service, preferences_service

router = APIRouter(tags=["guided build"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/intent/identify",
    response_model=RobotIdentification,
    summary="Identify the robot from a plain-language description",
)
async def identify(payload: IdentifyRequest) -> RobotIdentification:
    return identify_robot(payload.description, robot_type=payload.robot_type)


@router.get(
    "/projects/{project_id}/preferences",
    response_model=BuildPreferences,
    summary="Read the saved guided-flow answers",
)
async def get_preferences(project_id: uuid.UUID, session: SessionDep) -> BuildPreferences:
    return await preferences_service.get_preferences(session, project_id)


@router.put(
    "/projects/{project_id}/preferences",
    response_model=BuildPreferences,
    summary="Save the confirmed guided-flow answers",
)
async def save_preferences(
    project_id: uuid.UUID, payload: BuildPreferences, session: SessionDep
) -> BuildPreferences:
    return await preferences_service.save_preferences(session, project_id, payload)


@router.post(
    "/projects/{project_id}/build",
    response_model=BuildArtifactRead,
    status_code=status.HTTP_201_CREATED,
    summary="Run the full build pipeline",
    description=(
        "Runs planner, component research, electrical, programming, mechanical, and "
        "cost agents, then returns one artifact with sourced prices, schematic, "
        "code bundles, 3D/weight/price, and documentation."
    ),
)
async def generate_build(
    project_id: uuid.UUID,
    session: SessionDep,
    orchestrator: OrchestratorDep,
    provider: ProviderDep,
) -> BuildArtifactRead:
    return await build_service.generate_build(session, project_id, orchestrator, provider)


@router.get(
    "/projects/{project_id}/build",
    response_model=BuildArtifactRead,
    summary="Read the latest full build artifact",
)
async def get_build(project_id: uuid.UUID, session: SessionDep) -> BuildArtifactRead:
    return await build_service.get_build_artifact(session, project_id)


@router.put(
    "/projects/{project_id}/print-settings",
    response_model=BuildArtifactRead,
    summary="Change the print material, infill, or per-gram price",
    description=(
        "Saves the print controls and recomputes the 3D weight, material quote, "
        "and budget so the estimate matches a local price."
    ),
)
async def update_print_settings(
    project_id: uuid.UUID,
    payload: PrintSettings,
    session: SessionDep,
    orchestrator: OrchestratorDep,
    provider: ProviderDep,
) -> BuildArtifactRead:
    return await build_service.update_print_settings(
        session, project_id, payload, orchestrator, provider
    )


@router.get(
    "/projects/{project_id}/mechanical/stl",
    summary="Download the generated chassis STL",
    response_class=Response,
    responses={200: {"content": {"model/stl": {}, "text/plain": {}}}},
)
async def download_stl(project_id: uuid.UUID, session: SessionDep) -> Response:
    filename, content = await build_service.get_mechanical_stl(session, project_id)
    return Response(
        content=content,
        media_type="model/stl",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


__all__ = ["router"]
