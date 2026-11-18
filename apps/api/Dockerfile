# syntax=docker/dockerfile:1
# Albayraq API — production image.
# Build from apps/api: docker build -t albayraq-api .

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# uv is the same resolver used in development and CI.
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/

# Install locked runtime dependencies first so code changes do not bust the cache.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# The API is stateless; uploads and artifacts live in Postgres or response bodies.
RUN useradd --create-home --uid 10001 albayraq \
    && chown -R albayraq:albayraq /app
USER albayraq

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
