from __future__ import annotations

from typing import Any

from httpx import AsyncClient


async def create_project(client: AsyncClient, **overrides: Any) -> dict[str, Any]:
    payload = {
        "name": "Line Following Rover",
        "description": "A small rover that follows a black line indoors.",
        "robot_type": "line_follower",
        "difficulty": "beginner",
        "target_platform": "arduino",
        "budget_min_usd": 40,
        "budget_max_usd": 90,
        "requirements": ["Follow a line", "Stop at obstacles"],
        "constraints": ["Must run on a 9V battery"],
    }
    payload.update(overrides)
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_project_bootstraps_specification(client: AsyncClient) -> None:
    project = await create_project(client)
    assert project["slug"] == "line-following-rover"
    assert project["status"] == "draft"
    assert project["specification"]["target_platform"] == "arduino"
    assert project["specification"]["version"] == 1
    assert project["specification"]["summary"].startswith("A small rover")


async def test_duplicate_names_get_unique_slugs(client: AsyncClient) -> None:
    first = await create_project(client)
    second = await create_project(client)
    assert first["slug"] != second["slug"]
    assert second["slug"] == "line-following-rover-2"


async def test_list_projects_supports_filters_and_pagination(client: AsyncClient) -> None:
    await create_project(client)
    await create_project(
        client, name="Rover Two", robot_type="rover", description="An outdoor rover."
    )

    response = await client.get("/api/v1/projects")
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 2
    assert len(body["items"]) == 2
    assert "specification" not in body["items"][0]

    filtered = await client.get("/api/v1/projects", params={"robot_type": "rover"})
    assert filtered.json()["meta"]["total"] == 1

    searched = await client.get("/api/v1/projects", params={"search": "Line"})
    assert searched.json()["meta"]["total"] == 1

    paged = await client.get("/api/v1/projects", params={"limit": 1, "offset": 1})
    assert len(paged.json()["items"]) == 1


async def test_get_update_and_delete_project(client: AsyncClient) -> None:
    project = await create_project(client)
    url = f"/api/v1/projects/{project['id']}"

    fetched = await client.get(url)
    assert fetched.status_code == 200

    updated = await client.patch(url, json={"status": "planning", "budget_max_usd": 120})
    assert updated.status_code == 200
    assert updated.json()["status"] == "planning"
    assert updated.json()["budget_max_usd"] == 120.0

    spec = await client.get(f"{url}/specification")
    assert spec.status_code == 200

    spec_update = await client.put(
        f"{url}/specification",
        json={"summary": "Updated summary", "environment": "classroom"},
    )
    assert spec_update.status_code == 200
    assert spec_update.json()["version"] == 2
    assert spec_update.json()["environment"] == "classroom"

    deleted = await client.delete(url)
    assert deleted.status_code == 204
    assert (await client.get(url)).status_code == 404


async def test_invalid_budget_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Bad budget", "budget_min_usd": 100, "budget_max_usd": 10},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_missing_project_returns_404_envelope(client: AsyncClient) -> None:
    response = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
