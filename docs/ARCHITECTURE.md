# Architecture

## Components

```
 Browser ──► frontend (Next.js, :3000) ──server-side fetch──► backend (FastAPI, :8000) ──► db (PostgreSQL, :5432 in-network)
                                                               ▲
                              import bundles (JSON) ──► python -m app.ingestion
```

| Service | Source | Container | Notes |
| --- | --- | --- | --- |
| `frontend` | `frontend/` | `node:24-alpine`, Next.js standalone output, runs as `node` | Reads `API_URL` at request time |
| `backend` | `backend/` | `python:3.13-slim` + uv, runs as non-root `atlas` | On start: `alembic upgrade head`, seeds reference data, then uvicorn |
| `db` | `infra/postgres/init/` | `postgres:17-alpine` | Named volume `pgdata`; init script creates `<POSTGRES_DB>_test` |

All host port bindings are on `127.0.0.1` only.

## Backend

```
backend/
  app/
    config.py            Settings (pydantic-settings): env vars, then repo-root .env
    db.py                Base (constraint naming convention), Engine, per-request Session
    models.py            Domain model (see below)
    main.py              App factory: /api/v1 routers, generic 500 handler
    api/v1/health.py     GET /api/v1/health
    api/v1/catalog.py    Sectors, exchanges, companies, securities, evidence, financial statements
    api/v1/schemas.py    Public response models
    reference/           Versioned reference data: sector taxonomy, exchanges, metric dictionary
    ingestion/           connectors → schemas/normalize → jobs (importer, reference) → runs
  migrations/            Alembic
  tests/                 pytest against a real PostgreSQL test database
```

### Domain model

```
sectors ◄── companies ◄── securities ──► exchanges
  (self-parent)   │  ▲
                  │  └── evidence (entity_type, entity_id) ──► data_sources
                  │          ▲
                  │          └── verification_reviews (append-only, two-person)
                  ▼
        financial_statements ──► evidence (source)        ingestion_runs ──► data_sources
           │   └─ supersedes_id ─► financial_statements
           ▼
        financial_metrics
```

| Table | Purpose | Key constraints |
| --- | --- | --- |
| `sectors` | ATLAS taxonomy (`taxonomy_version`, `name_vi`) | `code` unique and formatted; optional `parent_sector_id` |
| `exchanges` | HOSE, HNX, UPCOM | `code` unique; ISO country code |
| `companies` | Legal entity | `tax_code` unique when present (10 or 10+3 digits); `website` must be http(s); `is_sample`; `last_verified_at` |
| `securities` | A tradable instrument on one exchange | Ticker and ISIN format; `(exchange, ticker)` unique among **non-delisted** rows; `delisted_at` set exactly when status is `delisted`; `delisted_at ≥ listed_at` |
| `data_sources` | Where data comes from | `commercial_usage_status` ∈ unknown, personal_only, licensed, public_official, restricted (default `unknown`) |
| `evidence` | Provenance for any entity | `retrieved_at` required; effective range ordered; SHA-256 format; unique (source, entity, URL, retrieved_at). Inserted only as `unverified`/`sample`; immutable; status changes only through a review (triggers) |
| `verification_reviews` | Two-person review decisions (Phase 2 WS1) | Append-only; curator ≠ reviewer; reviewer not a system name; allowed transitions only; `from_status` must match. See [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) |
| `financial_statements` | One reported statement | Belongs to the **company**; period ordered; quarter 1–4; identity unique (`NULLS NOT DISTINCT`) including `revision`; revision > 1 ⇔ `supersedes_id` set; `source_evidence_id` required |
| `financial_metrics` | One line item | `NUMERIC(38,6)`; code format; unique per statement; `source_page`, `reported_value`, `reported_scale` with `value = reported_value × reported_scale`; page and as-reported value required for real figures (trigger) |
| `ingestion_runs` | Audit of every import | status, input SHA-256, counts, issues (JSONB) |

Design decisions:

- **Company ≠ security ≠ ticker.** A company can have several securities (ordinary and
  preferred shares, listings on different venues). A ticker identifies a security only together
  with its exchange and only while that listing is active.
- **Ticker changes, transfers and delistings** never edit history. The old security row is set to
  `delisted` with `delisted_at`, and a new row is created for the new ticker or exchange. A
  partial unique index lets a ticker be reused after delisting. A move from HNX to HOSE is two
  rows on two exchanges.
- **Financial statements belong to the company**, not to a security. A legal entity files one
  set of statements however many securities it has, and attaching them to a ticker would break
  on transfers and duplicate data across share classes.
- **History is append-only.** Database triggers reject `UPDATE` and `DELETE` on
  `financial_statements` and `financial_metrics` (`restrict_violation`). A restatement is a new
  row with `revision = N+1` and `supersedes_id` pointing at revision N. The API returns the latest
  revisions unless `include_superseded=true`.
- **No cascading deletes.** Every foreign key is `ON DELETE RESTRICT`.
- **Money is exact.** PostgreSQL `NUMERIC(38,6)` maps to Python `Decimal`. Input JSON numbers are
  parsed as `Decimal` (never `float`), and the API serialises values as decimal **strings**.
  More than 6 decimal places is rejected at import rather than silently rounded.
- **Evidence is polymorphic** (`entity_type`, `entity_id`) and has no foreign key on `entity_id`.
  Integrity is enforced by the importer, which creates evidence only for rows it just resolved
  or created.
- **Timestamps** are `timestamptz`. Business dates (listing dates, reporting periods) are `date`.
- **Enums** are `VARCHAR` plus `CHECK` (not native PG enums), which keeps migrations simple and
  reversible.

Migrations: `2fa53e542881` (baseline) → `981ec5176312` (domain model with append-only triggers).
Both downgrade cleanly, and a test checks the round trip.

### Ingestion

`backend/app/ingestion/`, run as `python -m app.ingestion {reference | import <file>}`:

| Module | Job |
| --- | --- |
| `connectors.py` | Fetch raw bytes (local files only) and parse JSON with exact decimals and no duplicate keys |
| `normalize.py` | NFC Unicode, whitespace, code upper-casing, tax-code cleanup |
| `schemas.py` | Pydantic input models (`extra="forbid"`), validated one record at a time |
| `importer.py` | Business rules: identity resolution, idempotency, conflicts, restatements, sample/real separation |
| `reference.py` | Versioned taxonomy and exchange seeding; metric dictionary |
| `runs.py` | Records each run with counts and actionable issues |

Each record is applied inside a SAVEPOINT, so it lands completely or not at all. The caller (the
CLI) commits data and the run record together. The rules are listed in `data/README.md`.

### API (`/api/v1`)

| Endpoint | Notes |
| --- | --- |
| `GET /health` | 200, or 503 if the database is down |
| `GET /exchanges` | Paginated |
| `GET /sectors`, `GET /sectors/{id}` | Includes `company_count` (one query, scalar subquery) |
| `GET /companies` | `q` (name, English name or ticker; case-insensitive substring, wildcards escaped), `sector` (code), `exchange` (code, non-delisted listings only), `limit` 1–100, `offset` |
| `GET /companies/{id}` | With sector and all securities |
| `GET /securities/{id}` | With exchange and company |
| `GET /companies/{id}/evidence` | Evidence for the company and its securities, newest first, with data source and usage status |
| `GET /companies/{id}/financial-statements` | Latest revisions by default; `include_superseded`, `fiscal_year`, `statement_type`, `scope`. Each metric carries `reported_value`, `reported_scale` and a per-figure `source` (`evidence_id`, `document_title`, `document_url` only when it is a safe http(s) link, `link_status`, `page` or `null`, `verification_status`). See [WS3_CHECKLIST.md](WS3_CHECKLIST.md#response-contract-b-01) |

- Lists return `{items, total, limit, offset}` with a deterministic order (ties broken by `id`).
- Relationships are declared `lazy="raise"`, so any accidental lazy load fails loudly. Lists
  eager-load in a fixed number of queries; a test asserts the query count doesn't grow with page
  size.
- Errors: `404 {"detail": "Company not found"}`; `422` for invalid query or path values.
  Interactive docs are at `/docs`.
- Responses never include internal foreign keys such as `sector_id` or `data_source_id`.

## Frontend

```
frontend/src/
  proxy.ts                         Language routing: unprefixed URLs are Vietnamese (rewritten to /vi/...); /en/... is English; /vi/... redirects to the canonical URL
  i18n/routing.ts                  Locales (vi default, en), localePath/stripLocale/routeRequest (pure, unit-tested)
  i18n/vi.ts, i18n/en.ts           Dictionaries; en is typed against vi (same keys). Glossary: docs/GLOSSARY.md
  i18n/index.ts, i18n/text.ts      getI18n() (locale from next/root-params, dictionary, locale-aware href); error and unit text
  app/[lang]/layout.tsx            Root layout per language: <html lang>, fonts (latin + vietnamese subsets), Shell, API status
  app/[lang]/page.tsx              Discover workspace
  app/[lang]/companies/page.tsx    List with search, sector and exchange filters, pagination (GET form, no client JS needed)
  app/[lang]/companies/[id]/page.tsx  Detail: facts, listings, financial statements, sources
  app/[lang]/sectors/...           Taxonomy with company counts; sector with its companies
  app/[lang]/not-found.tsx, [...missing]  Localized not-found (unknown URLs return HTTP 404)
  app/[lang]/**/loading.tsx        Loading states (Suspense boundaries)
  lib/api-core.ts                  Pure API client and types; errors are kinds, not text; formatDecimal/formatDate per language (unit-tested)
  lib/api.ts                       Server-only wrapper: connection() + API_URL
  components/                      shell (nav, language switch), states, company list, filters, pagination
scripts/check-routes.mjs           Route check against a running build: lang, key text per language, status codes, backend up/down
```

- **Vietnamese first (A-4, WS2).** Vietnamese is the default at today's URLs; English is under
  `/en`. The language is never guessed from the browser. The switch keeps the current page and
  query. Data stays as stored: company and source names and taxonomy descriptions (English-only in
  v1.0.0) are shown as data, marked with `lang` where the language differs.
- Every data request runs server-side at request time. If the API is unreachable, each page shows
  an inline error panel in the page's language and the shell keeps working. A `404` from the API
  renders the localized not-found page.
- Sample records always show a "Sample data" / "Dữ liệu mẫu" badge, and a banner on the detail page.
- Financial values are shown from the API's decimal strings with digit grouping only
  (`1.234.567,89` in Vietnamese, `1,234,567.89` in English). They are never parsed to floats.
  Metric labels in Vietnamese come from the metric dictionary via the API (`metric_name_vi`).
  Timestamps are shown in Vietnam time (UTC+7).
- Cache Components: the nav highlight and the language switch read `usePathname()` /
  `useSearchParams()` inside their own `<Suspense>`, so routes still prerender a static shell per
  language.

## Decisions

| Decision | Why |
| --- | --- |
| Sync SQLAlchemy engine | Simple and sufficient so far. FastAPI runs sync endpoints in a threadpool. Revisit if I/O-bound load grows. |
| uv + `uv.lock` | Reproducible, fast installs locally, in Docker and in CI |
| Real Postgres in tests (no SQLite or mocks) | Constraints, triggers, `NUMERIC` and `NULLS NOT DISTINCT` are PostgreSQL behaviour |
| Separate test database | The migration round-trip test downgrades to base, so it must never touch dev data |
| Ingestion code inside the backend package | Shares models, settings, tests and CI; `data/` holds data files and docs |
| Reference data in `backend/app/reference/` | Ships in the backend image and is seeded on every start (idempotently) |
| Host Postgres port 5433 | Avoids clashing with a locally installed Postgres on 5432 |
