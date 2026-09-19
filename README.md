# ShopFast — Full Stack (React + FastAPI + PostgreSQL)

Single-product dropshipping storefront. Frontend and backend both run in Docker,
with PostgreSQL as the database.

## Required folder layout

Put all three items in the same parent folder:

```
shopfast/
├── docker-compose.yml       <- from this bundle
├── .env                     <- you create this from .env.example
├── dropship-frontend/       <- the React project
└── backend/                 <- the FastAPI project
```

The compose file builds from `./dropship-frontend` and `./backend`, so those exact
folder names matter.

## First run

```bash
# 1. Create your env file
cp .env.example .env

# 2. Generate a SECRET_KEY and paste it into .env
python -c "import secrets; print(secrets.token_urlsafe(64))"
#   (no Python on your machine? use: openssl rand -base64 48)

# 3. Build and start everything
docker compose up --build
```

First build takes a few minutes. When it settles you get:

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| PostgreSQL | localhost:5432 |

The backend entrypoint waits for PostgreSQL, generates and applies migrations, and
seeds the product automatically — no manual migration step on first run.

## Daily commands

```bash
docker compose up              # start (after the first build)
docker compose up --build      # rebuild after changing dependencies or Dockerfiles
docker compose down            # stop, keep database data
docker compose down -v         # stop and WIPE the database
docker compose logs -f backend # tail backend logs
docker compose exec backend bash   # shell inside the API container
docker compose exec db psql -U shopfast -d shopfast   # open psql
```

## How code changes behave

- **Backend**: `./backend` is mounted into the container and uvicorn runs with
  `--reload`, so Python edits apply on save. No rebuild needed.
- **Frontend**: it's built into static files and served by nginx, so a code change
  needs `docker compose up --build frontend`. For fast iteration, run the frontend
  outside Docker instead (`cd dropship-frontend && npm run dev` on port 5173) —
  that origin is already in the CORS allowlist.

## Why VITE_API_BASE_URL is `localhost:8000`, not `backend:8000`

Vite inlines `VITE_*` variables at build time, and the resulting JavaScript runs in
the visitor's browser — which has no idea what `backend` means. Only containers can
resolve service names. So the browser-facing URL belongs here, and changing it
requires a rebuild, not just a restart.

## Before deploying to a real server

- Set `ENVIRONMENT=production` in `.env`. That disables `/docs` and enables HSTS.
- Set a real `POSTGRES_PASSWORD` and a freshly generated `SECRET_KEY`.
- Remove the `ports:` block from the `db` service so PostgreSQL isn't reachable
  from the internet.
- Remove the `volumes:` mount and `--reload` from the `backend` service.
- Point `VITE_API_BASE_URL` and `BACKEND_CORS_ORIGINS` at your real domain, and
  rebuild the frontend so the new URL is baked in.
- Put a reverse proxy with TLS in front; nothing here terminates HTTPS.
- **Payments are not integrated yet** — orders record a payment method but no charge
  is made. Wire up bKash/Nagad/SSLCommerz/card plus their webhooks before taking
  real money.
