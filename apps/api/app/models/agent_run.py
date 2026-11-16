"""Audit record for every AI agent execution."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, enum_type
from app.models.enums import AgentName, AgentRunStatus

if TYPE_CHECKING:
    from app.models.project import RobotProject


class AgentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_project_created", "project_id", "created_at"),
        Index("ix_agent_runs_agent_status", "agent", "status"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("robot_projects.id", ondelete="CASCADE"), nullable=False
    )
    agent: Mapped[AgentName] = mapped_column(enum_type(AgentName, "agent_name"), nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(
        enum_type(AgentRunStatus, "agent_run_status"),
        default=AgentRunStatus.QUEUED,
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    model: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[RobotProject] = relationship(back_populates="agent_runs")
