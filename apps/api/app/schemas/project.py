"""Request/response schemas for robot projects and specifications."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.models.enums import (
    Difficulty,
    DriveType,
    ProjectStatus,
    RobotType,
    SpecificationStatus,
    TargetPlatform,
)
from app.schemas.common import APIModel


class SpecificationBase(APIModel):
    summary: str = Field(default="", max_length=5000)
    use_case: str = Field(default="", max_length=2000)
    environment: str = Field(default="indoor", max_length=120)
    target_platform: TargetPlatform = TargetPlatform.UNDECIDED
    drive_type: DriveType = DriveType.NONE
    power_source: str = Field(default="", max_length=120)
    payload_capacity_kg: float | None = Field(default=None, ge=0, le=10000)
    dimensions: dict[str, Any] = Field(default_factory=dict)
    requirements: list[str] = Field(default_factory=list, max_length=100)
    constraints: list[str] = Field(default_factory=list, max_length=100)


class SpecificationUpdate(SpecificationBase):
    status: SpecificationStatus | None = None


class SpecificationRead(SpecificationBase):
    id: UUID
    project_id: UUID
    status: SpecificationStatus
    version: int
    created_at: datetime
    updated_at: datetime


class ProjectCreate(APIModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=5000)
    robot_type: RobotType = RobotType.CUSTOM
    difficulty: Difficulty = Difficulty.BEGINNER
    target_platform: TargetPlatform = TargetPlatform.UNDECIDED
    budget_min_usd: float | None = Field(default=None, ge=0, le=1_000_000)
    budget_max_usd: float | None = Field(default=None, ge=0, le=1_000_000)
    requirements: list[str] = Field(default_factory=list, max_length=100)
    constraints: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("name", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_budget_range(self) -> ProjectCreate:
        if (
            self.budget_min_usd is not None
            and self.budget_max_usd is not None
            and self.budget_max_usd < self.budget_min_usd
        ):
            raise ValueError("budget_max_usd must be greater than or equal to budget_min_usd")
        return self


class ProjectUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus | None = None
    difficulty: Difficulty | None = None
    budget_min_usd: float | None = Field(default=None, ge=0, le=1_000_000)
    budget_max_usd: float | None = Field(default=None, ge=0, le=1_000_000)

    @field_validator("name", "description")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class ProjectRead(APIModel):
    id: UUID
    owner_id: UUID | None
    name: str
    slug: str
    description: str
    robot_type: RobotType
    status: ProjectStatus
    difficulty: Difficulty
    budget_min_usd: float | None
    budget_max_usd: float | None
    specification: SpecificationRead | None = None
    created_at: datetime
    updated_at: datetime


class ProjectSummary(APIModel):
    """Lightweight representation for dashboard lists."""

    id: UUID
    name: str
    slug: str
    description: str
    robot_type: RobotType
    status: ProjectStatus
    difficulty: Difficulty
    budget_max_usd: float | None
    created_at: datetime
    updated_at: datetime
