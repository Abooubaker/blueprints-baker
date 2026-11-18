"""Guided-flow and full build artifact schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.ai.contracts import (
    BuildPreferences,
    ComponentResearchOutput,
    CostEstimate,
    ElectricalPlan,
    MechanicalOutput,
    ProgrammingOutput,
    ProjectDocumentation,
    RobotIdentification,
    RobotSpecificationDraft,
)
from app.models.enums import RobotType
from app.schemas.common import APIModel


class IdentifyRequest(APIModel):
    description: str = Field(min_length=1, max_length=5000)
    robot_type: RobotType | None = None


class BuildArtifactRead(APIModel):
    project_id: UUID
    project_name: str
    status: Literal["ready", "partial", "empty"]
    generated_at: datetime
    preferences: BuildPreferences
    identification: RobotIdentification | None = None
    specification: RobotSpecificationDraft | None = None
    research: ComponentResearchOutput | None = None
    electrical: ElectricalPlan | None = None
    programming: ProgrammingOutput | None = None
    mechanical: MechanicalOutput | None = None
    cost: CostEstimate | None = None
    documentation: ProjectDocumentation = Field(default_factory=ProjectDocumentation)
    missing: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


__all__ = ["BuildArtifactRead", "IdentifyRequest"]
