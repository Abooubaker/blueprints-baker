#!/bin/sh
# Apply migrations, then serve. Hosting platforms inject $PORT (Render, Fly, etc.).
set -eu

echo "Applying database migrations…"
alembic upgrade head

echo "Starting API on port ${PORT:-8000}…"
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips="*"
