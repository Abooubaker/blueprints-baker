"""Electrical plan, validation, and export behaviour."""

from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET

from httpx import AsyncClient

from tests.test_projects import create_project


async def generate_electrical(client: AsyncClient, **overrides: object) -> dict[str, object]:
    project = await create_project(client, **overrides)
    response = await client.post(f"/api/v1/projects/{project['id']}/electrical")
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["agent_run_id"]
    return body


async def test_electrical_plan_requires_generation_first(client: AsyncClient) -> None:
    project = await create_project(client)
    response = await client.get(f"/api/v1/projects/{project['id']}/electrical")
    assert response.status_code == 404
    export = await client.get(f"/api/v1/projects/{project['id']}/electrical/export/wiring-csv")
    assert export.status_code == 404


async def test_generate_electrical_plan_has_real_nets(client: AsyncClient) -> None:
    artifact = await generate_electrical(client)
    plan = artifact["plan"]
    assert plan["library_version"]
    assert {node["kind"] for node in plan["nodes"]} >= {"controller", "power", "motor", "driver"}
    assert len(plan["connections"]) >= 15
    assert {"GND", "VBAT", "5V_CTRL"} <= {rail["name"] for rail in plan["power_rails"]}
    assert plan["pin_map"]
    assert artifact["bom"]["bill_of_materials"]
    assert artifact["total_estimated_usd"] > 0

    # No blocking errors for the curated line-follower reference design.
    errors = [issue for issue in plan["issues"] if issue["severity"] == "error"]
    assert errors == []
    codes = {issue["code"] for issue in plan["issues"]}
    assert "motor_overvoltage" in codes
    assert any("Common ground verified" in check for check in plan["safety_checks"])
    assert any("No physical pin" in check for check in plan["safety_checks"])
    assert plan["wiring_steps"]
    assert plan["power_budget"]["estimated_runtime_min"] > 0

    # The artifact is retrievable and stable until regenerated.
    fetched = await client.get(f"/api/v1/projects/{artifact['project_id']}/electrical")
    assert fetched.status_code == 200
    assert fetched.json()["agent_run_id"] == artifact["agent_run_id"]
    assert len(fetched.json()["export_formats"]) == 6


async def test_wiring_csv_and_bom_csv_are_parsable(client: AsyncClient) -> None:
    artifact = await generate_electrical(client)
    base = f"/api/v1/projects/{artifact['project_id']}/electrical/export"

    wiring = await client.get(f"{base}/wiring-csv")
    assert wiring.status_code == 200
    assert wiring.headers["content-type"].startswith("text/csv")
    assert 'filename="wiring.csv"' in wiring.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(wiring.text)))
    assert len(rows) == len(artifact["plan"]["connections"])
    assert {"net", "from_ref", "from_pin", "to_ref", "to_pin", "wire_color"} <= set(rows[0])

    bom = await client.get(f"{base}/bom-csv")
    assert bom.status_code == 200
    bom_rows = list(csv.DictReader(io.StringIO(bom.text)))
    assert len(bom_rows) == len(artifact["bom"]["bill_of_materials"])
    assert all(row["unit_price_usd"] for row in bom_rows)


async def test_svg_netlist_and_markdown_exports_are_well_formed(client: AsyncClient) -> None:
    artifact = await generate_electrical(client)
    base = f"/api/v1/projects/{artifact['project_id']}/electrical/export"

    svg = await client.get(f"{base}/svg")
    assert svg.status_code == 200
    assert svg.headers["content-type"].startswith("image/svg+xml")
    root = ET.fromstring(svg.text)
    assert root.tag.endswith("svg")

    netlist = await client.get(f"{base}/kicad-netlist")
    assert netlist.status_code == 200
    text = netlist.text
    assert text.startswith('(export (version "E")')
    assert "(components" in text
    assert "(nets" in text
    assert text.count("(") == text.count(")")

    guide = await client.get(f"{base}/markdown")
    assert guide.status_code == 200
    assert guide.headers["content-type"].startswith("text/markdown")
    assert "wiring guide" in guide.text
    assert "## Pin map" in guide.text
    assert "## Wiring order" in guide.text

    raw = await client.get(f"{base}/json")
    assert raw.status_code == 200
    payload = json.loads(raw.text)
    assert payload["library_version"] == artifact["plan"]["library_version"]


async def test_esp32_rover_flags_five_volt_sensor_on_three_volt_logic(
    client: AsyncClient,
) -> None:
    artifact = await generate_electrical(
        client,
        name="ESP32 Obstacle Rover",
        robot_type="obstacle_avoider",
        target_platform="esp32",
        requirements=["Avoid obstacles", "Report distance over serial"],
    )
    plan = artifact["plan"]
    node_labels = " ".join(node["label"] for node in plan["nodes"])
    assert "ESP32" in node_labels
    assert "HC-SR04" in node_labels
    issues = {(issue["code"], issue["severity"]) for issue in plan["issues"]}
    assert ("logic_level_mismatch", "warning") in issues
    mismatch = next(issue for issue in plan["issues"] if issue["code"] == "logic_level_mismatch")
    assert "level shifter" in mismatch["remediation"]
