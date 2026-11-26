# ATLAS

Vietnam Investment Discovery World: a platform for exploring Vietnam's listed economy by sector,
company and region.

**Status (2026-11-25, `main` @ `8007fe2`):** Phase 0 complete. Phase 1 software complete; its exit audit is a
**conditional pass** because non-software data blockers remain ([exit audit](docs/PHASE_1_EXIT_AUDIT.md)).
Phase 2 planning complete; **Phase 2 execution in progress under a conditional go** (see
[readiness](docs/PHASE_2_READINESS.md) and [roadmap](docs/ROADMAP.md)). 0 companies verified. The domain model (companies,
securities, exchanges, sectors, evidence, financial statements), the import framework, the
catalogue API and the companies and sectors UI are in place.

**No real company data is loaded yet.** No data provider is licensed or reachable (see
[data/SOURCES.md](data/SOURCES.md)), so ATLAS ships only a clearly labelled **fictional** sample
fixture. ATLAS never shows invented figures as real data.

## Phase 2: verified company discovery

**Objective:** turn the Phase 1 foundation into a usable discovery product, backed by at least 5
real, verified listed companies (stretch target 20–30) across the 4 approved sectors, with evidence-backed financials and
validation by real users.

**Current status:** planning complete; all product decisions (A-1 to A-11) approved on 2026-11-23.
Execution started under a **conditional go** (2026-11-23). 31 of 83 checklist items PASS
(37.3%). Workstreams 1–3 are merged to `main` (PRs #3–#5, CI green). Workstream 3 shows each financial figure's source document and page. Workstream 1 added a two-person verification workflow, per-figure source pages and
stricter period and unit checks ([docs/VERIFICATION_WORKFLOW.md](docs/VERIFICATION_WORKFLOW.md)).
Workstream 2 made the interface **Vietnamese-first**, with English at `/en`
([docs/GLOSSARY.md](docs/GLOSSARY.md); terms await a native-speaker review).
10 items are **blocked**, mostly on the legal opinion (G1). No real data is loaded.
Workstream 4 (ROE, ROA, missing data, period comparison, bank metrics) is specified, with the
owner's decisions recorded on 2026-11-24 ([docs/WS4_FINANCIAL_INTELLIGENCE_PLAN.md](docs/WS4_FINANCIAL_INTELLIGENCE_PLAN.md)).
WS4-1 (metric dictionary 1.1.0) is merged (PR #6). WS4-2 (ROE, ROA) is merged (PR #7, with display
fixes in PR #8; review in [docs/WS4_2_AUDIT.md](docs/WS4_2_AUDIT.md)). WS4-3 (period comparison) is
a plan awaiting owner decisions ([docs/WS4_3_IMPLEMENTATION_PLAN.md](docs/WS4_3_IMPLEMENTATION_PLAN.md)).

**Product direction (approved 2026-11-23):** start with Vietnamese investors learning to research
listed companies, with a Vietnamese-first interface; offer plain-language profiles where every
figure links to its source document. The MVP is M1–M5 (company profiles, key financials with
sources, discovery, data-status labels, Vietnamese UI). Data path (approved): a private 5-company pilot from companies' own audited reports now; public
display of real data only after a favourable Vietnamese legal opinion (gate G1). Pilot sectors
(approved): Banking & Financial Services, Consumer & Retail, Technology, Materials & Construction.
3D is deferred behind gate G3, and the core stays free with no paid tier in Phase 2 (A-5, A-8).
Details: [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md), with decisions in
[docs/PRODUCT_DECISIONS.md](docs/PRODUCT_DECISIONS.md).

**How progress is tracked:** [docs/PHASE_2_CHECKLIST.md](docs/PHASE_2_CHECKLIST.md) is the single
source of truth. Each item is `NOT STARTED`, `IN PROGRESS`, `PASS`, `BLOCKED` or `FAIL`. `PASS`
requires recorded evidence (test results, API responses, browser checks, source documents,
written licence terms); code existing is not enough. The percentage counts only PASS items.

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

- Frontend: http://localhost:3000 (Vietnamese), http://localhost:3000/en (English)
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
| GET | `/api/v1/companies/{id}/calculated-metrics` | ROE and ROA computed by ATLAS from the latest annual figures, with formula, inputs and their sources, or the reason they can't be computed; never stored |
| GET | `/api/v1/companies/{id}/comparisons?type=` | Changes between a period and its previous period (`annual_yoy`, `quarterly_qoq`, `quarterly_yoy`) for every reported metric, with both figures' sources, or the reason they can't be compared; never stored |
| GET | `/api/v1/metric-dictionary` | Metric dictionary (v1.1.0): names, vi/en definitions, unit, bank / non-bank applicability |
| GET | `/api/v1/sectors`, `/api/v1/sectors/{id}` | ATLAS sector taxonomy with company counts |
| GET | `/api/v1/companies` | Search (`q`: name or ticker), filter (`sector`, `exchange` codes), paginate (`limit`, `offset`) |
| GET | `/api/v1/companies/{id}` | Company with sector and securities |
| GET | `/api/v1/securities/{id}` | Security with exchange and company |
| GET | `/api/v1/companies/{id}/evidence` | Source evidence with data source and usage status |
| GET | `/api/v1/companies/{id}/financial-statements` | Latest revisions by default; values as exact decimal strings; each figure names its source document and page |

Full parameters and design notes: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#api-apiv1). OpenAPI
docs are at `/docs` on the backend.

Example response:

```json
{"status":"ok","version":"0.1.0","environment":"development","checks":{"database":{"status":"ok","latency_ms":1.3}}}
```

## Documentation

- [docs/ROADMAP.md](docs/ROADMAP.md): phases and gates at a glance
- [docs/PHASE_1_EXIT_AUDIT.md](docs/PHASE_1_EXIT_AUDIT.md),
  [docs/PHASE_2_READINESS.md](docs/PHASE_2_READINESS.md): Phase 1 exit audit and Phase 2 go/no-go
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): components, request flow, decisions
- [docs/VERIFICATION_WORKFLOW.md](docs/VERIFICATION_WORKFLOW.md),
  [docs/GLOSSARY.md](docs/GLOSSARY.md): two-person verification; Vietnamese UI terms
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): local setup, commands, troubleshooting
- [data/README.md](data/README.md): import format and rules, sector taxonomy, metric dictionary
- [data/SOURCES.md](data/SOURCES.md): data providers and licensing status
- [docs/PHASE_0_CHECKLIST.md](docs/PHASE_0_CHECKLIST.md),
  [docs/PHASE_1_CHECKLIST.md](docs/PHASE_1_CHECKLIST.md): verification evidence
- [docs/PHASE_2_CHECKLIST.md](docs/PHASE_2_CHECKLIST.md): Phase 2 plan, progress and evidence
- [docs/WS3_CHECKLIST.md](docs/WS3_CHECKLIST.md): per-figure source transparency acceptance record
- [docs/WS4_FINANCIAL_INTELLIGENCE_PLAN.md](docs/WS4_FINANCIAL_INTELLIGENCE_PLAN.md),
  [docs/WS4_CHECKLIST.md](docs/WS4_CHECKLIST.md): proposed ROE/ROA, missing-data and comparison
  rules, with the owner's decisions (2026-11-24)
- [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md),
  [docs/PRODUCT_DECISIONS.md](docs/PRODUCT_DECISIONS.md): product strategy and decision log
- [docs/PILOT_SELECTION_CRITERIA.md](docs/PILOT_SELECTION_CRITERIA.md): how pilot companies are
  chosen (approved)

## Known limitations

- No real company or financial data: 0 verified companies. Provider integration is blocked on
  licensing and credentials (see `data/SOURCES.md`). Publicly accessible documents are not treated
  as licensed, and no data is commercially licensed.
- Metric definitions and bank / non-bank applicability exist (dictionary 1.1.0), but companies have
  no bank / non-bank type yet, so a figure can't be shown as "not applicable" per company.
- ROE and ROA (WS4-2) are computed from unverified inputs until an independent reviewer exists (Q-3),
  and are labelled so; growth and other ratios are not implemented. Period comparison (WS4-3) is
  designed and its decisions approved, but not built.
- No authentication, and no price or market-event data.
- The 3D world view is not implemented; the Discover page only reserves space for it.
- `.env.example` credentials are for local development only. A production deployment needs
  real secrets management, which is out of scope so far.
