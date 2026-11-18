# Blueprints Baker API

FastAPI service for Blueprints Baker. See the repository root [`README.md`](../../README.md) and
[`docs/`](../../docs) for architecture, setup, and API documentation.

```bash
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Interactive OpenAPI docs: <http://localhost:8000/docs>

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Production image

```bash
docker build -t blueprints-baker-api apps/api
docker run --rm -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL='postgresql://…' \
  -e CORS_ORIGINS='https://your-web.example' \
  blueprints-baker-api
```

The entrypoint applies Alembic migrations once, then serves on `$PORT`. Hosted URLs from Neon and
Render are normalized automatically. See [`docs/deployment.md`](../../docs/deployment.md).
