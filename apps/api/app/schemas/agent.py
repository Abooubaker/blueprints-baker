"""Agent catalog, orchestration request, and audit-record schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.ai.contracts import SharedProjectContext
from app.models.enums import AgentName, AgentResultStatus, AgentRunStatus
from app.schemas.common import APIModel


class AgentCatalogEntry(APIModel):
    name: AgentName
    display_name: str
    description: str
    status: str
    depends_on: list[AgentName]
    input_schema: str
    output_schema: str
    milestone: str
    owner_area: str


class AgentCatalogResponse(APIModel):
    provider: str
    model: str
    agents: list[AgentCatalogEntry]


class AgentRunRequest(APIModel):
    agents: list[AgentName] | None = Field(
        default=None,
        description=(
            "Subset to execute. Dependencies are added automatically. "
            "Omit to run the full pipeline."
        ),
    )
    parameters: dict[str, Any] = Field(default_factory=dict)


class AgentRunRead(APIModel):
    id: UUID
    project_id: UUID
    agent: AgentName
    status: AgentRunStatus
    provider: str
    model: str
    summary: str = ""
    output_payload: dict[str, Any] | None
    error_message: str | None
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class OrchestrationRead(APIModel):
    project_id: UUID
    status: AgentResultStatus
    runs: list[AgentRunRead]
    shared_context: SharedProjectContext
    provider: str
    model: str
