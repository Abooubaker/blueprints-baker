"""Programming Agent — hardware-aware firmware generation."""

from __future__ import annotations

from app.ai.base import PlaceholderAgent
from app.ai.contracts import ProgrammingInput, ProgrammingOutput
from app.models.enums import AgentName


class ProgrammingAgent(PlaceholderAgent):
    """Generates and explains firmware for the selected hardware.

    Responsibilities (M6):
    - select language/framework for Arduino, ESP32, or Raspberry Pi;
    - generate files wired to the approved pin map;
    - declare libraries and pin assignments explicitly;
    - provide setup, upload, and validation steps;
    - never invent libraries or pins that are absent from shared context.

    Downstream contract: ``ProgrammingOutput`` is consumed by the UI and by
    static validation. Generated code must be treated as untrusted input.
    """

    name = AgentName.PROGRAMMING
    display_name = "Programming"
    description = (
        "Generates platform-specific code from the approved hardware "
        "configuration and explains how to deploy it."
    )
    depends_on = (
        AgentName.PLANNER,
        AgentName.COMPONENT_RESEARCH,
        AgentName.ELECTRICAL,
    )
    input_model = ProgrammingInput
    output_model = ProgrammingOutput
    milestone = "M6"
    owner_area = "AI Engineering / Firmware"
