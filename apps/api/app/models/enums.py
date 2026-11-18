"""Shared enums used by ORM models, API schemas, and AI contracts."""

from __future__ import annotations

from enum import StrEnum


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    ARCHIVED = "archived"


class RobotType(StrEnum):
    LINE_FOLLOWER = "line_follower"
    OBSTACLE_AVOIDER = "obstacle_avoider"
    ROVER = "rover"
    ROBOT_ARM = "robot_arm"
    DRONE = "drone"
    BALANCING_BOT = "balancing_bot"
    CUSTOM = "custom"


class Difficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TargetPlatform(StrEnum):
    ARDUINO = "arduino"
    ESP32 = "esp32"
    RASPBERRY_PI = "raspberry_pi"
    OTHER = "other"
    UNDECIDED = "undecided"


class DriveType(StrEnum):
    DIFFERENTIAL = "differential"
    MECANUM = "mecanum"
    OMNI = "omni"
    TANK = "tank"
    SERVO_ARM = "servo_arm"
    NONE = "none"


class SpecificationStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"


class ComponentCategory(StrEnum):
    CONTROLLER = "controller"
    MOTOR = "motor"
    MOTOR_DRIVER = "motor_driver"
    SENSOR = "sensor"
    POWER = "power"
    CHASSIS = "chassis"
    WHEEL = "wheel"
    ACTUATOR = "actuator"
    COMMUNICATION = "communication"
    DISPLAY = "display"
    WIRING = "wiring"
    TOOL = "tool"
    OTHER = "other"


class ComponentAvailability(StrEnum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"


class StoreName(StrEnum):
    """Stores the guided flow can price a part against."""

    TEMU = "temu"
    MIKROELECTRON = "mikroelectron"
    WASLLEH = "waslleh"
    AMAZON = "amazon"
    ALIEXPRESS = "aliexpress"
    GHANIMJO = "ghanimjo"


class CodeLanguage(StrEnum):
    """Programming languages the generated bundle can scaffold."""

    PYTHON = "python"
    CPP = "cpp"
    C = "c"
    STM32_ASSEMBLY = "stm32_assembly"
    VERILOG = "verilog"
    VHDL = "vhdl"
    OTHER = "other"


class PrintMaterial(StrEnum):
    """Materials carried by the 3D-print price chart."""

    PLA = "PLA"
    PETG = "PETG"
    ABS = "ABS"
    RESIN = "Resin"
    TPU = "TPU"


class AgentName(StrEnum):
    PLANNER = "robot_planner"
    COMPONENT_RESEARCH = "component_research"
    ELECTRICAL = "electrical_engineering"
    PROGRAMMING = "programming"
    MECHANICAL = "mechanical_design"
    COST = "cost_estimation"


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    NOT_IMPLEMENTED = "not_implemented"


class AgentResultStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_IMPLEMENTED = "not_implemented"
