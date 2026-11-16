#!/usr/bin/env python3
"""Export machine-readable contracts (OpenAPI + agent JSON Schemas).

Run from ``apps/api``:

    uv run python ../../scripts/export_contracts.py

The generated files are committed so the frontend and documentation stay in
sync with the backend without requiring a running server.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1] / "apps" / "api"
REPO_ROOT = API_DIR.parents[1]
CONTRACTS_DIR = REPO_ROOT / "packages" / "contracts"

sys.path.insert(0, str(API_DIR))

from app.ai import contracts as agent_contracts  # noqa: E402
from app.main import app  # noqa: E402

AGENT_MODELS = [
    "AgentRequest",
    "AgentResult",
    "RobotSpecificationDraft",
    "ComponentResearchOutput",
    "ElectricalPlan",
    "ProgrammingOutput",
    "MechanicalOutput",
    "CostEstimate",
    "SharedProjectContext",
    "ProjectContext",
    "PlannerInput",
    "ComponentResearchInput",
    "ElectricalInput",
    "ProgrammingInput",
    "MechanicalInput",
    "CostInput",
]


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(REPO_ROOT)}")


def main() -> None:
    write_json(CONTRACTS_DIR / "openapi.json", app.openapi())

    schemas_dir = CONTRACTS_DIR / "schemas"
    for model_name in AGENT_MODELS:
        model = getattr(agent_contracts, model_name)
        write_json(
            schemas_dir / f"{model_name}.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                **model.model_json_schema(),
            },
        )


if __name__ == "__main__":
    main()
