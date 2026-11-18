# Deployment

Albayraq runs as three pieces:

| Piece | Host | Why |
| --- | --- | --- |
| API (`apps/api`) | Render web service (Docker) | Stateless FastAPI container, automatic TLS, health checks |
| Web (`apps/web`) | Render web service (Node) | Server-rendered Next.js app with the API origin inlined at build time |
| PostgreSQL | Neon | Managed Postgres with branching, connection pooling, and a usable free tier |

The GitHub Pages build at <https://abooubaker.github.io/blueprints-baker/> is a **read-only demo**
built from fixtures. It is not the hosted product and cannot create projects.

Everything below is reproducible from [`render.yaml`](../render.yaml); the dashboard steps are the
same if you prefer clicking through.

## 1. Create the Neon database

1. Create a Neon project in the region closest to your Render region (this repo's blueprint uses
   `ohio` (US East), matching a Neon project in `us-east-2`).
2. Copy the **pooled** connection string. It looks like:

   ```text
   postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require&channel_binding=require
   ```

3. Keep it secret. Do not paste it into an issue, a `.env` committed to git, or a
   `NEXT_PUBLIC_*` variable.

The API normalizes provider URLs at startup:

- `postgres://` and `postgresql://` become `postgresql+asyncpg://`.
- `sslmode=require` becomes asyncpg's `ssl=require`.
- `channel_binding` is dropped (asyncpg does not implement it).
- A `-pooler` host automatically disables asyncpg's prepared-statement cache, which PgBouncer
  requires.

So the connection string Neon shows can be pasted as-is.

## 2. Deploy the API on Render

Create a Render Blueprint from this repository and apply `render.yaml`, or create one web service
manually:

| Setting | Value |
| --- | --- |
| Runtime | Docker |
| Root directory / context | `apps/api` |
| Dockerfile | `apps/api/Dockerfile` |
| Health check path | `/health` |
| Plan | Free is enough to try it; it sleeps when idle |

Environment variables:

| Variable | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Neon pooled connection string (secret) |
| `CORS_ORIGINS` | The deployed web origin, e.g. `https://albayraq-web.onrender.com` |
| `LOG_LEVEL` | `INFO` |

`CORS_ORIGINS` accepts a comma-separated list. Add local origins too if you develop against the
hosted API: `https://albayraq-web.onrender.com,http://localhost:3000`.

The container entrypoint runs `alembic upgrade head` once per deploy, then starts uvicorn on
`$PORT`. That keeps the free single-service plan usable without exposing a shell. If you move to a
platform with pre-deploy commands, run the migration there instead and skip the entrypoint step.

Verify:

```bash
curl https://YOUR-API.onrender.com/health
curl https://YOUR-API.onrender.com/health/ready
```

`/health` is liveness and does not touch the database. `/health/ready` returns `503`
`database_unavailable` until Neon accepts connections and the schema is current.

Production disables `/docs`, `/redoc`, and `/openapi.json`. The committed contract in
[`packages/contracts/openapi.json`](../packages/contracts/openapi.json) remains the reference.

## 3. Deploy the web app on Render

The frontend is a private app with no server-side secrets. Create a Node web service:

| Setting | Value |
| --- | --- |
| Runtime | Node |
| Root directory | `apps/web` |
| Build command | `npm ci && npm run build` |
| Start command | `npm run start` |
| Health check path | `/` |
| Node version | 22 |

Environment variables (build-time):

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | `https://YOUR-API.onrender.com` |
| `NEXT_PUBLIC_DEMO_MODE` | `false` |
| `NEXT_PUBLIC_BASE_PATH` | empty |

`NEXT_PUBLIC_*` values are inlined into the browser bundle at build time. If the API URL changes,
redeploy the web service — changing the variable alone does not update an existing build.

After the first web deploy:

1. Copy the web URL into the API's `CORS_ORIGINS`.
2. Redeploy the API.
3. Open the web URL, create a project, and confirm the redirect to the generated build.

If the frontend loads but the console reports CORS failures, the web origin does not exactly match
an entry in `CORS_ORIGINS` (scheme included, no trailing slash).

## 4. Order of operations

1. Neon project and connection string.
2. API service with `DATABASE_URL`; wait for `/health/ready` to return `200`.
3. Web service with `NEXT_PUBLIC_API_URL` pointing at step 2.
4. Set `CORS_ORIGINS` to the web origin and redeploy the API.
5. Create a project end to end and confirm all six artifacts appear.

## Local container check

The API image can be built and run locally against the Compose database:

```bash
docker build -t albayraq-api apps/api

docker run --rm -p 8000:8000 \
  -e ENVIRONMENT=development \
  -e DATABASE_URL=postgresql+asyncpg://albayraq:albayraq@host.docker.internal:5432/albayraq \
  -e CORS_ORIGINS=http://localhost:3000 \
  albayraq-api
```

On Linux, `host.docker.internal` requires
`--add-host=host.docker.internal:host-gateway`, or put the API on the same Compose network.

## Data and operations

- **Migrations** live in `apps/api/alembic/versions`. CI applies them to PostgreSQL 16, checks for
  drift with `alembic check`, downgrades to base, and upgrades again.
- **Backups** are Neon's responsibility; enable point-in-time restore on paid plans before storing
  real user data.
- **Uploads** are not used. STL, CSV, and code exports are generated response bodies.
- **Logs** are structured JSON in staging/production and include a request ID. Render captures
  stdout.
- **Scaling** is safe horizontally because each request owns its transaction and no build state
  lives in process memory.
- **Free-tier sleep**: Render free services spin down after inactivity. The first request after a
  sleep can take 30–60 seconds; the UI shows a loading state.
- **Secrets** belong only in the Render dashboard. The repository gate is
  `bash scripts/scan_secrets.sh`; it also runs in the demo build.

## Security notes

- The API is unauthenticated in this release. A public deployment lets anyone create and delete
  projects. Keep the URL private, or put it behind a proxy/access rule until M2 lands.
- Production disables Swagger/ReDoc/OpenAPI. Do not re-enable them on a public URL without auth.
- Never put `DATABASE_URL` or provider keys in `NEXT_PUBLIC_*` variables; those are inlined into
  the browser bundle.
- Run `bash scripts/scan_secrets.sh` before publishing an artifact.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Deploy exits during `alembic upgrade head` | Wrong `DATABASE_URL`, or Neon not reachable | Check the connection string, SSL mode, and Neon project status |
| `/health/ready` returns `503` | Database unavailable or schema missing | Read Render logs; confirm the migration step ran |
| Browser shows CORS error | `CORS_ORIGINS` mismatch | Add the exact web origin (scheme, no trailing slash), redeploy |
| UI calls `http://localhost:8000` | `NEXT_PUBLIC_API_URL` was missing at build time | Set it, rebuild the web service |
| `demo_read_only` errors on the hosted site | You are on the GitHub Pages demo | Use the Render web URL, not Pages |
| API sleeps on first request | Render free plan | Expected; upgrade or keep the service warm |
