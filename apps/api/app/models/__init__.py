"""ORM model registry — import every model so Alembic autogenerate sees it."""

from app.models.agent_run import AgentRun
from app.models.base import Base
from app.models.component import Component
from app.models.enums import (
    AgentName,
    AgentResultStatus,
    AgentRunStatus,
    ComponentAvailability,
    ComponentCategory,
    Difficulty,
    DriveType,
    ProjectStatus,
    RobotType,
    SpecificationStatus,
    TargetPlatform,
)
from app.models.project import (
    ProjectComponent,
    ProjectConfiguration,
    RobotProject,
    RobotSpecification,
)
from app.models.user import User

__all__ = [
    "AgentName",
    "AgentResultStatus",
    "AgentRun",
    "AgentRunStatus",
    "Base",
    "Component",
    "ComponentAvailability",
    "ComponentCategory",
    "Difficulty",
    "DriveType",
    "ProjectComponent",
    "ProjectConfiguration",
    "ProjectStatus",
    "RobotProject",
    "RobotSpecification",
    "RobotType",
    "SpecificationStatus",
    "TargetPlatform",
    "User",
]
