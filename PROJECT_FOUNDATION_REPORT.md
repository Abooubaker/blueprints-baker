# Albayraq foundation report

- **Date:** 2026-11-16
- **Repository:** https://github.com/Abooubaker/blueprints-baker (public)
- **Project board:** https://github.com/users/Abooubaker/projects/1
- **Branch:** `main`
- **Status:** foundation complete and verified; product modules are intentionally placeholders.

This report records what was built, how it was verified, what is on GitHub, and what remains.
Claims below are limited to checks that were actually run.

> **Addendum (2026-11-18):** the planner, component research, and electrical/wiring system now
> work deterministically, including validated nets, power budget, and KiCad/EasyEDA-compatible
> netlist exports. A static GitHub Pages demo is generated from the same engine. Sections below
> that call component research or wiring “not implemented” describe the original foundation
> snapshot. See [docs/electrical.md](docs/electrical.md) and [docs/demo-site.md](docs/demo-site.md).

## 1. Objective and scope

Build a trustworthy foundation for an AI-assisted robotics platform:

- a runnable Next.js frontend and FastAPI backend;
- a real PostgreSQL schema with reversible migrations;
- typed, provider-independent AI agent contracts and an orchestrator;
- documentation, CI, and a prioritized backlog with a populated project board.

Explicitly **not** implemented: authentication, real model calls, component research, wiring,
firmware generation, mechanical design, cost estimation, export, and collaboration. These are
scheduled as milestones M2–M10 rather than presented as working features.

## 2. Stack and justification

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | Next.js 16.4.6, React 19.3.1, TypeScript 5.9.3 | File-based routing, server/client boundaries, typed UI, and a mature App Router ecosystem. |
| Styling | Tailwind CSS 4.3.5 | Fast, consistent responsive styling without a separate component library; dark, lime-accent design system owned in-repo. |
| Backend | FastAPI 0.118+, Pydantic 2.11+ | Async HTTP, generated OpenAPI, and request/response validation that matches the agent contracts. |
| ORM / DB | SQLAlchemy 2.0 async, asyncpg, PostgreSQL 16 | Relational integrity for the project aggregate, JSON for evolving artifacts, and a single transactional boundary per request. |
| Migrations | Alembic 1.16+ | Reviewed, reversible schema history and CI drift detection. |
| AI boundary | `LLMProvider` port + deterministic mock | Agents never depend on a vendor SDK; tests run offline; provider adapters can be added without touching domain code. |
| Orchestration | Typed Pydantic contracts + sequential orchestrator | Invalid model output fails at a known boundary; dependency skips and audit runs are explicit and testable. |
| Tooling | uv, npm, Ruff, mypy strict, pytest, ESLint, Prettier, GitHub Actions | Fast reproducible installs on both sides of the monorepo and meaningful CI gates. |
| Repository | Single monorepo with independent apps | API, UI, contracts, and docs change together; no cross-language build orchestrator until it earns its cost. |

Decisions and tradeoffs are recorded in [`docs/decisions/`](docs/decisions/).

## 3. Architecture

```text
Browser
  │  Next.js App Router (apps/web)
  │  landing, dashboard, project creation, project workspace, module scaffolds
  ▼
FastAPI (apps/api)
  ├── api/v1        HTTP routing, request IDs, error envelopes
  ├── services      transactions, project/specification/agent-run logic
  ├── models        SQLAlchemy: users, projects, specifications,
  │                 configurations, components, project components, agent runs
  └── ai
      ├── contracts     Pydantic inputs/outputs + shared context
      ├── provider      LLMProvider port, mock provider, factory
      ├── agents        six placeholder agents with explicit dependencies
      └── orchestrator  dependency expansion, ordering, skip rules, audit
  ▼
PostgreSQL 16  ◀── Alembic migrations
```

### Agent pipeline

```text
robot_planner → component_research → electrical → programming
                                      └────────→ mechanical
                                      └────────→ cost
```

- Every agent declares input/output models, dependencies, and one owned slot in
  `SharedProjectContext`.
- The orchestrator expands requested agents with transitive dependencies, runs them in pipeline
  order, skips agents whose dependencies did not succeed, re-validates the shared context, and
  persists one `agent_runs` row per agent, including skips.
- In the foundation release all agents return `not_implemented`; downstream agents are `skipped`.
  This is deliberate and visible in the API response and audit history, not a hidden failure.
- Agent schemas use `extra="forbid"` and are exported as JSON Schema 2020-12.

### Data model

`users` (currently unused), `robot_projects`, `robot_specifications`,
`project_configurations`, `components`, `project_components`, and `agent_runs`.

- UUID primary keys; timezone-aware timestamps.
- `NUMERIC(10,2)` for money and `Decimal` in Python.
- String-backed enums for portable, readable rows.
- JSON for dimensions, requirements, constraints, and agent payloads; relational columns for
  anything queried or constrained.
- Project deletion cascades to specifications, configurations, components, and agent runs.

Details: [`docs/database.md`](docs/database.md).

### Contracts

- `packages/contracts/openapi.json` — full OpenAPI 3.1 document.
- `packages/contracts/schemas/` — 16 JSON Schemas (shared context, six inputs, six outputs,
  agent request/result, project context).
- `apps/web/src/lib/api-schema.ts` — generated TypeScript types consumed by the API client.

`make contracts` regenerates all three. CI fails if the working tree drifts.

## 4. Repository layout

```text
apps/api/                 FastAPI application, Alembic, tests
apps/web/                 Next.js App Router application
packages/contracts/       generated OpenAPI and agent schemas
docs/                     architecture, API, database, agents, development, roadmap,
                          backlog, prototype review, ADRs
scripts/                  contract export, backlog seeding, project board setup
.github/                  CI, issue templates, pull request template
```

Root commands are defined in [`Makefile`](Makefile): `make check`, `make api-check`,
`make web-check`, `make contracts`, `make migrate`, `make dev-api`, `make dev-web`.

## 5. Verification evidence

### 5.1 Local quality gates

`make check` completed successfully:

| Gate | Result |
| --- | --- |
| Ruff lint | All checks passed (51 files) |
| Ruff format check | 51 files already formatted |
| mypy (strict) | No issues in 43 source files |
| pytest | 21 passed in 0.43 s |
| ESLint | No errors |
| TypeScript (`tsc --noEmit`) | No errors |
| Prettier check | All files formatted |
| Next.js production build | Compiled; 7 routes generated |

The production build serves `/`, `/dashboard`, `/projects/new`, `/projects/[id]`, and
`/projects/[id]/[module]` (with `_not-found` and `icon.svg`).

### 5.2 CI

Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

Final run [`43951602732`](https://github.com/Abooubaker/blueprints-baker/actions/runs/43951602732) is
**success** with all four jobs green:

- Backend quality and tests
- PostgreSQL migrations
- Generated contracts are current
- Frontend quality and build

The first CI run failed because the Python-derived `.gitignore` rule `lib/` also excluded
`apps/web/src/lib`, so the API client and types were never committed. The rule was anchored to the
repository root and the missing files were added in commit `961d624`. This was a real defect caught
by CI, not a cosmetic failure.

Non-blocking annotations: GitHub warns that `actions/checkout@v4` and `astral-sh/setup-uv@v6`
target Node.js 20, and that `ubuntu-latest` will migrate to Ubuntu 26 in October 2026. Neither
affects the current result.

### 5.3 PostgreSQL migrations

Verified on PostgreSQL **16.2** in a fresh database:

```text
alembic upgrade head      → initial schema applied
alembic downgrade base    → initial schema removed
alembic upgrade head      → initial schema reapplied
alembic check             → "No new upgrade operations detected."
```

The temporary verification database was dropped afterwards. Migrations also run in the CI
`PostgreSQL migrations` job.

### 5.4 Live API smoke test on PostgreSQL

Against the freshly migrated database:

| Check | Result |
| --- | --- |
| `GET /health` | `200`, service/version/environment |
| `GET /health/ready` | `200`, `database.status = ok` |
| `POST /api/v1/projects` | `201`, project created with draft specification v1 |
| `GET /api/v1/projects?limit=50` | `200`, `meta.total = 1` |
| `POST /api/v1/projects/{id}/agent-runs` | `201`, `robot_planner` returned `not_implemented` |
| `GET /api/v1/projects/{id}/agent-runs` | `200`, persisted audit run |
| `DELETE /api/v1/projects/{id}` | `204` |

The smoke project and database were removed after verification.

### 5.5 Frontend browser QA

Automated checks would not prove layout or interaction, so the main routes were exercised in
system Chromium:

- Landing page, dashboard, new-project form, project overview, and module scaffold render.
- No console errors on the main routes.
- No horizontal overflow at desktop width or 360 px.
- Creating a project through the form succeeded; the created project was opened and then deleted
  through the API (`204`).
- Loading, empty, error, and placeholder states are present in the UI.

### 5.6 Contracts

- 16 agent JSON Schemas generated, all rejecting unknown fields.
- OpenAPI document generated from the running application.
- Frontend types regenerated from OpenAPI and committed.
- CI `Generated contracts are current` job passed, proving no drift after the final push.

### 5.7 Secrets and repository hygiene

- `.env` files are ignored; only `.env.example` files are tracked.
- No credentials, private keys, databases, or build artifacts are tracked.
- The commit set contains 133 source/doc/tooling files at roughly 1.5 MB, excluding ignored
  dependencies and caches.
- `apps/api/.env.example` contains empty placeholders only (`AI_API_KEY=`).

### 5.8 Prototype review

The contributor branch `AI-Robotics-Agent` (commit `3065333`) was reviewed, not merged:

- `py_compile` passes for all Python files.
- With the Ollama client stubbed, the deterministic path seeds six components and returns
  44.00 JOD for an ESP32 line follower, with a 7.4 V battery / 6 V motor warning.
- No secrets, `eval`/`exec`, destructive filesystem behavior, or unexpected network calls were found.
- **Not verified:** the AI conversation path, because Ollama and `qwen3:4b` are not installed.
- Decision: keep as a reference spike; adopt its seed catalog, deterministic selection, budget,
  voltage checks, and prompt guardrails in M4/M5.

Details and the adoption map: [`docs/prototype-review.md`](docs/prototype-review.md).

## 6. GitHub status

### 6.1 Repository and commits

`main` was pushed to https://github.com/Abooubaker/blueprints-baker. Foundation commits:

| Commit | Contents |
| --- | --- |
| `9f24b45` | Repository tooling, CI, license |
| `6786001` | FastAPI backend, database schema, agent orchestration, contracts |
| `1af9865` | Next.js workspace |
| `d7ec68a` | Architecture, ADRs, API/database/agent docs, roadmap, backlog, prototype review |
| `961d624` | Fix `.gitignore` excluding `apps/web/src/lib`; add missing frontend sources |

The final documentation and board tooling commit follows this report.

### 6.2 Labels, milestones, and issues

- **37 labels** covering type, priority, effort, area, status, and `prototype`.
- **10 milestones**, M1–M10, each with a goal description.
- **65 issues**: 63 open, 2 closed.
  - Closed: #6 “Foundation release: repository tooling, docs, and CI” and #7 “Triage the
    AI-Robotics-Agent prototype and map reusable parts”.
  - Every issue has context, scope, acceptance criteria, dependencies, priority, effort, area,
    and milestone.

### 6.3 Project board

https://github.com/users/Abooubaker/projects/1 — **65 items**, verified through GraphQL with no
missing field values.

Fields:

| Field | Type | Options |
| --- | --- | --- |
| Status | Single select | Backlog, Ready, In Progress, In Review, Done, Blocked |
| Priority | Single select | P0 Critical, P1 High, P2 Medium, P3 Low |
| Development Area | Single select | Frontend, Backend, AI Agents, Database, DevOps, Documentation, Design |
| Estimated Effort | Single select | XS, S, M, L, XL |
| Milestone | Built-in | M1–M10 |

Views present: **Backlog** (board), **Priority board** (board), **Team items** (table),
**Roadmap** (roadmap), **My items** (table). GitHub does not expose view mutations, so layout,
grouping, and filters remain UI-managed.

Board status after population:

| Status | Items |
| --- | ---: |
| Done | 2 |
| Ready | 6 |
| Blocked | 57 |
| In Progress | 0 |
| In Review | 0 |
| Backlog | 0 |

“Blocked” here means the issue has at least one open dependency. It is an honest view of a
dependency-ordered backlog, not a sign of external blockers.

### 6.4 Issue distribution

By milestone:

| Milestone | Issues |
| --- | ---: |
| M1 Foundation & specification | 7 |
| M2 Accounts & ownership | 6 |
| M3 AI provider layer & robot planner | 8 |
| M4 Component research & catalog | 9 |
| M5 Electrical engineering & wiring | 7 |
| M6 Programming & firmware | 6 |
| M7 Mechanical design | 5 |
| M8 Cost estimation | 5 |
| M9 Export, sharing & collaboration | 5 |
| M10 Production readiness | 7 |

By development area:

| Area | Issues |
| --- | ---: |
| Backend | 23 |
| Frontend | 17 |
| AI Agents | 13 |
| DevOps | 7 |
| Database | 2 |
| Design | 2 |
| Documentation | 1 |

By priority: **P0** 18, **P1** 38, **P2** 9, **P3** 0.

By effort: **XS** 0, **S** 3, **M** 25, **L** 30, **XL** 7.

The complete issue plan, dependencies, and links: [`docs/backlog.md`](docs/backlog.md).

### 6.5 Prototype follow-up issues

The prototype’s reusable parts are explicitly scheduled:

- #23 seed component catalog (including the prototype fixture)
- #26 deterministic selection and budget checks
- #27 compatibility engine (voltage/current/interfaces)
- #32 electrical safety validators
- #15 local Ollama provider adapter
- #7 triage review (closed)

## 7. Limitations and known gaps

These are intentional for a foundation release and are tracked as issues.

1. **No authentication or ownership.** Every route is public and `owner_id` is nullable. Do not
   deploy with real user data until M2 (#8–#13) is complete.
2. **Agents are placeholders.** Only the deterministic `mock` provider exists. No real model is
   called, no tokens are spent, and no robotics artifact is generated. Real providers, structured
   output, and the planner are M3 (#14–#21).
3. **Specification UI is read-only.** The API supports updates, but editing and approval arrive in
   M1 (#1).
4. **Feature modules are scaffolds.** Components, wiring, programming, mechanical, and cost routes
   explain scope and placeholders; they do not implement the workflows.
5. **Docker Compose was not executed here.** The Docker socket was inaccessible and `sudo` required
   a password, so local PostgreSQL was provided by an embedded PostgreSQL 16.2 server instead. The
   Compose file and CI PostgreSQL service are the supported paths for other environments.
6. **The prototype’s AI path is unverified.** Ollama and the model it references are not installed
   on this machine.
7. **Project views are UI-managed.** The GraphQL API can read views but cannot create or update
   them.
8. **No production deployment, observability, backups, or e2e suite yet.** These are M10 (#59–#65).
9. **CI uses Node 20-targeting actions.** GitHub reports deprecation warnings for
   `actions/checkout@v4` and `astral-sh/setup-uv@v6`; they currently run on Node 24 and pass.

## 8. Next steps

1. **M2 — close the public API.** Implement auth (#8), refresh sessions (#9), ownership (#10), and
   the auth UI (#11) before adding user data or deploying.
2. **M3 — make the planner real.** Add one hosted provider (#14), the Ollama adapter (#15),
   structured-output repair (#16), and the planner agent (#17), with an evaluation harness (#21).
3. **M4/M5 — absorb the prototype properly.** Seed the catalog (#23), port deterministic
   selection/budget (#26), build the compatibility engine (#27), and add safety validators (#32)
   before any wiring UI.
4. **Keep the gates green.** Every schema change runs `make contracts`; every behavior change adds
   tests and updates docs; every completed issue updates the board.
5. **Revisit deployment once auth and a real provider exist.** Container images, metrics, backups,
   and security review are premature before M2/M3.

## 9. Reproducing the verification

```bash
# from the repository root
make install
make check

# PostgreSQL (Docker path; embedded PostgreSQL was used for this report)
make db-up
make migrate

# Contracts
make contracts
git diff --exit-code packages/contracts apps/web/src/lib/api-schema.ts

# Run the stack
make dev-api   # :8000
make dev-web   # :3000
```

Backlog and board tooling:

```bash
python3 scripts/seed_github.py --dry-run   # inspect the plan
python3 scripts/seed_github.py --create    # labels, milestones, issues
python3 scripts/seed_github.py --backlog-only
python3 scripts/setup_project.py --dry-run
python3 scripts/setup_project.py
```

`setup_project.py` requires the `project` scope:

```bash
gh auth refresh --hostname github.com -s project,read:project
```
