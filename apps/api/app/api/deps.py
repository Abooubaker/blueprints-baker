"""Reusable FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Query

from app.ai.orchestrator import AgentOrchestrator, build_agent_registry
from app.ai.provider import LLMProvider, create_provider
from app.core.config import Settings, get_settings


@lru_cache
def get_llm_provider() -> LLMProvider:
    return create_provider(get_settings())


@lru_cache
def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator(build_agent_registry(get_llm_provider()))


SettingsDep = Annotated[Settings, Depends(get_settings)]
ProviderDep = Annotated[LLMProvider, Depends(get_llm_provider)]
OrchestratorDep = Annotated[AgentOrchestrator, Depends(get_orchestrator)]


class Pagination:
    """Offset pagination with defensive bounds."""

    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0, le=10_000)] = 0,
    ) -> None:
        self.limit = limit
        self.offset = offset


PaginationDep = Annotated[Pagination, Depends()]
