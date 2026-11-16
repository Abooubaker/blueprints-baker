"""Provider-independent LLM boundary.

Application code depends on the ``LLMProvider`` protocol, never on a vendor SDK.
A concrete provider (OpenAI, Anthropic, local model, ...) is selected through
``AI_PROVIDER`` and registered in ``PROVIDER_FACTORIES`` during milestone M3.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.config import Settings
from app.core.errors import NotImplementedFeatureError

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class LLMRequest:
    messages: list[LLMMessage]
    model: str
    temperature: float = 0.2
    max_tokens: int = 4096
    response_schema: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    provider: str
    model: str
    usage: LLMUsage = field(default_factory=LLMUsage)
    raw: dict[str, Any] | None = None


class ProviderConfigurationError(RuntimeError):
    """Raised when the selected provider is unknown or misconfigured."""


class LLMProvider(ABC):
    """Async text-generation boundary."""

    name: str

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Model identifier used when a request does not override it."""

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a single completion for ``request``."""

    async def health(self) -> bool:
        """Best-effort readiness probe. Offline providers return True."""
        return True


class MockProvider(LLMProvider):
    """Deterministic offline provider.

    It exists to exercise contracts, orchestration, and persistence without
    network access or credentials. It is *not* an AI implementation and every
    response is explicitly flagged as a placeholder.
    """

    name = "mock"

    def __init__(self, model: str = "placeholder") -> None:
        self._model = model

    @property
    def default_model(self) -> str:
        return self._model

    async def generate(self, request: LLMRequest) -> LLMResponse:
        del request
        return LLMResponse(
            content=json.dumps(
                {
                    "placeholder": True,
                    "message": "Mock provider: specialized agent logic is not implemented.",
                }
            ),
            provider=self.name,
            model=self.default_model,
        )


PROVIDER_FACTORIES: dict[str, type[LLMProvider]] = {"mock": MockProvider}


def create_provider(settings: Settings) -> LLMProvider:
    factory = PROVIDER_FACTORIES.get(settings.ai_provider.lower())
    if factory is None:
        supported = ", ".join(sorted(PROVIDER_FACTORIES))
        raise ProviderConfigurationError(
            f"Unknown AI provider '{settings.ai_provider}'. Supported: {supported}."
        )
    if factory is MockProvider:
        return MockProvider(model=settings.ai_model)
    raise NotImplementedFeatureError(
        f"Provider '{settings.ai_provider}' is registered but not implemented yet."
    )
