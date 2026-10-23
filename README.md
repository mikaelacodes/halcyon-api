# Halcyon API

Backend microservice for **Halcyon Systems** — ticket `HS-2026-0872`: a production-grade
REST API with token auth, role-based permissions, containerised deployment, and CI.

**Project assignment:** Inventory & Supply Chain Fulfilment API.

## Stack

Django 5.2 · Django REST Framework · JWT auth (`djangorestframework-simplejwt`) ·
PostgreSQL · drf-spectacular (OpenAPI/Swagger) · pytest · Docker · GitHub Actions

## Domain

- **`apps.accounts`** — `Profile` (role: `ADMIN` / `STANDARD`), auto-created for every user.
- **`apps.inventory`** — `Supplier`, `Warehouse`, `Product` (many-to-many with `Supplier`
  through `ProductSupplier`, which carries `supplier_sku`/`lead_time_days`), and
  `StockMovement` — the transaction log of receipts/shipments/adjustments against a
  product's stock at a warehouse.
- **`apps.core`** — shared infrastructure: the standardised error handler, `/health/`.

## Local setup

### With Docker (recommended)

```bash
docker compose up
```

This builds the image, starts PostgreSQL, waits for it to report healthy, runs
migrations, and starts the API on **http://localhost:8000**. No separate setup step
needed — `docker compose up` alone leaves you with a working API.

Create an admin user in another terminal once it's up:

```bash
docker compose exec web python manage.py createsuperuser
```

Tear down (`-v` also drops the Postgres volume, i.e. wipes the data):

```bash
docker compose down -v
```

### Without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate      # uses a local sqlite3 file by default
python manage.py createsuperuser
python manage.py runserver
```

Point `DATABASE_URL` (see `.env.example`) at a real Postgres instance instead of the
sqlite fallback if you want to match production more closely.

### Running tests

```bash
pytest
```

50 tests, 96.88% coverage (`pyproject.toml` enforces a floor of 80%). CI runs this
same command against a real ephemeral Postgres container, not sqlite.

## API walkthrough (curl)

All examples assume the API is running at `http://localhost:8000`.

### Register and authenticate

```bash
# Register (new users start as role: STANDARD)
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "a-strong-password-1"}'

# Log in — returns a JWT access/refresh pair
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "a-strong-password-1"}'
# => {"refresh": "...", "access": "..."}

# Refresh an expired access token
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'

# Who am I?
curl http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer <access_token>"
```

From here, set `TOKEN=<access_token>` and pass `-H "Authorization: Bearer $TOKEN"` on
every request below.

### Suppliers / warehouses / products (admin writes, anyone authenticated reads)

```bash
# List suppliers
curl http://localhost:8000/api/suppliers/ -H "Authorization: Bearer $TOKEN"

# Create a supplier (admin role required — a STANDARD user gets 403)
curl -X POST http://localhost:8000/api/suppliers/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Acme Co", "contact_email": "orders@acme.test"}'

# Create a warehouse
curl -X POST http://localhost:8000/api/warehouses/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"code": "SEA1", "name": "Seattle DC"}'

# Create a product
curl -X POST http://localhost:8000/api/products/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"sku": "WIDGET-001", "name": "Widget", "unit_price": "9.99"}'

# Link a supplier to a product (via the M2M through-table)
curl -X POST http://localhost:8000/api/product-suppliers/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product": 1, "supplier": 1, "lead_time_days": 3}'
```

### Stock movements (any authenticated user can log one; only admins edit/delete)

```bash
# Record a receipt
curl -X POST http://localhost:8000/api/stock-movements/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product": 1, "warehouse": 1, "movement_type": "RECEIPT", "quantity": 50}'

# Filter movement history
curl "http://localhost:8000/api/stock-movements/?warehouse=1&movement_type=RECEIPT" \
  -H "Authorization: Bearer $TOKEN"
```

### Health, docs

```bash
curl http://localhost:8000/health/
# => {"status": "ok", "uptime_seconds": 12.3, "database": {"connected": true, "engine": "postgresql"}}
```

Interactive docs: **http://localhost:8000/api/docs/** (Swagger UI) or
**http://localhost:8000/api/redoc/** (Redoc). Raw schema at `/api/schema/`.

### Error shape

Every error response — validation, auth, permission, not-found, conflict, or an
unhandled server error — comes back in the same shape:

```json
{"error": {"code": "invalid", "message": "...", "details": {"sku": ["..."]}}}
```

## Database index reasoning

Indexes were chosen against the queries the API actually runs, not added speculatively:

- **`Supplier.name`, `Product.sku`** — both are `unique=True`, which Postgres already
  backs with an implicit unique index, but they're also the fields every lookup/search
  filters or sorts by (`SearchFilter` on `name`/`sku`, and the natural "find this SKU"
  query), so an explicit index documents that intent and guarantees it regardless of
  how the unique constraint is implemented.
- **`Product.is_active`** — list views will commonly filter out discontinued products;
  a low-cardinality boolean index keeps that filter cheap even as the catalog grows.
- **`StockMovement(product, warehouse)`** — a composite index, because the API's main
  read pattern for movements is "history for this product at this warehouse" (see the
  `?product=&warehouse=` filter on `/api/stock-movements/`), not either field alone.
- **`StockMovement.created_at`** — movements are ordered newest-first by default
  (`Meta.ordering = ["-created_at"]`) and any time-range reporting query
  (e.g. "receipts this week") filters on this field, so it needs its own index
  rather than relying on the composite above.
- **`Warehouse.code`** — `unique=True` only; no extra index. Warehouses are a small,
  slow-changing reference table (a handful of rows), so the implicit unique index is
  enough and a dedicated one would just be overhead with no real benefit.

`ProductSupplier` has no extra index beyond its `UniqueConstraint(product, supplier)` —
that constraint already provides the index Postgres needs for the one query that
matters here (does this pair already exist), and the table is only ever queried by FK
joins from `Product`/`Supplier`, both of which Django indexes automatically.

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: **lint** (flake8, black,
isort) → **test** (pytest against a real `postgres:16-alpine` service container) →
**build** (`docker build` the image). Each stage gates the next.

## Project structure

```
apps/
  core/        shared infra: error handling, /health/
  accounts/    Profile (roles), register/login/me
  inventory/   Supplier, Warehouse, Product, ProductSupplier, StockMovement
config/
  settings/    base.py / dev.py / prod.py
  urls.py
Dockerfile              multi-stage build, non-root user, HEALTHCHECK
docker-compose.yml       app + postgres
.github/workflows/ci.yml
```
