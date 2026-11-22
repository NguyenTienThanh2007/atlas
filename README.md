# ATLAS

Vietnam Investment Discovery World: a platform for exploring Vietnam's listed economy by sector,
company and region.

**Status: Phase 1 (financial data foundation).** The domain model (companies, securities,
exchanges, sectors, evidence, financial statements), the import framework, the catalogue API and
the companies and sectors UI are in place.

**No real company data is loaded yet.** No data provider is licensed or reachable (see
[data/SOURCES.md](data/SOURCES.md)), so ATLAS ships only a clearly labelled **fictional** sample
fixture. ATLAS never shows invented figures as real data.

## Stack

| Layer | Tech |
| --- | --- |
| Frontend | Next.js 16 (App Router), TypeScript (strict), Tailwind CSS 4 |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, Pydantic Settings |
| Database | PostgreSQL 17 |
| Infra | Docker Compose, GitHub Actions |

## Quick start (Docker)

Requires Docker with Compose v2.

```bash
cp .env.example .env
docker compose up -d --build --wait
```

`.env.example` contains a placeholder database password for local development only. Replace it in
your `.env`; see [Database password](docs/DEVELOPMENT.md#database-password).

- Frontend: http://localhost:3000
- API health: http://localhost:8000/api/v1/health
- API docs (OpenAPI): http://localhost:8000/docs
- PostgreSQL: `localhost:5433` (host port 5433 so it doesn't clash with a local Postgres on 5432)

The backend applies migrations on startup. Stop with `docker compose down`; your data stays in the
`atlas_pgdata` volume. `docker compose down -v` deletes it.

For running services outside Docker, tests and day-to-day commands, see
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Repository layout

```
backend/     FastAPI app, Alembic migrations, pytest suite
frontend/    Next.js app
infra/       Infrastructure assets (Postgres init scripts)
data/        Import bundles (fictional sample fixture), data-source research, import rules
docs/        Architecture, development guide, phase checklists
.github/     CI workflows (backend, frontend, docker)
docker-compose.yml
```

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/health` | `200` when the API and database are reachable; `503` with the same body shape when the database check fails |
| GET | `/api/v1/exchanges` | Exchanges (HOSE, HNX, UPCOM) |
| GET | `/api/v1/sectors`, `/api/v1/sectors/{id}` | ATLAS sector taxonomy with company counts |
| GET | `/api/v1/companies` | Search (`q`: name or ticker), filter (`sector`, `exchange` codes), paginate (`limit`, `offset`) |
| GET | `/api/v1/companies/{id}` | Company with sector and securities |
| GET | `/api/v1/securities/{id}` | Security with exchange and company |
| GET | `/api/v1/companies/{id}/evidence` | Source evidence with data source and usage status |
| GET | `/api/v1/companies/{id}/financial-statements` | Latest revisions by default; values as exact decimal strings |

Full parameters and design notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#api-apiv1). OpenAPI
docs are at `/docs` on the backend.

Example response:

```json
{"status":"ok","version":"0.1.0","environment":"development","checks":{"database":{"status":"ok","latency_ms":1.3}}}
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): components, request flow, decisions
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): local setup, commands, troubleshooting
- [data/README.md](data/README.md): import format and rules, sector taxonomy, metric dictionary
- [data/SOURCES.md](data/SOURCES.md): data providers and licensing status
- [docs/PHASE_0_CHECKLIST.md](docs/PHASE_0_CHECKLIST.md),
  [docs/PHASE_1_CHECKLIST.md](docs/PHASE_1_CHECKLIST.md): verification evidence

## Known limitations

- No real company or financial data: 0 verified companies. Provider integration is blocked on
  licensing and credentials (see `data/SOURCES.md`).
- No authentication, and no price or market-event data.
- The 3D world view is not implemented; the Discover page only reserves space for it.
- `.env.example` credentials are for local development only. A production deployment needs
  real secrets management, which is out of scope so far.
