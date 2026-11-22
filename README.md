# ATLAS

Vietnam Investment Discovery World: a platform for exploring Vietnam's listed economy by sector,
company and region.

**Status: Phase 0 (foundation).** The app shell, API, database and tooling are in place. No market
data source is connected yet, so the UI shows empty states by design. ATLAS never shows invented
financial figures.

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
data/        Reserved for data-source docs and seed specs (no data yet)
docs/        Architecture, development guide, Phase 0 checklist
.github/     CI workflows (backend, frontend, docker)
docker-compose.yml
```

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/v1/health` | `200` when the API and database are reachable; `503` with the same body shape when the database check fails |

Example response:

```json
{"status":"ok","version":"0.1.0","environment":"development","checks":{"database":{"status":"ok","latency_ms":1.3}}}
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): components, request flow, decisions
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): local setup, commands, troubleshooting
- [docs/PHASE_0_CHECKLIST.md](docs/PHASE_0_CHECKLIST.md): verification evidence for Phase 0

## Known limitations

- No market data, domain models or authentication yet (Phase 1+).
- The 3D world view is not implemented; the Discover page only reserves space for it.
- `.env.example` credentials are for local development only. A production deployment needs
  real secrets management, which is out of scope for Phase 0.
