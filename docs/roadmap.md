# Roadmap

Ten milestones take RoboCraft from a verified foundation to a production-ready build assistant. Each
milestone produces a usable slice; no milestone depends on a later one. Issue-level work is tracked
on the [GitHub Project board](https://github.com/users/Abooubaker/projects/1) and mirrored in
[backlog.md](backlog.md).

```text
M1 Foundation ──▶ M2 Accounts ──▶ M3 Provider + Planner ──▶ M4 Components ──▶ M5 Electrical
                                                                         ├──▶ M6 Programming
                                                                         ├──▶ M7 Mechanical
                                                                         └──▶ M8 Cost
M9 Export & collaboration ──▶ M10 Production readiness
```

## M1 — Foundation and specification

**Goal:** a trustworthy skeleton that can be cloned, migrated, run, tested, and extended.

**Delivered**

- Monorepo, root tooling, CI, and documentation.
- PostgreSQL schema + reversible initial migration.
- Versioned FastAPI with health/readiness, structured errors, request IDs.
- Project/specification CRUD with validation and draft bootstrapping.
- Provider-independent contracts and JSON Schema export.
- Deterministic six-agent orchestrator with audit persistence.
- Next.js landing page, dashboard, project creation, project overview, module scaffolds.
- OpenAPI-driven frontend types.

**Exit criteria**

- `make check` passes.
- Migration upgrade → downgrade → upgrade verified on PostgreSQL 16.
- A project can be created in the browser and an agent run returns a persisted, correctly
  dependency-blocked audit trail.
- No secrets are committed.

**Remaining follow-ups** (tracked as M1 issues): richer specification editing/approval UI, project
settings, list filtering/search in the UI, and first-run onboarding.

## M2 — Accounts, ownership, and sessions

**Goal:** every project belongs to a user, and unauthenticated access is closed.

**Scope**

- Registration/login with Argon2 password hashing and short-lived access tokens.
- Refresh/session strategy with revocation.
- OAuth provider (optional, one provider first).
- Ownership checks on every project/specification/agent-run route.
- Frontend auth pages, protected workspace, profile/settings, sign-out.
- Per-user rate limiting and audit fields (`created_by`, `updated_by`) where needed.
- Migration backfill strategy for the currently nullable `owner_id`.

**Exit criteria**

- A user cannot read or mutate another user's project (tested).
- Existing local projects can be claimed by an admin or assigned during migration.
- Session expiry and refresh work without losing in-progress form data.
- Auth endpoints are rate-limited and covered by tests.

## M3 — AI provider layer and robot planner

**Goal:** replace the mock planner with a real, validated, cost-accounted agent.

**Scope**

- OpenAI and/or Anthropic adapter behind `LLMProvider`, plus a local Ollama adapter for development.
- Structured output, repair/retry policy, timeouts, and token ceilings.
- Planner prompt, input validation, and `RobotSpecificationDraft` output.
- Human approval/edit flow before downstream agents run.
- Run progress states, cancellation, and error surfaces in the UI.
- Prompt/model versioning and an evaluation harness with fixture briefs.
- Per-user quotas and usage reporting.

**Exit criteria**

- Planner outputs validate at ≥99% after repair on the fixture set.
- Agent runs record provider, model, tokens, latency, and failure reason.
- A failed or over-budget run is visible and retryable without duplicating audit rows.
- No vendor SDK is imported outside the provider adapter.

## M4 — Component research and catalog

**Goal:** turn an approved specification into a compatible, priced bill of materials.

**Scope**

- Component catalog CRUD, seed data, and admin tooling.
- Supplier adapter boundary (manual catalog first; one supplier integration next).
- Role-based BOM derivation and candidate ranking.
- Compatibility checks: voltage, current, interface, driver requirements, mechanical fit.
- Price/availability snapshots with timestamps and currency handling.
- BOM workspace: per-role selection, alternatives, unresolved requirements, swap action.
- Import the useful parts of the `AI-Robotics-Agent` prototype (see
  [prototype review](prototype-review.md)).

**Exit criteria**

- A line-follower specification produces a complete BOM with no invented parts.
- Every selected part has a source, price, availability, and rationale.
- Missing or incompatible parts are explicit, not silently skipped.
- Swapping a part revalidates dependent artifacts or marks them stale.

## M5 — Electrical engineering and wiring

**Goal:** produce a safe, explainable wiring plan and power budget.

**Scope**

- Electrical agent and deterministic validation rules.
- Pin map, bus/interface map, shared ground, level shifting, driver requirements.
- Power budget with peak/continuous current and margin.
- Wiring diagram renderer (node/connection graph first).
- Ordered wiring steps, safety warnings, and checklist.
- Validation fixtures for known-good and known-bad configurations.

**Exit criteria**

- Voltage/current incompatibilities are caught by deterministic tests, not only model prose.
- Every connection references existing component pins.
- Wiring instructions can be followed without the model.
- Unsafe configurations cannot be marked ready.

**Delivered (deterministic):** curated library and reference designs, pin allocation, named nets,
power rails and budget, severity-classified validation (`motor_overvoltage`, `logic_level_mismatch`,
`pin_conflict`, `missing_ground`, current headroom), wiring steps, and CSV/SVG/Markdown/JSON plus
KiCad-netlist exports. The web wiring workspace and the static demo are live. Remaining M5 work is
the model-backed electrical agent, richer interface/bus planning, and schematic-layout handoff.

## M6 — Programming and firmware

**Goal:** generate deployable firmware from the approved hardware plan.

**Scope**

- Programming agent for Arduino, ESP32, and Raspberry Pi.
- Pin assignments driven by the electrical plan; no invented pins/libraries.
- File tree, syntax highlighting, copy/download, and diff view.
- Library manifest and setup/upload instructions.
- Static validation (parse/compile where toolchain is available).
- Version history and regeneration with change summary.

**Exit criteria**

- Generated code parses and compiles for supported platforms in CI fixtures.
- Pin usage matches the electrical plan exactly.
- Generated code is displayed as untrusted text and never executed server-side.
- Users can download a complete firmware bundle.

## M7 — Mechanical design

**Goal:** plan the chassis and assembly around the selected electronics.

**Scope**

- Mechanical agent: chassis, mounts, drivetrain, fasteners, mass/clearance checks.
- Mechanical part library and material metadata.
- Assembly steps with tools, parts, and safety notes.
- Drawing/reference attachments (no CAD payloads in JSON).
- Consistency checks between mechanical parts and the BOM.

**Exit criteria**

- Assembly instructions reference only selected or explicitly additional parts.
- Mass/clearance warnings are deterministic and tested.
- Users can export a printable assembly guide.
- Mechanical changes mark electrical/programming artifacts stale when relevant.

## M8 — Cost estimation

**Goal:** give an honest, live budget with alternatives.

**Scope**

- Cost agent: line items, quantities, shipping, contingency, assumptions.
- Currency handling and date-stamped price sources.
- Budget status (under/within/over) with explicit unknown handling.
- Alternative bundles and savings/tradeoff comparison.
- Budget editing and re-estimation.
- Cost breakdown UI and export.

**Exit criteria**

- Totals reconcile exactly with line items and quantities.
- Every price is labelled as live, cached, or estimated with a date.
- Currency conversion is explicit and never silently mixed.
- Alternatives show real tradeoffs, not just cheaper parts.

## M9 — Export, sharing, and collaboration

**Goal:** make a finished design portable and reviewable.

**Scope**

- Build bundle export (spec, BOM, wiring, code, mechanical, cost).
- PDF/printable build guide.
- Read-only share links with expiry and revocation.
- Revision history and restore.
- Comments/annotations on artifacts.
- Optional team workspaces and roles.

**Exit criteria**

- An exported bundle is reproducible and includes generation metadata.
- Share links cannot expose another project or accept mutations.
- Revision restore is atomic and audited.
- A collaborator can comment without editing.

## M10 — Production readiness

**Goal:** operate RoboCraft safely and measure it.

**Scope**

- Container images, deployment pipeline, managed PostgreSQL, secret management.
- Structured logs, metrics, traces, dashboards, and alerting.
- Backups, restore drills, and retention policy.
- Security review: dependency/container scanning, authz tests, rate limits, CSP/headers.
- Accessibility audit (WCAG 2.2 AA) and keyboard/screen-reader testing.
- Performance budgets and load testing.
- End-to-end suite (Playwright) in CI.
- Launch checklist, status page, and incident runbook.

**Exit criteria**

- SLOs defined for availability and latency; alerts fire in staging.
- A restore from backup is demonstrated.
- No high/critical vulnerabilities in the release image or dependencies.
- Critical flows pass e2e on desktop and mobile viewports.
- Rollback procedure is documented and rehearsed.

## Cross-cutting rules

- A milestone is not done until its docs and contracts are updated and its issues are closed.
- Safety-critical checks are deterministic code with tests; LLM output is never the only guard.
- Every model-backed feature records provider, model, prompt version, tokens, latency, and cost.
- Data deletion/export is part of the feature, not a later cleanup.
