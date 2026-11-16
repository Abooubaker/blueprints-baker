"""Health and readiness endpoints (unversioned, used by infrastructure)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.schemas.common import APIModel

router = APIRouter(tags=["health"])


class HealthResponse(APIModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(HealthResponse):
    checks: dict[str, Any]


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get("/health/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def readiness(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    await session.execute(text("SELECT 1"))
    return ReadinessResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        checks={"database": {"status": "ok"}},
    )
