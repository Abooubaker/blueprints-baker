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
| POST | `/api/v1/projects/{project_id}/electrical` | Generate and persist the wiring plan |
| GET | `/api/v1/projects/{project_id}/electrical` | Read the latest wiring plan |
| GET | `/api/v1/projects/{project_id}/electrical/export/{format}` | Download a wiring export |

## Health

```bash
curl http://localhost:8000/health/ready
```

```json
{
  "status": "ok",
  "service": "RoboCraft API",
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
      "status": "placeholder",
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
- In the foundation release every specialized agent returns `not_implemented`; dependents are
  `skipped`, so an orchestration response will contain one `not_implemented` run and five `skipped`
  runs unless a subset is requested.
- A failed/skipped/not-implemented dependency blocks dependents but does not abort independent
  branches.

Response (`OrchestrationRead`):

```json
{
  "project_id": "bef286cd-2987-4032-b7ca-c4fc99046c16",
  "status": "not_implemented",
  "runs": [
    {
      "id": "b0f4…",
      "project_id": "bef286cd-2987-4032-b7ca-c4fc99046c16",
      "agent": "robot_planner",
      "status": "not_implemented",
      "provider": "mock",
      "model": "placeholder",
      "summary": "Robot Planner is a placeholder in the foundation release.",
      "output_payload": null,
      "error_message": "Specialized agent logic is not implemented yet.",
      "prompt_tokens": 0,
      "completion_tokens": 0,
      "latency_ms": 0,
      "started_at": "2026-11-16T21:12:00Z",
      "completed_at": "2026-11-16T21:12:00Z",
      "created_at": "2026-11-16T21:12:00Z"
    }
  ],
  "shared_context": {
    "specification": { "summary": "…", "confidence": 0.0 },
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
| `bom-csv` | `bill-of-materials.csv` |
| `kicad-netlist` | `robocraft.net` |
| `svg` | `wiring.svg` |
| `markdown` | `build-guide.md` |

The `.net` export is a KiCad S-expression netlist; EasyEDA Pro and KiCad can import it.
See [electrical.md](electrical.md) for validation rules and the full contract.

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

## Versioning policy

- `/api/v1` is stable for additive change. New optional fields and endpoints do not bump the version.
- Removing/renaming a field or changing its meaning requires `/api/v2` or a deprecation window.
- Agent JSON Schemas are versioned with the application; `extra="forbid"` makes drift visible.
- Regenerate contracts with `make contracts` and commit the result with the API change.
