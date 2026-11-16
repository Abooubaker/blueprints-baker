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
    assert all(agent["status"] == "placeholder" for agent in body["agents"])


async def test_pipeline_run_is_audited_and_honest(client: AsyncClient) -> None:
    project = await create_project(client)
    response = await client.post(f"/api/v1/projects/{project['id']}/agent-runs", json={})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "not_implemented"
    assert len(body["runs"]) == 6
    assert body["runs"][0]["agent"] == "robot_planner"
    assert body["runs"][0]["status"] == "not_implemented"
    assert all(run["status"] == "skipped" for run in body["runs"][1:])
    # The project already has a draft specification; the placeholder planner does
    # not replace it.
    assert body["shared_context"]["specification"]["summary"].startswith("A small rover")

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
