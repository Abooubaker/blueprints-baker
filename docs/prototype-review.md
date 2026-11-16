# Prototype review: `AI-Robotics-Agent`

- **Branch:** `AI-Robotics-Agent`
- **Commit:** `3065333` — “Add files via upload”
- **Author:** `aws ghraibeh`
- **Reviewed:** 2026-11-16
- **Decision:** keep as a reference spike; do **not** merge into `main`. Reuse selected ideas in M4/M5.

## What was submitted

Six files at the repository root, 982 lines total:

| File | Lines | Purpose |
| --- | --- | --- |
| `agent.py` | 609 | Line-follower component selection, budget/voltage checks, Ollama chat loop, tool definition |
| `components.py` | 226 | SQLite schema seeding plus six sample components |
| `database.py` | 121 | SQLite `components` table, additive column migration, indexes |
| `main.py` | 26 | Separate minimal Ollama chat demo |
| `store.py` | 0 | Empty placeholder |
| `robotics.db` | binary | SQLite database with six seeded rows |

The branch is based on the initial commit and does not modify `main` or the foundation application.

## What was verified

- `python -m py_compile` passes for all Python files.
- With the Ollama client stubbed out, `components.add_sample_components()` seeds six rows and
  `agent.build_robot_proposal()` returns:
  - ESP32 DevKit, TB6612FNG, 2× N20 motors, 5-channel IR sensor, 2S LiPo;
  - total 44.00 JOD, within a 60 JOD budget;
  - a warning that the 7.4 V battery exceeds the 6 V motor rating.
- The database contains only the `components` table and six sample rows. No unexpected data.
- Static inspection found no network calls other than the local Ollama client, no `eval`/`exec`, no
  credential access, and no destructive filesystem behavior.
- **Not verified:** the AI conversation path. Ollama and the model (`qwen3:4b`) are not installed in
  this environment.

## Strengths

- Deterministic selection and budget math are separated from the LLM narrative.
- The prompt tells the model not to invent parts, prices, stock, or compatibility, and not to change
  the computed total.
- The proposal explicitly lists parts missing from the database (chassis, wheels, wiring, switch,
  hardware) instead of pretending the total is complete.
- Tool calls are bounded (`max_tool_rounds = 8`) and tool errors are caught.
- User approval is required before “finalizing”.
- Useful starter fields: role, rated/min/max voltage, quantity per robot, supported robot type,
  source metadata.

## Gaps and risks

| Area | Finding |
| --- | --- |
| Architecture | Root-level synchronous scripts and SQLite; disconnected from FastAPI/PostgreSQL/SQLAlchemy |
| Packaging | No `requirements.txt`/`pyproject.toml`, no README, no run instructions |
| Entry points | `main.py` and `agent.py` are unrelated demos; `store.py` is empty |
| Testing | No tests; only ad-hoc manual execution |
| Data | Binary `robotics.db` committed; schema is created by ad-hoc `ALTER TABLE`, not migrations |
| Currency | Prices in JOD while the platform uses USD |
| Completeness | Chassis, wheels, wiring, switch, and hardware are excluded from the total |
| Compatibility | Only checks battery nominal voltage > motor rated voltage; ignores current, logic levels, driver supply, interfaces, and mechanical fit |
| Selection | `select_component()` ignores `robot_type` and picks the cheapest part; `performance` is unused |
| Safety | No current budget, no level-shifting check, no explicit “verify before purchase” disclaimer |
| UX | CLI-only, no persistence of proposals, no project model |

## Decision

Do not merge the branch as-is. Its architecture conflicts with the accepted
[monorepo](../decisions/0001-monorepo.md), [modular monolith](../decisions/0002-modular-monolith.md),
and [persistence](../decisions/0004-postgres-sqlalchemy-alembic.md) decisions, and it would add
untested code at the repository root.

Instead:

1. Keep the branch for reference; do not delete it without the author's agreement.
2. Extract the seed catalog, role-based selection, and budget/voltage checks during M4.
3. Expand compatibility validation deterministically during M5.
4. Add tests, currency handling, missing-part reporting, and provenance before any of it reaches the
   UI.

## Adoption map

| Prototype element | Destination | Notes |
| --- | --- | --- |
| Six sample components | M4 seed fixture / migration | Normalize into the existing `components` + `specs` JSON model; convert JOD to USD or store currency explicitly |
| Role-based selection | M4 component research service | Rank candidates, respect stock, expose alternatives, never invent parts |
| Budget calculation | M8 cost service (basic version in M4) | Use `Decimal`, quantities, shipping/contingency, explicit assumptions |
| Battery/motor voltage check | M5 deterministic validator | Extend to current, logic level, driver supply, interfaces |
| Missing-parts list | M4 BOM output | Keep; add chassis/wheels/wiring to the catalog rather than hard-coding |
| Ollama tool loop | M3 provider adapter (optional local provider) | Must sit behind `LLMProvider`; no direct SDK calls in agents |
| Prompt guardrails | M3/M4 prompt templates | Keep the “proposal is source of truth” and “no invented parts” rules |
| CLI flow | — | Superseded by the web workspace and API |

## Follow-up issues

The M4/M5 backlog includes explicit tasks for the adoption above. Search the issue tracker for
`prototype` or see [backlog.md](backlog.md).
