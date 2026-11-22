# Architecture

## Components

```
 Browser ──► frontend (Next.js, :3000) ──server-side fetch──► backend (FastAPI, :8000) ──► db (PostgreSQL, :5432 in-network)
```

| Service | Source | Container | Notes |
| --- | --- | --- | --- |
| `frontend` | `frontend/` | `node:24-alpine`, Next.js standalone output, runs as `node` | Reads `API_URL` at request time |
| `backend` | `backend/` | `python:3.13-slim` + uv, runs as non-root `atlas` | Runs `alembic upgrade head` then uvicorn |
| `db` | `infra/postgres/init/` | `postgres:17-alpine` | Named volume `pgdata`; init script creates `<POSTGRES_DB>_test` |

All host port bindings are on `127.0.0.1` only.

## Backend

```
backend/
  app/
    config.py        Settings (pydantic-settings): env vars, then repo-root .env
    db.py            Declarative Base + cached Engine (pool_pre_ping, connect timeout)
    main.py          App factory: /api/v1 router, generic 500 handler
    api/v1/health.py GET /api/v1/health
  migrations/        Alembic (env.py reads DATABASE_URL via app.config)
  tests/             pytest against a real PostgreSQL test database
```

- **Configuration.** `DATABASE_URL` is required, so the app refuses to start without it. Values
  come from the environment first, then from the repo-root `.env`. Docker Compose injects
  `DATABASE_URL` pointing at the `db` service.
- **Health check.** Runs `SELECT 1` on a pooled connection. Returns `200` if it succeeds and
  `503` if it fails, with the same JSON body in both cases. It logs only the exception type,
  because driver messages can contain hosts or usernames.
- **Errors.** Unhandled exceptions are logged with a stack trace and returned as
  `{"detail": "Internal server error"}` with status `500`. Internals are never echoed.
- **Migrations.** One schema-free baseline revision (`2fa53e542881`) sets up version tracking.
  Domain tables arrive in later phases. `alembic check` in CI fails if models and migrations
  drift apart.

## Frontend

```
frontend/src/
  app/layout.tsx        Fonts (Fraunces + IBM Plex Sans), Shell, API status slot
  app/page.tsx          Discover workspace
  app/{sectors,companies,watchlist}/page.tsx   Section pages with empty states
  components/shell.tsx  Client: responsive sidebar / mobile drawer, active nav
  components/api-status.tsx  Server: calls /api/v1/health per request
  components/empty-state.tsx, graticule.tsx
```

- Cache Components is enabled (Next 16 default). Pages are prerendered static shells. The API
  status line is the only dynamic part: it calls `connection()` and is streamed in under
  `<Suspense>`.
- The browser never calls the API directly, so CORS is not configured. Add it when client-side
  API calls appear.
- Design tokens (navy/charcoal palette, brass accent, fonts) live in `src/app/globals.css`
  under `@theme`.

## Decisions

| Decision | Why |
| --- | --- |
| Sync SQLAlchemy engine | Simple and sufficient for Phase 0. FastAPI runs sync endpoints in a threadpool. Revisit if I/O-bound load grows. |
| uv + `uv.lock` | Reproducible, fast installs locally, in Docker and in CI |
| Real Postgres in tests (no SQLite or mocks) | The health check and migrations exercise real driver behaviour |
| Separate test database | The migration round-trip test downgrades to base, so it must never touch dev data |
| Host Postgres port 5433 | Avoids clashing with a locally installed Postgres on 5432 |
