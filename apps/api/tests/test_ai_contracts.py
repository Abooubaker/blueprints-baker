"""Contract-level tests that protect the architecture from drift."""

from __future__ import annotations

import json
import uuid

import pytest

from app.ai.contracts import (
    AgentRequest,
    AgentResultStatus,
    ProjectContext,
    RobotSpecificationDraft,
)
from app.ai.orchestrator import (
    PIPELINE_ORDER,
    AgentOrchestrator,
    OrchestrationError,
    build_agent_registry,
    get_agent_descriptors,
)
from app.ai.provider import MockProvider, create_provider
from app.core.config import Settings
from app.models.enums import AgentName


def make_context(with_spec: bool = False) -> ProjectContext:
    return ProjectContext(
        project_id=uuid.uuid4(),
        project_name="Test rover",
        robot_type="rover",
        description="A rover",
        shared=(
            {"specification": RobotSpecificationDraft(summary="A small rover")} if with_spec else {}
        ),
    )


def test_agent_registry_matches_pipeline_order() -> None:
    provider = MockProvider()
    registry = build_agent_registry(provider)
    assert list(registry) == list(PIPELINE_ORDER)
    descriptors = get_agent_descriptors(provider)
    assert [descriptor.name for descriptor in descriptors] == list(PIPELINE_ORDER)
    for descriptor in descriptors:
        assert descriptor.input_schema
        assert descriptor.output_schema


def test_dependency_resolution_adds_prerequisites() -> None:
    orchestrator = AgentOrchestrator(build_agent_registry(MockProvider()))
    order = orchestrator.order([AgentName.PROGRAMMING])
    assert order == [
        AgentName.PLANNER,
        AgentName.COMPONENT_RESEARCH,
        AgentName.ELECTRICAL,
        AgentName.PROGRAMMING,
    ]


def test_unknown_agent_is_rejected() -> None:
    orchestrator = AgentOrchestrator(build_agent_registry(MockProvider()))
    with pytest.raises(OrchestrationError):
        orchestrator.order(["does_not_exist"])  # type: ignore[list-item]


async def test_pipeline_runs_deterministic_agents_then_reports_placeholders() -> None:
    orchestrator = AgentOrchestrator(build_agent_registry(MockProvider()))
    result = await orchestrator.run(make_context())
    assert result.status == AgentResultStatus.NOT_IMPLEMENTED
    assert [item.status for item in result.results[:3]] == [
        AgentResultStatus.SUCCEEDED,
        AgentResultStatus.SUCCEEDED,
        AgentResultStatus.SUCCEEDED,
    ]
    assert all(item.status == AgentResultStatus.NOT_IMPLEMENTED for item in result.results[3:])
    assert result.context.specification is not None
    assert result.context.component_research is not None
    assert result.context.electrical is not None
    assert result.context.electrical.connections


async def test_planner_requires_no_spec_but_others_do() -> None:
    registry = build_agent_registry(MockProvider())
    planner = registry[AgentName.PLANNER]
    electrical = registry[AgentName.ELECTRICAL]

    planner_result = await planner.run(AgentRequest(context=make_context()))
    assert planner_result.status == AgentResultStatus.SUCCEEDED
    assert planner_result.output is not None
    assert planner_result.output["robot_type"] == "rover"

    electrical_result = await electrical.run(AgentRequest(context=make_context()))
    assert electrical_result.status == AgentResultStatus.FAILED
    assert "requires an approved robot specification" in (electrical_result.error or "")


def test_mock_provider_is_deterministic_and_explicit() -> None:
    provider = create_provider(Settings(_env_file=None, ai_provider="mock"))
    assert isinstance(provider, MockProvider)


def test_contracts_are_serializable() -> None:
    spec = RobotSpecificationDraft(summary="Rover", requirements=["drive"])
    payload = json.loads(spec.model_dump_json())
    assert payload["summary"] == "Rover"
    schema = RobotSpecificationDraft.model_json_schema()
    assert schema["properties"]["requirements"]["type"] == "array"
