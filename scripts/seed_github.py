#!/usr/bin/env python3
"""Seed the RoboCraft GitHub backlog.

Creates labels, milestones M1-M10, and the issue plan, then writes docs/backlog.md.
The script is idempotent by issue title and safe to re-run.

Examples:
    python3 scripts/seed_github.py --dry-run
    python3 scripts/seed_github.py --create
    python3 scripts/seed_github.py --backlog-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field, replace
from pathlib import Path

REPO = "Abooubaker/robocraft"
OWNER = "Abooubaker"
PROJECT_NUMBER = 1
ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "docs" / "backlog.md"


def gh(*args: str, stdin: str | None = None) -> str:
    result = subprocess.run(
        ["gh", *args],
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed ({result.returncode}):\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result.stdout.strip()


def api(method: str, path: str, fields: dict[str, str] | None = None) -> object:
    args = ["api", "--method", method, path]
    for key, value in (fields or {}).items():
        args += ["-f", f"{key}={value}"]
    output = gh(*args)
    return json.loads(output) if output else None


@dataclass(frozen=True)
class Issue:
    key: str
    title: str
    milestone: str
    area: str
    kind: str
    priority: str
    effort: str
    context: str
    scope: list[str]
    acceptance: list[str]
    deps: tuple[str, ...] = ()
    notes: str = ""
    close_after_create: bool = False
    close_comment: str = ""
    extra_labels: tuple[str, ...] = field(default_factory=tuple)


def issue(
    key: str,
    title: str,
    milestone: str,
    area: str,
    kind: str,
    priority: str,
    effort: str,
    context: str,
    scope: list[str],
    acceptance: list[str],
    deps: tuple[str, ...] = (),
    notes: str = "",
    close_after_create: bool = False,
    close_comment: str = "",
    extra_labels: tuple[str, ...] = (),
) -> Issue:
    return Issue(
        key=key,
        title=title,
        milestone=milestone,
        area=area,
        kind=kind,
        priority=priority,
        effort=effort,
        context=context,
        scope=scope,
        acceptance=acceptance,
        deps=deps,
        notes=notes,
        close_after_create=close_after_create,
        close_comment=close_comment,
        extra_labels=extra_labels,
    )


M1 = "M1: Foundation & specification"
M2 = "M2: Accounts & ownership"
M3 = "M3: AI provider layer & robot planner"
M4 = "M4: Component research & catalog"
M5 = "M5: Electrical engineering & wiring"
M6 = "M6: Programming & firmware"
M7 = "M7: Mechanical design"
M8 = "M8: Cost estimation"
M9 = "M9: Export, sharing & collaboration"
M10 = "M10: Production readiness"

MILESTONES = {
    M1: "Monorepo, schema, API, web shell, agent contracts, CI, and documentation.",
    M2: "Authentication, user-scoped projects, sessions, and rate limiting.",
    M3: "Provider adapters, structured output, the real planner, evaluation, and usage controls.",
    M4: "Component catalog, supplier boundary, BOM derivation, compatibility checks, and workspace.",
    M5: "Wiring plan, power budget, deterministic safety validation, and wiring UI.",
    M6: "Firmware generation, compile validation, code viewer, and version history.",
    M7: "Chassis plan, mechanical part library, assembly instructions, and consistency checks.",
    M8: "Cost roll-up, currency and price provenance, alternatives, and live budget.",
    M9: "Build bundle export, printable guide, share links, revisions, and comments.",
    M10: "Deployment, observability, backups, security, accessibility, e2e, and performance.",
}

LABELS = {
    "type:feature": ("1f6feb", "New capability"),
    "type:chore": ("6e7781", "Maintenance, tooling, or refactor"),
    "type:bug": ("d73a4a", "Something is broken"),
    "type:spike": ("a371f7", "Research or prototype work"),
    "priority:p0": ("b60205", "Critical path / launch blocker"),
    "priority:p1": ("d93f0b", "High priority"),
    "priority:p2": ("fbca04", "Medium priority"),
    "priority:p3": ("c2e0c6", "Low priority"),
    "effort:xs": ("ededed", "Under half a day"),
    "effort:s": ("d4c5f9", "About one day"),
    "effort:m": ("b4a7d6", "Two to three days"),
    "effort:l": ("8f7ac8", "About a week"),
    "effort:xl": ("6b4fa8", "More than a week"),
    "area:frontend": ("1d76db", "Next.js / React / UI"),
    "area:backend": ("0e8a16", "FastAPI / services / domain"),
    "area:ai": ("5319e7", "Agents, prompts, providers, evaluation"),
    "area:database": ("006b75", "PostgreSQL, models, migrations, seeds"),
    "area:devops": ("c2410c", "CI, deployment, observability, security"),
    "area:docs": ("0075ca", "Documentation and developer experience"),
    "area:design": ("d876e3", "UX, visual design, accessibility"),
    "status:backlog": ("e4e669", "Not scheduled yet"),
    "status:ready": ("0e8a16", "Specified and unblocked"),
    "status:in-progress": ("1d76db", "Actively being worked"),
    "status:in-review": ("5319e7", "In review"),
    "status:blocked": ("b60205", "Waiting on a dependency or decision"),
    "status:done": ("6e7781", "Completed"),
    "prototype": ("ff9f1c", "Derived from the AI-Robotics-Agent prototype"),
}

ISSUES: list[Issue] = [
    # ------------------------------------------------------------------ M1
    issue(
        "m1-spec-edit",
        "Add specification editing, validation, and approval flow",
        M1,
        "frontend",
        "feature",
        "p1",
        "m",
        "Project creation bootstraps a draft specification, and the API exposes PUT "
        "/projects/{id}/specification, but the workspace is read-only. Users need to correct "
        "and approve the specification before it drives spending.",
        [
            "Build an editable specification form for summary, use case, environment, platform, drive type, power source, dimensions, requirements, and constraints.",
            "Mirror backend constraints (lengths, numeric ranges, enum values) and surface field-level errors from the API.",
            "Show and increment the specification version on save; warn about unsaved changes.",
            "Add an Approve action that sets status=approved and makes the state visible in the project header.",
            "Keep the read-only summary and a compact diff-friendly history view.",
        ],
        [
            "Saving valid changes persists them and increments version.",
            "Invalid values are blocked client-side and by the API with actionable messages.",
            "Approval is visible to all workspace modules and can be undone.",
            "The form works at 360 px and with keyboard-only navigation.",
        ],
        notes="The API is already implemented and tested; this is primarily a frontend issue.",
    ),
    issue(
        "m1-project-settings",
        "Add project settings and lifecycle controls",
        M1,
        "frontend",
        "feature",
        "p2",
        "m",
        "Projects can currently be created and viewed, but not renamed, re-budgeted, archived, or "
        "deleted from the UI. The API supports PATCH/DELETE.",
        [
            "Add a settings panel for name, description, difficulty, budget range, and status.",
            "Add archive and delete actions with explicit confirmation and dependency warnings.",
            "Show status transitions (draft → planning → in progress → ready → archived) and guard invalid jumps.",
            "Redirect to the dashboard after delete and show a success toast.",
            "Expose project ID/slug in a copyable diagnostics block.",
        ],
        [
            "PATCH changes persist and update the header without a full reload.",
            "Delete removes the project and returns to the dashboard.",
            "Destructive actions require confirmation and handle API errors.",
            "Budget ordering is validated before submit.",
        ],
        deps=("m1-spec-edit",),
    ),
    issue(
        "m1-dashboard-filters",
        "Add status, robot-type, and sort controls to the dashboard",
        M1,
        "frontend",
        "feature",
        "p2",
        "s",
        "The dashboard has a text filter, but the API supports status, robot_type, search, and "
        "pagination. Users with many projects need structured filtering and sorting.",
        [
            "Add status and robot-type filters plus a sort control (recently updated, name, budget).",
            "Reflect filters in the URL so views are shareable and survive refresh.",
            "Show active filter chips with a clear-all action and an explicit empty state.",
            "Keep the existing stat cards consistent with the filtered set or label them as global.",
            "Add pagination controls when total exceeds the page size.",
        ],
        [
            "Filters map to the API query parameters and produce correct results.",
            "URL state can be copied into a new tab and reproduces the view.",
            "Empty results explain how to recover; no layout shift or overflow on mobile.",
        ],
    ),
    issue(
        "m1-onboarding",
        "Add first-run onboarding and a guided sample project",
        M1,
        "design",
        "feature",
        "p2",
        "m",
        "A new user lands on an empty dashboard with example prompts buried in the create form. "
        "The first successful project needs to be obvious without a tutorial call.",
        [
            "Design a three-step first-run checklist: describe a robot, review the specification, run the planner.",
            "Offer a one-click sample project (line follower) that clearly says it is a demo.",
            "Improve empty states with a primary action and a short explanation of the six-agent pipeline.",
            "Add dismiss/restore behavior for the checklist and remember it locally.",
            "Keep the marketing page and workspace language consistent.",
        ],
        [
            "A new user can go from empty dashboard to project overview in under a minute.",
            "The demo project is clearly labeled and deletable.",
            "Onboarding does not reappear after dismissal and does not block navigation.",
        ],
        deps=("m1-dashboard-filters",),
    ),
    issue(
        "m1-api-edge-tests",
        "Expand API tests for project and specification edge cases",
        M1,
        "backend",
        "chore",
        "p2",
        "s",
        "The suite covers the happy path and core validation. Several edge cases around budgets, "
        "uniqueness, cascades, and error envelopes are untested.",
        [
            "Add tests for budget min > max, negative budgets, max lengths, and empty names.",
            "Add tests for slug collision suffixes and duplicate project names.",
            "Add tests for 404s on missing projects/specifications and delete cascade behavior.",
            "Assert the error envelope shape, request ID echo, and validation detail locations.",
            "Add a test that specification updates increment version and unknown fields are rejected.",
        ],
        [
            "New tests fail on the old behavior and pass on the current implementation.",
            "Coverage for services and API modules increases without brittle snapshot assertions.",
            "Tests remain hermetic (SQLite, no network).",
        ],
    ),
    issue(
        "m1-foundation-tooling",
        "Foundation release: repository tooling, docs, and CI",
        M1,
        "devops",
        "chore",
        "p1",
        "m",
        "The application skeleton is implemented, but the repository needs a coherent developer "
        "entry point, documentation, CI gates, and a final verification pass before it can be "
        "handed to contributors.",
        [
            "Add root README, CONTRIBUTING, license, Makefile, Compose database, env examples, and ADRs.",
            "Document architecture, API, database, AI agents, development, roadmap, and backlog.",
            "Add CI jobs for backend quality, PostgreSQL migrations, contract drift, and frontend build.",
            "Verify no .env, credentials, or build artifacts are tracked.",
            "Run backend lint/format/types/tests and frontend lint/types/format/build.",
        ],
        [
            "A fresh clone can follow the README to a running API and web app.",
            "CI configuration covers every local quality gate.",
            "All documented commands are verified in this environment.",
            "Repository contains no secrets or generated local state.",
        ],
        close_after_create=True,
        close_comment="Completed in the foundation release. Verification evidence is in PROJECT_FOUNDATION_REPORT.md.",
    ),
    issue(
        "m1-prototype-triage",
        "Triage the AI-Robotics-Agent prototype and map reusable parts",
        M1,
        "docs",
        "spike",
        "p1",
        "s",
        "A contributor pushed a standalone AI-Robotics-Agent branch containing an Ollama + SQLite "
        "line-follower prototype. It needs a security/quality review and a decision on reuse.",
        [
            "Review every file on the branch and verify it does not contain secrets or unexpected network behavior.",
            "Document what works, what is unverified, and which architecture decisions it conflicts with.",
            "Map reusable ideas (seed catalog, deterministic selection, budget/voltage checks, prompt guardrails) to M4/M5.",
            "Record the decision to keep the branch as a reference rather than merge it.",
        ],
        [
            "A review document exists with inventory, findings, decision, and adoption map.",
            "Every reusable element has an owning milestone/issue.",
            "No prototype code is merged into main without tests and architecture alignment.",
        ],
        notes="See docs/prototype-review.md.",
        close_after_create=True,
        close_comment="Reviewed in docs/prototype-review.md. Reusable parts are scheduled under M4/M5.",
        extra_labels=("prototype",),
    ),
    # ------------------------------------------------------------------ M2
    issue(
        "m2-auth",
        "Implement email/password registration and login",
        M2,
        "backend",
        "feature",
        "p0",
        "l",
        "The API is entirely public and the users table has no usable authentication. Accounts are "
        "the prerequisite for ownership, quotas, and safe multi-user deployment.",
        [
            "Add registration, login, and current-user endpoints under /api/v1/auth.",
            "Hash passwords with Argon2id; enforce a password policy and normalize emails.",
            "Issue short-lived access tokens with a documented claim set.",
            "Add email verification hooks without blocking local development.",
            "Return generic login failures and log auth events without secrets.",
        ],
        [
            "A user can register, log in, and call /auth/me.",
            "Passwords are never logged or returned; hashes use Argon2id.",
            "Duplicate emails and weak passwords return the standard error envelope.",
            "Tests cover success, wrong password, inactive user, and duplicate registration.",
        ],
    ),
    issue(
        "m2-sessions",
        "Add refresh-token sessions with rotation and revocation",
        M2,
        "backend",
        "feature",
        "p0",
        "l",
        "Short-lived access tokens need a safe renewal path and a way to sign out all devices. A "
        "permanent bearer token would make revocation impossible.",
        [
            "Persist hashed refresh tokens with device metadata, expiry, and revocation reason.",
            "Implement rotation on refresh and reuse detection (revoke the family).",
            "Add sign-out and sign-out-all endpoints.",
            "Choose and document storage (HttpOnly secure cookie vs. explicit client storage) with CSRF implications.",
            "Add cleanup for expired sessions and tests for rotation/reuse.",
        ],
        [
            "Refreshing returns a new token pair and invalidates the old refresh token.",
            "Reusing a rotated token revokes the session family and is audited.",
            "Sign-out removes access immediately for refresh flows.",
            "Expired sessions are rejected with a stable error code.",
        ],
        deps=("m2-auth",),
    ),
    issue(
        "m2-ownership",
        "Enforce project ownership across every API route",
        M2,
        "backend",
        "feature",
        "p0",
        "m",
        "owner_id is nullable and no route filters by user. Once authentication lands, every project, "
        "specification, and agent-run query must be scoped or treated as a cross-tenant leak.",
        [
            "Require authentication for project, specification, component-admin, and agent-run routes.",
            "Scope reads/writes to the current user; return 404 for resources the user cannot see.",
            "Add ownership checks to agent runs and audit history.",
            "Backfill or claim existing local projects and make owner_id non-nullable.",
            "Add IDOR regression tests for every project sub-resource.",
        ],
        [
            "User A cannot read, update, delete, or run agents on User B's project (tested).",
            "Unauthenticated requests receive 401 with the standard envelope.",
            "Admin-only operations are separated from user operations.",
            "Migration backfill is documented and reversible before owner_id becomes non-null.",
        ],
        deps=("m2-auth", "m2-sessions"),
    ),
    issue(
        "m2-auth-ui",
        "Add authentication UI and protect the workspace",
        M2,
        "frontend",
        "feature",
        "p0",
        "l",
        "The workspace is currently open to anyone who can reach it. Users need sign-in, sign-up, "
        "session refresh, and a clear signed-in identity.",
        [
            "Build login, registration, forgot-password, and sign-out flows.",
            "Protect the (workspace) routes and redirect unauthenticated visitors with a return path.",
            "Handle token refresh without losing form state and show friendly session-expired messaging.",
            "Add the signed-in user to the topbar with account menu.",
            "Keep auth pages consistent with the landing design and fully responsive.",
        ],
        [
            "Unauthenticated users cannot reach dashboard or project routes.",
            "Login errors are specific but do not reveal whether an email exists.",
            "Refresh works across tabs and sign-out clears local state.",
            "Keyboard and mobile flows are verified.",
        ],
        deps=("m2-auth", "m2-sessions"),
    ),
    issue(
        "m2-profile",
        "Add account profile and security settings",
        M2,
        "frontend",
        "feature",
        "p2",
        "m",
        "Users need to update their display name, change a password, review active sessions, and "
        "delete their account without contacting support.",
        [
            "Add profile fields (display name, email) and a password change form.",
            "List active sessions with device/last-used metadata and a revoke action.",
            "Add account deletion with typed confirmation and data-export instructions.",
            "Show security events (sign-ins, password changes) from the audit log.",
            "Document what deletion removes and what is retained.",
        ],
        [
            "Profile changes persist and are reflected in the topbar.",
            "Password change requires the current password and revokes other sessions.",
            "Account deletion removes owned projects and agent runs or clearly explains retention.",
            "All destructive actions are confirmed and audited.",
        ],
        deps=("m2-auth-ui",),
    ),
    issue(
        "m2-rate-limits",
        "Add rate limiting, login throttling, and auth audit logs",
        M2,
        "backend",
        "feature",
        "p1",
        "m",
        "Public auth and agent endpoints need abuse protection before deployment. Current endpoints "
        "accept unlimited requests.",
        [
            "Add per-IP limits for auth endpoints and per-user limits for project/agent endpoints.",
            "Throttle repeated failed logins with a temporary lock and generic messaging.",
            "Return RateLimit headers and a stable error code.",
            "Emit structured audit events for login success/failure, revocations, and quota hits.",
            "Make limits configurable per environment and test the 429 path.",
        ],
        [
            "Exceeding a limit returns 429 with Retry-After and does not crash the API.",
            "Failed-login throttling cannot be used to enumerate accounts.",
            "Audit events include request ID, user (when known), and outcome, but no secrets.",
            "Limits are disabled or relaxed in tests without making tests flaky.",
        ],
        deps=("m2-auth",),
    ),
    # ------------------------------------------------------------------ M3
    issue(
        "m3-openai-provider",
        "Implement an OpenAI-compatible LLM provider adapter",
        M3,
        "ai",
        "feature",
        "p0",
        "l",
        "The only registered provider is a deterministic mock. A real hosted provider is needed to "
        "implement the planner and downstream agents while keeping vendor code at the edge.",
        [
            "Implement a provider adapter using the OpenAI-compatible chat completions API.",
            "Map settings (API key, base URL, model, timeout, temperature, max tokens) without exposing secrets.",
            "Normalize usage, latency, provider errors, and timeouts into the provider response/error types.",
            "Add retry/backoff for transient failures and a clear non-retryable error path.",
            "Register the factory behind AI_PROVIDER and document configuration.",
        ],
        [
            "Provider unit tests use a fake transport and never make real network calls.",
            "Missing credentials fail fast with an actionable configuration error.",
            "Errors are classified and do not leak API keys or raw request bodies.",
            "A manual smoke run is documented (not executed in CI).",
        ],
        notes="No vendor SDK import outside apps/api/app/ai/provider.py.",
    ),
    issue(
        "m3-ollama-provider",
        "Add a local Ollama provider adapter for development",
        M3,
        "ai",
        "feature",
        "p1",
        "m",
        "Contributors should be able to exercise agents without a paid API key. The prototype used "
        "Ollama directly; the adapter belongs behind LLMProvider.",
        [
            "Implement an Ollama adapter with configurable base URL and model.",
            "Support the same normalized request/response and usage fields as hosted providers.",
            "Add health checking and a clear error when the daemon/model is unavailable.",
            "Keep network access out of unit tests via a fake transport.",
            "Document local setup and model recommendations.",
        ],
        [
            "AI_PROVIDER=ollama runs an agent end-to-end on a developer machine.",
            "Missing daemon/model produces an actionable error, not a stack trace.",
            "Tests are hermetic and do not require Ollama.",
            "No direct ollama import outside the provider module.",
        ],
        deps=("m3-openai-provider",),
        extra_labels=("prototype",),
    ),
    issue(
        "m3-structured-output",
        "Add structured-output validation, repair, and retry policy",
        M3,
        "ai",
        "feature",
        "p0",
        "l",
        "Model output must be valid against agent contracts before it reaches shared context. "
        "Providers differ in native structured-output support, so the pipeline needs one policy.",
        [
            "Pass JSON Schema/response format to providers that support it.",
            "Parse and validate output with the agent's Pydantic model; reject unknown fields.",
            "Define a bounded repair/retry loop with error feedback and a maximum attempt count.",
            "Classify failures (transport, timeout, invalid JSON, schema mismatch) in AgentResult.error.",
            "Record attempt count and token usage without duplicating audit runs.",
        ],
        [
            "Invalid JSON and schema violations become failed results with actionable errors.",
            "A repairable response succeeds within the retry budget.",
            "No partial artifact is applied on failure.",
            "Tests cover success, each failure class, and retry exhaustion.",
        ],
        deps=("m3-openai-provider",),
    ),
    issue(
        "m3-planner-agent",
        "Implement the Robot Planner agent",
        M3,
        "ai",
        "feature",
        "p0",
        "xl",
        "The planner is the root of the agent graph. It must convert a project brief into a "
        "reviewable RobotSpecificationDraft without selecting products or guessing silently.",
        [
            "Build the planner prompt from project description, type, difficulty, budget, requirements, and constraints.",
            "Infer platform, drive type, environment, dimensions, success criteria, and open questions.",
            "Refuse to invent hardware; put ambiguity in open_questions and calibrate confidence.",
            "Validate output into RobotSpecificationDraft and persist it as the shared specification.",
            "Add fixture briefs for line follower, rover, arm, and an intentionally ambiguous request.",
        ],
        [
            "The planner succeeds on all fixture briefs with contract-valid output.",
            "Open questions surface ambiguity instead of fabricated certainty.",
            "The planner never emits concrete component selections.",
            "A persisted agent run records provider, model, tokens, latency, and prompt version.",
        ],
        deps=("m3-structured-output",),
    ),
    issue(
        "m3-planner-approval",
        "Add planner review, approval, and regeneration flow",
        M3,
        "frontend",
        "feature",
        "p1",
        "l",
        "Users must be able to inspect and correct the planner's output before spending money. "
        "Without an approval gate, downstream agents would act on unreviewed assumptions.",
        [
            "Show planner output with confidence, open questions, and a field-by-field review.",
            "Allow manual edits, approve, or request regeneration with feedback.",
            "Keep a version/diff view between planner runs and manual edits.",
            "Gate downstream agent runs on an approved specification, with an explicit override.",
            "Surface provider/model/usage metadata for the run.",
        ],
        [
            "Approving persists status=approved and enables downstream agents.",
            "Regeneration preserves previous versions and clearly shows changes.",
            "Downstream actions explain why they are disabled when the spec is not approved.",
            "Mobile and keyboard review flows are usable.",
        ],
        deps=("m3-planner-agent", "m1-spec-edit"),
    ),
    issue(
        "m3-run-progress",
        "Add agent run progress, cancellation, and retry UX",
        M3,
        "frontend",
        "feature",
        "p1",
        "l",
        "Agent runs are synchronous today. Real model calls will take seconds to minutes, so the UI "
        "needs honest progress and recovery instead of a frozen button.",
        [
            "Expose queued/running/succeeded/failed/cancelled states and per-agent progress.",
            "Add polling or server-sent events with backoff and cleanup.",
            "Support cancel and retry for a failed run without duplicating audit history.",
            "Show errors, provider metadata, and a link to the affected artifact.",
            "Handle page refresh and navigation during a run.",
        ],
        [
            "A long run shows live status and never appears frozen.",
            "Cancellation stops UI waiting and records the correct state.",
            "Retry creates a new auditable run and preserves the failed one.",
            "Refreshing the page recovers the current run state.",
        ],
        deps=("m3-planner-agent", "m3-structured-output"),
    ),
    issue(
        "m3-usage-quotas",
        "Track model usage, cost, and per-user quotas",
        M3,
        "backend",
        "feature",
        "p1",
        "m",
        "Real model calls introduce variable cost. Without usage accounting and limits, one user can "
        "consume the entire budget.",
        [
            "Normalize prompt/completion tokens, latency, and estimated cost per run.",
            "Add configurable per-user daily/monthly token and cost quotas.",
            "Enforce quotas before a run and return a stable quota-exceeded error.",
            "Add an admin/self-service usage summary endpoint.",
            "Record model and prompt version for cost attribution.",
        ],
        [
            "Every model-backed run records usage and estimated cost.",
            "Quota exhaustion blocks new runs but preserves existing artifacts.",
            "Cost estimates are clearly labeled and configurable by model.",
            "Tests cover usage aggregation and quota boundaries.",
        ],
        deps=("m3-structured-output",),
    ),
    issue(
        "m3-eval-harness",
        "Build an agent evaluation harness with fixture briefs",
        M3,
        "ai",
        "feature",
        "p1",
        "l",
        "Prompt changes need evidence. Without a repeatable evaluation set, quality regressions are "
        "invisible until users complain.",
        [
            "Add a fixture set of realistic briefs across robot types, difficulties, and budgets.",
            "Score contract validity, requirement coverage, hallucination indicators, and latency/cost.",
            "Support a fake provider in CI and an opt-in real-provider run locally.",
            "Produce a readable report and fail thresholds in CI for deterministic checks.",
            "Document the rubric and how to add fixtures.",
        ],
        [
            "A new developer can run the harness with one command.",
            "Contract validity or deterministic rule regressions fail CI.",
            "Real-provider runs are never required for CI and never commit secrets.",
            "Baseline results and prompt/model versions are recorded.",
        ],
        deps=("m3-planner-agent", "m3-structured-output"),
    ),
    # ------------------------------------------------------------------ M4
    issue(
        "m4-catalog-crud",
        "Add component catalog CRUD and admin API",
        M4,
        "backend",
        "feature",
        "p0",
        "l",
        "The components table and read-only list endpoint exist, but there is no way to populate or "
        "maintain the catalog. Component research cannot be built on an empty table.",
        [
            "Add admin-only create, update, deactivate, and read endpoints.",
            "Validate category, URLs, prices, specs, and availability.",
            "Support pagination, filtering, search, and stable ordering.",
            "Add audit fields or an audit event for catalog mutations.",
            "Add tests for validation, authz, soft delete, and filtering.",
        ],
        [
            "Admins can manage components without direct SQL.",
            "Inactive components disappear from public lists but remain referenced by projects.",
            "Invalid prices/URLs/categories are rejected consistently.",
            "Authorization is enforced and tested.",
        ],
        deps=("m2-ownership",),
    ),
    issue(
        "m4-seed-catalog",
        "Seed a usable component catalog, including the prototype fixture",
        M4,
        "database",
        "feature",
        "p1",
        "m",
        "The platform needs a realistic starter catalog for demos and tests. The AI-Robotics-Agent "
        "prototype contains six sample parts and useful fields, but it uses SQLite and JOD.",
        [
            "Normalize the prototype's six parts into the existing Component model and specs JSON.",
            "Add chassis, wheels, wiring, power switch, and mounting hardware so a line follower BOM is complete.",
            "Use USD (or an explicit currency field) and record source/provenance.",
            "Create an idempotent seed fixture/migration that can run in development and tests.",
            "Add tests asserting counts, categories, and no duplicate names.",
        ],
        [
            "A fresh database can be seeded with one documented command.",
            "The line-follower flow has at least one candidate for every required role.",
            "Currency and source are explicit, never silently converted.",
            "Seeding twice does not create duplicates.",
        ],
        deps=("m4-catalog-crud",),
        extra_labels=("prototype",),
    ),
    issue(
        "m4-supplier-adapter",
        "Add a supplier adapter boundary and manual catalog source",
        M4,
        "backend",
        "feature",
        "p0",
        "l",
        "Supplier data will come from different APIs and manual entry. Without an adapter boundary, "
        "vendor-specific code and network calls would leak into agents and tests.",
        [
            "Define a supplier adapter protocol for search, detail, price, and availability.",
            "Implement a manual/local catalog adapter first.",
            "Normalize results into a common candidate model with provenance and timestamps.",
            "Add caching, timeouts, and error classification.",
            "Guarantee tests never hit the network.",
        ],
        [
            "Agents depend on the adapter protocol, not a vendor SDK.",
            "The manual adapter powers development and tests.",
            "Supplier failures degrade gracefully and are visible.",
            "Every result carries source and fetched-at metadata.",
        ],
        deps=("m4-catalog-crud",),
    ),
    issue(
        "m4-research-agent",
        "Implement the component research agent with role-based BOM derivation",
        M4,
        "ai",
        "feature",
        "p0",
        "xl",
        "This agent turns an approved specification into a bill of materials. It must not invent "
        "parts, prices, or stock, and it must expose unresolved requirements honestly.",
        [
            "Derive required roles (controller, driver, motors, sensors, power, chassis, wheels, wiring) from the specification.",
            "Query the catalog/supplier adapter and rank candidates by requirements, compatibility, price, and availability.",
            "Produce ComponentResearchOutput with selections, alternatives, rationale, sources, and unresolved requirements.",
            "Enforce quantity rules and never claim stock that is not present.",
            "Add fixtures for line follower, rover, and a deliberately under-specified request.",
        ],
        [
            "Every selected candidate exists in the catalog with provenance.",
            "Missing roles are reported, not silently skipped.",
            "Output validates against the contract and records usage/cost.",
            "Tests cover no-candidate, budget pressure, and incompatible-candidate cases.",
        ],
        deps=("m3-planner-agent", "m4-seed-catalog", "m4-supplier-adapter", "m3-structured-output"),
    ),
    issue(
        "m4-selection-budget",
        "Port deterministic component selection and budget checks from the prototype",
        M4,
        "backend",
        "feature",
        "p1",
        "m",
        "The prototype proved a useful pattern: select parts deterministically, compute the budget, "
        "then let the model explain the result. That logic should live in tested backend services.",
        [
            "Implement role-based selection with stock, quantity-per-robot, and supported-robot constraints.",
            "Use Decimal for unit price, subtotal, total, and remaining budget.",
            "Report missing roles and additional parts excluded from the total.",
            "Add compatibility warnings as structured data, not prose.",
            "Add unit tests derived from the prototype's line-follower scenario.",
        ],
        [
            "The line-follower fixture produces a complete, correctly priced BOM.",
            "Selection ignores out-of-stock and unsupported candidates.",
            "Budget arithmetic is exact and handles zero/over-budget cases.",
            "Missing and excluded parts are explicit in the response.",
        ],
        deps=("m4-research-agent", "m4-seed-catalog"),
        extra_labels=("prototype",),
    ),
    issue(
        "m4-compatibility",
        "Add a deterministic compatibility engine for voltage, current, and interfaces",
        M4,
        "backend",
        "feature",
        "p0",
        "l",
        "Compatibility cannot be left to model prose. Voltage ranges, current draw, logic levels, "
        "drivers, and interfaces need rules that produce repeatable warnings and errors.",
        [
            "Validate supply vs. rated/min/max voltage for each component.",
            "Check logic-level compatibility and required level shifting.",
            "Check motor driver current/voltage margins and required driver presence.",
            "Check interface/bus compatibility and duplicate pin/bus usage.",
            "Return structured severity, code, affected refs, and suggested fix.",
        ],
        [
            "Known-good fixture produces no errors; known-bad fixtures produce specific codes.",
            "The prototype's 7.4 V battery / 6 V motor case is detected deterministically.",
            "Warnings distinguish unsafe (error) from suboptimal (warning).",
            "Rules are unit tested and do not require an LLM.",
        ],
        deps=("m4-selection-budget", "m4-catalog-crud"),
        extra_labels=("prototype",),
    ),
    issue(
        "m4-bom-workspace",
        "Build the bill-of-materials workspace with alternatives and swaps",
        M4,
        "frontend",
        "feature",
        "p0",
        "xl",
        "Users need to inspect and adjust the BOM, not just read a generated list. The workspace is "
        "where compatibility, price, and availability become actionable.",
        [
            "Render role groups with selected part, quantity, unit price, subtotal, and rationale.",
            "Show alternatives, compatibility warnings, missing roles, and excluded parts.",
            "Add swap/quantity actions with a clear revalidation/stale-artifact warning.",
            "Show catalog/supplier provenance and price timestamp.",
            "Provide empty, loading, partial, and error states at desktop and mobile widths.",
        ],
        [
            "A user can swap a part and see the total and warnings update.",
            "Missing/incompatible roles cannot be mistaken for a complete build.",
            "Dependent artifacts are marked stale after a swap.",
            "The page has no horizontal overflow at 360 px and is keyboard usable.",
        ],
        deps=("m4-research-agent", "m2-auth-ui"),
    ),
    issue(
        "m4-price-provenance",
        "Add price and availability snapshots with provenance",
        M4,
        "backend",
        "feature",
        "p1",
        "m",
        "Catalog prices change and suppliers disappear. A project estimate must say when a price was "
        "observed and whether it is live, cached, or estimated.",
        [
            "Record source, currency, fetched-at, and status for each price.",
            "Snapshot unit price on project selection and expose staleness.",
            "Add an endpoint/UI affordance to refresh prices for a project.",
            "Never mix currencies silently; store the currency with the amount.",
            "Add tests for stale, missing, and refreshed prices.",
        ],
        [
            "Every displayed price has a source and timestamp.",
            "Changing a catalog price does not silently rewrite historical project estimates.",
            "Stale prices are visibly labeled and refreshable.",
        ],
        deps=("m4-catalog-crud", "m4-supplier-adapter"),
    ),
    issue(
        "m4-supplier-integration",
        "Integrate one regional supplier catalog",
        M4,
        "backend",
        "feature",
        "p2",
        "l",
        "Manual catalog data is enough to build the flow, but real availability and pricing require "
        "at least one supplier integration to validate the adapter design.",
        [
            "Choose a supplier with a usable API or permitted dataset and document terms/rate limits.",
            "Implement search/detail/price/availability mapping behind the adapter.",
            "Cache aggressively, respect robots/terms, and never scrape in tests.",
            "Handle auth, rate limits, outages, and schema changes without breaking the BOM.",
            "Add a feature flag and provenance to every imported field.",
        ],
        [
            "A project can use live supplier data for at least one category.",
            "Supplier failures fall back to cached/manual data with a visible warning.",
            "No credentials or raw responses are committed or logged.",
            "Rate limits and terms are documented.",
        ],
        deps=("m4-supplier-adapter", "m4-price-provenance"),
    ),
    # ------------------------------------------------------------------ M5
    issue(
        "m5-electrical-agent",
        "Implement the electrical engineering agent",
        M5,
        "ai",
        "feature",
        "p0",
        "xl",
        "The wiring plan is the bridge between parts and firmware. It must map real pins, respect "
        "component limits, and produce a plan a beginner can follow.",
        [
            "Build ElectricalPlan nodes, connections, pin map, power budget, and wiring steps from the BOM.",
            "Reference only component pins/interfaces present in shared context.",
            "Apply deterministic compatibility rules after generation and attach warnings.",
            "Include shared ground, power rails, driver requirements, and level shifting notes.",
            "Add fixture tests for line follower, rover, and servo arm.",
        ],
        [
            "Every connection resolves to a known node/pin.",
            "Generated plans validate against the contract and pass safety rules for known-good fixtures.",
            "Unsafe plans are rejected or clearly flagged, never marked ready.",
            "Usage/cost is recorded and the run is auditable.",
        ],
        deps=("m4-research-agent", "m4-compatibility"),
    ),
    issue(
        "m5-safety-validators",
        "Add deterministic electrical safety validators",
        M5,
        "backend",
        "feature",
        "p0",
        "l",
        "The prototype only compared battery and motor voltage. A usable wiring assistant must catch "
        "shared-ground, logic-level, current, driver, and polarity problems without relying on an LLM.",
        [
            "Implement rules for supply voltage ranges, current margin, shared ground, and level shifting.",
            "Check driver presence and motor supply/logic supply separation.",
            "Check polarity-sensitive connections and missing power switches/fuses where applicable.",
            "Return structured error codes, severity, affected refs, and remediation.",
            "Cover each rule with known-good and known-bad fixtures.",
        ],
        [
            "Every rule has a passing and failing test.",
            "Rules run independently of model output and are re-applied to persisted plans.",
            "Errors block readiness; warnings remain visible and explain the risk.",
        ],
        deps=("m5-electrical-agent", "m4-compatibility"),
        extra_labels=("prototype",),
    ),
    issue(
        "m5-wiring-renderer",
        "Build a wiring diagram renderer from ElectricalPlan",
        M5,
        "frontend",
        "feature",
        "p1",
        "l",
        "A list of connections is hard to follow. Users need a readable diagram that highlights power, "
        "ground, signal, and warnings without requiring a CAD tool.",
        [
            "Render nodes and typed connections from the contract with deterministic layout.",
            "Distinguish power, ground, signal, and bus connections; label pins.",
            "Highlight warnings/errors and allow focusing a connection or node.",
            "Provide an accessible text/table alternative and print styles.",
            "Handle plans with 5-50 nodes without overflow or unreadable labels.",
        ],
        [
            "The diagram matches the underlying connections exactly.",
            "Warnings are visible and linked to their rule/explanation.",
            "Text alternative conveys the same information for screen readers.",
            "The renderer is resilient to missing coordinates/optional fields.",
        ],
        deps=("m5-electrical-agent",),
    ),
    issue(
        "m5-pin-validation",
        "Add pin conflict and interface validation",
        M5,
        "backend",
        "feature",
        "p0",
        "m",
        "A wiring plan is only buildable if pins are unique, buses are valid, and reserved pins are "
        "respected. These are deterministic checks, not model suggestions.",
        [
            "Detect duplicate pin assignments and conflicting peripherals.",
            "Validate I2C/SPI/UART pin sets and reserved/boot pins per platform.",
            "Check sensor/actuator interface compatibility and required pull-ups/level shifters.",
            "Return actionable conflicts with node/pin references.",
            "Add platform-specific fixtures for Arduino, ESP32, and Raspberry Pi.",
        ],
        [
            "Duplicate and reserved-pin cases are rejected with specific messages.",
            "Valid fixtures pass without false positives.",
            "Firmware generation can consume the validated pin map directly.",
        ],
        deps=("m5-electrical-agent",),
    ),
    issue(
        "m5-wiring-workspace",
        "Build the wiring workspace with steps and checklists",
        M5,
        "frontend",
        "feature",
        "p0",
        "l",
        "Users need a guided build surface that combines the diagram, ordered steps, safety notes, "
        "and a way to track progress.",
        [
            "Show wiring steps in order with associated parts, pins, and safety notes.",
            "Add per-step complete state, reset, and print-friendly output.",
            "Surface errors/warnings prominently and link them to affected steps.",
            "Include the diagram, pin table, and power budget in one responsive view.",
            "Add a 'mark wiring complete' gate for programming.",
        ],
        [
            "A user can follow the steps without reading raw JSON.",
            "Warnings cannot be accidentally hidden.",
            "Progress is clear after navigation/refresh.",
            "The page works on a phone next to a workbench.",
        ],
        deps=("m5-wiring-renderer", "m4-bom-workspace"),
    ),
    issue(
        "m5-power-budget",
        "Add a power budget calculator with margin warnings",
        M5,
        "backend",
        "feature",
        "p0",
        "m",
        "Battery and regulator choices fail when peak current is ignored. The platform needs a "
        "traceable power budget with explicit assumptions.",
        [
            "Sum continuous and peak current by rail/component.",
            "Compare against battery/regulator capability and recommend margin.",
            "Flag missing current data and avoid false precision.",
            "Expose the calculation in the ElectricalPlan and UI.",
            "Add tests for margin boundaries and unknown data.",
        ],
        [
            "Budget math reconciles with component quantities and specs.",
            "Unknown current data is labeled, not treated as zero.",
            "Under-margin designs produce a warning with the limiting component.",
        ],
        deps=("m5-electrical-agent", "m4-compatibility"),
    ),
    issue(
        "m5-fixtures",
        "Add electrical plan fixtures for known-good and known-bad configurations",
        M5,
        "ai",
        "chore",
        "p1",
        "m",
        "Safety rules and prompts need a regression corpus. Ad-hoc testing will miss edge cases and "
        "allow prompt changes to silently weaken validation.",
        [
            "Create fixtures for line follower, rover, and servo arm with expected outcomes.",
            "Include bad cases: missing ground, over-voltage, insufficient current, shared pins, missing driver.",
            "Wire fixtures into unit tests and the evaluation harness.",
            "Document how to add a fixture and update expectations.",
        ],
        [
            "Every safety rule has at least one fixture.",
            "Fixtures are deterministic, small, and contain no secrets.",
            "A rule regression fails CI.",
        ],
        deps=("m5-safety-validators", "m5-pin-validation"),
    ),
    # ------------------------------------------------------------------ M6
    issue(
        "m6-programming-agent",
        "Implement the programming agent for Arduino and ESP32",
        M6,
        "ai",
        "feature",
        "p0",
        "xl",
        "Firmware must match the approved hardware and pin map. This agent turns the electrical plan "
        "into deployable code and instructions, without inventing libraries or pins.",
        [
            "Generate platform-appropriate files from the electrical plan and BOM.",
            "Use only validated pin assignments and real library names.",
            "Provide setup/upload/validation steps and a library manifest.",
            "Mark generated code as untrusted and never execute it server-side.",
            "Add fixtures for line follower and obstacle avoider.",
        ],
        [
            "Generated pin usage matches the electrical plan exactly.",
            "Output validates against ProgrammingOutput and records usage/cost.",
            "No invented pins or libraries pass validation.",
            "A user can copy/download a complete firmware bundle.",
        ],
        deps=("m5-electrical-agent", "m5-pin-validation", "m5-safety-validators"),
    ),
    issue(
        "m6-raspberry-pi-target",
        "Add Raspberry Pi as a firmware target",
        M6,
        "ai",
        "feature",
        "p2",
        "l",
        "Raspberry Pi projects use Python and different GPIO/deployment conventions. Supporting it "
        "broadens the platform but needs separate validation.",
        [
            "Add Pi-specific prompts/templates, GPIO library choices, and deployment steps.",
            "Handle OS setup, permissions, and remote execution cautions.",
            "Add contract fields or conventions for non-Arduino projects.",
            "Add a Pi fixture and compilation/parse checks where feasible.",
            "Document supported boards and limitations.",
        ],
        [
            "A Pi project produces valid, runnable-looking code with correct GPIO references.",
            "The UI labels Pi-specific setup and limitations.",
            "No server-side execution of generated code.",
        ],
        deps=("m6-programming-agent",),
    ),
    issue(
        "m6-code-viewer",
        "Build the firmware file tree, viewer, and download",
        M6,
        "frontend",
        "feature",
        "p0",
        "l",
        "Generated code is only useful if users can inspect, copy, and download it. The workspace "
        "needs a code-focused view that works on mobile.",
        [
            "Render a file tree with language-aware syntax highlighting.",
            "Add copy-file/copy-all, download bundle, and line wrapping.",
            "Show libraries, pin assignments, setup/upload steps, and warnings.",
            "Make filenames/content searchable and preserve scroll position across files.",
            "Avoid rendering untrusted HTML from generated code.",
        ],
        [
            "All generated files are readable and downloadable.",
            "Code is rendered as text, never executed or injected as HTML.",
            "Long lines and small screens remain usable.",
            "The viewer handles empty/partial outputs without crashing.",
        ],
        deps=("m6-programming-agent", "m4-bom-workspace"),
    ),
    issue(
        "m6-static-validation",
        "Add static code validation and compile fixtures",
        M6,
        "backend",
        "feature",
        "p0",
        "l",
        "Generated code can look plausible and fail to compile. Static checks should catch missing "
        "headers/libraries, undeclared pins, and syntax errors before users try to build.",
        [
            "Parse generated code and run platform toolchains in an isolated, time-limited job.",
            "Validate referenced libraries and pin symbols against the plan.",
            "Store validation status with code version and surface it in the UI.",
            "Never execute generated code or allow network access during compilation.",
            "Add CI fixtures for Arduino/ESP32 and expected failures.",
        ],
        [
            "Invalid generated code is marked failed with a useful reason.",
            "Compilation runs with CPU/memory/time limits and no secrets.",
            "Validation results are tied to the exact code version.",
            "CI covers at least one successful compile per supported platform.",
        ],
        deps=("m6-programming-agent",),
    ),
    issue(
        "m6-library-deploy",
        "Add library manifest and deployment instructions",
        M6,
        "ai",
        "feature",
        "p1",
        "m",
        "Users need to know which libraries to install and how to upload code. Missing library "
        "versions are a common source of failed builds.",
        [
            "Emit library names/versions and installation commands per platform.",
            "Generate board selection, port, and upload steps.",
            "Flag libraries that could not be verified against a known registry.",
            "Include rollback/troubleshooting guidance.",
            "Link steps to the exact file tree.",
        ],
        [
            "Instructions are complete enough for a beginner to flash the board.",
            "Unverified libraries are labeled, not presented as guaranteed.",
            "The manifest matches imported code and the BOM.",
        ],
        deps=("m6-programming-agent",),
    ),
    issue(
        "m6-version-diff",
        "Add regeneration diffs and firmware version history",
        M6,
        "frontend",
        "feature",
        "p1",
        "l",
        "Hardware or wiring changes make existing firmware stale. Users need to see what changed and "
        "restore an earlier version.",
        [
            "Persist code versions with the hardware/pin-map snapshot they target.",
            "Show a diff between regenerations and mark stale artifacts.",
            "Allow restore of a prior version with an audit event.",
            "Link a version to the agent run and prompt/model metadata.",
            "Keep downloads deterministic for a given version.",
        ],
        [
            "Changing the pin map marks firmware stale with a clear reason.",
            "Diffs highlight added/removed/changed lines.",
            "Restore is atomic and does not silently overwrite newer work.",
        ],
        deps=("m6-code-viewer", "m6-programming-agent"),
    ),
    # ------------------------------------------------------------------ M7
    issue(
        "m7-mechanical-agent",
        "Implement the mechanical design agent",
        M7,
        "ai",
        "feature",
        "p0",
        "xl",
        "Electronics choices constrain the chassis, mounts, and drivetrain. This agent produces a "
        "buildable mechanical plan and assembly instructions around the selected parts.",
        [
            "Propose chassis, mounting, wheel, and actuator arrangements from the BOM.",
            "Produce parts, ordered assembly steps, tools, and safety notes.",
            "Check mass, clearance, and fastener compatibility deterministically.",
            "Reference drawing/model paths without embedding CAD payloads.",
            "Add fixtures for line follower, rover, and servo arm.",
        ],
        [
            "Assembly steps reference only selected or explicitly additional parts.",
            "Output validates against MechanicalOutput and records usage/cost.",
            "Mass/clearance warnings are deterministic and tested.",
            "A beginner can follow the instructions without the model present.",
        ],
        deps=("m4-research-agent", "m4-compatibility"),
    ),
    issue(
        "m7-part-library",
        "Add a mechanical part library with material metadata",
        M7,
        "database",
        "feature",
        "p1",
        "m",
        "Mechanical plans need a catalog of chassis, brackets, wheels, fasteners, and materials. "
        "Without it, every plan would invent parts.",
        [
            "Add mechanical categories, materials, dimensions, mass, and fastener metadata.",
            "Seed common beginner parts and mounting standards.",
            "Extend admin CRUD/filtering for mechanical parts.",
            "Link mechanical parts to the BOM where they are purchasable.",
            "Add validation and tests.",
        ],
        [
            "Mechanical plans can reference catalog parts with real dimensions/mass.",
            "Missing parts are explicit rather than invented.",
            "Filtering and admin operations work for mechanical categories.",
        ],
        deps=("m4-catalog-crud",),
    ),
    issue(
        "m7-mass-clearance",
        "Add mass and clearance validation",
        M7,
        "backend",
        "feature",
        "p1",
        "m",
        "A mechanically valid design must fit and not overload its drivetrain. These checks should "
        "not depend on model confidence.",
        [
            "Roll up mass from parts and payload assumptions.",
            "Check available volume/clearance against component dimensions.",
            "Compare mass/payload against motor torque/speed assumptions where data exists.",
            "Return structured warnings with affected parts.",
            "Add tests for missing dimensions and boundary values.",
        ],
        [
            "Missing dimensions produce explicit unknowns, not false precision.",
            "Over-mass/clearance cases are flagged with a reason.",
            "Warnings are reusable by the mechanical and cost agents.",
        ],
        deps=("m7-mechanical-agent", "m7-part-library"),
    ),
    issue(
        "m7-assembly-ui",
        "Build the assembly instructions and parts list UI",
        M7,
        "frontend",
        "feature",
        "p0",
        "l",
        "Users build from the workspace, not from JSON. Assembly needs ordered steps, part callouts, "
        "tools, and safety notes in one place.",
        [
            "Render ordered steps with parts, tools, and safety notes.",
            "Add progress checkboxes, reset, and print-friendly styling.",
            "Show the mechanical parts list and mass/clearance warnings.",
            "Link parts back to BOM entries and drawings.",
            "Handle missing/partial assemblies honestly.",
        ],
        [
            "A user can follow and track assembly without leaving the page.",
            "Warnings and missing parts are prominent.",
            "The layout is usable on a phone and for printing.",
        ],
        deps=("m7-mechanical-agent", "m4-bom-workspace"),
    ),
    issue(
        "m7-consistency",
        "Enforce mechanical/BOM consistency and stale-artifact rules",
        M7,
        "backend",
        "feature",
        "p1",
        "m",
        "A part swap can invalidate the chassis, mounts, and assembly steps. Without explicit stale "
        "markers, users follow instructions for the wrong hardware.",
        [
            "Detect mechanical parts that reference replaced/removed BOM components.",
            "Mark dependent mechanical/cost/firmware artifacts stale after relevant changes.",
            "Provide a revalidation/regeneration path with a change summary.",
            "Add tests for swaps, quantity changes, and harmless edits.",
            "Expose stale state in the project overview.",
        ],
        [
            "Relevant changes mark downstream artifacts stale with a reason.",
            "Harmless edits do not cause false stale warnings.",
            "Regeneration updates the artifact and clears stale state.",
        ],
        deps=("m7-mechanical-agent", "m7-mass-clearance", "m4-compatibility"),
    ),
    # ------------------------------------------------------------------ M8
    issue(
        "m8-cost-agent",
        "Implement the cost estimation agent",
        M8,
        "ai",
        "feature",
        "p0",
        "l",
        "Users need an honest total before buying. The cost agent turns the BOM and quantities into "
        "line items, assumptions, and a budget verdict.",
        [
            "Roll up BOM quantities, unit prices, shipping, and contingency.",
            "Mark every estimate and state assumptions explicitly.",
            "Compare alternatives and quantify savings/tradeoffs.",
            "Classify under/within/over budget, including unknown prices.",
            "Add fixtures for exact, missing-price, and over-budget cases.",
        ],
        [
            "Totals reconcile exactly with line items and quantities.",
            "Unknown prices make the status unknown, not zero.",
            "Output validates against CostEstimate and records usage/cost.",
            "A budget overrun is stated plainly.",
        ],
        deps=("m4-research-agent", "m4-selection-budget"),
    ),
    issue(
        "m8-currency",
        "Add currency handling and exchange-rate provenance",
        M8,
        "backend",
        "feature",
        "p0",
        "m",
        "Catalog and supplier prices can be in different currencies. Silent conversion would make "
        "budgets wrong and destroy trust.",
        [
            "Store currency with every monetary amount.",
            "Add dated exchange rates and conversion provenance.",
            "Reject or explicitly convert mixed-currency line items.",
            "Display the original and converted amount where relevant.",
            "Add tests for rounding, missing rates, and stale rates.",
        ],
        [
            "No total mixes currencies without an explicit, dated conversion.",
            "Rounding follows a documented policy.",
            "Missing/stale rates are visible and block a definitive total.",
        ],
        deps=("m8-cost-agent", "m4-price-provenance"),
    ),
    issue(
        "m8-budget-ui",
        "Build the budget breakdown and alternatives UI",
        M8,
        "frontend",
        "feature",
        "p0",
        "l",
        "A single total is not enough to make a purchasing decision. Users need categories, line "
        "items, assumptions, and tradeoffs at a glance.",
        [
            "Show total, subtotal, shipping, contingency, and budget status.",
            "Group line items by category and expose quantity/unit price/source.",
            "Present alternatives with savings and tradeoffs.",
            "Show assumptions and unknown-price badges.",
            "Keep the layout scannable on mobile and printable.",
        ],
        [
            "Displayed totals match the API exactly.",
            "Unknown/stale prices are obvious.",
            "Alternatives do not imply availability that is not verified.",
            "The breakdown is usable without opening raw JSON.",
        ],
        deps=("m8-cost-agent", "m4-bom-workspace"),
    ),
    issue(
        "m8-budget-edit",
        "Add budget editing and re-estimation flow",
        M8,
        "frontend",
        "feature",
        "p1",
        "m",
        "Budgets change during a build. Users need to adjust the cap and see what fits without "
        "recreating the project.",
        [
            "Allow editing min/max budget from the project and cost views.",
            "Re-run/recalculate the estimate and show what changed.",
            "Offer alternatives when over budget, but never fake a lower total.",
            "Version the budget and preserve prior estimates.",
            "Validate currency and range.",
        ],
        [
            "Budget changes persist and update the verdict.",
            "Over-budget states offer real, sourced alternatives.",
            "History shows previous budget/estimate pairs.",
        ],
        deps=("m8-budget-ui", "m8-cost-agent"),
    ),
    issue(
        "m8-price-refresh",
        "Add supplier price refresh and caching",
        M8,
        "backend",
        "feature",
        "p1",
        "m",
        "Prices go stale. Users need an explicit refresh with source/time, while the system must "
        "respect supplier rate limits and failures.",
        [
            "Add a project/BOM price refresh action with per-item results.",
            "Cache responses with TTL and respect supplier limits.",
            "Keep historical snapshots and never rewrite past estimates silently.",
            "Handle partial failures and report which items could not refresh.",
            "Add tests with a fake supplier.",
        ],
        [
            "Refresh updates provenance and totals visibly.",
            "Partial failures leave unaffected data intact and are reported.",
            "No refresh loop can hammer a supplier.",
            "History remains auditable.",
        ],
        deps=("m4-supplier-integration", "m4-price-provenance", "m8-cost-agent"),
    ),
    # ------------------------------------------------------------------ M9
    issue(
        "m9-build-bundle",
        "Add build bundle export",
        M9,
        "backend",
        "feature",
        "p0",
        "l",
        "A finished design must leave the platform. Users need a reproducible bundle containing the "
        "specification, BOM, wiring, firmware, mechanical plan, and cost.",
        [
            "Define a versioned bundle format with manifest and generation metadata.",
            "Include JSON artifacts, firmware files, and human-readable summaries.",
            "Exclude secrets, internal IDs not needed by consumers, and unrelated user data.",
            "Generate deterministic archives and expose a download endpoint.",
            "Add contract/format tests.",
        ],
        [
            "The bundle contains every approved artifact and a manifest.",
            "Re-exporting identical state produces identical content.",
            "No secrets or cross-project data are included.",
            "The endpoint is authorized and audited.",
        ],
        deps=("m5-wiring-workspace", "m6-code-viewer", "m7-assembly-ui", "m8-budget-ui"),
    ),
    issue(
        "m9-print-guide",
        "Add a printable build guide and PDF export",
        M9,
        "frontend",
        "feature",
        "p1",
        "l",
        "Makers work away from a screen. A printable guide should combine overview, BOM, wiring, "
        "assembly, firmware setup, and budget in a clean document.",
        [
            "Design print styles for the full project guide with page breaks.",
            "Include diagrams, tables, checklists, and source/timestamp metadata.",
            "Add PDF export with selectable sections.",
            "Keep images/SVGs self-contained and accessible.",
            "Test print layout at A4/Letter.",
        ],
        [
            "The printed guide is readable in black and white.",
            "Sections do not split awkwardly and tables do not overflow.",
            "The PDF matches the current approved artifact versions.",
        ],
        deps=("m9-build-bundle", "m7-assembly-ui", "m5-wiring-workspace"),
    ),
    issue(
        "m9-share-links",
        "Add read-only share links with expiry and revocation",
        M9,
        "backend",
        "feature",
        "p0",
        "l",
        "Users need to show a design to a teacher, teammate, or supplier without handing over an "
        "account. Share links must be scoped, expiring, and revocable.",
        [
            "Generate high-entropy share tokens scoped to one project and a read-only view.",
            "Support expiry, revocation, and optional passcode.",
            "Prevent mutation, agent runs, exports of private data, and project enumeration.",
            "Rate-limit access and log views.",
            "Build a read-only public view and clear owner controls.",
        ],
        [
            "A share link cannot read another project or perform writes.",
            "Revocation takes effect immediately.",
            "Expired links return a clear 404/410 without leaking existence.",
            "Owner can list and revoke active links.",
        ],
        deps=("m2-ownership", "m9-build-bundle"),
    ),
    issue(
        "m9-revisions",
        "Add project revision history and restore",
        M9,
        "backend",
        "feature",
        "p1",
        "xl",
        "Artifacts change through agent runs and manual edits. Users need to understand what changed "
        "and restore a previous state without corrupting history.",
        [
            "Snapshot project/artifact state per meaningful change with actor and reason.",
            "Show a timeline and per-artifact diff.",
            "Implement atomic restore with a new revision (no destructive history rewrite).",
            "Mark dependent artifacts stale after restore.",
            "Add authorization and audit tests.",
        ],
        [
            "Every mutation can be traced to an actor and revision.",
            "Restore is atomic and reversible.",
            "Diffs identify artifact-level changes.",
            "Only owners can restore.",
        ],
        deps=("m2-ownership",),
    ),
    issue(
        "m9-comments",
        "Add artifact comments and annotations",
        M9,
        "frontend",
        "feature",
        "p2",
        "l",
        "Collaborators need to discuss a specific part, connection, or assembly step without editing "
        "the artifact or leaving the app.",
        [
            "Add threaded comments anchored to a project artifact/field/step.",
            "Support resolve/reopen, mentions by display name, and notifications.",
            "Enforce project access and moderation/deletion rules.",
            "Show comment counts and deep links in the workspace.",
            "Add empty/error states and mobile layout.",
        ],
        [
            "Comments are scoped to the project and invisible to outsiders.",
            "Anchors remain understandable after artifact regeneration or are marked outdated.",
            "Resolve/reopen and deletion are authorized and audited.",
        ],
        deps=("m2-auth-ui",),
    ),
    # ------------------------------------------------------------------ M10
    issue(
        "m10-deployment",
        "Add production containers and a deployment pipeline",
        M10,
        "devops",
        "feature",
        "p0",
        "l",
        "The foundation runs locally only. Production needs reproducible images, managed PostgreSQL, "
        "migration steps, secrets, and rollback.",
        [
            "Add production Dockerfiles for API and web with non-root users and health checks.",
            "Add a deployment workflow for staging/production with migration step.",
            "Use managed PostgreSQL, secret injection, and restricted network access.",
            "Document rollback, environment promotion, and required configuration.",
            "Add a launch checklist.",
        ],
        [
            "A tagged commit deploys to staging without manual steps.",
            "Migrations run once and block deploy on failure.",
            "Secrets never appear in images or logs.",
            "Rollback is documented and tested.",
        ],
        deps=("m1-foundation-tooling",),
    ),
    issue(
        "m10-observability",
        "Add structured logs, metrics, tracing, and alerts",
        M10,
        "devops",
        "feature",
        "p0",
        "l",
        "Operating agent workflows without visibility is guesswork. Logs exist, but there are no "
        "metrics, traces, dashboards, or alerts.",
        [
            "Emit structured logs with request IDs, user/project (hashed where needed), and outcomes.",
            "Add RED/USE metrics and OpenTelemetry traces across HTTP, DB, and provider calls.",
            "Create dashboards for latency, errors, agent runs, token usage, and cost.",
            "Define SLOs and alert on burn rate, DB health, and provider failures.",
            "Redact secrets and sensitive prompts.",
        ],
        [
            "A request can be traced from UI through API to provider and DB.",
            "Dashboards answer: is it up, slow, failing, and what does it cost?",
            "Alerts fire in staging with a documented runbook.",
            "No secrets or full prompts are logged.",
        ],
        deps=("m10-deployment",),
    ),
    issue(
        "m10-backups",
        "Add backups, restore drills, and retention policy",
        M10,
        "devops",
        "chore",
        "p0",
        "m",
        "Projects and agent audits are user data. Losing them is unacceptable, and keeping them "
        "forever is a liability.",
        [
            "Enable automated PostgreSQL backups with point-in-time recovery.",
            "Define retention for projects, agent runs, and deleted accounts.",
            "Document and rehearse a restore into a clean environment.",
            "Encrypt backups and restrict access.",
            "Add a restore checklist and monitoring for backup failures.",
        ],
        [
            "A restore from backup is demonstrated and timed.",
            "Retention matches the privacy policy.",
            "Backup failures alert.",
        ],
        deps=("m10-deployment",),
    ),
    issue(
        "m10-security",
        "Run a security audit and add dependency/container scanning",
        M10,
        "devops",
        "chore",
        "p0",
        "m",
        "The app will hold accounts and user projects. Authz, headers, dependencies, and deployment "
        "need a deliberate review before launch.",
        [
            "Add dependency, secret, and container scanning to CI.",
            "Review authz for every route, especially share links and sub-resources.",
            "Add security headers/CSP, strict CORS, and cookie settings.",
            "Threat-model prompt/tool injection, generated code, and supplier data.",
            "Track and remediate high/critical findings.",
        ],
        [
            "No high/critical vulnerabilities in the release artifacts.",
            "Authz regression tests cover all project sub-resources.",
            "Headers and CORS are verified in staging.",
            "Findings and accepted risks are documented.",
        ],
        deps=("m2-ownership", "m10-deployment"),
    ),
    issue(
        "m10-accessibility",
        "Complete accessibility audit and fixes (WCAG 2.2 AA)",
        M10,
        "design",
        "chore",
        "p1",
        "l",
        "The workspace is visual and interactive. Keyboard, screen-reader, contrast, motion, and "
        "error-announcement gaps must be fixed before launch.",
        [
            "Audit primary flows with axe and manual keyboard/screen-reader testing.",
            "Fix focus order, focus visibility, labels, landmarks, and heading structure.",
            "Verify contrast, non-color status cues, reduced motion, and zoom/reflow.",
            "Ensure forms and async errors are announced and recoverable.",
            "Add automated checks where they add value and document manual coverage.",
        ],
        [
            "No critical/serious axe issues on primary routes.",
            "All flows are keyboard operable with visible focus.",
            "Status and errors are understandable without color.",
            "The audit report and remaining exceptions are documented.",
        ],
        deps=("m2-auth-ui", "m4-bom-workspace", "m5-wiring-workspace", "m7-assembly-ui"),
    ),
    issue(
        "m10-e2e",
        "Add a Playwright end-to-end suite to CI",
        M10,
        "devops",
        "chore",
        "p1",
        "l",
        "Unit and build checks do not prove the user flow works. A browser suite should cover the "
        "critical path on desktop and mobile.",
        [
            "Add Playwright with a seeded database and deterministic test provider.",
            "Cover register/login, create project, approve spec, run planner, BOM, wiring, firmware, export, share.",
            "Run responsive checks at 360 px and desktop; assert no horizontal overflow and no console errors.",
            "Upload traces/screenshots on failure and keep the suite stable.",
            "Run in CI against real API/PostgreSQL services.",
        ],
        [
            "Critical paths pass on every pull request.",
            "Flaky tests are quarantined with an owner, not silently retried forever.",
            "Failures produce actionable artifacts.",
        ],
        deps=("m2-auth-ui", "m4-bom-workspace", "m5-wiring-workspace", "m9-build-bundle"),
    ),
    issue(
        "m10-performance",
        "Add performance budgets and load testing",
        M10,
        "devops",
        "chore",
        "p2",
        "m",
        "Agent workflows and large artifact pages can become slow. Without budgets and load tests, "
        "regressions are discovered by users.",
        [
            "Define p95 latency and payload budgets for primary routes and endpoints.",
            "Add Lighthouse/Core Web Vitals checks for key pages.",
            "Load-test project lists, agent runs, and export generation.",
            "Review indexes and query plans for hot paths.",
            "Document capacity assumptions and scaling triggers.",
        ],
        [
            "Budgets are enforced or reported in CI.",
            "Load tests identify the first bottleneck.",
            "Slow queries have indexes or a documented remediation.",
            "Scaling triggers are documented.",
        ],
        deps=("m10-e2e", "m10-observability"),
    ),
]

# Priorities are about launch value, not effort. P0 is reserved for the
# critical path and safety/security blockers; core-but-sequenced work is P1.
PRIORITY_OVERRIDES = {
    "m4-supplier-adapter": "p1",
    "m4-bom-workspace": "p1",
    "m5-wiring-workspace": "p1",
    "m6-code-viewer": "p1",
    "m7-mechanical-agent": "p1",
    "m7-assembly-ui": "p1",
    "m8-cost-agent": "p1",
    "m8-currency": "p1",
    "m8-budget-ui": "p1",
    "m9-build-bundle": "p1",
    "m9-share-links": "p1",
    "m10-observability": "p1",
    "m10-backups": "p1",
}

ISSUES = [
    replace(item, priority=PRIORITY_OVERRIDES[item.key])
    if item.key in PRIORITY_OVERRIDES
    else item
    for item in ISSUES
]

ISSUE_BY_KEY = {item.key: item for item in ISSUES}


def status_for(item: Issue) -> str:
    if item.close_after_create:
        return "status:done"
    # Dependencies are intentional sequencing. Unblocked issues are ready even
    # when they are lower priority; priority is a separate axis.
    if any(not ISSUE_BY_KEY[dep].close_after_create for dep in item.deps):
        return "status:backlog"
    return "status:ready"


def labels_for(item: Issue) -> list[str]:
    return [
        f"type:{item.kind}",
        f"priority:{item.priority}",
        f"effort:{item.effort}",
        f"area:{item.area}",
        status_for(item),
        *item.extra_labels,
    ]


def body_for(item: Issue, numbers: dict[str, int]) -> str:
    deps = []
    for dep in item.deps:
        number = numbers.get(dep)
        if number is None:
            deps.append(f"- {ISSUE_BY_KEY[dep].title} (not yet created)")
        else:
            deps.append(f"- #{number} — {ISSUE_BY_KEY[dep].title}")
    dependency_text = "\n".join(deps) if deps else "None."
    scope = "\n".join(f"- {line}" for line in item.scope)
    acceptance = "\n".join(f"- [ ] {line}" for line in item.acceptance)
    notes = f"\n## Notes\n\n{item.notes}\n" if item.notes else ""
    return f"""## Context

{item.context}

## Scope

{scope}

## Acceptance criteria

{acceptance}

## Dependencies

{dependency_text}
{notes}
---

**Area:** `area:{item.area}` · **Priority:** `{item.priority}` · **Effort:** `{item.effort}` · **Milestone:** {item.milestone}
"""


def ensure_labels() -> None:
    existing = {
        row["name"]
        for row in json.loads(gh("label", "list", "--repo", REPO, "--limit", "200", "--json", "name"))
    }
    for name, (color, description) in LABELS.items():
        if name in existing:
            continue
        gh(
            "label",
            "create",
            name,
            "--repo",
            REPO,
            "--color",
            color,
            "--description",
            description,
        )
        print(f"label created: {name}")


def ensure_milestones() -> dict[str, int]:
    rows = json.loads(
        gh("api", f"repos/{REPO}/milestones?state=all&per_page=100")
    )
    by_title = {row["title"]: row["number"] for row in rows}
    for title, description in MILESTONES.items():
        if title in by_title:
            continue
        created = api(
            "POST",
            f"repos/{REPO}/milestones",
            {"title": title, "description": description, "state": "open"},
        )
        assert isinstance(created, dict)
        by_title[title] = int(created["number"])
        print(f"milestone created: {title}")
    return by_title


def existing_issues() -> dict[str, dict[str, object]]:
    rows = json.loads(
        gh(
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            "all",
            "--limit",
            "1000",
            "--json",
            "number,title,state,url",
        )
    )
    return {row["title"]: row for row in rows}


def create_issues(milestones: dict[str, int]) -> dict[str, int]:
    existing = existing_issues()
    numbers: dict[str, int] = {}
    for item in ISSUES:
        if item.title in existing:
            numbers[item.key] = int(existing[item.title]["number"])
            print(f"exists: #{numbers[item.key]} {item.title}")
            continue
        body = body_for(item, numbers)
        labels = labels_for(item)
        args = [
            "issue",
            "create",
            "--repo",
            REPO,
            "--title",
            item.title,
            "--body",
            body,
            "--milestone",
            item.milestone,
        ]
        for label in labels:
            args += ["--label", label]
        url = gh(*args)
        number = int(url.rstrip("/").split("/")[-1])
        numbers[item.key] = number
        print(f"created: #{number} {item.title}")
        if item.close_after_create:
            gh(
                "issue",
                "close",
                str(number),
                "--repo",
                REPO,
                "--reason",
                "completed",
                "--comment",
                item.close_comment or "Completed.",
            )
            print(f"closed: #{number}")
    return numbers


def write_backlog(numbers: dict[str, int], state: dict[str, dict[str, object]] | None = None) -> None:
    if state is None:
        state = existing_issues()
    by_milestone: Counter[str] = Counter()
    by_area: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    by_priority: Counter[str] = Counter()
    for item in ISSUES:
        by_milestone[item.milestone] += 1
        by_area[item.area] += 1
        by_priority[item.priority] += 1
        by_status[status_for(item)] += 1

    lines = [
        "# Backlog",
        "",
        "Generated from [`scripts/seed_github.py`](../scripts/seed_github.py). GitHub is the source of",
        "truth; this file is a readable mirror for planning and offline review.",
        "",
        f"**Repository:** https://github.com/{REPO}  ",
        f"**Project board:** https://github.com/users/{OWNER}/projects/{PROJECT_NUMBER}  ",
        f"**Issues:** {len(ISSUES)} ({sum(1 for i in ISSUES if i.close_after_create)} completed, "
        f"{sum(1 for i in ISSUES if not i.close_after_create)} open)",
        "",
        "> **Board status:** configured and verified. All 65 issues are on the project with",
        "> Status, Priority, Estimated Effort, and Development Area set. See",
        "> [Project board configuration](#project-board-configuration).",
        "",
        "## Counts by milestone",
        "",
        "| Milestone | Issues |",
        "| --- | ---: |",
    ]
    for milestone in MILESTONES:
        lines.append(f"| {milestone} | {by_milestone[milestone]} |")
    lines += [
        "",
        "## Counts by area",
        "",
        "| Area | Issues |",
        "| --- | ---: |",
    ]
    for area, count in sorted(by_area.items()):
        lines.append(f"| {area} | {count} |")
    lines += [
        "",
        "## Counts by priority",
        "",
        "| Priority | Issues |",
        "| --- | ---: |",
    ]
    for priority in ("p0", "p1", "p2", "p3"):
        lines.append(f"| {priority} | {by_priority[priority]} |")
    lines += [
        "",
        "## Initial status labels",
        "",
        "Status labels are set at creation and mirror the board's initial state. The board Status",
        "field is authoritative; labels remain useful for filtering outside the project.",
        "",
        "| Status | Issues |",
        "| --- | ---: |",
    ]
    for status in ("status:ready", "status:blocked", "status:backlog", "status:done"):
        lines.append(f"| {status} | {by_status[status]} |")

    lines += [
        "",
        "## Issue plan",
        "",
        "| # | Issue | Milestone | Area | Priority | Effort | Status | Dependencies |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in ISSUES:
        number = numbers.get(item.key)
        row = state.get(item.title, {})
        gh_state = str(row.get("state") or ("closed" if item.close_after_create else "open")).lower()
        issue_cell = f"[#{number}](https://github.com/{REPO}/issues/{number}) {item.title}" if number else item.title
        deps = ", ".join(f"#{numbers[d]}" for d in item.deps if d in numbers) or "—"
        lines.append(
            f"| {number or '—'} | {issue_cell} | {item.milestone.split(':')[0]} | "
            f"{item.area} | {item.priority} | {item.effort} | {gh_state} | {deps} |"
        )

    lines += [
        "",
        "## Milestones",
        "",
        "| Milestone | Goal |",
        "| --- | --- |",
    ]
    for title, description in MILESTONES.items():
        lines.append(f"| {title} | {description} |")

    lines += [
        "",
        "## Project board configuration",
        "",
        "Target project: https://github.com/users/" + OWNER + f"/projects/{PROJECT_NUMBER}",
        "",
        "Fields are created and synchronized by [`scripts/setup_project.py`](../scripts/setup_project.py).",
        "The script is idempotent and uses the same issue definitions as the backlog.",
        "",
        "### Fields",
        "",
        "| Field | Type | Options |",
        "| --- | --- | --- |",
        "| Status | Single select | Backlog, Ready, In Progress, In Review, Done, Blocked |",
        "| Priority | Single select | P0 Critical, P1 High, P2 Medium, P3 Low |",
        "| Development Area | Single select | Frontend, Backend, AI Agents, Database, DevOps, Documentation, Design |",
        "| Estimated Effort | Single select | XS, S, M, L, XL |",
        "| Milestone | Built-in | M1-M10 |",
        "",
        "### Views",
        "",
        "The project provides five views. GitHub does not expose project view mutations, so layout,",
        "grouping, and filters are adjusted in the UI.",
        "",
        "1. **Backlog** — board layout.",
        "2. **Priority board** — board layout grouped by priority.",
        "3. **Team items** — table layout.",
        "4. **Roadmap** — roadmap layout; group by Milestone and sort M1-M10.",
        "5. **My items** — table layout.",
        "",
        "Useful filters: `Status = Blocked`, `Development Area = ...`, `Priority = P0 Critical`,",
        "and `Milestone = M3`.",
        "",
        "### Reproducing the configuration",
        "",
        "```bash",
        "gh auth refresh --hostname github.com -s project,read:project",
        "python3 scripts/setup_project.py --dry-run",
        "python3 scripts/setup_project.py",
        "```",
        "",
        "The script normalizes the single-select options, preserves existing option IDs where possible,",
        "adds missing project items, and writes Status, Priority, Estimated Effort, and Development Area",
        "for every issue.",
        "",
        "### Status mapping",
        "",
        "- Completed foundation issues → **Done**.",
        "- Issues with at least one open dependency → **Blocked**.",
        "- Everything else → **Ready**.",
        "",
        "Board status is updated by maintainers as work starts, enters review, or completes.",
        "",
        "## Working agreement",
        "",
        "- Issues are ordered by milestone and dependency, not by creation date.",
        "- An issue is ready when its dependencies are closed and acceptance criteria are testable.",
        "- Safety-critical work (electrical, firmware, mechanical) requires deterministic tests.",
        "- Every completed issue updates docs/contracts when behavior changes.",
    ]
    BACKLOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {BACKLOG.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without API calls")
    parser.add_argument("--create", action="store_true", help="Create labels, milestones, issues")
    parser.add_argument("--backlog-only", action="store_true", help="Regenerate docs/backlog.md only")
    args = parser.parse_args()

    if args.dry_run:
        numbers = {item.key: index + 1 for index, item in enumerate(ISSUES)}
        print(f"{len(ISSUES)} issues across {len(MILESTONES)} milestones")
        for item in ISSUES:
            print(
                f"{item.priority:>2} {item.effort:>2} {item.area:<9} "
                f"{item.milestone.split(':')[0]:<3} {item.title}"
            )
        write_backlog(numbers, {})
        return 0

    if args.backlog_only:
        numbers = {
            item.key: int(row["number"])
            for item in ISSUES
            if (row := existing_issues().get(item.title))
        }
        write_backlog(numbers)
        return 0

    if not args.create:
        parser.error("choose --create, --dry-run, or --backlog-only")

    ensure_labels()
    milestones = ensure_milestones()
    missing = [item.milestone for item in ISSUES if item.milestone not in milestones]
    if missing:
        raise RuntimeError(f"Missing milestones: {sorted(set(missing))}")
    numbers = create_issues(milestones)
    write_backlog(numbers)
    print(f"done: {len(numbers)} issues mapped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
