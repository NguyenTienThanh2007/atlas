# Development

## Prerequisites

- Docker with Compose v2
- [uv](https://docs.astral.sh/uv/) (installs Python 3.13 automatically from `backend/.python-version`)
- Node.js 24 + npm

## First-time setup

```bash
cp .env.example .env
# Edit .env: replace the placeholder password (see "Database password" below)
docker compose up -d db          # PostgreSQL on localhost:5433, creates atlas + atlas_test
cd backend && uv sync && uv run alembic upgrade head && cd ..
cd frontend && npm ci && cd ..
```

## Database password

`.env.example` ships the placeholder `local_dev_only_change_me`. It is for local development
only. Set your own value in `.env`, which git ignores:

1. Choose a password made of letters, digits, `_` or `-`. It is embedded in connection URLs, so
   characters like `@ / : #` would break them.
2. Put the same value in all three places in `.env`: `POSTGRES_PASSWORD`, `DATABASE_URL` and
   `TEST_DATABASE_URL`.
3. Docker Compose reads `POSTGRES_PASSWORD` for the `db` service and builds the backend
   container's `DATABASE_URL` from it, so containers need no other change.

Postgres applies `POSTGRES_PASSWORD` only when the `pgdata` volume is **first created**. Changing
it later in `.env` does not change the database password. To change it on an existing volume,
either:

- keep your data and set the new password inside Postgres:
  `docker compose exec db psql -U atlas -d atlas -c "ALTER USER atlas PASSWORD 'new_value';"`,
  then update `.env`, or
- start over (this **deletes all local data**): `docker compose down -v`, then
  `docker compose up -d db`.

CI uses its own throwaway credentials in `.github/workflows/backend.yml`. Those exist only
inside the ephemeral CI database container.

## Run services on the host

Run the database in Docker and the apps on the host, which gives hot reload:

```bash
docker compose up -d db
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev       # http://localhost:3000, reads API_URL from the environment
```

The backend reads the repo-root `.env`. Next.js does **not** read it (it only reads
`frontend/.env*`). The frontend's `API_URL` defaults to `http://localhost:8000`, which matches the
host setup. To override it, run `API_URL=... npm run dev`.

## Run everything in Docker

```bash
docker compose up -d --build --wait
docker compose logs -f backend
docker compose down              # keeps data
```

## Data: reference seed and imports

The backend container seeds exchanges and the sector taxonomy on every start (idempotent). On the
host:

```bash
cd backend
uv run python -m app.ingestion reference
uv run python -m app.ingestion import ../data/seed/sample_companies.json   # FICTIONAL sample data
```

The sample fixture shows up in the UI with a "Sample data" badge. Bundle format, import rules,
exit codes, taxonomy and metric dictionary: [data/README.md](../data/README.md). Provider and
licensing status: [data/SOURCES.md](../data/SOURCES.md).

Sample rows can't be deleted one by one, because financial history is append-only and foreign
keys never cascade. To start from a clean dev database, run `docker compose down -v` (this
**deletes all local data**), then `docker compose up -d --build --wait`.

## Checks (same as CI)

Backend (needs the `db` container running; tests use `TEST_DATABASE_URL`):

```bash
cd backend
uv run ruff check . && uv run ruff format --check .
uv run mypy app tests migrations/env.py
uv run pytest
uv run alembic upgrade head && uv run alembic check
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm test          # unit tests (node --test, no extra dependencies)
npm run build
```

Docker:

```bash
docker compose config -q
docker compose build
```

## Migrations

```bash
cd backend
uv run alembic revision --autogenerate -m "describe change"   # after editing models
uv run alembic upgrade head
uv run alembic downgrade -1
```

Models live in `app/models.py`, which `migrations/env.py` imports so autogenerate sees them. Review
every generated migration. Autogenerate can't express triggers or data changes, so add those by
hand, as the domain-model revision does for the append-only triggers. Keep `downgrade()` working:
the test suite runs upgrade, downgrade to base, then upgrade again.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Import exits `2` | Some records were rejected or conflicted. Read `issues` in the printed JSON (record index, key, reason). Nothing was overwritten |
| Import exits `1` with "differs from the stored data source" | A bundle tried to change a data source's terms. Update the `data_sources` row deliberately instead |
| `port is already allocated` on 5433/8000/3000 | Change `POSTGRES_PORT` / `BACKEND_PORT` / `FRONTEND_PORT` in `.env` and update `DATABASE_URL`, `TEST_DATABASE_URL` and `API_URL` to match |
| Tests exit with `TEST_DATABASE_URL is not set` | Create `.env` from `.env.example` or export the variable |
| `password authentication failed for user "atlas"` | The password in `.env` doesn't match the one the volume was created with. See "Database password" above |
| `database "atlas_test" does not exist` | The init script runs only on an empty volume. Run `docker compose exec db createdb -U atlas atlas_test` |
| Sidebar shows "API unreachable" | Backend isn't running or `API_URL` is wrong |
| Sidebar shows "API online, database unreachable" | Start the database: `docker compose up -d db` |
