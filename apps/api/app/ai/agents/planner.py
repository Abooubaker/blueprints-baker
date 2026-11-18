"""Robot Planner — turns a project brief into a structured specification.

The planner is deterministic in this milestone. It normalises the user's brief
and fills only the fields needed by downstream engineering agents; it never
invents a component or a pin. An LLM-backed implementation can replace
``execute`` later without changing the contract.
"""

from __future__ import annotations

from app.ai.base import BaseAgent
from app.ai.contracts import (
    AgentRequest,
    Dimensions,
    PlannerInput,
    RobotSpecificationDraft,
)
from app.models.enums import (
    AgentName,
    Difficulty,
    DriveType,
    RobotType,
    TargetPlatform,
)

_DRIVE_BY_ROBOT: dict[RobotType, DriveType] = {
    RobotType.LINE_FOLLOWER: DriveType.DIFFERENTIAL,
    RobotType.OBSTACLE_AVOIDER: DriveType.DIFFERENTIAL,
    RobotType.ROVER: DriveType.DIFFERENTIAL,
    RobotType.BALANCING_BOT: DriveType.DIFFERENTIAL,
    RobotType.ROBOT_ARM: DriveType.SERVO_ARM,
    RobotType.DRONE: DriveType.NONE,
    RobotType.CUSTOM: DriveType.NONE,
}

_REQUIREMENTS_BY_ROBOT: dict[RobotType, tuple[str, ...]] = {
    RobotType.LINE_FOLLOWER: (
        "Follow a high-contrast line without leaving the track",
        "Stop safely when the path is lost",
    ),
    RobotType.OBSTACLE_AVOIDER: (
        "Detect obstacles before contact",
        "Turn or stop without losing control",
    ),
    RobotType.ROVER: (
        "Drive over small indoor obstacles",
        "Maintain a stable control link",
    ),
    RobotType.ROBOT_ARM: (
        "Reach the target position repeatably",
        "Hold a payload without overheating a servo",
    ),
    RobotType.BALANCING_BOT: (
        "Stay upright with a closed-loop controller",
        "Recover safely from a small push",
    ),
}


def _default_platform(difficulty: Difficulty, robot_type: RobotType) -> TargetPlatform:
    if difficulty is Difficulty.ADVANCED or robot_type in {
        RobotType.ROVER,
        RobotType.BALANCING_BOT,
    }:
        return TargetPlatform.ESP32
    return TargetPlatform.ARDUINO


class RobotPlannerAgent(BaseAgent):
    """Normalises intent into the shared specification."""

    name = AgentName.PLANNER
    display_name = "Robot Planner"
    description = (
        "Turns a plain-language robot idea into a structured specification: "
        "platform, drivetrain, power source, requirements, and constraints."
    )
    depends_on = ()
    input_model = PlannerInput
    output_model = RobotSpecificationDraft
    requires_specification = False
    status = "available"
    milestone = "M3"
    owner_area = "Robotics / Systems Engineering"

    async def execute(self, request: AgentRequest) -> RobotSpecificationDraft:
        context = request.context
        existing = context.shared.specification
        parameters = request.parameters

        difficulty = (
            existing.difficulty
            if existing is not None
            else Difficulty(str(parameters.get("skill_level", Difficulty.BEGINNER)))
        )
        robot_type = context.robot_type
        summary = (
            existing.summary
            if existing is not None and existing.summary.strip()
            else context.description.strip() or f"A {robot_type.value.replace('_', ' ')} robot."
        )
        use_case = (
            existing.use_case
            if existing is not None and existing.use_case.strip()
            else context.description.strip()
        )
        platform = existing.target_platform if existing is not None else TargetPlatform.UNDECIDED
        if platform is TargetPlatform.UNDECIDED:
            platform = _default_platform(difficulty, robot_type)

        drive_type = existing.drive_type if existing is not None else DriveType.NONE
        if drive_type is DriveType.NONE:
            drive_type = _DRIVE_BY_ROBOT.get(robot_type, DriveType.NONE)

        requirements = list(existing.requirements) if existing is not None else []
        for requirement in _REQUIREMENTS_BY_ROBOT.get(robot_type, ()):
            if requirement not in requirements:
                requirements.append(requirement)

        constraints = list(existing.constraints) if existing is not None else []
        budget = context.budget
        if budget.max_usd is not None:
            constraint = f"Total component cost must stay below ${budget.max_usd:.2f}."
            if constraint not in constraints:
                constraints.append(constraint)

        power_source = (
            existing.power_source
            if existing is not None and existing.power_source.strip()
            else "2S LiPo (7.4 V) with a regulated 5 V rail"
        )

        return RobotSpecificationDraft(
            summary=summary,
            use_case=use_case,
            robot_type=robot_type,
            difficulty=difficulty,
            target_platform=platform,
            drive_type=drive_type,
            environment=(
                existing.environment
                if existing is not None and existing.environment.strip()
                else "indoor"
            ),
            power_source=power_source,
            dimensions=existing.dimensions if existing is not None else Dimensions(),
            payload_capacity_kg=existing.payload_capacity_kg if existing is not None else None,
            requirements=requirements,
            constraints=constraints,
            success_criteria=[
                "All electrical validation checks pass before power-on",
                "The robot completes its stated task in a supervised test",
            ],
            open_questions=[],
            confidence=0.85 if existing is not None else 0.7,
        )


__all__ = ["RobotPlannerAgent"]
