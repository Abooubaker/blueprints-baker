# Contributing to Blueprints Baker

Thanks for helping build a better way to design robots. This document covers the workflow, quality
bar, and conventions used in this repository.

## Code of conduct

Be direct about problems, generous with context, and respectful of people. Review the code, not the
author. Harassment or discrimination is not welcome.

## Before you start

- Read the [architecture](docs/architecture.md), [development](docs/development.md), and
  [AI agent](docs/ai-agents.md) docs.
- Check the [roadmap](docs/roadmap.md) and the GitHub Project board for current priorities.
- For a non-trivial change, open an issue (or comment on the existing one) before writing code.
  This avoids duplicated effort and keeps the design review small.

## Local setup

```bash
git clone https://github.com/Abooubaker/blueprints-baker.git
cd blueprints-baker
docker compose up -d db

cd apps/api
cp .env.example .env
uv sync
uv run alembic upgrade head

cd ../web
cp .env.example .env.local
npm ci
```

Then run the API and web app in separate terminals:

```bash
make dev-api
make dev-web
```

Full instructions, including tests and troubleshooting, are in
[docs/development.md](docs/development.md).

## Branch and commit conventions

- Branch from `main`: `feat/component-catalog`, `fix/budget-validation`, `docs/agent-contracts`,
  `chore/ci-cache`.
- Use imperative, scoped commit subjects:
  `feat(api): expose component catalog filters`,
  `fix(web): keep project cards from overflowing on mobile`,
  `docs(ai): explain artifact ownership`.
- Keep commits reviewable. Separate refactors from behavior changes.
- Never commit `.env` files, credentials, dumps, or generated secrets.

## What "done" means

A pull request is ready when:

1. The behavior is implemented, including edge cases and error states.
2. Tests cover the new behavior; bug fixes include a regression test.
3. `make check` passes locally (Ruff, mypy, pytest, ESLint, TypeScript, Prettier, production build).
4. API changes update `packages/contracts` via `make contracts` and the docs.
5. Database changes include a reversible Alembic migration that upgrades cleanly from `head`.
6. Documentation and the roadmap/issue status are updated.
7. No secrets, debugging leftovers, or unrelated formatting noise are included.

## Backend standards

- Python 3.12, full type hints, `from __future__ import annotations` in application modules.
- Keep HTTP concerns in `app/api`, use-cases in `app/services`, persistence in `app/models`, and
  pure domain/agent logic in `app/ai`.
- Raise domain exceptions from `app/core/errors.py`; the global handlers produce the error envelope.
- All database access goes through the async `AsyncSession` dependency. Do not create ad-hoc engines
  in request handlers.
- New settings belong in `Settings` with a safe default and an `.env.example` entry.
- Migrations are generated with Alembic and reviewed by hand. Verify both `upgrade head` and
  `downgrade base` on PostgreSQL before opening a PR.

Commands run from `apps/api`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

## Frontend standards

- TypeScript strict mode, React Server Components by default; add `"use client"` only for
  interaction, browser APIs, or hooks.
- Reuse the primitives in `src/components/ui` instead of one-off styles.
- Keep API calls in `src/lib/api.ts`; do not call `fetch` from components.
- UI-facing types live in `src/lib/types.ts`. `src/lib/api-schema.ts` is generated — do not edit it.
- Every route must work on mobile (360 px wide) without horizontal overflow.
- Prefer semantic HTML and keyboard-accessible controls; visible focus states are required.
- Use Tailwind theme tokens (CSS variables) rather than hard-coded colors.

Commands run from `apps/web`:

```bash
npm run lint
npm run typecheck
npm run format:check
npm run build
```

## Contracts

The OpenAPI document and agent JSON Schemas are generated artifacts committed for consumers:

```bash
make contracts   # runs scripts/export_contracts.py, then npm run codegen
```

Do not hand-edit `packages/contracts/openapi.json`, `packages/contracts/schemas/*`, or
`apps/web/src/lib/api-schema.ts`. If a contract changes intentionally, include the regenerated files
in the same pull request and call out the change in the description.

## AI agent contributions

- Agents depend on the `LLMProvider` abstraction, never on a vendor SDK.
- Inputs and outputs are Pydantic contracts in `app/ai/contracts.py`; unknown fields are rejected.
- An agent owns exactly one shared-context slot and must not mutate another agent's artifact.
- Dependencies are declared on the agent class and re-validated by the orchestrator.
- Model output must be validated before it is applied. Invalid output becomes `failed`, not a
  best-effort partial artifact.
- Add contract tests and orchestration tests that do not require network access.

See [docs/ai-agents.md](docs/ai-agents.md) for the pipeline and a step-by-step guide to implementing
a placeholder agent.

## Review process

- Keep pull requests focused; large PRs should explain why they cannot be split.
- A reviewer may request changes, ask questions, or approve. At least one approval is required.
- Address review comments with new commits; avoid force-pushing during review unless asked.
- Squash merge is preferred; the PR title becomes the commit subject.

## Reporting bugs and proposing features

Use the issue templates. Include reproduction steps, expected vs. actual behavior, environment, and
screenshots for UI issues. For security problems, do not open a public issue — contact the maintainer
privately.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
