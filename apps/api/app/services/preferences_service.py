"""Persistence for the guided project flow.

The answers live in ``project_configurations.configuration`` as JSON. Saving a
confirmed answer also updates the project identity and its specification so the
planner, component research, programming, and mechanical agents all read the
same decisions.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.contracts import BuildPreferences
from app.models.enums import DriveType, RobotType, SpecificationStatus, TargetPlatform
from app.models.project import ProjectConfiguration, RobotProject, RobotSpecification
from app.services.project_service import get_project

_DRIVE_BY_ROBOT: dict[RobotType, DriveType] = {
    RobotType.LINE_FOLLOWER: DriveType.DIFFERENTIAL,
    RobotType.OBSTACLE_AVOIDER: DriveType.DIFFERENTIAL,
    RobotType.ROVER: DriveType.DIFFERENTIAL,
    RobotType.BALANCING_BOT: DriveType.DIFFERENTIAL,
    RobotType.ROBOT_ARM: DriveType.SERVO_ARM,
    RobotType.DRONE: DriveType.NONE,
    RobotType.CUSTOM: DriveType.NONE,
}


def infer_platform(controllers: list[str], notes: str = "") -> TargetPlatform:
    """Map free-text controller preferences to the planner's platform enum."""

    text = " ".join([*controllers, notes]).lower()
    if "esp32" in text:
        return TargetPlatform.ESP32
    if any(name in text for name in ("raspberry pi", "pico", "rp2040")):
        return TargetPlatform.RASPBERRY_PI
    if any(name in text for name in ("arduino", "uno", "nano", "mega", "teensy")):
        return TargetPlatform.ARDUINO
    if any(name in text for name in ("stm32", "arm", "custom", "other")):
        return TargetPlatform.OTHER
    return TargetPlatform.UNDECIDED


def _default_preferences(project: RobotProject) -> BuildPreferences:
    return BuildPreferences(
        description=project.description,
        robot_name=project.name,
        robot_type=project.robot_type,
        difficulty=project.difficulty,
        budget_max_usd=project.budget_max_usd,
        confirmed=False,
    )


async def get_preferences(session: AsyncSession, project_id: uuid.UUID) -> BuildPreferences:
    project = await get_project(session, project_id)
    configuration = await session.scalar(
        select(ProjectConfiguration).where(ProjectConfiguration.project_id == project_id)
    )
    if configuration is None:
        return _default_preferences(project)
    payload = configuration.configuration.get("preferences")
    if not isinstance(payload, dict):
        return _default_preferences(project)
    try:
        return BuildPreferences.model_validate(payload)
    except Exception:
        return _default_preferences(project)


async def save_preferences(
    session: AsyncSession, project_id: uuid.UUID, preferences: BuildPreferences
) -> BuildPreferences:
    project = await get_project(session, project_id)
    platform = infer_platform(preferences.controllers, preferences.controller_notes)

    project.description = preferences.description or project.description
    project.robot_type = preferences.robot_type
    project.difficulty = preferences.difficulty
    if preferences.robot_name.strip():
        project.name = preferences.robot_name.strip()
    if preferences.budget_max_usd is not None:
        project.budget_max_usd = preferences.budget_max_usd

    configuration = await session.scalar(
        select(ProjectConfiguration).where(ProjectConfiguration.project_id == project_id)
    )
    if configuration is None:
        configuration = ProjectConfiguration(
            project_id=project.id,
            name="Guided build",
            version=1,
            is_active=True,
            configuration={},
        )
        session.add(configuration)
    configuration.configuration = {
        "version": 1,
        "preferences": preferences.model_dump(mode="json"),
    }

    specification = project.specification
    if specification is None:
        specification = RobotSpecification(project_id=project.id)
        session.add(specification)
        project.specification = specification
    specification.summary = preferences.description or project.description or project.name
    specification.use_case = preferences.description or project.description
    specification.target_platform = platform
    specification.drive_type = _DRIVE_BY_ROBOT.get(preferences.robot_type, DriveType.NONE)
    specification.requirements = list(dict.fromkeys(preferences_requirements(preferences)))
    specification.constraints = (
        [f"Total component cost must stay below ${preferences.budget_max_usd:.2f}."]
        if preferences.budget_max_usd is not None
        else []
    )
    specification.status = SpecificationStatus.GENERATED
    specification.version = (specification.version or 0) + 1

    await session.commit()
    await session.refresh(project)
    return preferences


def preferences_requirements(preferences: BuildPreferences) -> tuple[str, ...]:
    """Requirements implied by the confirmed robot archetype."""

    mapping: dict[RobotType, tuple[str, ...]] = {
        RobotType.LINE_FOLLOWER: (
            "Follow a marked line without losing the track",
            "Stop safely when the line is lost",
        ),
        RobotType.OBSTACLE_AVOIDER: (
            "Detect obstacles before contact",
            "Steer around an obstacle and resume travel",
        ),
        RobotType.ROVER: (
            "Drive over small indoor or patio obstacles",
            "Maintain a stable control link",
        ),
        RobotType.ROBOT_ARM: (
            "Reach a target position repeatably",
            "Hold and release a small payload",
        ),
        RobotType.BALANCING_BOT: (
            "Remain upright with closed-loop control",
            "Recover from a small push",
        ),
        RobotType.DRONE: (
            "Maintain stable flight in a supervised area",
            "Land safely on low battery",
        ),
        RobotType.CUSTOM: (
            "Complete the described task under supervision",
            "Pass all electrical checks before power-on",
        ),
    }
    return mapping[preferences.robot_type]


def preferences_parameters(preferences: BuildPreferences) -> dict[str, Any]:
    """Translate saved answers into agent request parameters."""

    return {
        "preferred_suppliers": [store.value for store in preferences.shops],
        "languages": [language.value for language in preferences.languages],
        "controllers": preferences.controllers,
        "controller_notes": preferences.controller_notes,
        "custom_pcb": preferences.custom_pcb,
        "skill_level": preferences.difficulty.value,
    }


__all__ = [
    "get_preferences",
    "infer_platform",
    "preferences_parameters",
    "preferences_requirements",
    "save_preferences",
]
