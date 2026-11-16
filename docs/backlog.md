# Backlog

Generated from [`scripts/seed_github.py`](../scripts/seed_github.py). GitHub is the source of
truth; this file is a readable mirror for planning and offline review.

**Repository:** https://github.com/Abooubaker/robocraft  
**Project board:** https://github.com/users/Abooubaker/projects/1  
**Issues:** 65 (2 completed, 63 open)

> **Board status:** configured and verified. All 65 issues are on the project with
> Status, Priority, Estimated Effort, and Development Area set. See
> [Project board configuration](#project-board-configuration).

## Counts by milestone

| Milestone | Issues |
| --- | ---: |
| M1: Foundation & specification | 7 |
| M2: Accounts & ownership | 6 |
| M3: AI provider layer & robot planner | 8 |
| M4: Component research & catalog | 9 |
| M5: Electrical engineering & wiring | 7 |
| M6: Programming & firmware | 6 |
| M7: Mechanical design | 5 |
| M8: Cost estimation | 5 |
| M9: Export, sharing & collaboration | 5 |
| M10: Production readiness | 7 |

## Counts by area

| Area | Issues |
| --- | ---: |
| ai | 13 |
| backend | 23 |
| database | 2 |
| design | 2 |
| devops | 7 |
| docs | 1 |
| frontend | 17 |

## Counts by priority

| Priority | Issues |
| --- | ---: |
| p0 | 18 |
| p1 | 38 |
| p2 | 9 |
| p3 | 0 |

## Initial status labels

Status labels are set at creation and mirror the board's initial state. The board Status
field is authoritative; labels remain useful for filtering outside the project.

| Status | Issues |
| --- | ---: |
| status:ready | 6 |
| status:blocked | 0 |
| status:backlog | 57 |
| status:done | 2 |

## Issue plan

| # | Issue | Milestone | Area | Priority | Effort | Status | Dependencies |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | [#1](https://github.com/Abooubaker/robocraft/issues/1) Add specification editing, validation, and approval flow | M1 | frontend | p1 | m | open | — |
| 2 | [#2](https://github.com/Abooubaker/robocraft/issues/2) Add project settings and lifecycle controls | M1 | frontend | p2 | m | open | #1 |
| 3 | [#3](https://github.com/Abooubaker/robocraft/issues/3) Add status, robot-type, and sort controls to the dashboard | M1 | frontend | p2 | s | open | — |
| 4 | [#4](https://github.com/Abooubaker/robocraft/issues/4) Add first-run onboarding and a guided sample project | M1 | design | p2 | m | open | #3 |
| 5 | [#5](https://github.com/Abooubaker/robocraft/issues/5) Expand API tests for project and specification edge cases | M1 | backend | p2 | s | open | — |
| 6 | [#6](https://github.com/Abooubaker/robocraft/issues/6) Foundation release: repository tooling, docs, and CI | M1 | devops | p1 | m | closed | — |
| 7 | [#7](https://github.com/Abooubaker/robocraft/issues/7) Triage the AI-Robotics-Agent prototype and map reusable parts | M1 | docs | p1 | s | closed | — |
| 8 | [#8](https://github.com/Abooubaker/robocraft/issues/8) Implement email/password registration and login | M2 | backend | p0 | l | open | — |
| 9 | [#9](https://github.com/Abooubaker/robocraft/issues/9) Add refresh-token sessions with rotation and revocation | M2 | backend | p0 | l | open | #8 |
| 10 | [#10](https://github.com/Abooubaker/robocraft/issues/10) Enforce project ownership across every API route | M2 | backend | p0 | m | open | #8, #9 |
| 11 | [#11](https://github.com/Abooubaker/robocraft/issues/11) Add authentication UI and protect the workspace | M2 | frontend | p0 | l | open | #8, #9 |
| 12 | [#12](https://github.com/Abooubaker/robocraft/issues/12) Add account profile and security settings | M2 | frontend | p2 | m | open | #11 |
| 13 | [#13](https://github.com/Abooubaker/robocraft/issues/13) Add rate limiting, login throttling, and auth audit logs | M2 | backend | p1 | m | open | #8 |
| 14 | [#14](https://github.com/Abooubaker/robocraft/issues/14) Implement an OpenAI-compatible LLM provider adapter | M3 | ai | p0 | l | open | — |
| 15 | [#15](https://github.com/Abooubaker/robocraft/issues/15) Add a local Ollama provider adapter for development | M3 | ai | p1 | m | open | #14 |
| 16 | [#16](https://github.com/Abooubaker/robocraft/issues/16) Add structured-output validation, repair, and retry policy | M3 | ai | p0 | l | open | #14 |
| 17 | [#17](https://github.com/Abooubaker/robocraft/issues/17) Implement the Robot Planner agent | M3 | ai | p0 | xl | open | #16 |
| 18 | [#18](https://github.com/Abooubaker/robocraft/issues/18) Add planner review, approval, and regeneration flow | M3 | frontend | p1 | l | open | #17, #1 |
| 19 | [#19](https://github.com/Abooubaker/robocraft/issues/19) Add agent run progress, cancellation, and retry UX | M3 | frontend | p1 | l | open | #17, #16 |
| 20 | [#20](https://github.com/Abooubaker/robocraft/issues/20) Track model usage, cost, and per-user quotas | M3 | backend | p1 | m | open | #16 |
| 21 | [#21](https://github.com/Abooubaker/robocraft/issues/21) Build an agent evaluation harness with fixture briefs | M3 | ai | p1 | l | open | #17, #16 |
| 22 | [#22](https://github.com/Abooubaker/robocraft/issues/22) Add component catalog CRUD and admin API | M4 | backend | p0 | l | open | #10 |
| 23 | [#23](https://github.com/Abooubaker/robocraft/issues/23) Seed a usable component catalog, including the prototype fixture | M4 | database | p1 | m | open | #22 |
| 24 | [#24](https://github.com/Abooubaker/robocraft/issues/24) Add a supplier adapter boundary and manual catalog source | M4 | backend | p1 | l | open | #22 |
| 25 | [#25](https://github.com/Abooubaker/robocraft/issues/25) Implement the component research agent with role-based BOM derivation | M4 | ai | p0 | xl | open | #17, #23, #24, #16 |
| 26 | [#26](https://github.com/Abooubaker/robocraft/issues/26) Port deterministic component selection and budget checks from the prototype | M4 | backend | p1 | m | open | #25, #23 |
| 27 | [#27](https://github.com/Abooubaker/robocraft/issues/27) Add a deterministic compatibility engine for voltage, current, and interfaces | M4 | backend | p0 | l | open | #26, #22 |
| 28 | [#28](https://github.com/Abooubaker/robocraft/issues/28) Build the bill-of-materials workspace with alternatives and swaps | M4 | frontend | p1 | xl | open | #25, #11 |
| 29 | [#29](https://github.com/Abooubaker/robocraft/issues/29) Add price and availability snapshots with provenance | M4 | backend | p1 | m | open | #22, #24 |
| 30 | [#30](https://github.com/Abooubaker/robocraft/issues/30) Integrate one regional supplier catalog | M4 | backend | p2 | l | open | #24, #29 |
| 31 | [#31](https://github.com/Abooubaker/robocraft/issues/31) Implement the electrical engineering agent | M5 | ai | p0 | xl | open | #25, #27 |
| 32 | [#32](https://github.com/Abooubaker/robocraft/issues/32) Add deterministic electrical safety validators | M5 | backend | p0 | l | open | #31, #27 |
| 33 | [#33](https://github.com/Abooubaker/robocraft/issues/33) Build a wiring diagram renderer from ElectricalPlan | M5 | frontend | p1 | l | open | #31 |
| 34 | [#34](https://github.com/Abooubaker/robocraft/issues/34) Add pin conflict and interface validation | M5 | backend | p0 | m | open | #31 |
| 35 | [#35](https://github.com/Abooubaker/robocraft/issues/35) Build the wiring workspace with steps and checklists | M5 | frontend | p1 | l | open | #33, #28 |
| 36 | [#36](https://github.com/Abooubaker/robocraft/issues/36) Add a power budget calculator with margin warnings | M5 | backend | p0 | m | open | #31, #27 |
| 37 | [#37](https://github.com/Abooubaker/robocraft/issues/37) Add electrical plan fixtures for known-good and known-bad configurations | M5 | ai | p1 | m | open | #32, #34 |
| 38 | [#38](https://github.com/Abooubaker/robocraft/issues/38) Implement the programming agent for Arduino and ESP32 | M6 | ai | p0 | xl | open | #31, #34, #32 |
| 39 | [#39](https://github.com/Abooubaker/robocraft/issues/39) Add Raspberry Pi as a firmware target | M6 | ai | p2 | l | open | #38 |
| 40 | [#40](https://github.com/Abooubaker/robocraft/issues/40) Build the firmware file tree, viewer, and download | M6 | frontend | p1 | l | open | #38, #28 |
| 41 | [#41](https://github.com/Abooubaker/robocraft/issues/41) Add static code validation and compile fixtures | M6 | backend | p0 | l | open | #38 |
| 42 | [#42](https://github.com/Abooubaker/robocraft/issues/42) Add library manifest and deployment instructions | M6 | ai | p1 | m | open | #38 |
| 43 | [#43](https://github.com/Abooubaker/robocraft/issues/43) Add regeneration diffs and firmware version history | M6 | frontend | p1 | l | open | #40, #38 |
| 44 | [#44](https://github.com/Abooubaker/robocraft/issues/44) Implement the mechanical design agent | M7 | ai | p1 | xl | open | #25, #27 |
| 45 | [#45](https://github.com/Abooubaker/robocraft/issues/45) Add a mechanical part library with material metadata | M7 | database | p1 | m | open | #22 |
| 46 | [#46](https://github.com/Abooubaker/robocraft/issues/46) Add mass and clearance validation | M7 | backend | p1 | m | open | #44, #45 |
| 47 | [#47](https://github.com/Abooubaker/robocraft/issues/47) Build the assembly instructions and parts list UI | M7 | frontend | p1 | l | open | #44, #28 |
| 48 | [#48](https://github.com/Abooubaker/robocraft/issues/48) Enforce mechanical/BOM consistency and stale-artifact rules | M7 | backend | p1 | m | open | #44, #46, #27 |
| 49 | [#49](https://github.com/Abooubaker/robocraft/issues/49) Implement the cost estimation agent | M8 | ai | p1 | l | open | #25, #26 |
| 50 | [#50](https://github.com/Abooubaker/robocraft/issues/50) Add currency handling and exchange-rate provenance | M8 | backend | p1 | m | open | #49, #29 |
| 51 | [#51](https://github.com/Abooubaker/robocraft/issues/51) Build the budget breakdown and alternatives UI | M8 | frontend | p1 | l | open | #49, #28 |
| 52 | [#52](https://github.com/Abooubaker/robocraft/issues/52) Add budget editing and re-estimation flow | M8 | frontend | p1 | m | open | #51, #49 |
| 53 | [#53](https://github.com/Abooubaker/robocraft/issues/53) Add supplier price refresh and caching | M8 | backend | p1 | m | open | #30, #29, #49 |
| 54 | [#54](https://github.com/Abooubaker/robocraft/issues/54) Add build bundle export | M9 | backend | p1 | l | open | #35, #40, #47, #51 |
| 55 | [#55](https://github.com/Abooubaker/robocraft/issues/55) Add a printable build guide and PDF export | M9 | frontend | p1 | l | open | #54, #47, #35 |
| 56 | [#56](https://github.com/Abooubaker/robocraft/issues/56) Add read-only share links with expiry and revocation | M9 | backend | p1 | l | open | #10, #54 |
| 57 | [#57](https://github.com/Abooubaker/robocraft/issues/57) Add project revision history and restore | M9 | backend | p1 | xl | open | #10 |
| 58 | [#58](https://github.com/Abooubaker/robocraft/issues/58) Add artifact comments and annotations | M9 | frontend | p2 | l | open | #11 |
| 59 | [#59](https://github.com/Abooubaker/robocraft/issues/59) Add production containers and a deployment pipeline | M10 | devops | p0 | l | open | #6 |
| 60 | [#60](https://github.com/Abooubaker/robocraft/issues/60) Add structured logs, metrics, tracing, and alerts | M10 | devops | p1 | l | open | #59 |
| 61 | [#61](https://github.com/Abooubaker/robocraft/issues/61) Add backups, restore drills, and retention policy | M10 | devops | p1 | m | open | #59 |
| 62 | [#62](https://github.com/Abooubaker/robocraft/issues/62) Run a security audit and add dependency/container scanning | M10 | devops | p0 | m | open | #10, #59 |
| 63 | [#63](https://github.com/Abooubaker/robocraft/issues/63) Complete accessibility audit and fixes (WCAG 2.2 AA) | M10 | design | p1 | l | open | #11, #28, #35, #47 |
| 64 | [#64](https://github.com/Abooubaker/robocraft/issues/64) Add a Playwright end-to-end suite to CI | M10 | devops | p1 | l | open | #11, #28, #35, #54 |
| 65 | [#65](https://github.com/Abooubaker/robocraft/issues/65) Add performance budgets and load testing | M10 | devops | p2 | m | open | #64, #60 |

## Milestones

| Milestone | Goal |
| --- | --- |
| M1: Foundation & specification | Monorepo, schema, API, web shell, agent contracts, CI, and documentation. |
| M2: Accounts & ownership | Authentication, user-scoped projects, sessions, and rate limiting. |
| M3: AI provider layer & robot planner | Provider adapters, structured output, the real planner, evaluation, and usage controls. |
| M4: Component research & catalog | Component catalog, supplier boundary, BOM derivation, compatibility checks, and workspace. |
| M5: Electrical engineering & wiring | Wiring plan, power budget, deterministic safety validation, and wiring UI. |
| M6: Programming & firmware | Firmware generation, compile validation, code viewer, and version history. |
| M7: Mechanical design | Chassis plan, mechanical part library, assembly instructions, and consistency checks. |
| M8: Cost estimation | Cost roll-up, currency and price provenance, alternatives, and live budget. |
| M9: Export, sharing & collaboration | Build bundle export, printable guide, share links, revisions, and comments. |
| M10: Production readiness | Deployment, observability, backups, security, accessibility, e2e, and performance. |

## Project board configuration

Target project: https://github.com/users/Abooubaker/projects/1

Fields are created and synchronized by [`scripts/setup_project.py`](../scripts/setup_project.py).
The script is idempotent and uses the same issue definitions as the backlog.

### Fields

| Field | Type | Options |
| --- | --- | --- |
| Status | Single select | Backlog, Ready, In Progress, In Review, Done, Blocked |
| Priority | Single select | P0 Critical, P1 High, P2 Medium, P3 Low |
| Development Area | Single select | Frontend, Backend, AI Agents, Database, DevOps, Documentation, Design |
| Estimated Effort | Single select | XS, S, M, L, XL |
| Milestone | Built-in | M1-M10 |

### Views

The project provides five views. GitHub does not expose project view mutations, so layout,
grouping, and filters are adjusted in the UI.

1. **Backlog** — board layout.
2. **Priority board** — board layout grouped by priority.
3. **Team items** — table layout.
4. **Roadmap** — roadmap layout; group by Milestone and sort M1-M10.
5. **My items** — table layout.

Useful filters: `Status = Blocked`, `Development Area = ...`, `Priority = P0 Critical`,
and `Milestone = M3`.

### Reproducing the configuration

```bash
gh auth refresh --hostname github.com -s project,read:project
python3 scripts/setup_project.py --dry-run
python3 scripts/setup_project.py
```

The script normalizes the single-select options, preserves existing option IDs where possible,
adds missing project items, and writes Status, Priority, Estimated Effort, and Development Area
for every issue.

### Status mapping

- Completed foundation issues → **Done**.
- Issues with at least one open dependency → **Blocked**.
- Everything else → **Ready**.

Board status is updated by maintainers as work starts, enters review, or completes.

## Working agreement

- Issues are ordered by milestone and dependency, not by creation date.
- An issue is ready when its dependencies are closed and acceptance criteria are testable.
- Safety-critical work (electrical, firmware, mechanical) requires deterministic tests.
- Every completed issue updates docs/contracts when behavior changes.
