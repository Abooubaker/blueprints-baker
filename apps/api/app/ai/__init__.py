"""AI layer: contracts, providers, agents, and orchestration."""

from app.ai.base import BaseAgent, LLMBackedAgent, PlaceholderAgent
from app.ai.contracts import AgentRequest, AgentResult, ProjectContext, SharedProjectContext
from app.ai.orchestrator import AgentOrchestrator, build_agent_registry, get_agent_descriptors
from app.ai.provider import LLMProvider, MockProvider, create_provider

__all__ = [
    "AgentOrchestrator",
    "AgentRequest",
    "AgentResult",
    "BaseAgent",
    "LLMBackedAgent",
    "LLMProvider",
    "MockProvider",
    "PlaceholderAgent",
    "ProjectContext",
    "SharedProjectContext",
    "build_agent_registry",
    "create_provider",
    "get_agent_descriptors",
]
