# Development guide

This guide covers local setup, everyday commands, testing, contracts, and conventions. For system
design see [architecture.md](architecture.md); for endpoint payloads see [api.md](api.md).

## Prerequisites

| Tool | Version | Check |
| --- | --- | --- |
| Python | 3.12–3.14 | `python --version` |
| uv | current | `uv --version` |
| Node.js | 20.9+ (22 LTS recommended) | `node --version` |
| npm | 10+ | `npm --version` |
| PostgreSQL | 16 | `psql --version` |
| Docker + Compose | optional, for the dev database | `docker compose version` |

No AI provider account or API key is required. The default provider is a deterministic offline mock.

## First-time setup

```bash
git clone https://github.com/Abooubaker/robocraft.git
cd robocraft

# 1. Database (or use an existing PostgreSQL 16 instance)
docker compose up -d db

# 2. API
cd apps/api
cp .env.example .env
uv sync
uv run alembic upgrade head
cd ../..

# 3. Web
cd apps/web
cp .env.example .env.local
npm ci
cd ../..
```

If port 5432 is already in use, set `POSTGRES_PORT` in the repository-root `.env` and use the same
port in `apps/api/.env`'s `DATABASE_URL`.

## Running services

```bash
make dev-api    # http://localhost:8000  (OpenAPI: /docs)
make dev-web    # http://localhost:3000
```

Run them in separate terminals. The web app reads `NEXT_PUBLIC_API_URL` at build/start time and
defaults to `http://localhost:8000`.

Useful URLs:

| URL | Purpose |
| --- | --- |
| `http://localhost:8000/health` | Liveness |
| `http://localhost:8000/health/ready` | Database readiness |
| `http://localhost:8000/docs` | Swagger UI (non-production) |
| `http://localhost:3000/` | Landing page |
| `http://localhost:3000/dashboard` | Project dashboard |
| `http://localhost:3000/projects/new` | Create project |

## Commands

Run from the repository root:

| Command | What it does |
| --- | --- |
| `make install` | `uv sync` + `npm ci` |
| `make db-up` / `make db-down` | Start/stop local PostgreSQL |
| `make db-reset` | Delete the database volume and recreate it (destructive) |
| `make migrate` | Apply Alembic migrations |
| `make revision m="…"` | Autogenerate a migration |
| `make dev-api` / `make dev-web` | Development servers |
| `make test` | Backend pytest + frontend typecheck |
| `make lint` | Ruff + ESLint |
| `make format` | Ruff format + Prettier |
| `make typecheck` | mypy strict + `tsc --noEmit` |
| `make build` | Production Next.js build |
| `make contracts` | Export OpenAPI/schemas and regenerate API types |
| `make demo-data` | Regenerate the static Pages fixtures from the electrical engine |
| `make demo-build` | Build the static Pages export and scan it for credentials |
| `make check` | Every quality gate (`api-check` + `web-check`) |
| `make clean` | Remove local caches and build output |

Backend commands (from `apps/api`):

```bash
uv run pytest                      # 26 tests, SQLite, no network
uv run pytest -k agent             # focused selection
uv run pytest --cov=app            # coverage
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run alembic check               # requires PostgreSQL
```

Frontend commands (from `apps/web`):

```bash
npm run dev
npm run lint
npm run typecheck
npm run format:check
npm run build
npm run start                      # serve the production build
npm run codegen                    # regenerate src/lib/api-schema.ts
```

## Environment variables

### API (`apps/api/.env`)

| Variable | Default | Notes |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | `development`, `test`, `staging`, `production` |
| `DEBUG` | `false` | Debug logging behavior |
| `LOG_LEVEL` | `INFO` | `CRITICAL`/`ERROR`/`WARNING`/`INFO`/`DEBUG` |
| `API_V1_PREFIX` | `/api/v1` | Router prefix |
| `CORS_ORIGINS` | localhost:3000 origins | Comma-separated allow-list |
| `DATABASE_URL` | local robocraft DSN | Must use `postgresql+asyncpg://` at runtime |
| `DATABASE_ECHO` | `false` | Log SQL (noisy) |
| `DATABASE_POOL_SIZE` | `5` | Ignored for SQLite |
| `DATABASE_MAX_OVERFLOW` | `10` | Ignored for SQLite |
| `AI_PROVIDER` | `mock` | Registered provider key |
| `AI_MODEL` | `placeholder` | Default model identifier |
| `AI_API_KEY` | empty | Never commit a real key |
| `AI_REQUEST_TIMEOUT_SECONDS` | `60` | Provider timeout |

### Web (`apps/web/.env.local`)

| Variable | Default | Notes |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Browser-visible API origin |
| `NEXT_PUBLIC_DEMO_MODE` | `false` | Read precomputed fixtures and export statically |
| `NEXT_PUBLIC_BASE_PATH` | empty | Pages project-site prefix, e.g. `/robocraft` |

Never put a provider key in a `NEXT_PUBLIC_*` variable: Next.js inlines those values into the
browser bundle. Provider keys belong only in the API environment. See
[demo-site.md](demo-site.md) for the Pages build and `scripts/scan_secrets.sh`.

`.env`, `.env.local`, and variants are git-ignored. Only `.env.example` files belong in git.

## Database workflow

```bash
cd apps/api

# after changing a model
uv run alembic revision --autogenerate -m "describe change"
# inspect the generated file under alembic/versions/
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
uv run alembic check
```

Review autogenerated migrations: Alembic does not always detect enum changes, renames, or JSON
defaults correctly. Verify on PostgreSQL, not SQLite. See [database.md](database.md).

The test suite creates a temporary SQLite database per session and overrides the `get_db` dependency;
tests never require PostgreSQL or network access. PostgreSQL migration behavior is covered by CI.

## Contracts workflow

The API's OpenAPI document and agent JSON Schemas are build artifacts committed for the frontend and
external consumers.

```bash
make contracts
```

This runs `scripts/export_contracts.py` from `apps/api` (writing
`packages/contracts/openapi.json` and `packages/contracts/schemas/*.json`) and then
`openapi-typescript` in `apps/web` to regenerate `src/lib/api-schema.ts`.

CI regenerates contracts and fails on any diff, so commit regenerated files with the API change. Do
not hand-edit generated files.

## Testing strategy

| Layer | Tool | Scope |
| --- | --- | --- |
| API behavior | pytest + httpx ASGI transport | Health, project lifecycle, validation, specification updates, agent runs, audit history |
| Agent graph | pytest | Dependency resolution, skip propagation, status aggregation, contract rejection |
| Electrical | pytest | Plan generation, pin/net wiring, validation findings, all six exports, API round-trip |
| Contracts | pytest / JSON Schema export | Unknown-field rejection, enum validity, serialization |
| Frontend | TypeScript, ESLint, Prettier | Type safety, hooks rules, formatting |
| Build | `next build` | Route compilation and production bundling |
| Static demo | `next build` + `scripts/scan_secrets.sh` | Pages export, base path, fixtures are current, no credential-shaped strings |
| Browser | manual/Playwright (outside CI today) | Routes, responsive layout, create/delete project flow |

There is no frontend unit-test runner yet; the build/type/lint gate is the current regression net.
Adding component tests is tracked in M10.

### Writing tests

- Prefer behavior over implementation: call the API and assert the envelope.
- Keep tests hermetic. Do not call real suppliers, models, or PostgreSQL from `pytest`.
- Add a regression test for every bug fix.
- For agents, inject a fake provider and assert both the result status and the persisted run.

## CI

`.github/workflows/ci.yml` runs five jobs on pushes to `main` and every pull request:

1. **Backend** — uv sync, Ruff, format check, mypy strict, pytest with coverage.
2. **Migrations** — real PostgreSQL 16 service: upgrade head, `alembic check`, downgrade base,
   upgrade again.
3. **Contracts** — regenerate and fail if committed artifacts drift.
4. **Frontend** — npm ci, ESLint, TypeScript, Prettier check, production build.
5. **Demo** — regenerate fixtures, fail on drift, build the static Pages export, scan it for
   credential-shaped strings.

`.github/workflows/pages.yml` deploys that export to GitHub Pages on pushes to `main`. Enable
**Settings → Pages → Source: GitHub Actions** once. See [demo-site.md](demo-site.md).

A pull request should not be merged while a required job is failing.

## Code organization

### Backend

```text
app/
├── api/          routers and dependencies (HTTP only)
├── services/     use-cases and transactions
├── schemas/      request/response models
├── models/       SQLAlchemy models and enums
├── ai/           provider, contracts, agents, orchestrator
└── core/         settings, db, logging, errors
```

Rules of thumb:

- Routers validate and delegate; services own transactions.
- Raise `NotFoundError`, `ValidationError`, etc. from `core/errors.py`.
- Keep response models separate from ORM models; `model_validate` bridges them.
- Avoid lazy-loading surprises: relationships used by responses are `selectin` where appropriate.
- Use `Decimal` for money and `datetime` with `UTC`.

### Frontend

```text
src/
├── app/          routes and layouts
├── components/   ui primitives + feature components
├── hooks/        data/state hooks
└── lib/          api client, types, constants, utils
```

Rules of thumb:

- Server components by default; `"use client"` only when needed.
- All HTTP goes through `src/lib/api.ts` and throws `ApiError`.
- Reuse `ui/` primitives and theme tokens; avoid arbitrary hex colors.
- Test every route at 360 px and desktop width; no horizontal scroll.
- Keep loading, empty, and error states explicit.

## Troubleshooting

### `database_unavailable` / readiness 503

- Check PostgreSQL: `pg_isready -h localhost -p 5432 -U robocraft`.
- Confirm `DATABASE_URL` uses `postgresql+asyncpg://`, not `postgresql://`.
- If using Compose, wait for the health check: `docker compose ps`.
- Run `uv run alembic upgrade head` if the schema is missing.

### `Cannot reach the RoboCraft API`

- Confirm the API is on port 8000 and `NEXT_PUBLIC_API_URL` matches.
- CORS failures appear in the browser console; add the web origin to `CORS_ORIGINS`.
- `NEXT_PUBLIC_*` values are inlined at build time; restart/rebuild the web app after changing them.

### Port already in use

```bash
ss -ltnp | grep -E ':(3000|5432|8000)'
```

Stop the conflicting process or change `POSTGRES_PORT` / use `--port` for the API; set
`NEXT_PUBLIC_API_URL` accordingly.

### Migration drift

`alembic check` reporting changes means a model changed without a migration. Autogenerate, review,
and commit the revision. If you edited an already-applied migration locally, downgrade to base and
re-apply rather than hand-patching the database.

### Docker permission denied

If the Docker socket is unavailable on your machine, run PostgreSQL directly or use an existing
server and point `DATABASE_URL` at it. Docker is a convenience, not a requirement.

### Frontend build cannot find `api-schema.ts`

Run `make contracts`. The file is generated and committed; a fresh clone should already contain it.

## Conventions

- Backend: Ruff (line length 100, py312), mypy strict, Pydantic 2.
- Frontend: TypeScript strict, ESLint Next config, Prettier with Tailwind class sorting.
- Commits: imperative, scoped (`feat(api): …`, `fix(web): …`, `docs(ai): …`).
- Branches: `feat/…`, `fix/…`, `docs/…`, `chore/…`.
- Pull requests: use the template; include verification commands and screenshots for UI changes.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full review and definition-of-done checklist.
