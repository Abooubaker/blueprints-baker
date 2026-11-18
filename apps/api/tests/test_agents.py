from __future__ import annotations

from httpx import AsyncClient

from tests.test_projects import create_project


async def test_agent_catalog_lists_six_agents(client: AsyncClient) -> None:
    response = await client.get("/api/v1/agents")
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "mock"
    assert len(body["agents"]) == 6
    names = [agent["name"] for agent in body["agents"]]
    assert names[0] == "robot_planner"
    planner = body["agents"][0]
    assert planner["depends_on"] == []
    assert planner["output_schema"] == "RobotSpecificationDraft"
    statuses = {agent["name"]: agent["status"] for agent in body["agents"]}
    assert statuses == {
        "robot_planner": "available",
        "component_research": "available",
        "electrical_engineering": "available",
        "programming": "placeholder",
        "mechanical_design": "placeholder",
        "cost_estimation": "placeholder",
    }


async def test_pipeline_run_is_audited_and_honest(client: AsyncClient) -> None:
    project = await create_project(client)
    response = await client.post(f"/api/v1/projects/{project['id']}/agent-runs", json={})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "not_implemented"
    assert len(body["runs"]) == 6
    assert [run["agent"] for run in body["runs"]] == [
        "robot_planner",
        "component_research",
        "electrical_engineering",
        "programming",
        "mechanical_design",
        "cost_estimation",
    ]
    assert [run["status"] for run in body["runs"][:3]] == ["succeeded"] * 3
    assert all(run["status"] == "not_implemented" for run in body["runs"][3:])

    # The planner keeps the approved draft specification rather than overwriting it.
    assert body["shared_context"]["specification"]["summary"].startswith("A small rover")
    assert body["shared_context"]["component_research"]["bill_of_materials"]
    assert body["shared_context"]["electrical"]["connections"]

    audit = await client.get(f"/api/v1/projects/{project['id']}/agent-runs")
    assert audit.status_code == 200
    assert audit.json()["meta"]["total"] == 6


async def test_running_agents_requires_existing_project(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000/agent-runs", json={}
    )
    assert response.status_code == 404


async def test_component_catalog_is_empty_but_available(client: AsyncClient) -> None:
    response = await client.get("/api/v1/components")
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "meta": {"total": 0, "limit": 20, "offset": 0},
    }
