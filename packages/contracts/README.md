# Albayraq contracts

Machine-readable contracts shared by the API, web app, agents, and external tools.

Everything in this directory is **generated** from the backend:

```bash
# from the repository root
make contracts
```

The command runs [`scripts/export_contracts.py`](../../scripts/export_contracts.py) from `apps/api`,
then regenerates `apps/web/src/lib/api-schema.ts` with `openapi-typescript`. CI regenerates the same
files and fails if the working tree changes, so never hand-edit them.

## Contents

```text
packages/contracts/
├── openapi.json                 Full OpenAPI 3.1 document for the HTTP API
└── schemas/
    ├── AgentRequest.schema.json
    ├── AgentResult.schema.json
    ├── SharedProjectContext.schema.json
    ├── ProjectContext.schema.json
    ├── RobotSpecificationDraft.schema.json
    ├── ComponentResearchOutput.schema.json
    ├── ElectricalPlan.schema.json
    ├── ProgrammingOutput.schema.json
    ├── MechanicalOutput.schema.json
    ├── CostEstimate.schema.json
    ├── PlannerInput.schema.json
    ├── ComponentResearchInput.schema.json
    ├── ElectricalInput.schema.json
    ├── ProgrammingInput.schema.json
    ├── MechanicalInput.schema.json
    └── CostInput.schema.json
```

All agent schemas are JSON Schema 2020-12 and reject unknown fields (`additionalProperties: false`).

## Consumers

### Web app

The OpenAPI document generates low-level TypeScript types:

```ts
import type { paths, components } from "@/lib/api-schema";

type Project = components["schemas"]["ProjectRead"];
```

Feature UI code uses the hand-written types in `src/lib/types.ts` where optionality or naming needs
to be modeled explicitly. The generated file remains the source of truth for route shapes.

### Python clients

```python
import json
from pathlib import Path

schema = json.loads(Path("packages/contracts/schemas/ElectricalPlan.schema.json").read_text())
# Feed schema["properties"] to a validator, code generator, or prompt builder.
```

The backend imports the original Pydantic models directly; the exported files are for external
consumers and documentation.

### Agent implementations

When an agent calls a model with structured output:

1. Load the output schema.
2. Ask the provider for JSON matching it.
3. Validate with the corresponding Pydantic model before returning an `AgentResult`.
4. On validation failure, return `failed` — do not apply a partial artifact.

## Changing a contract

1. Edit the Pydantic model in `apps/api/app/ai/contracts.py` (or an HTTP schema).
2. Add/adjust tests for the new field and its validation.
3. Run `make contracts`.
4. Review the diff. Treat schema removals/renames as breaking changes.
5. Commit the model change and generated files together.
6. Update [docs/ai-agents.md](../../docs/ai-agents.md) or [docs/api.md](../../docs/api.md) if the
   meaning changed.

OpenAPI changes are additive within `/api/v1`; breaking changes require a new major version or a
deprecation window. Agent schemas are versioned with the application and are not currently published
as a separate package.

## Verification

```bash
make contracts
git diff --exit-code packages/contracts apps/web/src/lib/api-schema.ts
```

The same check runs in the `contracts` CI job.
