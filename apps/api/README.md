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
