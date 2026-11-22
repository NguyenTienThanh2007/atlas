# Phase 1 checklist: financial data foundation

Last verified: 2026-11-22, macOS (Docker 29.6.1, Node 24.16, uv-managed Python 3.13, PostgreSQL 17).
Branch: `feat/p1-financial-data-foundation` (uncommitted at time of writing).

Status legend: **PASS** (verified by running it) · **FAIL** · **BLOCKED** (couldn't be done, reason
given) · **NOT STARTED**.

"Clean copy" means the final checks ran on a copy holding only the files git would commit (no
`.venv`, `node_modules`, `.next` or `.env`). That rules out local leftovers masking a problem.

## Data outcome (reported separately from software completion)

| Item | Value |
| --- | --- |
| Real verified companies | **0** |
| Real verified securities | **0** |
| Real evidence records | **0** |
| Sample fixture (fictional, `is_sample=true`, evidence `sample`) | 3 companies, 4 securities, 3 evidence records, 0 financial figures |
| Data providers integrated | **None** (see the blockers below) |

## 1. Domain schema

| Item | Status | Verification | Result | Files |
| --- | --- | --- | --- | --- |
| Entities: Sector, Exchange, Company, Security, DataSource, Evidence, FinancialStatement, FinancialMetric (+ IngestionRun) | PASS | `alembic upgrade head`; `alembic check` | Tables created; "No new upgrade operations detected" (models = migration) | `backend/app/models.py` |
| UUID primary keys, `timestamptz` timestamps | PASS | `test_timestamps_are_timezone_aware`; migration review | `gen_random_uuid()` server default and `uuid4` client default; tz-aware values read back | same |
| Company ≠ security; several securities per company | PASS | `test_company_can_have_several_securities`; sample "Beta" (HNX + UPCOM) in API and UI | Two securities returned in ticker order | same |
| Unique exchange code; (exchange, ticker) unique among non-delisted rows; ticker reusable after delisting | PASS | `test_exchange_code_is_unique`, `test_active_ticker_unique_per_exchange_but_reusable_after_delisting` | Duplicate active ticker rejected; same ticker on another exchange allowed; reuse after delisting allowed, history kept (3 rows) | same |
| Format and date checks (ticker, ISIN, currency, tax code, website scheme, delisted ⇔ date, delisted ≥ listed, period order, quarter 1–4, fiscal-year range) | PASS | `test_security_constraints[*]`, `test_delisted_before_listed_is_rejected`, `test_company_constraints`, `test_statement_identity_and_revision_rules` | All rejected by PostgreSQL CHECKs | same |
| No cascading deletes | PASS | `test_deletes_never_cascade` | Deleting a company with securities, or a sector in use → FK violation | same |
| Historical financial records never silently overwritten | PASS | `test_financial_history_is_append_only` | Triggers reject UPDATE and DELETE on statements and metrics (`restrict_violation`); value unchanged afterwards; `pg_trigger` lists both triggers | migration `981ec5176312` |
| Restatements as revisions | PASS | `test_statement_identity_and_revision_rules`, `test_restatement_is_a_new_revision_and_history_is_kept` | revision > 1 requires `supersedes_id`; old revision and metrics kept | `models.py`, `ingestion/importer.py` |
| Statement belongs to company (documented decision) | PASS | Read through | Rationale in `docs/ARCHITECTURE.md`, "Domain model" | `docs/ARCHITECTURE.md` |
| Ticker change, transfer and delisting handling documented | PASS | Read through | Same section | same |

## 2. Migrations

| Item | Status | Verification | Result |
| --- | --- | --- | --- |
| Upgrade / downgrade / re-upgrade | PASS | `alembic upgrade head` → `downgrade base` → `upgrade head` on `atlas_test`; `test_migrations_upgrade_downgrade_roundtrip` | Downgrade leaves only `alembic_version`; trigger function dropped; re-upgrade OK |
| Fresh database in Docker | PASS | Isolated compose projects `atlasp1` and `atlasp1ci` on new volumes | Logs show `2fa53e542881` then `981ec5176312` applied, then reference seeded |
| Revisions | PASS | `alembic history` | `2fa53e542881` baseline → `981ec5176312` domain model |

## 3. Sector taxonomy and 4. Exchanges

| Item | Status | Verification | Result | Files |
| --- | --- | --- | --- | --- |
| 7 sectors with stable codes, English and Vietnamese names, descriptions, version, methodology | PASS | `GET /api/v1/sectors` on a fresh stack → `total 7`; browser shows Vietnamese names | v1.0.0; methodology states it is not an official classification (also shown in the UI) | `backend/app/reference/sector_taxonomy.json`, `data/README.md` |
| Versioned changes only | PASS | `test_taxonomy_changes_need_a_version_bump` | Same-version edit → conflict, not applied; bumped version → updated | `ingestion/reference.py` |
| HOSE, HNX, UPCOM | PASS | `GET /api/v1/exchanges` on a fresh stack | `['HNX', 'HOSE', 'UPCOM']` | `backend/app/reference/exchanges.json` |
| Seeded idempotently on every container start | PASS | Container logs after restart | First start `created 3 / 7`; restart `unchanged 3 / 7` | `backend/Dockerfile` |

## 5–8. Models, provenance, statements, decimals

| Item | Status | Verification | Result |
| --- | --- | --- | --- |
| Company and security models tested | PASS | `tests/test_models.py` | 18 tests pass |
| Evidence provenance (source, URL, retrieved_at, verification status, usage status) | PASS | `test_valid_import_creates_records_with_provenance`, `test_company_evidence_includes_provenance` | Evidence linked to its data source; API exposes source name and `commercial_usage_status` |
| `commercial_usage_status` distinguishes unknown / personal_only / licensed / public_official / restricted; defaults to unknown | PASS | Schema CHECK; `test_changed_data_source_terms_fail_the_run` | Terms can't change through an import |
| Financial statement schema tested | PASS | `test_statement_identity_and_revision_rules`, statement import and API tests | — |
| Decimal precision (`NUMERIC(38,6)`, `Decimal`, no floats) | PASS | `test_metric_values_round_trip_exactly[*]` (38 digits, −0.000001, 0.1+0.2, 10^15), `test_json_numbers_are_parsed_as_decimals_not_floats`, `test_invalid_metrics_are_rejected[…decimal places]`, API test asserting `"2000000000.000001"` as a string; UI shows `1,111,111,111,111.123456 VND` | All exact; more than 6 decimal places rejected rather than rounded |
| Documented metric dictionary | PASS | Read through | 16 metrics, versioned; Vietnamese names | `backend/app/reference/metric_dictionary.json`, `data/README.md` |

## 9. Ingestion framework

| Item | Status | Verification | Result |
| --- | --- | --- | --- |
| Modular (connectors / normalize / schemas / jobs / runs) | PASS | Read through | `backend/app/ingestion/`; mapping in `docs/ARCHITECTURE.md` |
| Valid import | PASS | `test_valid_import_creates_records_with_provenance`; CLI import of the sample fixture | `created 3 companies / 4 securities / 3 evidence` |
| Idempotent (repeatable) | PASS | `test_sample_fixture_imports_flagged_and_idempotently`, `test_statement_import_is_exact_and_idempotent`; CLI re-import | Second run `{"companies.seen": 3, "companies.unchanged": 3}`, row counts unchanged |
| Duplicate detection | PASS | `test_duplicate_in_bundle_is_flagged` | `duplicate` issue; one row |
| Invalid records reported, others still import | PASS | `test_invalid_record_is_reported_and_others_still_import` | Missing evidence, bad listing and unknown field each rejected with record index |
| Conflicts detected, never overwritten, rolled back as a unit | PASS | `test_conflicting_record_never_overwrites`, `test_conflicting_record_rolls_back_as_a_unit`, `test_changed_figures_are_a_conflict_not_an_overwrite`, `test_identifiers_pointing_at_two_companies_conflict` | Stored values unchanged; issue names the differing fields |
| Missing evidence / references | PASS | `test_invalid_record_…`, `test_missing_references_are_reported`, `test_revision_gap_and_unknown_company_are_reported` | Rejected with an actionable message |
| Unexpected DB constraint rejects only that record | PASS | `test_database_constraint_violation_rejects_only_that_record` | Duplicate ISIN → `conflict (uq_securities_isin)`; other records imported |
| Normalisation (NFC Vietnamese, whitespace, codes, tax codes) | PASS | `test_text_and_codes_are_normalised`, `test_valid_import_…` (`"0100 000 001"` → `0100000001`) | — |
| Runs recorded with source, retrieval time, SHA-256, counts, issues | PASS | `test_unreadable_bundle_fails_and_is_recorded[*]`; `ingestion_runs` rows in Docker | Failed runs recorded too |
| Failures logged with context; CLI exit codes 0 / 2 / 1 | PASS | `test_cli_exit_codes`; CLI against malformed file | `exit=1`, log: "not valid JSON: Expecting ',' delimiter at line 2" |
| Sample data can't pose as real | PASS | `test_sample_and_real_data_never_mix`, `test_statement_for_sample_company_from_real_source_is_rejected` | — |
| No credentials in code; tests need no API credentials | PASS | Read through; `git grep` | Only local-file connector |

## 10. API

| Item | Status | Verification | Result |
| --- | --- | --- | --- |
| 8 required endpoints | PASS | `test_openapi_documents_catalog` plus per-endpoint tests | All present in OpenAPI |
| Pagination, stable sort | PASS | `test_pagination_is_stable_and_complete` | Pages concatenate to the full ordered list |
| Search (name, English name, ticker; wildcards escaped) and filters (sector, exchange) | PASS | `test_search_and_filters[*]` (13 cases) | `%` and `_` treated literally; delisted listings excluded from exchange filter |
| Query validation → 422; missing → 404 with clear detail | PASS | `test_invalid_query_is_422[*]`, `test_missing_records_are_404`, `test_sector_not_found_and_bad_id` | — |
| No N+1 | PASS | `test_company_list_has_no_n_plus_one` | Same query count (≤ 3) for 1 and 100 rows; relationships are `lazy="raise"` |
| Internal fields not exposed | PASS | `test_list_item_shape_hides_internal_fields`, `test_company_detail`, evidence test | No `sector_id` or `data_source_id` |
| Superseded revisions hidden by default | PASS | `test_financial_statements_latest_revision_and_exact_values` | `include_superseded=true` returns history with `is_superseded` |

## 11–12. Frontend

| Item | Status | Verification | Result |
| --- | --- | --- | --- |
| Reads real API responses | PASS | Browser against an isolated stack | Companies, sectors and detail pages render API data |
| Companies list with search and filters | PASS | Browser: typed `sample2p` plus sector filter → 1 result; values kept in the form; Clear link | — |
| Company detail, sectors list, sector detail | PASS | Browser + `curl` | Listings, statements (restated revision label, exact value), sources with usage rights |
| Loading states | PASS | Observed "Loading…" skeleton during navigation | `loading.tsx` on all 4 routes |
| Empty states | PASS | Fresh stack: `/companies` → "No companies yet"; sector with no companies; "No companies match" | — |
| Error states / usable with backend down | PASS | `docker compose stop backend` → each page shows its error panel; sidebar "API unreachable"; Discover renders | — |
| Unknown ids → not-found page | PASS | `/companies/<zero uuid>`, `/companies/not-a-uuid`, `/sectors/<zero uuid>` | Not-found page rendered |
| Sample data clearly labelled | PASS | Browser | Badge on list items, banner on detail page |
| Unit tests (API client, error mapping, decimal and date formatting) | PASS | `npm test` | 8/8 |
| Mobile | PASS | 375×812 | No horizontal scroll (`scrollWidth 375`) |
| No console errors | PASS | Browser console (production build) | "No console logs" |
| Lint / typecheck / build | PASS | `npm run lint`, `npm run typecheck`, `npm run build` (clean copy) | All pass; `npm audit` 0 vulnerabilities |

## 13–17. Tests, Docker, CI, docs

| Item | Status | Verification | Result |
| --- | --- | --- | --- |
| Backend tests | PASS | `uv run pytest` (clean copy) | **87 passed** |
| Backend lint and types | PASS | `ruff check`, `ruff format --check`, `mypy` strict (clean copy) | Clean |
| Test DB guard | PASS | `pytest` with `TEST_DATABASE_URL` pointing at `atlas` | Refuses to run (exit 4); suite requires a `*_test` database |
| Docker stack | PASS | Clean copy, `.env.example` as committed: `config -q`, `build`, `up --wait` | Health 200; 7 sectors; 3 exchanges; frontend `/`, `/companies`, `/sectors` → 200 |
| Data survives restart | PASS | `down` → `up` on `atlasp1` | 3 companies / 2 statements and revision chain intact |
| GitHub Actions ready | PASS (local) | Each workflow's commands run locally on the clean copy | Backend CI database renamed `atlas_ci_test` (guard); frontend CI runs `npm test`; backend CI also triggers on `data/**` |
| GitHub Actions executed remotely | BLOCKED | Needs a push, which needs authorization | Not run |
| Documentation | PASS | Read through | README, ARCHITECTURE, DEVELOPMENT, `data/README.md`, `data/SOURCES.md`, this checklist |

## Blockers (data, not software)

| Blocker | Status | What unblocks it |
| --- | --- | --- |
| No licensed data provider | BLOCKED | Decision on provider and intended use; written terms (see `data/SOURCES.md`) |
| SSI FastConnect | BLOCKED | SSI trading account, API keys, commercial-use and storage terms (not found in docs) |
| SSC disclosure portal, HNX | BLOCKED | Not reachable from this environment (DNS / TLS errors) |
| HOSE | BLOCKED | No usable content to an automated fetch; terms unknown |
| 50–100 verified companies | BLOCKED | Depends on the above, or on manual curation from reviewed documents |

## Self-review findings

| ID | Severity | Finding | Resolution |
| --- | --- | --- | --- |
| H-1 | HIGH | A DB constraint the validators didn't foresee (or a concurrent import) aborted the whole import run | Fixed: per-record `IntegrityError` → `conflict` naming the constraint; test added |
| H-2 | HIGH | Production build failed: `usePathname()` in the root layout blocked prerendering of dynamic routes | Fixed: active-link read moved into its own `<Suspense>` leaf |
| H-3 | HIGH | Test suite could wipe a non-test database (Phase 0 audit #2, now real with tables) | Fixed: refuses any database not ending in `_test`; CI renamed |
| M-1 | MEDIUM | CLI exit code ranked "partial" above "failed" | Fixed |
| M-2 | MEDIUM | Timestamps shown as UTC dates (a retrieval at 00:00 +07:00 displayed as the previous day) | Fixed: `formatDate` in Vietnam time; test added |
| M-3 | MEDIUM | `fixture://` and `file://` evidence URLs rendered as links | Fixed: only http(s) links |
| M-4 | MEDIUM | Sidebar status blamed the database for any non-OK API reply (Phase 0 audit #1) | Fixed: decided by HTTP status; separate "API returned an error" state |
| L-1 | LOW | `assert` used for an invariant in production code | Fixed: explicit error |
| L-2 | LOW | Evidence is polymorphic, with no FK on `entity_id` | Documented; integrity enforced by the importer |
| L-3 | LOW | Company master data can't be *updated* through imports (conflicts only) | Deliberate for now; needs a reviewed update path later |
| L-4 | LOW | Not-found on streamed dynamic routes: the not-found page renders, but the HTTP status code was not checked | NOT VERIFIED |
| L-5 | LOW | Detail page titles are generic ("Company · ATLAS") | Open |
| L-6 | LOW | pytest shows Starlette's `httpx` → `httpx2` deprecation warning (from Phase 0) | Open |

No CRITICAL or HIGH findings remain open.

## Completion gate

| # | Criterion | Status |
| --- | --- | --- |
| 1 | Domain schema implemented | PASS |
| 2 | Migrations upgrade and downgrade | PASS |
| 3 | Sector taxonomy available | PASS |
| 4 | Exchange records available | PASS |
| 5 | Company and security models tested | PASS |
| 6 | Evidence provenance implemented | PASS |
| 7 | Financial statement schema tested | PASS |
| 8 | Decimal precision tests pass | PASS |
| 9 | Import framework idempotent | PASS |
| 10 | Company and sector APIs work | PASS |
| 11 | Frontend reads real API responses | PASS |
| 12 | Loading, empty and error states work | PASS |
| 13 | Backend tests pass | PASS (87) |
| 14 | Frontend lint / typecheck / build pass | PASS |
| 15 | Docker stack works | PASS |
| 16 | GitHub Actions pass locally and are ready for remote execution | PASS (local); remote run BLOCKED pending push |
| 17 | Documentation updated | PASS |
| 18 | No unresolved CRITICAL or HIGH defects | PASS |

Data provider integration: **BLOCKED** (licensing and credentials). It is reported above and was not
faked to satisfy the gate.
