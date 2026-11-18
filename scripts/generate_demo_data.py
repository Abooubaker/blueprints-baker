"""Generate the static GitHub Pages demo fixtures.

The demo is built from the same deterministic engine as the API, so the wiring
diagram, exports, validation results, and BOM shown on GitHub Pages are real
engine output rather than hand-written mock data. The generated files contain no
credentials and no live API responses.

Run from the repository root:

    python scripts/generate_demo_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
WEB_ROOT = ROOT / "apps" / "web"
sys.path.insert(0, str(API_ROOT))

from app.ai.contracts import (  # noqa: E402
    BillOfMaterialsItem,
    ComponentCandidate,
    ComponentResearchOutput,
    ElectricalPlan,
    RobotSpecificationDraft,
)
from app.electrical.engine import build_electrical_plan  # noqa: E402
from app.electrical.exporters import EXPORT_SPECS, export_artifact  # noqa: E402
from app.electrical.library import (  # noqa: E402
    COMPONENT_LIBRARY,
    build_reference_bom,
)
from app.models.enums import (  # noqa: E402
    Difficulty,
    DriveType,
    ProjectStatus,
    RobotType,
    TargetPlatform,
)

PROJECT_ID = UUID("11111111-1111-4111-8111-111111111111")
RUN_IDS = {
    "robot_planner": UUID("a0000000-0000-4000-8000-000000000001"),
    "component_research": UUID("a0000000-0000-4000-8000-000000000002"),
    "electrical_engineering": UUID("a0000000-0000-4000-8000-000000000003"),
    "programming": UUID("a0000000-0000-4000-8000-000000000004"),
    "mechanical_design": UUID("a0000000-0000-4000-8000-000000000005"),
    "cost_estimation": UUID("a0000000-0000-4000-8000-000000000006"),
}
GENERATED_AT = "2026-11-18T09:30:00Z"
UPDATED_AT = "2026-11-18T09:31:00Z"


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _specification() -> RobotSpecificationDraft:
    return RobotSpecificationDraft(
        summary=(
            "A compact ESP32 obstacle-avoiding rover that scans ahead with an HC-SR04, "
            "steers around furniture, and reports distance over Wi-Fi."
        ),
        use_case="Indoor patio and hallway inspection demonstrations.",
        robot_type=RobotType.OBSTACLE_AVOIDER,
        difficulty=Difficulty.INTERMEDIATE,
        target_platform=TargetPlatform.ESP32,
        drive_type=DriveType.DIFFERENTIAL,
        environment="indoor",
        power_source="2S LiPo (7.4 V) with a regulated 5 V rail",
        payload_capacity_kg=0.5,
        requirements=[
            "Detect obstacles before contact",
            "Turn or stop without losing control",
            "Stream distance readings over Wi-Fi",
        ],
        constraints=[
            "Total component cost must stay below $150.00.",
            "All electronics must run from a single 2S LiPo pack.",
        ],
        success_criteria=[
            "All electrical validation checks pass before power-on",
            "The rover crosses a 3 m hallway without touching an obstacle",
        ],
        open_questions=[],
        confidence=0.86,
    )


def _research() -> ComponentResearchOutput:
    parts, unresolved = build_reference_bom(
        robot_type=RobotType.OBSTACLE_AVOIDER,
        target_platform=TargetPlatform.ESP32.value,
        difficulty=Difficulty.INTERMEDIATE.value,
        drive_type=DriveType.DIFFERENTIAL.value,
        budget_max_usd=None,
    )
    items: list[BillOfMaterialsItem] = []
    total = 0
    for part in parts:
        profile = part.profile
        total += int(profile.price_usd * 100) * part.quantity
        items.append(
            BillOfMaterialsItem(
                role=part.role,
                category=profile.category.value,
                quantity=part.quantity,
                required=True,
                selection=ComponentCandidate(
                    name=profile.name,
                    manufacturer=profile.manufacturer,
                    model_number=profile.model_number,
                    category=profile.category.value,
                    specs={
                        "library_key": profile.key,
                        "logic_voltage_v": profile.logic_voltage_v,
                        "supply_min_v": profile.supply_min_v,
                        "supply_max_v": profile.supply_max_v,
                        "typical_current_ma": profile.current_ma_typical,
                        "peak_current_ma": profile.current_ma_peak,
                        "interfaces": list(profile.interfaces),
                        "pins": [pin.name for pin in profile.pins],
                        "electrical_notes": profile.notes,
                    },
                    price_usd=profile.price_usd,
                    supplier="RoboCraft curated library",
                    supplier_url=None,
                    availability="in_stock",
                    compatibility_notes=[profile.notes] if profile.notes else [],
                    score=0.9,
                ),
                rationale=part.rationale,
            )
        )
    return ComponentResearchOutput(
        bill_of_materials=items,
        unresolved_requirements=unresolved,
        compatibility_notes=[
            f"Controller: {COMPONENT_LIBRARY['esp32_devkit'].name}",
            "All selected parts are in the curated electrical library, so pin-level "
            "wiring can be generated.",
            "Prices are planning estimates in USD, not live supplier quotes.",
        ],
        total_estimated_usd=f"{total // 100}.{total % 100:02d}",
        sources=["RoboCraft curated component library v1.0"],
    )


def _agent_descriptor(
    name: str,
    display_name: str,
    description: str,
    status: str,
    depends_on: list[str],
    input_schema: str,
    output_schema: str,
    milestone: str,
    owner_area: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "display_name": display_name,
        "description": description,
        "status": status,
        "depends_on": depends_on,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "milestone": milestone,
        "owner_area": owner_area,
    }


def _agent_runs() -> list[dict[str, Any]]:
    definitions = [
        (
            "robot_planner",
            "succeeded",
            "Robot Planner completed.",
            None,
            24,
        ),
        (
            "component_research",
            "succeeded",
            "Component Research completed.",
            None,
            31,
        ),
        (
            "electrical_engineering",
            "succeeded",
            "Electrical Engineering completed.",
            None,
            46,
        ),
        (
            "programming",
            "not_implemented",
            "Programming is a foundation placeholder.",
            "Programming is not implemented yet. It will be delivered in milestone M6.",
            2,
        ),
        (
            "mechanical_design",
            "not_implemented",
            "Mechanical Design is a foundation placeholder.",
            "Mechanical Design is not implemented yet. It will be delivered in milestone M7.",
            2,
        ),
        (
            "cost_estimation",
            "not_implemented",
            "Cost Estimation is a foundation placeholder.",
            "Cost Estimation is not implemented yet. It will be delivered in milestone M8.",
            2,
        ),
    ]
    runs: list[dict[str, Any]] = []
    for agent, status, summary, error, latency in definitions:
        runs.append(
            {
                "id": str(RUN_IDS[agent]),
                "project_id": str(PROJECT_ID),
                "agent": agent,
                "status": status,
                "provider": "mock",
                "model": "deterministic-v1",
                "summary": summary,
                "output_payload": None,
                "error_message": error,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_ms": latency,
                "started_at": GENERATED_AT,
                "completed_at": UPDATED_AT if status == "succeeded" else GENERATED_AT,
                "created_at": GENERATED_AT,
            }
        )
    return runs


def main() -> None:
    specification = _specification()
    research = _research()
    plan = build_electrical_plan(specification, research)
    runs = _agent_runs()

    catalog = {
        "provider": "mock",
        "model": "deterministic-v1",
        "agents": [
            _agent_descriptor(
                "robot_planner",
                "Robot Planner",
                "Turns a plain-language robot idea into a structured specification.",
                "available",
                [],
                "PlannerInput",
                "RobotSpecificationDraft",
                "M3",
                "Robotics / Systems Engineering",
            ),
            _agent_descriptor(
                "component_research",
                "Component Research",
                "Selects a compatible bill of materials for the robot archetype.",
                "available",
                ["robot_planner"],
                "ComponentResearchInput",
                "ComponentResearchOutput",
                "M4",
                "Robotics / Hardware Engineering",
            ),
            _agent_descriptor(
                "electrical_engineering",
                "Electrical Engineering",
                "Creates pin maps, nets, power budgets, and validates the wiring.",
                "available",
                ["robot_planner", "component_research"],
                "ElectricalInput",
                "ElectricalPlan",
                "M5",
                "Robotics / Electrical Engineering",
            ),
            _agent_descriptor(
                "programming",
                "Programming",
                "Generates firmware for the selected hardware.",
                "placeholder",
                ["robot_planner", "component_research", "electrical_engineering"],
                "ProgrammingInput",
                "ProgrammingOutput",
                "M6",
                "Robotics / Software Engineering",
            ),
            _agent_descriptor(
                "mechanical_design",
                "Mechanical Design",
                "Plans the chassis, mounts, and assembly order.",
                "placeholder",
                ["robot_planner", "component_research"],
                "MechanicalInput",
                "MechanicalOutput",
                "M7",
                "Robotics / Mechanical Engineering",
            ),
            _agent_descriptor(
                "cost_estimation",
                "Cost Estimation",
                "Builds the line-item budget and alternatives.",
                "placeholder",
                ["robot_planner", "component_research"],
                "CostInput",
                "CostEstimate",
                "M8",
                "Robotics / Product Engineering",
            ),
        ],
    }

    project = {
        "id": str(PROJECT_ID),
        "name": "Patio Scout",
        "slug": "patio-scout",
        "description": (
            "An ESP32 obstacle-avoiding rover with ultrasonic distance sensing, "
            "a scanning servo, and a fused 2S LiPo power tree."
        ),
        "robot_type": "obstacle_avoider",
        "status": ProjectStatus.PLANNING.value,
        "difficulty": "intermediate",
        "budget_min_usd": 80,
        "budget_max_usd": 150,
        "owner_id": None,
        "specification": {
            "id": "22222222-2222-4222-8222-222222222222",
            "project_id": str(PROJECT_ID),
            "summary": specification.summary,
            "use_case": specification.use_case,
            "environment": specification.environment,
            "target_platform": specification.target_platform.value,
            "drive_type": specification.drive_type.value,
            "power_source": specification.power_source,
            "payload_capacity_kg": specification.payload_capacity_kg,
            "dimensions": specification.dimensions.model_dump(),
            "requirements": specification.requirements,
            "constraints": specification.constraints,
            "status": "generated",
            "version": 2,
            "created_at": GENERATED_AT,
            "updated_at": UPDATED_AT,
        },
        "created_at": GENERATED_AT,
        "updated_at": UPDATED_AT,
    }

    export_formats = [
        {
            "format": spec.format,
            "label": spec.label,
            "filename": spec.filename,
            "media_type": spec.media_type,
            "description": spec.description,
        }
        for spec in EXPORT_SPECS.values()
    ]
    artifact = {
        "project_id": str(PROJECT_ID),
        "project_name": project["name"],
        "agent_run_id": str(RUN_IDS["electrical_engineering"]),
        "generated_at": UPDATED_AT,
        "plan": plan.model_dump(mode="json"),
        "bom": research.model_dump(mode="json"),
        "total_estimated_usd": float(research.total_estimated_usd or 0),
        "export_formats": export_formats,
    }

    orchestration = {
        "project_id": str(PROJECT_ID),
        "status": "not_implemented",
        "runs": runs,
        "shared_context": {
            "specification": specification.model_dump(mode="json"),
            "component_research": research.model_dump(mode="json"),
            "electrical": plan.model_dump(mode="json"),
            "programming": None,
            "mechanical": None,
            "cost": None,
            "artifacts": {},
            "notes": [],
        },
        "provider": "mock",
        "model": "deterministic-v1",
    }

    _write_json(WEB_ROOT / "src" / "lib" / "demo" / "project.json", project)
    _write_json(WEB_ROOT / "src" / "lib" / "demo" / "agent-runs.json", runs)
    _write_json(WEB_ROOT / "src" / "lib" / "demo" / "agent-catalog.json", catalog)
    _write_json(WEB_ROOT / "src" / "lib" / "demo" / "electrical.json", artifact)
    _write_json(WEB_ROOT / "src" / "lib" / "demo" / "orchestration.json", orchestration)

    export_dir = WEB_ROOT / "public" / "demo" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    for fmt, spec in EXPORT_SPECS.items():
        content = export_artifact(
            fmt,
            plan,
            research,
            project_name=project["name"],
        ).content
        (export_dir / spec.filename).write_text(content, encoding="utf-8")

    summary = {
        "project_id": str(PROJECT_ID),
        "nodes": len(plan.nodes),
        "connections": len(plan.connections),
        "nets": len({connection.net for connection in plan.connections}),
        "issues": [issue.code for issue in plan.issues],
        "exports": sorted(spec.filename for spec in EXPORT_SPECS.values()),
        "generated_at": UPDATED_AT,
    }
    _write_json(export_dir / "manifest.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
