from __future__ import annotations

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["environment"] == "test"
    assert response.headers["x-request-id"]


async def test_readiness_checks_database(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"]["database"]["status"] == "ok"


async def test_unknown_route_uses_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["request_id"]


async def test_request_id_is_propagated(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "test-request-1"})
    assert response.headers["x-request-id"] == "test-request-1"
