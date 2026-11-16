"""Robot project aggregate: project, specification, configuration, selections."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from app.models.enums import (
    Difficulty,
    DriveType,
    ProjectStatus,
    RobotType,
    SpecificationStatus,
    TargetPlatform,
)

if TYPE_CHECKING:
    from app.models.agent_run import AgentRun
    from app.models.component import Component
    from app.models.user import User


class RobotProject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "robot_projects"
    __table_args__ = (
        CheckConstraint(
            "budget_max_usd IS NULL OR budget_min_usd IS NULL OR budget_max_usd >= budget_min_usd",
            name="budget_range_valid",
        ),
        Index("ix_robot_projects_status_created", "status", "created_at"),
    )

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    robot_type: Mapped[RobotType] = mapped_column(
        enum_type(RobotType, "robot_type"), default=RobotType.CUSTOM, nullable=False
    )
    status: Mapped[ProjectStatus] = mapped_column(
        enum_type(ProjectStatus, "project_status"), default=ProjectStatus.DRAFT, nullable=False
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        enum_type(Difficulty, "difficulty"), default=Difficulty.BEGINNER, nullable=False
    )
    budget_min_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    owner: Mapped[User | None] = relationship(back_populates="projects")
    specification: Mapped[RobotSpecification | None] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    configuration: Mapped[ProjectConfiguration | None] = relationship(
        back_populates="project", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    component_selections: Mapped[list[ProjectComponent]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    agent_runs: Mapped[list[AgentRun]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )


class RobotSpecification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Structured interpretation of the user's intent, produced by the Planner."""

    __tablename__ = "robot_specifications"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("robot_projects.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    use_case: Mapped[str] = mapped_column(Text, default="", nullable=False)
    environment: Mapped[str] = mapped_column(String(120), default="indoor", nullable=False)
    target_platform: Mapped[TargetPlatform] = mapped_column(
        enum_type(TargetPlatform, "target_platform"),
        default=TargetPlatform.UNDECIDED,
        nullable=False,
    )
    drive_type: Mapped[DriveType] = mapped_column(
        enum_type(DriveType, "drive_type"), default=DriveType.NONE, nullable=False
    )
    power_source: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    payload_capacity_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    dimensions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    requirements: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    constraints: Mapped[list[Any]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[SpecificationStatus] = mapped_column(
        enum_type(SpecificationStatus, "specification_status"),
        default=SpecificationStatus.DRAFT,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    project: Mapped[RobotProject] = relationship(back_populates="specification")


class ProjectConfiguration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Resolved hardware/software configuration for a project."""

    __tablename__ = "project_configurations"
    __table_args__ = (UniqueConstraint("project_id", name="uq_project_configurations_project_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("robot_projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), default="Default", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    project: Mapped[RobotProject] = relationship(back_populates="configuration")


class ProjectComponent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A component selected for a project, with quantity and price snapshot."""

    __tablename__ = "project_components"
    __table_args__ = (
        UniqueConstraint("project_id", "component_id", "role", name="uq_project_component_role"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("robot_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("components.id", ondelete="RESTRICT"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    project: Mapped[RobotProject] = relationship(back_populates="component_selections")
    component: Mapped[Component] = relationship(lazy="selectin")
