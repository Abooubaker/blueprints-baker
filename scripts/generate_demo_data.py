"""Generate the static GitHub Pages demo fixtures.

The demo is built from the same deterministic engine as the API, so the wiring
diagram, exports, validation results, BOM, code bundles, 3D pricing, and
documentation shown on GitHub Pages are real engine output rather than
hand-written mock data. The generated files contain no credentials and no live
API responses.

Run from the repository root:

    python scripts/generate_demo_data.py
"""

from __future__ import annotations

import asyncio
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
    AgentRequest,
    BuildPreferences,
    ProjectContext,
    RobotSpecificationDraft,
    SharedProjectContext,
)
from app.ai.documentation import build_documentation  # noqa: E402
from app.ai.orchestrator import (  # noqa: E402
    PIPELINE_ORDER,
    AgentOrchestrator,
    build_agent_registry,
    get_agent_descriptors,
)
from app.ai.provider import MockProvider  # noqa: E402
from app.electrical.exporters import EXPORT_SPECS, export_artifact  # noqa: E402
from app.models.enums import (  # noqa: E402
    CodeLanguage,
    Difficulty,
    DriveType,
    ProjectStatus,
    RobotType,
    StoreName,
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
        payload_capacity_kg=Decimal("0.5"),
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


def _preferences() -> BuildPreferences:
    return BuildPreferences(
        description=(
            "An ESP32 obstacle-avoiding rover with ultrasonic distance sensing, "
            "a scanning servo, and a fused 2S LiPo power tree."
        ),
        robot_name="Patio Scout",
        robot_type=RobotType.OBSTACLE_AVOIDER,
        difficulty=Difficulty.INTERMEDIATE,
        shops=[
            StoreName.TEMU,
            StoreName.MIKROELECTRON,
            StoreName.WASLLEH,
            StoreName.AMAZON,
            StoreName.ALIEXPRESS,
            StoreName.GHANIMJO,
        ],
        languages=[
            CodeLanguage.PYTHON,
            CodeLanguage.CPP,
            CodeLanguage.C,
            CodeLanguage.VERILOG,
        ],
        controllers=["ESP32 DevKit"],
        controller_notes="Using an ESP32 DevKit already on the bench.",
        custom_pcb=False,
        confirmed=True,
        budget_max_usd=Decimal("150"),
        identification_rationale=(
            "Matched obstacle, ultrasonic, and rover keywords in the description."
        ),
        identification_confidence=0.86,
    )


def _agent_descriptors(provider: MockProvider) -> list[dict[str, Any]]:
    return [descriptor.model_dump(mode="json") for descriptor in get_agent_descriptors(provider)]


async def _run_pipeline(
    specification: RobotSpecificationDraft, preferences: BuildPreferences
) -> tuple[Any, Any, Any, Any, Any, Any]:
    provider = MockProvider("deterministic-v1")
    orchestrator = AgentOrchestrator(build_agent_registry(provider))
    context = ProjectContext(
        project_id=PROJECT_ID,
        project_name=preferences.robot_name,
        robot_type=preferences.robot_type,
        description=preferences.description,
        budget={"max_usd": preferences.budget_max_usd, "currency": "USD"},
        shared=SharedProjectContext(specification=specification),
    )
    parameters = {
        "preferred_suppliers": [store.value for store in preferences.shops],
        "languages": [language.value for language in preferences.languages],
        "controllers": preferences.controllers,
        "controller_notes": preferences.controller_notes,
        "custom_pcb": preferences.custom_pcb,
        "skill_level": preferences.difficulty.value,
    }
    result = await orchestrator.run(context, parameters=parameters)
    shared = result.context
    return (
        shared.specification,
        shared.component_research,
        shared.electrical,
        shared.programming,
        shared.mechanical,
        shared.cost,
    )


def _agent_runs(shared: tuple[Any, ...]) -> list[dict[str, Any]]:
    latencies = {
        "robot_planner": 24,
        "component_research": 31,
        "electrical_engineering": 46,
        "programming": 52,
        "mechanical_design": 39,
        "cost_estimation": 18,
    }
    payloads = {
        "robot_planner": shared[0],
        "component_research": shared[1],
        "electrical_engineering": shared[2],
        "programming": shared[3],
        "mechanical_design": shared[4],
        "cost_estimation": shared[5],
    }
    runs: list[dict[str, Any]] = []
    for agent in (name.value for name in PIPELINE_ORDER):
        payload = payloads.get(agent)
        runs.append(
            {
                "id": str(RUN_IDS[agent]),
                "project_id": str(PROJECT_ID),
                "agent": agent,
                "status": "succeeded",
                "provider": "mock",
                "model": "deterministic-v1",
                "summary": f"{agent.replace('_', ' ').title()} completed.",
                "output_payload": payload.model_dump(mode="json") if payload else None,
                "error_message": None,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_ms": latencies[agent],
                "started_at": GENERATED_AT,
                "completed_at": UPDATED_AT,
                "created_at": GENERATED_AT,
            }
        )
    return runs


def main() -> None:
    preferences = _preferences()
    specification, research, plan, programming, mechanical, cost = asyncio.run(
        _run_pipeline(_specification(), preferences)
    )
    assert research is not None and plan is not None
    assert programming is not None and mechanical is not None and cost is not None

    runs = _agent_runs((specification, research, plan, programming, mechanical, cost))
    catalog = {
        "provider": "mock",
        "model": "deterministic-v1",
        "agents": _agent_descriptors(MockProvider("deterministic-v1")),
    }

    documentation = build_documentation(
        project_name=preferences.robot_name,
        description=preferences.description,
        preferences=preferences,
        identification=None,
        specification=specification,
        research=research,
        electrical=plan,
        programming=programming,
        mechanical=mechanical,
        cost=cost,
    )

    project = {
        "id": str(PROJECT_ID),
        "name": preferences.robot_name,
        "slug": "patio-scout",
        "description": preferences.description,
        "robot_type": preferences.robot_type.value,
        "status": ProjectStatus.READY.value,
        "difficulty": preferences.difficulty.value,
        "budget_min_usd": 80,
        "budget_max_usd": float(preferences.budget_max_usd or 150),
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
            "payload_capacity_kg": float(specification.payload_capacity_kg or 0),
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

    build = {
        "project_id": str(PROJECT_ID),
        "project_name": project["name"],
        "status": "ready",
        "generated_at": UPDATED_AT,
        "preferences": preferences.model_dump(mode="json"),
        "identification": {
            "proposed_name": project["name"],
            "robot_type": preferences.robot_type.value,
            "confidence": preferences.identification_confidence,
            "rationale": preferences.identification_rationale,
            "suggested_platform": TargetPlatform.ESP32.value,
            "suggested_difficulty": preferences.difficulty.value,
            "key_requirements": specification.requirements,
            "needs_confirmation": False,
        },
        "specification": specification.model_dump(mode="json"),
        "research": research.model_dump(mode="json"),
        "electrical": plan.model_dump(mode="json"),
        "programming": programming.model_dump(mode="json"),
        "mechanical": mechanical.model_dump(mode="json"),
        "cost": cost.model_dump(mode="json"),
        "documentation": documentation.model_dump(mode="json"),
        "missing": [],
        "warnings": [],
    }

    orchestration = {
        "project_id": str(PROJECT_ID),
        "status": "succeeded",
        "runs": runs,
        "shared_context": {
            "specification": specification.model_dump(mode="json"),
            "component_research": research.model_dump(mode="json"),
            "electrical": plan.model_dump(mode="json"),
            "programming": programming.model_dump(mode="json"),
            "mechanical": mechanical.model_dump(mode="json"),
            "cost": cost.model_dump(mode="json"),
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
    _write_json(WEB_ROOT / "src" / "lib" / "demo" / "build.json", build)
    _write_json(WEB_ROOT / "src" / "lib" / "demo" / "orchestration.json", orchestration)

    export_dir = WEB_ROOT / "public" / "demo" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    expected_files = {spec.filename for spec in EXPORT_SPECS.values()} | {"manifest.json"}
    for stale in export_dir.iterdir():
        if stale.is_file() and stale.name not in expected_files:
            stale.unlink()
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
        "offers": len(research.bill_of_materials[0].selection.offers),
        "languages": [bundle.language.value for bundle in programming.bundles],
        "print_quotes": len(mechanical.material_quotes),
        "docs": [doc.path for doc in documentation.files],
        "exports": sorted(spec.filename for spec in EXPORT_SPECS.values()),
        "generated_at": UPDATED_AT,
    }
    _write_json(export_dir / "manifest.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
