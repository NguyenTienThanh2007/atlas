# WS3 checklist: per-figure source transparency

Single source of truth for workstream 3 (Phase 2 item P2-4.13). Statuses: `NOT STARTED`,
`IN PROGRESS`, `PASS`, `BLOCKED`, `FAIL`. PASS needs recorded evidence.

**Branch:** `feat/ws3-per-figure-sources`, from `main` @ `78cf577` (PR #4 merged).

## Objective

Every financial figure ATLAS displays is traceable to its source document and page. From a figure,
a user reaches the document at that page in at most two clicks. Missing provenance is shown
explicitly, never invented.

## Scope and non-goals

- **In scope:**
  - per-figure provenance in the API (`GET /companies/{id}/financial-statements`)
  - per-figure source display (Vietnamese and English)
  - tests and documentation
- **Not in scope:**
  - schema or migration changes
  - real data
  - the metric dictionary (F-1, F-2)
  - verification state changes
  - fetching external URLs
  - G1, Q-3

## Architecture finding (A-02 to A-04)

Data path:
- Database: `financial_metrics.source_page`, `reported_value`, `reported_scale`
- → `financial_statements.source_evidence_id` (a **non-null** foreign key to exactly **one** `evidence` row)
- → `evidence.data_source_id` → `data_sources`
- ORM `FinancialStatement.metrics` / `.source_evidence`
- → `FinancialStatementOut` / `MetricOut`
- → `frontend/src/lib/api-core.ts`
- → `app/[lang]/companies/[id]/page.tsx`

Consequences:
- **A figure's document is its statement's evidence**, which is a one-to-one link. There is no
  multi-evidence case and so no ambiguity to resolve; the schema can't express one.
- **Evidence can't be missing for a stored statement:** `NOT NULL` plus a foreign key, tested at the
  database level.
- **The page can be missing:** fictional sample figures, and rows from before WS1 that have
  `NULL`. It must be shown as unknown, never as 0.
- **The URL can be non-linkable:** the database allows `http(s)`, `file`, or `fixture` URLs.
  Only well-formed http(s) URLs with a host are links.
- **The title can be missing** (`document_title` is nullable).

No schema change is needed.

## Response contract (B-01)

New fields on each metric. All existing fields are kept unchanged, including the statement-level
`source_evidence`:

```jsonc
{
  "metric_code": "net_revenue", "metric_name": "Net revenue", "metric_name_vi": "Doanh thu thuần",
  "value": "1234567890000",            // full units, exact decimal string (unchanged)
  "unit": "VND",
  "reported_value": "1234567.89",      // as printed; null for rows from before WS1
  "reported_scale": 1000000,           // 1 | 1000 | 1000000; null for rows from before WS1
  "source": {
    "evidence_id": "…",                // the statement's evidence row
    "document_title": "…" | null,
    "document_url": "https://…" | null,// only a well-formed http(s) URL with a host
    "link_status": "linkable" | "not_linkable",
    "page": 42 | null,                 // null = unknown, never 0
    "verification_status": "unverified" | "verified" | "disputed" | "rejected" | "superseded" | "sample"
  }
}
```

## Tasks

Statuses and evidence are filled in as work completes (see the final table below).

### Results (2026-11-24)

**Evidence keys used below:**
- **BT:** backend `pytest`, **201 passed**. It adds 31 tests in `backend/tests/test_provenance.py`, and the 170 earlier tests are unchanged. ruff, format and mypy clean; `alembic check` clean; run on a clean copy.
- **FT:** frontend `npm test` **24/24**, including `src/lib/provenance.test.ts`; lint, typecheck and build pass on a clean copy.
- **RC:** `scripts/check-routes.mjs` on the isolated stack: online, offline, and per-figure (`PROVENANCE_COMPANY_ID`) for a fictional linkable company and the sample company, in vi and en.
- **BR:** browser pass on the isolated stack.

#### A. Repository and architecture

| Task | Status | Evidence |
| --- | --- | --- |
| A01 Latest main, WS1/WS2 merged | PASS | `origin/main` = `78cf577` (PR #4 merge); `31b1317163eb` migration present; Backend/Frontend/Docker CI success on `78cf577` |
| A02 Models and relationships | PASS | Architecture finding above (`models.py`: `FinancialStatement.source_evidence_id` NOT NULL FK; `FinancialMetric.source_page/reported_*`) |
| A03 Statement API | PASS | `catalog.py` `list_financial_statements`; `schemas.py` `FinancialStatementOut`/`MetricOut` |
| A04 Evidence and data-source APIs | PASS | `GET /companies/{id}/evidence` (`EvidenceOut` + `DataSourceRef`); statement-level `source_evidence` |
| A05 Frontend statement UI | PASS | `app/[lang]/companies/[id]/page.tsx` (statement header link; figures had no source before WS3) |
| A06 Baseline | PASS | Before changes: `pytest` 170 passed; `npm test` 17/17; eslint 0; ruff/mypy clean; migration head `31b1317163eb`; CI green on `78cf577` |
| A07 Feature branch | PASS | `feat/ws3-per-figure-sources` from `main` @ `78cf577`; tree was clean |

#### B. Backend API and provenance

| Task | Status | Evidence |
| --- | --- | --- |
| B01 Contract | PASS | "Response contract" above; `MetricSourceOut` in `backend/app/api/v1/schemas.py` |
| B02 Page per metric | PASS | `source.page` from `financial_metrics.source_page`; `test_each_figure_carries_its_document_and_page` (pages 7 and 9 on two figures) |
| B03 Document title | PASS | `source.document_title`; same test |
| B04 Document URL | PASS | `source.document_url` (only when linkable); same test, `test_figures_link_to_their_own_statement_document` |
| B05 Evidence id | PASS | `source.evidence_id` equals the statement's `source_evidence.id` (`test_existing_fields_unchanged_…`) |
| B06 Verification status | PASS | `source.verification_status`; `test_figure_status_follows_reviews` (disputed after a review) |
| B07 Exact decimals | PASS | `test_decimals_are_json_strings` (JSON parsed with a float trap), `test_values_round_trip_unchanged` (32-digit value) |
| B08 Reported and normalised | PASS | `reported_value`, `reported_scale`; `test_each_figure_…` (1234567.89 triệu → 1234567890000) |
| B09 Missing page | PASS | `page: null`, never 0; `test_sample_figures_show_unknown_page_and_no_link` |
| B10 Missing evidence | PASS | Impossible by schema; `test_a_statement_cannot_exist_without_evidence` (DB refuses). `source` is therefore always present |
| B11 Missing or invalid URL | PASS | `linkable_url` (urlsplit: http(s), host, no credentials, no whitespace/control chars) → `document_url: null`, `link_status: not_linkable`; `test_unsafe_or_malformed_urls_are_not_links` (16 cases), `test_evidence_cannot_lack_a_url` |
| B12 Backward compatibility | PASS | Only fields added; all 170 earlier tests pass unchanged; `test_existing_fields_unchanged_…` |
| B13 Contract documented | PASS | This file, `docs/ARCHITECTURE.md` API table, README; OpenAPI asserted by `test_openapi_documents_the_contract` |

#### C. Backend testing

| Task | Status | Evidence |
| --- | --- | --- |
| C01 Valid provenance | PASS | `test_each_figure_carries_its_document_and_page` |
| C02 Missing page | PASS | `test_sample_figures_show_unknown_page_and_no_link` |
| C03 Missing evidence | PASS | `test_a_statement_cannot_exist_without_evidence` |
| C04 Missing URL | PASS | `test_evidence_cannot_lack_a_url`; non-linkable fixture URL in the sample test |
| C05 Multiple evidence | PASS | Schema allows one document per statement. `test_figures_link_to_their_own_statement_document` (FY and Q4 docs never mixed); `test_company_evidence_is_never_used_as_a_figure_source` |
| C06 Exact decimals | PASS | `test_decimals_are_json_strings`, `test_values_round_trip_unchanged` |
| C07 Sample provenance | PASS | `test_sample_figures_show_unknown_page_and_no_link` (`sample`, no link, page null) |
| C08 Status preserved | PASS | `test_figure_status_follows_reviews` |
| C09 Invalid URLs | PASS | `test_unsafe_or_malformed_urls_are_not_links`, `test_linkable_urls` |
| C10 Compatibility | PASS | `test_existing_fields_unchanged_…`, `test_openapi_documents_the_contract`, earlier 170 tests |
| C11 Private-field exposure | PASS | `source` has exactly 6 keys (no hash, notes, data-source ids, paths). The API is public and read-only with no auth, so authorization is not applicable |

#### D. Frontend implementation

| Task | Status | Evidence |
| --- | --- | --- |
| D01 Types | PASS | `lib/api-core.ts` (`reported_value`, `reported_scale`, `source: FigureSource`); typecheck clean |
| D02 Per-figure provenance | PASS | `FigureSourceLine` in `companies/[id]/page.tsx`; BR, RC |
| D03 Document title | PASS | Shown per figure; `Tài liệu không có tiêu đề` / `Untitled document` when null (also in the statement header) |
| D04 Source page | PASS | `Trang N` / `Page N`; RC per-figure |
| D05 Direct link | PASS | `<document>#page=N`, one click, new tab; RC per-figure, BR |
| D06 Unavailable state | PASS | `Chưa có số trang nguồn`, `Liên kết nguồn không khả dụng` (and English); BR on the sample company and the credential-URL figure |
| D07 Reported vs normalised | PASS | `Giá trị báo cáo: 12.345,678 triệu đồng` under `12.345.678.000 đồng` when scale > 1; BR |
| D08 Status labels | PASS | Statement header keeps the localized status; per-figure status in the API |
| D09 Vietnamese copy | PASS | `i18n/vi.ts` `company.figure`; FT |
| D10 English copy | PASS | `i18n/en.ts`; key parity test; FT |
| D11 Responsive | PASS | 375×812: `scrollWidth` 375 and 0 overflowing elements on 8 pages incl. both company pages in vi/en; long titles wrap (BR screenshot) |
| D12 Keyboard | PASS | Tab reaches the figure link; 2px brass focus outline; descriptive `aria-label` naming metric, document, page, new tab (BR) |

#### E. Frontend testing

| Task | Status | Evidence |
| --- | --- | --- |
| E01 Link rendering | PASS | `provenance.test.ts` (`#page=42`), RC |
| E02 Page rendering | PASS | FT labels, RC |
| E03 Missing provenance | PASS | FT (null page/URL), RC on the sample company |
| E04 Invalid URL | PASS | FT (9 unsafe URLs refused even if the API said linkable), RC/BR credential-URL figure |
| E05 Vietnamese route | PASS | RC, BR |
| E06 English route | PASS | RC, BR |
| E07 Mobile | PASS | BR 375×812 |
| E08 Keyboard | PASS | BR |
| E09 Loading, empty, error | IN PROGRESS | Error verified: RC offline and the company page with the backend stopped ("Không tải được thông tin doanh nghiệp"). **Not re-observed in this pass:** the loading state (`companies/[id]/loading.tsx`) and the "no statements" empty text. Both are unchanged code paths |
| E10 Console | PASS | Fresh tab across vi/en company pages and the list: "No console logs"; all requests 200 |

#### F. Integration and security

| Task | Status | Evidence |
| --- | --- | --- |
| F01 API-to-UI mapping | PASS | RC per-figure (every metric of both companies, vi and en) |
| F02 Correct document | PASS | RC; FY and Q4 docs never mixed (backend test) |
| F03 Page belongs to figure | PASS | RC checks `#page=N` per metric (pages 9, 12, 13, 14) |
| F04 No fabricated provenance | PASS | Null page → "not recorded" text, no `#page`; non-linkable → no anchor (RC asserts zero links) |
| F05 Only http(s) clickable | PASS | Backend `linkable_url` + UI `safeHref`; RC asserts every `target=_blank` href is http(s) |
| F06 Link safety | PASS | `rel="noopener noreferrer"` on every new-tab link (RC + source grep) |
| F07 Sample vs real | PASS | Sample figures: `Dữ liệu mẫu` status, no link, no page; badge and banner unchanged |
| F08 Security checks | PASS | `pip-audit --strict`: no known vulnerabilities; `npm audit`: 0; no `dangerouslySetInnerHTML`; React escapes titles; no server-side URL fetching |
| F09 Isolated Docker | PASS | Project `atlasws3`, new volume, ports 5463/8063/3063; 3 migrations applied; health 200; removed afterwards |
| F10 User data untouched | PASS | `atlas` containers kept running; `atlas_pgdata` still present; no `.env` change |

#### G. Documentation and acceptance

| Task | Status | Evidence |
| --- | --- | --- |
| G01 This checklist | PASS | This file |
| G02 API docs | PASS | `docs/ARCHITECTURE.md` API table, README, OpenAPI |
| G03 Development docs | PASS | `docs/DEVELOPMENT.md` (route check modes) |
| G04 Phase 2 checklist | PASS | P2-4.13 → PASS with E-WS3 evidence |
| G05 Recount | PASS | From item lines: 28 PASS, 25 IN PROGRESS, 20 NOT STARTED, 10 BLOCKED, 0 FAIL (33.7%) |
| G06 Test evidence | PASS | BT, FT, RC, BR above |
| G07 Limits and blockers | PASS | Below |
| G08 Self-review | PASS | Below |
| G09 Acceptance report | PASS | Final decision below; reported to the owner |

### Security review

| Severity | Finding | Status |
| --- | --- | --- |
| — | No critical, high or medium findings in WS3 code | — |
| LOW (pre-existing, Phase 1) | The existing statement-level `source_evidence.source_url` field returns the stored URL verbatim. If a curator stored credentials in a URL, the API would expose them. WS3's new `document_url` excludes such URLs, and the UI never links or prints them | Open: recommend the importer rejecting URLs with credentials (validation change, outside WS3) |
| LOW | `#page=N` opens the right page in browser PDF viewers; other document types ignore it and open at the start | Documented |

### Limits and blockers

- **E09:** the loading state and the "no statements" empty text were not re-observed. Both are unchanged code.
- **Balance-sheet period:** shown as "31/12/2025 to 31/12/2025" (Phase 1 presentation, not WS3). It would read better as "at 31/12/2025".
- **No real data:** every figure is still unverified or sample. **Q-3** (independent reviewer) and **G1** (legal opinion) stay open, and WS3 does not change them.
- GitHub Actions has not run on this branch (nothing pushed).

### Final decision

**READY WITH DOCUMENTED LIMITATIONS.** Every acceptance criterion for P2-4.13 is met and evidenced; the open items are E09 (re-observe one unchanged loading state), one pre-existing low-severity API exposure, and the non-engineering gates Q-3 and G1.
