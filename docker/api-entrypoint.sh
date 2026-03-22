#!/usr/bin/env sh
set -eu

echo "Waiting for database..."
until uv run python -c "from app.infrastructure.db.session import engine; conn = engine.connect(); conn.close()"; do
  echo "Database not ready yet, retrying..."
  sleep 2
done

echo "Running database migrations..."
uv run alembic upgrade head

echo "Starting API..."
exec uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload