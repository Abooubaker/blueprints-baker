from __future__ import annotations

from httpx import AsyncClient

from tests.test_projects import create_project


async def test_identification_returns_a_confirmable_robot(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/intent/identify",
        json={
            "description": (
                "A WiFi rover that drives on the patio, avoids obstacles with an "
                "ultrasonic sensor, and streams distance readings."
            )
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["robot_type"] in {"rover", "obstacle_avoider"}
    assert body["proposed_name"]
    assert body["needs_confirmation"] is True
    assert body["confidence"] > 0
    assert body["key_requirements"]


async def test_save_preferences_updates_project_and_specification(client: AsyncClient) -> None:
    project = await create_project(client)
    url = f"/api/v1/projects/{project['id']}/preferences"
    payload = {
        "description": "A line follower for a school competition.",
        "robot_name": "Tape Runner",
        "robot_type": "line_follower",
        "difficulty": "beginner",
        "shops": ["temu", "amazon"],
        "languages": ["python", "c", "verilog"],
        "controllers": ["ESP32 DevKit", "Arduino Nano"],
        "controller_notes": "I have an ESP32 and a spare Nano.",
        "custom_pcb": True,
        "confirmed": True,
        "budget_max_usd": 75,
        "identification_rationale": "Matched line and track keywords.",
        "identification_confidence": 0.77,
    }
    saved = await client.put(url, json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["shops"] == ["temu", "amazon"]
    assert saved.json()["custom_pcb"] is True

    fetched = await client.get(url)
    assert fetched.status_code == 200
    assert fetched.json()["controllers"] == ["ESP32 DevKit", "Arduino Nano"]

    updated = await client.get(f"/api/v1/projects/{project['id']}")
    assert updated.json()["name"] == "Tape Runner"
    assert updated.json()["specification"]["target_platform"] == "esp32"


async def test_full_build_returns_prices_code_3d_and_docs(client: AsyncClient) -> None:
    project = await create_project(client)
    preferences = {
        "description": "A line follower that stops at obstacles.",
        "robot_name": "Tape Runner",
        "robot_type": "line_follower",
        "difficulty": "beginner",
        "shops": ["temu", "amazon"],
        "languages": ["python", "cpp", "c", "verilog"],
        "controllers": ["ESP32"],
        "controller_notes": "",
        "custom_pcb": False,
        "confirmed": True,
        "budget_max_usd": 90,
        "identification_rationale": "Matched line and track keywords.",
        "identification_confidence": 0.81,
    }
    saved = await client.put(f"/api/v1/projects/{project['id']}/preferences", json=preferences)
    assert saved.status_code == 200, saved.text

    response = await client.post(f"/api/v1/projects/{project['id']}/build")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["missing"] == []

    offers = body["research"]["bill_of_materials"][0]["selection"]["offers"]
    assert [offer["store"] for offer in offers] == ["temu", "amazon"]
    assert [offer["price_jod"] for offer in offers] == sorted(
        offer["price_jod"] for offer in offers
    )
    assert body["research"]["selected_shops"] == ["temu", "amazon"]

    bundles = body["programming"]["bundles"]
    assert [bundle["language"] for bundle in bundles] == ["python", "cpp", "c", "verilog"]
    assert all(len(bundle["files"]) >= 2 for bundle in bundles)
    assert body["programming"]["pin_assignments"]

    mechanical = body["mechanical"]
    assert mechanical["stl_ascii"].startswith("solid ")
    assert mechanical["stl_filename"].endswith(".stl")
    assert len(mechanical["material_quotes"]) == 5
    assert sum(1 for quote in mechanical["material_quotes"] if quote["is_cheapest"]) == 1
    assert body["electrical"]["pinout"]

    assert body["cost"]["total_jod"] is not None
    assert body["cost"]["print_cost_jod"] is not None

    docs = {doc["path"] for doc in body["documentation"]["files"]}
    assert "README.md" in docs
    assert "docs/wiring.md" in docs
    assert "docs/firmware.md" in docs
    assert "docs/mechanical.md" in docs
    assert "docs/budget.md" in docs

    fetched = await client.get(f"/api/v1/projects/{project['id']}/build")
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "ready"

    stl = await client.get(f"/api/v1/projects/{project['id']}/mechanical/stl")
    assert stl.status_code == 200
    assert stl.text.startswith("solid ")
    assert "attachment" in stl.headers["content-disposition"]


async def test_print_settings_control_material_infill_and_price(client: AsyncClient) -> None:
    project = await create_project(client)
    preferences = {
        "description": "A rover with a printable chassis.",
        "robot_name": "Print Lab",
        "robot_type": "rover",
        "difficulty": "beginner",
        "shops": ["temu"],
        "languages": ["python"],
        "controllers": ["ESP32"],
        "controller_notes": "",
        "custom_pcb": False,
        "confirmed": True,
        "budget_max_usd": 120,
        "identification_rationale": "Matched rover keywords.",
        "identification_confidence": 0.8,
        "print_settings": {
            "material": "PETG",
            "infill_percent": 60,
            "price_per_gram_jod": 0.15,
        },
    }
    saved = await client.put(f"/api/v1/projects/{project['id']}/preferences", json=preferences)
    assert saved.status_code == 200, saved.text
    assert saved.json()["print_settings"]["material"] == "PETG"

    built = await client.post(f"/api/v1/projects/{project['id']}/build")
    assert built.status_code == 201, built.text
    body = built.json()

    mechanical = body["mechanical"]
    assert mechanical["selected_material"] == "PETG"
    assert mechanical["infill_percent"] == 60
    assert mechanical["custom_price_per_gram_jod"] == "0.15"
    selected = next(quote for quote in mechanical["material_quotes"] if quote["is_selected"])
    assert selected["material"] == "PETG"
    assert selected["price_per_gram_jod"] == "0.15"
    assert mechanical["print_price_jod"] == selected["total_jod"]
    assert round(float(body["cost"]["print_cost_jod"]), 2) == round(float(selected["total_jod"]), 2)
    assert any("PETG, 60% infill" in item["label"] for item in body["cost"]["line_items"])

    updated = await client.put(
        f"/api/v1/projects/{project['id']}/print-settings",
        json={"material": "TPU", "infill_percent": 20, "price_per_gram_jod": None},
    )
    assert updated.status_code == 200, updated.text
    refreshed = updated.json()
    refreshed_mechanical = refreshed["mechanical"]
    assert refreshed_mechanical["selected_material"] == "TPU"
    assert refreshed_mechanical["infill_percent"] == 20
    assert refreshed_mechanical["custom_price_per_gram_jod"] is None
    tpu = next(quote for quote in refreshed_mechanical["material_quotes"] if quote["is_selected"])
    assert tpu["price_per_gram_jod"] == "0.200"
    assert float(tpu["weight_g"]) < float(selected["weight_g"])
    assert round(float(refreshed["cost"]["print_cost_jod"]), 2) == round(float(tpu["total_jod"]), 2)

    preferences_after = await client.get(f"/api/v1/projects/{project['id']}/preferences")
    assert preferences_after.json()["print_settings"]["material"] == "TPU"
    assert preferences_after.json()["print_settings"]["infill_percent"] == 20


async def test_build_requires_confirmed_preferences(client: AsyncClient) -> None:
    project = await create_project(client)
    response = await client.post(f"/api/v1/projects/{project['id']}/build")
    assert response.status_code == 422
    assert "Confirm the guided flow" in response.json()["error"]["message"]
