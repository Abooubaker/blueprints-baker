"""Electrical plan generation, retrieval, and export endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import OrchestratorDep, ProviderDep
from app.core.db import get_db
from app.electrical.exporters import export_artifact
from app.schemas.electrical import ElectricalArtifactRead, ExportFormatName
from app.services import electrical_service

router = APIRouter(prefix="/projects/{project_id}/electrical", tags=["electrical"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "",
    response_model=ElectricalArtifactRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate the wiring plan",
    description=(
        "Runs the deterministic planner, component research, and electrical agents, "
        "then returns the validated plan, bill of materials, and export formats."
    ),
)
async def generate_electrical(
    project_id: uuid.UUID,
    session: SessionDep,
    orchestrator: OrchestratorDep,
    provider: ProviderDep,
) -> ElectricalArtifactRead:
    return await electrical_service.generate_artifact(session, project_id, orchestrator, provider)


@router.get(
    "",
    response_model=ElectricalArtifactRead,
    summary="Get the latest wiring plan",
)
async def get_electrical(project_id: uuid.UUID, session: SessionDep) -> ElectricalArtifactRead:
    return await electrical_service.get_artifact(session, project_id)


@router.get(
    "/export/{export_format}",
    summary="Download a wiring export",
    response_class=Response,
    responses={
        200: {
            "description": "The requested export file.",
            "content": {
                "text/csv": {},
                "text/plain": {},
                "image/svg+xml": {},
                "text/markdown": {},
                "application/json": {},
            },
        }
    },
)
async def export_electrical(
    project_id: uuid.UUID,
    export_format: ExportFormatName,
    session: SessionDep,
) -> Response:
    artifact = await electrical_service.get_artifact(session, project_id)
    exported = export_artifact(
        export_format,
        artifact.plan,
        artifact.bom,
        project_name=artifact.project_name,
    )
    return Response(
        content=exported.content,
        media_type=exported.spec.media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{exported.spec.filename}"',
            "X-Robocraft-Export": exported.spec.format,
        },
    )


__all__ = ["router"]
