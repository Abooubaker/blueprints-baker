# RoboCraft

**An AI-assisted robotics engineering platform.** Describe the robot you want to build, and
RoboCraft turns the idea into a structured specification, a compatible bill of materials, wiring,
firmware, a mechanical plan, and a realistic budget.

> **Project status: foundation release (v0.1.0).** The platform skeleton, data model, API contracts,
> and agent orchestration are in place and tested. The six AI agents are deliberate placeholders
> that return `not_implemented`; product features are scheduled in the
> [roadmap](docs/roadmap.md) and tracked on the
> [GitHub Project board](https://github.com/users/Abooubaker/projects/1).

---

## Why RoboCraft

Building a robot from scratch means juggling five coupled decisions: what to build, which parts fit
together, how to wire them, how to program them, and whether the result fits the budget. Mistakes
are expensive and usually discovered after the parts arrive.

RoboCraft keeps those decisions in one typed project workspace. Each specialized AI agent owns one
artifact and consumes the artifacts produced before it. That makes the output inspectable, lets a
human correct any step, and keeps the system provider-independent — no vendor SDK leaks into the
domain layer.

## What works today

| Area | Status |
| --- | --- |
| Next.js 16 web app (landing, dashboard, project creation, project workspace, module scaffolds) | ✅ Implemented |
| FastAPI service, versioned REST API, OpenAPI docs, structured errors, request IDs | ✅ Implemented |
| PostgreSQL schema for users, projects, specifications, configurations, components, selections, agent runs | ✅ Implemented + migration |
| Provider-independent agent contracts and JSON Schema export | ✅ Implemented |
| Deterministic orchestrator with dependency resolution, artifact ownership, and audit persistence | ✅ Implemented |
| Six specialized agents (planner, components, electrical, programming, mechanical, cost) | 🚧 Placeholders (`not_implemented`) |
| Authentication, supplier integrations, code generation, exports, collaboration | 📋 Planned (M2–M10) |

The placeholder agents are not fake intelligence: they exercise the real orchestration contract,
return an explicit `not_implemented` status, and cause dependent agents to be marked `skipped`.
This is intentional so the foundation can be verified end-to-end before any model is wired in.

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Web | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4 | Server-first rendering for marketing pages, client components only where interaction is needed, one toolchain for UI and API types. |
| API | Python 3.12, FastAPI, Pydantic 2 | Async I/O, first-class OpenAPI generation, and validation shared by the HTTP and agent layers. |
| Data | PostgreSQL 16, SQLAlchemy 2 (async), Alembic | Relational integrity for coupled engineering artifacts, JSONB-ready flexible fields, reversible migrations. |
| AI | Provider-independent `LLMProvider` boundary, typed agent contracts | Swap OpenAI/Anthropic/local models without touching domain code; validate model output before it enters the graph. |
| Tooling | uv, npm, Ruff, mypy (strict), pytest, ESLint, Prettier, GitHub Actions | Fast, reproducible installs on both sides of the monorepo and meaningful CI gates. |

## Repository layout

```text
robocraft/
├── apps/
│   ├── api/                 FastAPI service, SQLAlchemy models, Alembic migrations, tests
│   └── web/                 Next.js App Router application
├── packages/
│   └── contracts/           Generated OpenAPI document + agent JSON Schemas
├── docs/                    Architecture, API, database, AI agent, development docs and ADRs
├── scripts/                 Contract export and backlog utilities
├── docker-compose.yml       Local PostgreSQL 16 for development
├── Makefile                 Day-to-day commands
└── .github/workflows/       CI: backend quality/tests + frontend quality/build
```

## Quick start

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20.9+ and npm 10+
- PostgreSQL 16 (local install or Docker)

### 1. Start PostgreSQL

```bash
docker compose up -d db
# or point DATABASE_URL at an existing PostgreSQL instance
```

### 2. Run the API

```bash
cd apps/api
cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000>
- OpenAPI UI: <http://localhost:8000/docs>
- Readiness: <http://localhost:8000/health/ready>

### 3. Run the web app

```bash
cd apps/web
cp .env.example .env.local
npm ci
npm run dev
```

Open <http://localhost:3000>, create a project, and open its workspace.

### 4. Run the quality gates

```bash
make check          # backend lint/types/tests + frontend lint/types/format/build
# or individually
make api-check
make web-check
```

See [docs/development.md](docs/development.md) for the full setup, test strategy, contract workflow,
and troubleshooting guide.

## Documentation

| Document | Contents |
| --- | --- |
| [Architecture](docs/architecture.md) | System context, monorepo boundaries, request flow, deployment topology, tradeoffs |
| [API](docs/api.md) | Endpoints, payloads, error envelope, pagination, examples |
| [Database](docs/database.md) | ERD, tables, constraints, migration policy |
| [AI agents](docs/ai-agents.md) | Pipeline, contracts, dependency rules, failure semantics, how to implement an agent |
| [Development](docs/development.md) | Local setup, commands, tests, contracts, conventions, troubleshooting |
| [Roadmap](docs/roadmap.md) | Milestones M1–M10 and exit criteria |
| [Backlog](docs/backlog.md) | Issue-level plan mirrored from GitHub |
| [Prototype review](docs/prototype-review.md) | Review of the AI-Robotics-Agent branch and adoption plan |
| [ADRs](docs/decisions/) | Recorded architecture decisions |
| [Foundation report](PROJECT_FOUNDATION_REPORT.md) | What was built, verification evidence, limitations, next steps |

## API at a glance

```bash
curl http://localhost:8000/health/ready

curl -X POST http://localhost:8000/api/v1/projects \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Science Fair Line Follower",
    "description": "Follows a black tape track and stops at obstacles.",
    "robot_type": "line_follower",
    "difficulty": "beginner",
    "target_platform": "arduino",
    "budget_max_usd": 60
  }'
```

Project creation bootstraps a draft specification. Running agents on the project returns the
orchestration audit trail:

```bash
curl -X POST http://localhost:8000/api/v1/projects/<project-id>/agent-runs \
  -H 'Content-Type: application/json' -d '{"agents": ["robot_planner"]}'
```

## Development workflow

1. Pick an issue from the [Project board](https://github.com/users/Abooubaker/projects/1).
2. Branch from `main` (`feat/…`, `fix/…`, `docs/…`).
3. Implement with tests; keep the API contract in sync (`make contracts`).
4. Run `make check` and open a pull request using the template.
5. A change is done when CI is green, docs are updated, and the issue is moved to **Done**.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before your first pull request.

## Roadmap summary

| Milestone | Theme | Outcome |
| --- | --- | --- |
| M1 | Foundation & specification | Monorepo, schema, API, web shell, orchestration contract |
| M2 | Accounts & ownership | Authentication, user-scoped projects, session UI |
| M3 | AI provider layer & planner | Real model provider, structured planner output, evaluation harness |
| M4 | Component research | Catalog, supplier adapters, compatibility checks, BOM workspace |
| M5 | Electrical engineering | Wiring plan, power budget, validation, wiring UI |
| M6 | Programming | Firmware generation, code viewer, build validation |
| M7 | Mechanical design | Chassis plan, part library, assembly instructions |
| M8 | Cost estimation | Live budget, alternatives, supplier pricing |
| M9 | Export & collaboration | Build bundle, PDF, sharing, revisions, comments |
| M10 | Production readiness | Deployment, observability, security, accessibility, e2e |

## Limitations (foundation release)

- No authentication or authorization yet; `owner_id` is nullable by design.
- Agents return placeholder results; no LLM is called.
- The component catalog has no seed data; supplier integrations do not exist.
- The Docker Compose file is a convenience for PostgreSQL and is not exercised by CI.
- SQLite is supported for tests only; PostgreSQL is the supported runtime database.

## License

[MIT](LICENSE)
