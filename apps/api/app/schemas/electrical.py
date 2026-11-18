"""Electrical artifact and export schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.ai.contracts import ComponentResearchOutput, ElectricalPlan
from app.schemas.common import APIModel

ExportFormatName = Literal["json", "wiring-csv", "bom-csv", "kicad-netlist", "svg", "markdown"]


class ExportFormatRead(APIModel):
    format: ExportFormatName
    label: str
    filename: str
    media_type: str
    description: str


class ElectricalArtifactRead(APIModel):
    project_id: UUID
    project_name: str
    agent_run_id: UUID
    generated_at: datetime
    plan: ElectricalPlan
    bom: ComponentResearchOutput | None = None
    total_estimated_usd: float | None = None
    export_formats: list[ExportFormatRead] = Field(default_factory=list)


__all__ = ["ElectricalArtifactRead", "ExportFormatName", "ExportFormatRead"]
