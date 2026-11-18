# Static demo site (GitHub Pages)

The repository publishes a read-only demo to GitHub Pages. It is the same Next.js app,
built in demo mode against precomputed fixtures instead of a live API.

Live site: <https://abooubaker.github.io/robocraft/> — the workflow derives the base path from
the repository name, so a project site is served from `/<repository>/`.

## What the demo is

- One project, **Patio Scout** (ESP32 obstacle avoider), with a generated specification,
  bill of materials, agent-run audit trail, and a complete wiring plan.
- The wiring workspace, exports, validation findings, and power budget are all real output
  from the deterministic engine in `apps/api/app/electrical/`.
- The dashboard, project overview, and every module route render from the same JSON.

## What the demo is not

- It is not a live deployment. There is no API, database, LLM provider, or write path.
  Creating projects and running agents return a clear "needs the full API" message.
- It contains no credentials. The build never receives provider keys and the API URL is
  forced empty, so no live endpoint is baked into the bundle.

## How it is generated

`scripts/generate_demo_data.py` imports the API's electrical engine and writes:

```text
apps/web/src/lib/demo/project.json          project + specification
apps/web/src/lib/demo/agent-runs.json       audit trail for the six agents
apps/web/src/lib/demo/agent-catalog.json    agent roster with real statuses
apps/web/src/lib/demo/electrical.json       ElectricalArtifact (plan + BOM + formats)
apps/web/src/lib/demo/orchestration.json    shared pipeline context
apps/web/public/demo/exports/*              the six downloadable exports
apps/web/public/demo/exports/manifest.json  engine summary
```

Because the fixtures are committed, the Pages build does not need Python. CI regenerates
them and fails on drift, so the demo cannot silently diverge from the engine.

```bash
make demo-data     # regenerate fixtures
make demo-build    # static export + credential scan
```

## Running the export locally

```bash
cd apps/web
NEXT_PUBLIC_DEMO_MODE=true \
NEXT_PUBLIC_BASE_PATH=/robocraft \
NEXT_PUBLIC_API_URL= \
npm run build
npx serve out
```

Open `http://localhost:3000/robocraft/`. `next.config.ts` switches `output: "export"`,
`trailingSlash`, and unoptimized images when `NEXT_PUBLIC_DEMO_MODE=true`.

## Demo mode in code

- `DEMO_MODE` and `BASE_PATH` live in `apps/web/src/lib/constants.ts`.
- `apps/web/src/lib/api.ts` branches per call: demo mode reads fixtures, otherwise it calls
  the API. The call sites and return types are identical.
- `generateStaticParams` in the project and module routes emits the demo project paths so
  the export has real pages.
- `assetPath()` prefixes `/demo/exports/...` with the Pages base path.

## Credential hygiene

`scripts/scan_secrets.sh` fails the build if tracked files or `apps/web/out` contain
provider key prefixes, private-key headers, committed `.env` files, or a database URL with
a non-loopback host. The Pages workflow runs it after building.

Rules:

1. Never set a provider key in a `NEXT_PUBLIC_*` variable; those are compiled into the
   bundle.
2. Never point the Pages build at a live API (`NEXT_PUBLIC_API_URL` is forced empty).
3. Fixtures are generated from code and the curated library — never from live API
   responses or user records.
4. Server secrets belong only in the API environment (`apps/api/.env`, never committed).

## Workflow

`.github/workflows/pages.yml` runs on pushes to `main` and on manual dispatch:

1. install API dependencies and regenerate fixtures;
2. derive the Pages base path from the repository name;
3. `npm ci` and `npm run build` with demo env;
4. run the credential scan;
5. check whether Pages is enabled, then upload `apps/web/out` and deploy with
   `actions/deploy-pages`.

Enable **Settings → Pages → Source: GitHub Actions** once in the repository. CI
(`.github/workflows/ci.yml`, job `demo`) builds the same export on every pull request and
fails if the committed fixtures drift.

### Repository requirements

This repository is public and Pages is enabled with **Source: GitHub Actions**. The workflow
also supports forks:

- **Public repository:** Pages is free; enable it once with **Source: GitHub Actions**.
- **Private repository:** requires a GitHub plan that includes Pages for private repositories,
  and Pages must still be enabled with the GitHub Actions source.

Until Pages is available the workflow still builds and scans the static export, prints a
notice, and skips the deploy job instead of failing. It does not silently publish anything.

The deploy job intentionally has no custom domain or CORS configuration: the demo is entirely
static and must never call a live API.
