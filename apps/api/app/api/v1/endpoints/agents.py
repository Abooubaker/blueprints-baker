"""AI agent catalog endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.ai.orchestrator import get_agent_descriptors
from app.api.deps import ProviderDep
from app.schemas.agent import AgentCatalogEntry, AgentCatalogResponse

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentCatalogResponse, summary="List the AI agent roster")
async def list_agents(provider: ProviderDep) -> AgentCatalogResponse:
    descriptors = get_agent_descriptors(provider)
    return AgentCatalogResponse(
        provider=provider.name,
        model=provider.default_model,
        agents=[AgentCatalogEntry.model_validate(descriptor) for descriptor in descriptors],
    )
