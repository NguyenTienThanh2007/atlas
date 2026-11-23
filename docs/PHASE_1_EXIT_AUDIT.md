# Phase 1 exit audit

Date: 2026-11-23. Auditor: Claude Code (automated audit, owner review pending). Environment: macOS,
Docker 29.6.1, Node 24.16.0, uv 0.12.21 / Python 3.13, PostgreSQL 17 (`postgres:17-alpine`).

**Exit decision: CONDITIONAL PASS.** The Phase 1 software foundation is complete and was reproduced
from a clean copy of the committed code. Data blockers remain, and they are not software: there is no
licensed provider, the legal opinion (G1) is outstanding, and there are 0 verified real companies.
Software completion is **not** verified-company readiness.

## 1. Method

- **Code under test:** `HEAD` = `3660e5f` (merge of PR #2, same as `origin/main`), extracted with
  `git archive HEAD` into an empty directory. That copy has no `.env`, `.venv`, `node_modules` or
  `.next`, so local leftovers can't hide a missing dependency.
- **Isolated stack:** Docker Compose project `atlasexit` on a **new volume** and spare ports
  (5463 / 8063 / 3063). It used `.env.example` with only the ports changed. The owner's running
  `atlas` stack and its `atlas_pgdata` volume were not touched.
- **Remote CI:** read with `gh run list` / `gh run view` (read-only).
- **Excluded:** the uncommitted planning docs on branch `docs/p2-checklist` are not code, and are
  outside this test.

## 2. Repository baseline

| Check | Result |
| --- | --- |
| Path / branch | `/Users/nguyentienthanh/Documents/atlas`, branch `docs/p2-checklist` (= `main` + uncommitted docs) |
| Remote / default branch | `origin` = `github.com/NguyenTienThanh2007/atlas`; default `main` |
| Working tree at start | Modified: `README.md`, `data/SOURCES.md`. Untracked: `docs/PHASE_2_CHECKLIST.md`, `PILOT_SELECTION_CRITERIA.md`, `PRODUCT_DECISIONS.md`, `PRODUCT_STRATEGY.md` (Phase 2 planning, preserved) |
| Tracked files | 90; only `.env.example` matches env/secret name patterns |
| Secrets in history | `git log -p --all` scanned for AWS keys, private keys, GitHub/OpenAI tokens, `password=` literals: no hits |
| Build artefacts tracked | None (`node_modules`, `.next`, `__pycache__`, `.venv`, `dist` absent from the index) |
| iCloud duplicates | Only inside the ignored build folder `frontend/.next` (`… 2` copies); none tracked (see F-5, risk R-1) |
| Private G2 package | Outside the repo (`~/ATLAS-private/g2`); no repo file references it; 23/23 SHA-256 sums verify |

## 3. Results

| Area | Status | Evidence |
| --- | --- | --- |
| **Phase 0** foundation | PASS | Monorepo layout present; `.gitignore` rules unchanged since the Phase 0 probes; fresh-volume start, health, persistence and shutdown re-run below; containers non-root (`backend` → `atlas`, `frontend` → `node`); ports bound to `127.0.0.1` |
| Domain model | PASS | `alembic check`: "No new upgrade operations detected"; model tests in the 87 passing (UUID PKs, `timestamptz`, company ≠ security, ticker reuse after delisting, `RESTRICT` FKs, append-only triggers, revision chain) |
| Financial precision | PASS | `NUMERIC(38,6)`; exact round-trip tests and >6 decimal places rejected (in the 87 passing). The API returns decimal strings |
| Migrations | PASS | `atlas_test`: `upgrade head` → `check` → `downgrade base` → `upgrade head`; `current` = `981ec5176312 (head)`. Fresh container log: `2fa53e542881` then `981ec5176312` |
| Reference data | PASS | Fresh stack: exchanges `['HNX','HOSE','UPCOM']`, 7 sectors (v1.0.0); restart log `exchanges.unchanged 3`, `sectors.unchanged 7` (idempotent) |
| Metric dictionary | PASS with gaps | 16 unique codes, Vietnamese names, units, version 1.0.0. **No per-metric definitions** (F-1) and **no bank applicability** (F-2) |
| Ingestion | PASS | Tests in the 87 passing. CLI on the fresh stack: sample import exit 0; re-import `companies.unchanged 3`, exit 0; malformed JSON exit 1; `ingestion_runs`: 6 succeeded, 1 failed (the failure was recorded) |
| Sample separation / provenance | PASS | API: 3 companies, all `is_sample: true`; evidence `verification_status: sample`, source `commercial_usage_status: restricted`; UI shows "Sample data" badges and a "fictional" banner |
| API | PASS | Health 200; `/docs` 200; unknown company → 404 `Company not found`; `limit=0` → 422; non-UUID id → 422; superseded revisions, pagination, N+1 and field exposure covered by tests |
| Frontend | PASS | Routes `/`, `/companies`, `/sectors`, `/watchlist` → 200; `/nope` → 404. Browser: list, company detail and sectors render API data; one `h1` per page; 0 unnamed links/buttons; all inputs labelled; 375 px wide has no horizontal scroll; keyboard focus ring visible (2 px brass outline); backend stopped → "API unreachable", "Couldn't load companies / sectors"; no app console errors |
| Backend quality | PASS | `uv sync --frozen` OK; `ruff check` "All checks passed!"; `ruff format --check` "29 files already formatted"; `mypy app tests migrations/env.py` "no issues in 27 source files"; **`pytest`: 87 passed, 1 warning** (L-6) |
| Frontend quality | PASS | `npm ci` (lockfile); `lint` exit 0; `typecheck` exit 0; **`npm test`: 8 passed, 0 failed**; `build` OK (9 routes, partial prerender); `npm audit`: 0 vulnerabilities |
| Docker | PASS | `config -q` OK; `build` OK; `up --wait` on a new volume: db healthy, backend healthy, frontend up. `down` → `up`: 3 companies still present. `down -v`: volume removed |
| CI | PASS (remote) | GitHub Actions on `3660e5f` (push to `main`, 2026-11-22): Backend ✅, Frontend ✅, Docker ✅. Also ✅ on the PR #2 head. The CI commands match the local ones above |
| Security | See §5 | `pip-audit --strict`: no known vulnerabilities; `npm audit`: 0 |
| Documentation | PASS after fixes | F-1 doc line corrected; README status updated; `docs/ROADMAP.md` added |

## 4. Data outcome (unchanged; reported separately)

| Item | Value |
| --- | --- |
| Real verified companies / securities / evidence records | **0 / 0 / 0** |
| Fictional sample fixture | 3 companies, 4 securities, 3 evidence records, **0** financial figures |
| Licensed provider integrated | **None** |
| Commercial data rights | None assumed; every source `unknown` (`data/SOURCES.md`) |

No pilot-company data was imported during this audit, and the private G2 package was not modified.

## 5. Security and configuration

| Kind | Items |
| --- | --- |
| Verified controls | Env-driven config with `:?` guards in Compose; `.env` ignored at every depth; no secrets in history (pattern scan); non-root app containers; ports bound to localhost; generic 500 body and DB errors logged by type only; all queries via the SQLAlchemy expression API (only raw SQL: `SELECT 1` and static DDL defaults); test-DB guard (`*_test` only); 0 known dependency vulnerabilities (pip-audit, npm audit) |
| Untested controls | Behaviour behind a reverse proxy; rate limiting (none exists); log volume and retention |
| Known risks | No authentication (none needed yet: read-only, local); placeholder DB password in `.env.example` (local only, documented); repo in iCloud-synced folder (R-1) |
| Out of scope (production) | Secrets management, TLS, CORS policy for browser clients (the UI calls the API server-side, so none is configured), backups, monitoring, hosting (Q-7) |

This is not a claim that the system is production-secure.

## 6. Defects

Counts: CRITICAL 0 · HIGH 0 · MEDIUM 2 (open) · LOW 5 (1 fixed, 4 open) · INFORMATIONAL 3.

| ID | Sev. | Description | Impact | Reproduce | Root cause | Fix | Files | Tests | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F-1 | MEDIUM | Metrics have no definitions, and `data/README.md` claimed "description[s] are in `metric_dictionary.json`" | A learner-facing glossary can't be built from the dictionary; the doc overstated it | Inspect the metric entries: keys are `code, name, name_vi, statement_type, unit` only | Definitions never written | Doc corrected now. Writing definitions is a dictionary version bump, so owner approval is needed (Phase 2, before figures are shown) | `data/README.md`, `backend/app/reference/metric_dictionary.json` | n/a | Doc FIXED; definitions OPEN |
| F-2 | MEDIUM | No "not applicable" marker per metric (e.g. `gross_profit` for banks) | P2-5.15 needs "not applicable" vs "not reported" for the bank in the pilot | Dictionary has no applicability field | Out of Phase 1 scope | Decide with Q-5; add applicability in a versioned dictionary change | same | none yet | OPEN (Phase 2) |
| F-3 | LOW | Not-found on dynamic routes returns HTTP **200** (page body is the 404 page, with `noindex`) | Monitoring and crawlers see 200; users see the correct page | `curl -w '%{http_code}' :3063/companies/<zero uuid>` → 200 | Streamed partial prerender sends headers before `notFound()` | Revisit when the routes are reworked for Vietnamese UI; not a correctness defect | `frontend/src/app/*/[id]/page.tsx` | none | OPEN (was L-4 "not verified"; now verified) |
| F-4 | LOW | `frontend` service has no Compose healthcheck | `up --wait` can't prove the UI is serving | `docker compose ps` shows "Up" without "(healthy)" | Not added in Phase 0 | Add a healthcheck when deployment is planned | `docker-compose.yml` | CI curls `/` | OPEN |
| F-5 | INFO | iCloud conflict copies inside ignored `frontend/.next` | None for Git; possible confusion locally | `find frontend/.next -name '* 2*'` | Repo in iCloud `~/Documents` | Q-8 / R-1: move the repo | — | — | OPEN (risk) |
| F-6 | INFO | Phase 1 checklist listed remote CI as BLOCKED | Outdated | `gh run list` | CI ran after the checklist was written | Recorded as new evidence in the checklist addendum | `docs/PHASE_1_CHECKLIST.md` | — | FIXED |
| F-7 | INFO | README said "Phase 2 in planning" without distinguishing planning done vs execution | Status ambiguity | Read README | — | README status updated | `README.md` | — | FIXED |
| L-2/L-3/L-5/L-6 | LOW | Carried from Phase 1: polymorphic evidence without FK; no reviewed update path; generic detail titles; `httpx` deprecation warning (still printed) | As recorded in the Phase 1 checklist | — | — | Unchanged | — | — | OPEN |

No CRITICAL or HIGH defects were found, so no code was changed.

## 7. Exit criteria

| Criterion | Status |
| --- | --- |
| Mandatory Phase 1 software requirements | PASS |
| Domain model correct; migrations reproducible | PASS |
| Ingestion, provenance, sample separation | PASS |
| API and frontend verified | PASS |
| Backend and frontend quality checks | PASS |
| Docker fresh start, persistence, shutdown | PASS |
| Documentation matches implementation | PASS (after F-1, F-6, F-7) |
| No open CRITICAL/HIGH defects | PASS |
| Blockers documented; data outcome accurate | PASS |
| Git working tree understood | PASS |

**Decision: CONDITIONAL PASS.** The software foundation is complete. These non-software blockers
remain: no licensed data provider, G1 legal opinion pending, 0 verified companies, and Q-3 reviewer
not appointed. Phase 2 readiness is in [PHASE_2_READINESS.md](PHASE_2_READINESS.md).
