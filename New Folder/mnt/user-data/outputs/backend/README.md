# ShopFast Backend — FastAPI + PostgreSQL

REST API for the ShopFast single-product dropshipping storefront. Endpoint paths,
query-parameter names, and JSON field casing are built to match the React
frontend's `src/services/*.js` exactly, so switching the frontend from mocks to
this API only requires editing `.env`.

## Requirements

- Python 3.11+
- PostgreSQL 14+

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Generate a real secret and paste it into .env as SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Create the database:

```bash
createdb shopfast
# or:  psql -U postgres -c "CREATE DATABASE shopfast;"
```

Run migrations, seed the product, start the server:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/docs  •  Health: http://localhost:8000/health

## Connecting the frontend

In the frontend's `.env`:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_USE_MOCKS=false
```

## Endpoints

| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Returns access + refresh tokens |
| POST | `/api/v1/auth/login` | — | Same generic error for bad email or password |
| POST | `/api/v1/auth/refresh` | — | Refresh token only; access tokens rejected |
| GET | `/api/v1/auth/me` | Bearer | Current user |
| POST | `/api/v1/auth/logout` | Bearer | Client clears tokens (see note below) |
| GET | `/api/v1/categories` | — | |
| GET | `/api/v1/products` | — | `search`, `category`, `minPrice`, `maxPrice`, `inStockOnly`, `sortBy`, `limit`, `offset` |
| GET | `/api/v1/products/featured` | — | Declared before `/{slug}` so it isn't parsed as a slug |
| GET | `/api/v1/products/{slug}` | — | Full detail incl. variants and reviews |
| POST | `/api/v1/orders` | Optional | Guests allowed; links to user when a token is sent |
| GET | `/api/v1/orders/track/{tracking_id}` | — | Shipping progress only |

## Security decisions

- **Secrets** come only from environment variables. The app refuses to start if
  `SECRET_KEY` is missing, short, or still the placeholder.
- **Passwords** are bcrypt-hashed via passlib; plaintext is never stored or logged.
- **JWTs** carry a `type` claim and it is verified, so a refresh token cannot be
  replayed as an access token.
- **Order totals are recalculated server-side** from the products table. The
  `totals` object the frontend sends is ignored — otherwise a user could edit the
  request and buy at any price they liked.
- **Stock is checked and decremented** during order creation, so overselling past
  supplier inventory is rejected with a 409.
- **Tracking IDs are random**, not sequential, and the tracking route returns only
  shipping status — no address, phone, totals, or line items — because it is public.
- **Rate limits** on auth and order routes (slowapi) blunt brute-force and spam.
- **SQL injection** is structurally prevented: every query goes through SQLAlchemy
  bound parameters; no string-built SQL anywhere.
- **Input validation** with Pydantic mirrors the frontend rules server-side, since
  client-side validation can always be bypassed by calling the API directly.
- **CORS** uses an explicit origin allowlist (never `*`, which would be unsafe with
  credentials enabled).
- **Security headers** (`nosniff`, `DENY` framing, referrer policy, HSTS in prod).
- **Error responses are generic**; SQLAlchemy errors are logged server-side only so
  table names and SQL fragments never reach the browser.
- **API docs are disabled in production** (`ENVIRONMENT=production`).

## Known gaps before going live

- **Payments are not integrated.** `payment_method` is recorded and `payment_status`
  defaults to `pending`; no bKash/Nagad/SSLCommerz/card charge is actually made.
  Add each provider's initiation call plus a webhook that flips `payment_status`,
  and only then treat an order as paid.
- **Logout does not revoke tokens.** JWTs stay valid until they expire. For real
  revocation, persist each token's `jti` in a denylist table and check it in
  `app/core/deps.py`.
- **Tracking is not wired to a carrier.** Timeline steps exist in the DB but only
  "Order Placed" is completed; advancing the rest needs an admin action or a
  carrier-API sync job.
- **No admin endpoints yet** for creating/editing products or advancing orders.
- **Rate limiting is in-memory**, so it resets on restart and isn't shared across
  workers. Point slowapi at Redis before running more than one process.
- **`ProductVariant` rows are display options only.** They have no per-variant SKU,
  price, or stock, so stock is tracked at the product level.
