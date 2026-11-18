# API reference

Base URL (local): `http://localhost:8000` · All application endpoints are versioned under
`/api/v1`. Health probes are intentionally unversioned.

Interactive documentation is available at `/docs` (Swagger UI), `/redoc`, and `/openapi.json`
outside production. The machine-readable document is committed at
[`packages/contracts/openapi.json`](../packages/contracts/openapi.json).

## Conventions

| Topic | Behavior |
| --- | --- |
| Content type | JSON (`application/json`) for all bodies except 204 responses |
| IDs | UUID v4 strings |
| Timestamps | ISO 8601 with UTC offset |
| Money | Decimal values serialized as JSON numbers in request/response; USD by default |
| Pagination | `limit` (1–100, default 20) and `offset` (0–10,000, default 0) |
| Request ID | Send `X-Request-ID` to correlate logs; the response always includes one |
| Auth | None yet. Endpoints are public in the foundation release. |

### Success envelope

Single resources are returned directly. Collections use a page envelope:

```json
{
  "items": [],
  "meta": { "total": 0, "limit": 20, "offset": 0 }
}
```

### Error envelope

Every handled error has the same shape:

```json
{
  "error": {
    "code": "not_found",
    "message": "Robot project 7f4c… was not found.",
    "details": null,
    "request_id": "1b5f0f0e-6a92-4bd3-84a7-2b2f0e7a9c11"
  }
}
```

| Status | Codes | Meaning |
| --- | --- | --- |
| 400 | `bad_request` | Invalid use-case input |
| 404 | `not_found` | Project/specification does not exist |
| 405 | `method_not_allowed` | Wrong HTTP method |
| 409 | `conflict`, `invalid_state` | Uniqueness or lifecycle violation |
| 422 | `validation_error` | Payload failed Pydantic validation; `details` lists field locations |
| 503 | `database_unavailable` | Database connection/query failure |
| 500 | `internal_error` | Unexpected failure; details are logged, not returned |

Validation detail entries look like:

```json
{ "location": ["body", "name"], "message": "String should have at least 1 character", "type": "string_too_short" }
```

## Endpoint map

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Service discovery metadata |
| GET | `/health` | Liveness probe (no database access) |
| GET | `/health/ready` | Readiness probe (runs `SELECT 1`) |
| GET | `/api/v1/projects` | List/filter projects |
| POST | `/api/v1/projects` | Create a project + draft specification |
| GET | `/api/v1/projects/{project_id}` | Get a project with its specification |
| PATCH | `/api/v1/projects/{project_id}` | Update project metadata/status |
| DELETE | `/api/v1/projects/{project_id}` | Delete a project and dependents |
| GET | `/api/v1/projects/{project_id}/specification` | Read the specification |
| PUT | `/api/v1/projects/{project_id}/specification` | Replace editable specification fields |
| POST | `/api/v1/projects/{project_id}/agent-runs` | Run agents and persist the audit trail |
| GET | `/api/v1/projects/{project_id}/agent-runs` | List agent executions (newest first) |
| GET | `/api/v1/agents` | Agent catalog with provider and dependencies |
| GET | `/api/v1/components` | List/filter the component catalog |
| POST | `/api/v1/projects/{project_id}/electrical` | Generate and persist the electrical plan |
| GET | `/api/v1/projects/{project_id}/electrical` | Read the latest electrical plan |
| GET | `/api/v1/projects/{project_id}/electrical/export/{format}` | Download an export |
| POST | `/api/v1/intent/identify` | Identify a robot from a plain-language description |
| GET | `/api/v1/projects/{project_id}/preferences` | Read the saved guided-flow answers |
| PUT | `/api/v1/projects/{project_id}/preferences` | Save stores, languages, controllers, PCB choice |
| POST | `/api/v1/projects/{project_id}/build` | Run the full build and persist the artifact |
| GET | `/api/v1/projects/{project_id}/build` | Read the latest build artifact |
| PUT | `/api/v1/projects/{project_id}/print-settings` | Change print material, infill, or JOD/g price |
| GET | `/api/v1/projects/{project_id}/mechanical/stl` | Download the generated reference STL |

## Health

```bash
curl http://localhost:8000/health/ready
```

```json
{
  "status": "ok",
  "service": "Albayraq API",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-11-16T22:00:00Z",
  "checks": { "database": { "status": "ok" } }
}
```

`/health` does not touch the database and is safe for liveness probes. `/health/ready` returns 503
through the database error handler if PostgreSQL is unreachable.

## Projects

### List projects

`GET /api/v1/projects?limit=20&offset=0&status=draft&robot_type=rover&search=patio`

Filters are optional and combine with AND. `search` matches name or description,
case-insensitively. Results are ordered by `updated_at` descending.

```json
{
  "items": [
    {
      "id": "bef286cd-2987-4032-b7ca-c4fc99046c16",
      "name": "Science Fair Line Follower",
      "slug": "science-fair-line-follower",
      "description": "Follows a black tape track and stops at obstacles.",
      "robot_type": "line_follower",
      "status": "draft",
      "difficulty": "beginner",
      "budget_max_usd": 60.0,
      "created_at": "2026-11-16T21:10:00Z",
      "updated_at": "2026-11-16T21:10:00Z"
    }
  ],
  "meta": { "total": 1, "limit": 20, "offset": 0 }
}
```

### Create a project

`POST /api/v1/projects` → `201 Created`

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | string | yes | 1–120 chars, trimmed |
| `description` | string | no | ≤5000 chars |
| `robot_type` | enum | no | Default `custom` |
| `difficulty` | enum | no | `beginner`, `intermediate`, `advanced` |
| `target_platform` | enum | no | `arduino`, `esp32`, `raspberry_pi`, `other`, `undecided` |
| `budget_min_usd`, `budget_max_usd` | number | no | 0–1,000,000; max must be ≥ min |
| `requirements`, `constraints` | string[] | no | ≤100 items each |

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Science Fair Line Follower",
    "description": "Follows black tape and stops at obstacles.",
    "robot_type": "line_follower",
    "difficulty": "beginner",
    "target_platform": "arduino",
    "budget_max_usd": 60,
    "requirements": ["Runs 30 minutes on AA batteries"]
  }'
```

The response is a `ProjectRead` including the bootstrapped draft specification:

```json
{
  "id": "bef286cd-2987-4032-b7ca-c4fc99046c16",
  "owner_id": null,
  "name": "Science Fair Line Follower",
  "slug": "science-fair-line-follower",
  "description": "Follows black tape and stops at obstacles.",
  "robot_type": "line_follower",
  "status": "draft",
  "difficulty": "beginner",
  "budget_min_usd": null,
  "budget_max_usd": 60.0,
  "specification": {
    "id": "5d0b…",
    "project_id": "bef286cd-2987-4032-b7ca-c4fc99046c16",
    "summary": "Follows black tape and stops at obstacles.",
    "use_case": "Follows black tape and stops at obstacles.",
    "environment": "indoor",
    "target_platform": "arduino",
    "drive_type": "none",
    "power_source": "",
    "payload_capacity_kg": null,
    "dimensions": {},
    "requirements": ["Runs 30 minutes on AA batteries"],
    "constraints": [],
    "status": "draft",
    "version": 1,
    "created_at": "2026-11-16T21:10:00Z",
    "updated_at": "2026-11-16T21:10:00Z"
  },
  "created_at": "2026-11-16T21:10:00Z",
  "updated_at": "2026-11-16T21:10:00Z"
}
```

Slugs are derived from the name (ASCII, lower-case, hyphenated) and made unique with `-2`, `-3`, …
suffixes.

### Get / update / delete

```bash
curl http://localhost:8000/api/v1/projects/<id>

curl -X PATCH http://localhost:8000/api/v1/projects/<id> \
  -H 'Content-Type: application/json' \
  -d '{"status": "planning", "budget_max_usd": 75}'

curl -i -X DELETE http://localhost:8000/api/v1/projects/<id>   # 204 No Content
```

`PATCH` accepts only the mutable subset: `name`, `description`, `status`, `difficulty`,
`budget_min_usd`, `budget_max_usd`. `robot_type` and `target_platform` are fixed after creation
(target platform is edited through the specification). Deleting a project cascades to its
specification, configuration, component selections, and agent runs.

## Specification

`GET` returns the specification. `PUT` is a **full replacement** of editable fields; omitted fields
reset to their defaults. Successful updates increment `version`. `status` accepts `draft`,
`generated`, or `approved`.

```bash
curl -X PUT http://localhost:8000/api/v1/projects/<id>/specification \
  -H 'Content-Type: application/json' \
  -d '{
    "summary": "Beginner line follower with obstacle stop.",
    "use_case": "Classroom science fair demo",
    "environment": "indoor",
    "target_platform": "arduino",
    "drive_type": "differential",
    "power_source": "4x AA",
    "dimensions": {"length_mm": 150, "width_mm": 110, "height_mm": 60},
    "requirements": ["Follow 19 mm black tape", "Stop within 10 cm of an obstacle"],
    "constraints": ["Budget under $60"],
    "status": "approved"
  }'
```

## Agents

### Catalog

```bash
curl http://localhost:8000/api/v1/agents
```

```json
{
  "provider": "mock",
  "model": "placeholder",
  "agents": [
    {
      "name": "robot_planner",
      "display_name": "Robot Planner",
      "description": "Turns a natural-language idea into a structured, buildable specification.",
      "status": "available",
      "depends_on": [],
      "input_schema": "PlannerInput",
      "output_schema": "RobotSpecificationDraft",
      "milestone": "M3",
      "owner_area": "AI"
    }
  ]
}
```

### Run agents

`POST /api/v1/projects/{project_id}/agent-runs` → `201 Created`

```json
{ "agents": ["robot_planner"], "parameters": {} }
```

- Omit `agents` to request the full pipeline.
- Requested agents are expanded with transitive dependencies and executed in pipeline order.
- Every agent is implemented and deterministic; the catalog reports `available`.
- A failed dependency marks dependents `skipped` but does not abort independent branches.
- `POST /api/v1/projects/{project_id}/build` is the higher-level call that runs the full pipeline
  and assembles the artifact the web workspace renders.

Response (`OrchestrationRead`):

```json
{
  "project_id": "bef286cd-2987-4032-b7ca-c4fc99046c16",
  "status": "succeeded",
  "runs": [
    {
      "id": "b0f4…",
      "project_id": "bef286cd-2987-4032-b7ca-c4fc99046c16",
      "agent": "robot_planner",
      "status": "succeeded",
      "provider": "mock",
      "model": "placeholder",
      "summary": "Specification generated deterministically from the project brief.",
      "output_payload": { "summary": "…", "confidence": 0.9 },
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "latency_ms": 0,
      "started_at": "2026-11-16T21:12:00Z",
      "completed_at": "2026-11-16T21:12:00Z",
      "created_at": "2026-11-16T21:12:00Z"
    }
  ],
  "shared_context": {
    "specification": { "summary": "…", "confidence": 0.9 },
    "component_research": null,
    "electrical": null,
    "programming": null,
    "mechanical": null,
    "cost": null,
    "artifacts": {},
    "notes": []
  },
  "provider": "mock",
  "model": "placeholder"
}
```

### Audit history

`GET /api/v1/projects/{project_id}/agent-runs?limit=50&offset=0` returns a page of `AgentRunRead`
records, newest first.

## Components

`GET /api/v1/components?category=sensor&search=ultrasonic&limit=20`

Returns active catalog entries. `category` is one of `controller`, `motor`, `motor_driver`, `sensor`,
`power`, `chassis`, `wheel`, `actuator`, `communication`, `display`, `wiring`, `tool`, `other`.
There is no seed data and no write endpoint yet (M4).

## Electrical

`POST /api/v1/projects/{project_id}/electrical` runs planner → component research → electrical and
persists an `ElectricalArtifactRead` (`201`). It is deterministic, so re-running produces the same
plan. `GET` returns the latest artifact (`404` before the first run).

```json
{
  "project_id": "…",
  "project_name": "Science Fair Line Follower",
  "agent_run_id": "…",
  "generated_at": "2026-11-18T09:30:00Z",
  "plan": {
    "nodes": [],
    "connections": [],
    "pinout": [],
    "pin_map": {},
    "power_budget": {},
    "power_rails": [],
    "issues": [],
    "safety_checks": [],
    "wiring_steps": [],
    "library_version": "1.0"
  },
  "bom": {},
  "total_estimated_usd": 67.4,
  "export_formats": []
}
```

Exports are attachments with a fixed filename:

| `format` | Filename |
| --- | --- |
| `json` | `electrical-plan.json` |
| `wiring-csv` | `wiring.csv` |
| `pinout-csv` | `pinout.csv` |
| `bom-csv` | `bill-of-materials.csv` |
| `kicad-netlist` | `albayraq.net` |
| `kicad-schematic` | `albayraq.kicad_sch` |
| `svg` | `wiring.svg` |
| `markdown` | `build-guide.md` |

The `.net` export is a KiCad S-expression netlist and the `.kicad_sch` export is a KiCad 8
schematic with embedded symbols and a labelled wire on every physical pin. EasyEDA Pro and
KiCad can import both.
See [electrical.md](electrical.md) for validation rules and the full contract.

## Guided build

The guided flow is four calls: identify → save preferences → generate build → read the artifact.
Everything the web workspace renders comes from the last build response. Print settings can be
changed afterward without rerunning the electrical, programming, or component stages.

### Identify a robot

`POST /api/v1/intent/identify`

```json
{
  "description": "A small four-wheel rover that avoids obstacles and streams distance over Wi-Fi."
}
```

```json
{
  "proposed_name": "Patio Scout",
  "robot_type": "rover",
  "confidence": 0.72,
  "rationale": "Four wheels and obstacle avoidance describe a rover…",
  "key_requirements": ["Wi-Fi telemetry", "Obstacle avoidance"],
  "suggested_difficulty": "beginner",
  "suggested_platform": "esp32"
}
```

The identification is deterministic and offline; it proposes a name and type for the user to
confirm or correct. Nothing is persisted by this call.

### Save preferences

`PUT /api/v1/projects/{project_id}/preferences` replaces the saved answers:

```json
{
  "description": "…",
  "robot_name": "Patio Scout",
  "robot_type": "rover",
  "difficulty": "beginner",
  "shops": ["temu", "mikroelectron", "waslleh", "amazon"],
  "languages": ["python", "cpp", "c"],
  "controllers": ["ESP32"],
  "controller_notes": "I have a spare L298N driver",
  "custom_pcb": false,
  "confirmed": true,
  "budget_max_usd": 80,
  "identification_rationale": "…",
  "identification_confidence": 0.72,
  "print_settings": {
    "material": "PLA",
    "infill_percent": 35,
    "price_per_gram_jod": null
  }
}
```

Preferences are stored in `ProjectConfiguration.configuration` so every later agent reads the same
confirmed answers. `GET` returns the saved values or the project defaults.

### Print settings

`PUT /api/v1/projects/{project_id}/print-settings` changes the 3D-print assumptions and returns the
refreshed `BuildArtifactRead`:

```json
{
  "material": "PETG",
  "infill_percent": 60,
  "price_per_gram_jod": 0.15
}
```

`price_per_gram_jod` is optional. When it is set, it replaces the chart rate for the selected
material so the estimate can match a local spool or print-shop quote. The endpoint persists the
settings and recomputes the mechanical and cost artifacts; the budget line and total use the
selected material instead of the cheapest one. Weight derives from volume, density, and an
effective material fraction of `8% + 92% × infill%`.

### Generate and read the build

`POST /api/v1/projects/{project_id}/build` runs component research → electrical → programming →
mechanical → cost → documentation and returns a `BuildArtifactRead` (`201`). `status` is `ready`,
`partial`, or `empty`; `missing` lists artifacts that could not be produced.

```json
{
  "project_id": "…",
  "project_name": "Patio Scout",
  "status": "ready",
  "generated_at": "2026-11-18T09:30:00Z",
  "preferences": {},
  "identification": {},
  "specification": {},
  "research": { "selected_shops": [], "bill_of_materials": [] },
  "electrical": {},
  "programming": { "bundles": [] },
  "mechanical": {
    "selected_material": "PLA",
    "infill_percent": 35,
    "material_fraction": "0.402",
    "custom_price_per_gram_jod": null,
    "print_price_jod": "3.556",
    "material_quotes": [],
    "stl_filename": "patio-scout.stl"
  },
  "cost": {},
  "documentation": { "files": [] },
  "missing": [],
  "warnings": []
}
```

`GET /api/v1/projects/{project_id}/build` returns the latest artifact or `404` before the first run.
`GET /api/v1/projects/{project_id}/mechanical/stl` returns the same STL as an attachment.

Every BOM candidate carries `offers` sorted cheapest → most expensive. Store prices are curated
JOD planning estimates, not live supplier quotes, and each response says so.

## Enum reference

| Enum | Values |
| --- | --- |
| `ProjectStatus` | `draft`, `planning`, `in_progress`, `ready`, `archived` |
| `RobotType` | `line_follower`, `obstacle_avoider`, `rover`, `robot_arm`, `drone`, `balancing_bot`, `custom` |
| `Difficulty` | `beginner`, `intermediate`, `advanced` |
| `TargetPlatform` | `arduino`, `esp32`, `raspberry_pi`, `other`, `undecided` |
| `DriveType` | `differential`, `mecanum`, `omni`, `tank`, `servo_arm`, `none` |
| `SpecificationStatus` | `draft`, `generated`, `approved` |
| `AgentName` | `robot_planner`, `component_research`, `electrical_engineering`, `programming`, `mechanical_design`, `cost_estimation` |
| `AgentRunStatus` | `queued`, `running`, `succeeded`, `failed`, `cancelled`, `skipped`, `not_implemented` |
| `AgentResultStatus` | `succeeded`, `failed`, `skipped`, `not_implemented` |
| `StoreName` | `temu`, `mikroelectron`, `waslleh`, `amazon`, `aliexpress`, `ghanimjo` |
| `CodeLanguage` | `python`, `cpp`, `c`, `stm32_assembly`, `verilog`, `vhdl`, `other` |
| `PrintMaterial` | `PLA`, `PETG`, `ABS`, `Resin`, `TPU` |

## Versioning policy

- `/api/v1` is stable for additive change. New optional fields and endpoints do not bump the version.
- Removing/renaming a field or changing its meaning requires `/api/v2` or a deprecation window.
- Agent JSON Schemas are versioned with the application; `extra="forbid"` makes drift visible.
- Regenerate contracts with `make contracts` and commit the result with the API change.
