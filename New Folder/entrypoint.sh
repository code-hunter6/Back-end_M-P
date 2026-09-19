#!/usr/bin/env bash
# Waits for PostgreSQL, applies migrations, seeds the catalog, then starts the API.
# Used as the container entrypoint in docker-compose so a fresh `docker compose up`
# gives you a working database with no manual steps.
set -e

echo "Waiting for PostgreSQL at ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
until python -c "
import asyncio, os, sys
import asyncpg

async def check():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'db'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            user=os.getenv('POSTGRES_USER', 'shopfast'),
            password=os.getenv('POSTGRES_PASSWORD', 'shopfast'),
            database=os.getenv('POSTGRES_DB', 'shopfast'),
        )
        await conn.close()
    except Exception:
        sys.exit(1)

asyncio.run(check())
" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL is ready."

# Generate the first migration only if none exists yet.
if [ -z "$(ls -A alembic/versions/*.py 2>/dev/null)" ]; then
  echo "No migrations found — generating initial schema..."
  alembic revision --autogenerate -m "initial schema"
fi

echo "Applying migrations..."
alembic upgrade head

echo "Seeding catalog (skips if already seeded)..."
python -m app.seed || echo "Seed step skipped."

echo "Starting API..."
exec "$@"
