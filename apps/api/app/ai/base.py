"""Base agent contract and LLM-backed execution helper."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from app.ai.contracts import (
    AgentDescriptor,
    AgentRequest,
    AgentResult,
    ProjectContext,
    TokenUsage,
)
from app.ai.provider import LLMMessage, LLMProvider, LLMRequest
from app.core.errors import NotImplementedFeatureError
from app.models.enums import AgentName, AgentResultStatus

if TYPE_CHECKING:
    pass


class BaseAgent(ABC):
    """A specialized, independently developed unit of AI work.

    Team contract:
    - one subclass per agent, one module under ``app/ai/agents``;
    - ``input_model`` / ``output_model`` are the only data it may exchange;
    - implement ``execute`` and never mutate another agent's artifact;
    - raise ``AgentError`` for expected failures.
    """

    name: ClassVar[AgentName]
    display_name: ClassVar[str]
    description: ClassVar[str]
    depends_on: ClassVar[tuple[AgentName, ...]] = ()
    input_model: ClassVar[type[BaseModel]]
    output_model: ClassVar[type[BaseModel]]
    milestone: ClassVar[str] = "M3"
    owner_area: ClassVar[str] = "AI Engineering"
    requires_specification: ClassVar[bool] = True

    def descriptor(self) -> AgentDescriptor:
        return AgentDescriptor(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            status="placeholder",
            depends_on=list(self.depends_on),
            input_schema=self.input_model.__name__,
            output_schema=self.output_model.__name__,
            milestone=self.milestone,
            owner_area=self.owner_area,
        )

    async def run(self, request: AgentRequest) -> AgentResult:
        """Validate prerequisites, execute, and normalize errors."""
        started_at = datetime.now(UTC)
        started = time.perf_counter()

        try:
            self.validate(request.context)
            output = await self.execute(request)
            if not isinstance(output, self.output_model):
                raise TypeError(
                    f"{self.name} returned {type(output).__name__}, "
                    f"expected {self.output_model.__name__}"
                )
            status = AgentResultStatus.SUCCEEDED
            payload = output.model_dump(mode="json")
            summary = f"{self.display_name} completed."
            error = None
        except NotImplementedFeatureError as exc:
            status = AgentResultStatus.NOT_IMPLEMENTED
            payload = None
            summary = f"{self.display_name} is a foundation placeholder."
            error = exc.message
        except Exception as exc:
            status = AgentResultStatus.FAILED
            payload = None
            summary = f"{self.display_name} failed."
            error = str(exc) or type(exc).__name__

        completed_at = datetime.now(UTC)
        latency_ms = int((time.perf_counter() - started) * 1000)
        return AgentResult(
            agent=self.name,
            status=status,
            summary=summary,
            output=payload,
            warnings=[error] if error and status != AgentResultStatus.SUCCEEDED else [],
            usage=TokenUsage(latency_ms=latency_ms),
            error=error,
            started_at=started_at,
            completed_at=completed_at,
        )

    def validate(self, context: ProjectContext) -> None:
        if self.requires_specification and context.shared.specification is None:
            raise ValueError(
                f"{self.display_name} requires an approved robot specification. "
                "Run the Robot Planner first."
            )

    @abstractmethod
    async def execute(self, request: AgentRequest) -> BaseModel:
        """Perform the agent's work and return a validated output model."""
        raise NotImplementedError


class PlaceholderAgent(BaseAgent):
    """Deliberate M1 stub: exposes the contract without AI behaviour."""

    async def execute(self, request: AgentRequest) -> BaseModel:
        del request
        raise NotImplementedFeatureError(
            f"{self.display_name} is not implemented yet. "
            f"It will be delivered in milestone {self.milestone}. "
            "See docs/ai-agents.md for its prompt blueprint and acceptance criteria."
        )

    def build_prompt_blueprint(self, context: ProjectContext) -> str:
        """Starter prompt text for the implementing engineer.

        This method is intentionally unused by the placeholder behaviour; it
        documents the intended reasoning inputs and is covered by tests so the
        contract does not drift while the agent is built.
        """
        schema = json.dumps(self.output_model.model_json_schema(), indent=2)
        return (
            f"You are the RoboCraft {self.display_name}.\n"
            f"{self.description}\n"
            f"Project: {context.project_name} ({context.robot_type.value}).\n"
            f"Description: {context.description}\n"
            f"Shared context: {context.shared.model_dump_json()}\n"
            "Return only JSON that satisfies this schema:\n"
            f"{schema}\n"
        )


class LLMBackedAgent(BaseAgent):
    """Convenience base for agents that ask a provider for structured JSON."""

    provider: LLMProvider
    system_prompt: ClassVar[str] = ""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def build_messages(self, request: AgentRequest) -> list[LLMMessage]:
        return [
            LLMMessage(
                role="system",
                content=self.system_prompt or f"You are the RoboCraft {self.display_name}.",
            ),
            LLMMessage(role="user", content=self.build_user_prompt(request)),
        ]

    def build_user_prompt(self, request: AgentRequest) -> str:
        return (
            f"{self.description}\n"
            f"Project context (JSON):\n{request.context.model_dump_json()}\n"
            f"Parameters (JSON):\n{json.dumps(request.parameters, default=str)}\n"
            "Respond with JSON only, conforming to the provided schema."
        )

    async def execute(self, request: AgentRequest) -> BaseModel:
        response = await self.provider.generate(
            LLMRequest(
                messages=self.build_messages(request),
                model=self.provider.default_model,
                response_schema=self.output_model.model_json_schema(),
            )
        )
        return self.output_model.model_validate(json.loads(response.content))
