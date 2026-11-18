"""Guided-flow intent research.

The first question in the product is plain language: "what do you want to
build?". This module turns that sentence into a named robot type the user can
confirm before any shopping or wiring happens. It is deterministic and offline
so the flow works without an LLM key; an LLM-backed implementation can replace
:func:`identify_robot` behind the same ``RobotIdentification`` contract.
"""

from __future__ import annotations

import re

from app.ai.contracts import RobotIdentification
from app.models.enums import Difficulty, RobotType, TargetPlatform

_KEYWORDS: tuple[tuple[RobotType, tuple[str, ...]], ...] = (
    (
        RobotType.LINE_FOLLOWER,
        ("line follow", "line-follow", "follow a line", "track", "tape", "tracing"),
    ),
    (
        RobotType.OBSTACLE_AVOIDER,
        ("obstacle", "avoid", "collision", "ultrasonic", "distance sensor", "bump"),
    ),
    (
        RobotType.ROBOT_ARM,
        ("arm", "pick", "place", "gripper", "servo", "manipulat", "3-dof", "3 dof"),
    ),
    (
        RobotType.BALANCING_BOT,
        ("balance", "self-balanc", "two-wheel", "inverted pendulum", "upright"),
    ),
    (
        RobotType.DRONE,
        ("drone", "quadcopter", "fly", "flight", "aerial"),
    ),
    (
        RobotType.ROVER,
        ("rover", "car", "patio", "terrain", "four-wheel", "4wd", "inspection"),
    ),
)

_NAME_BY_TYPE: dict[RobotType, str] = {
    RobotType.LINE_FOLLOWER: "Line Scout",
    RobotType.OBSTACLE_AVOIDER: "Pathfinder",
    RobotType.ROBOT_ARM: "Workbench Arm",
    RobotType.BALANCING_BOT: "Balance Bot",
    RobotType.DRONE: "Air Scout",
    RobotType.ROVER: "Trail Rover",
    RobotType.CUSTOM: "Custom Build",
}

_REQUIREMENTS_BY_TYPE: dict[RobotType, tuple[str, ...]] = {
    RobotType.LINE_FOLLOWER: (
        "Follow a marked line without losing the track",
        "Stop safely when the line is lost",
    ),
    RobotType.OBSTACLE_AVOIDER: (
        "Detect obstacles before contact",
        "Steer around an obstacle and resume travel",
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
        "Return to a safe landing state on low battery",
    ),
    RobotType.ROVER: (
        "Drive over small indoor or patio obstacles",
        "Maintain a stable control link",
    ),
    RobotType.CUSTOM: (
        "Complete the described task under supervision",
        "Pass all electrical checks before power-on",
    ),
}

_ADVANCED_HINTS = ("wifi", "wi-fi", "camera", "stream", "autonomous", "slam", "lidar", "stm32")
_INTERMEDIATE_HINTS = ("esp32", "sensor", "servo", "bluetooth", "pid", "encoder")


def _title_from_description(description: str, robot_type: RobotType) -> str:
    cleaned = re.sub(r"[^a-z0-9 ]", " ", description.lower())
    words = [word for word in cleaned.split() if len(word) > 3]
    if robot_type is RobotType.CUSTOM and words:
        return f"{words[0].title()} Build"[:120]
    return _NAME_BY_TYPE[robot_type]


def identify_robot(description: str, *, robot_type: RobotType | None = None) -> RobotIdentification:
    """Classify a build description into a confirmable robot identification."""

    text = description.strip()
    lowered = text.lower()

    if robot_type is not None and robot_type is not RobotType.CUSTOM:
        chosen: RobotType = robot_type
        scores: dict[RobotType, int] = {chosen: 1}
    else:
        scores = {}
        for candidate, keywords in _KEYWORDS:
            scores[candidate] = sum(1 for keyword in keywords if keyword in lowered)
        best_score = max(scores.values(), default=0)
        chosen = RobotType.CUSTOM
        if best_score > 0:
            order = [candidate for candidate, _ in _KEYWORDS]
            chosen = max(order, key=lambda candidate: (scores[candidate], -order.index(candidate)))

    best_score = scores.get(chosen, 0)
    confidence = min(0.94, 0.55 + 0.11 * best_score) if chosen is not RobotType.CUSTOM else 0.42
    if not text:
        confidence = 0.2

    if any(hint in lowered for hint in _ADVANCED_HINTS):
        difficulty = Difficulty.ADVANCED
    elif any(hint in lowered for hint in _INTERMEDIATE_HINTS):
        difficulty = Difficulty.INTERMEDIATE
    else:
        difficulty = Difficulty.BEGINNER

    if chosen in {RobotType.ROVER, RobotType.BALANCING_BOT} or difficulty is Difficulty.ADVANCED:
        platform = TargetPlatform.ESP32
    elif "raspberry pi" in lowered or "pico" in lowered:
        platform = TargetPlatform.RASPBERRY_PI
    else:
        platform = TargetPlatform.ARDUINO

    matched = [keyword for keyword in dict(_KEYWORDS).get(chosen, ()) if keyword in lowered]
    rationale = (
        f"Matched {', '.join(matched)} in your description."
        if matched
        else "No strong archetype matched, so this is treated as a custom build for now."
    )

    return RobotIdentification(
        proposed_name=_title_from_description(text, chosen),
        robot_type=chosen,
        confidence=confidence,
        rationale=rationale,
        suggested_platform=platform,
        suggested_difficulty=difficulty,
        key_requirements=list(_REQUIREMENTS_BY_TYPE[chosen]),
        needs_confirmation=True,
    )


__all__ = ["identify_robot"]
