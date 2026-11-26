# WS4-3 checklist: financial period comparison

Acceptance checklist for [WS4_3_IMPLEMENTATION_PLAN.md](WS4_3_IMPLEMENTATION_PLAN.md). **Design approved,
implementation not started:** decisions W3-D1 to W3-D10 were approved on 2026-11-25; no WS4-3 code
exists, and implementation (W3-B3) is not authorised yet.

**Status update (2026-11-26):** audited against `main` @ `407ed63`
([WS4_3_AUDIT.md](WS4_3_AUDIT.md)); the plan gained §12 (implementation specification). New rows:
W3-A9, W3-A10, W3-B4, W3-D-8, W3-F8, W3-F9, W3-G7. Still no WS4-3 code; W3-B3 not given.
Later the same day W3-B4 passed (owner approval of plan §12.15).

**Status update (2026-11-26, implementation):** the owner authorised implementation (W3-B3).
WS4-3 is implemented on branch `feat/ws4-3-period-comparison` (not committed). Each PASS below
cites the test or check that ran; PR, CI, recorded review and merge (W3-H2 to W3-H4) are not done.

**Status update (2026-11-26, after merge):** committed as `42f2f8a` and merged as PR #10
(`609864c`) with CI green on head and merge; W3-H3 and W3-H4 PASS on that evidence. **W3-H2 (recorded
owner review) stays NOT STARTED**: PR #10 has no review submissions or comments, and CI is not a
review. Post-merge audit: [WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md).

| | |
| --- | --- |
| Last verified | 2026-11-26, `main` @ `609864c` (PR #10 merge; earlier the same day on branch `feat/ws4-3-period-comparison`; 2026-11-25, `main` @ `8007fe2`) |
| Statuses | `NOT STARTED`, `IN PROGRESS`, `PASS`, `BLOCKED`, `FAIL` only |
| Parent items | WS4_CHECKLIST group G (WS4-G9 implemented and tested); PHASE_2_CHECKLIST P2-5.13 |

PASS in group A means the design is written in the plan. It does not mean the design is approved or
built.

## Summary (recounted from the item rows below)

| Group | Items | PASS | IN PROGRESS | NOT STARTED | BLOCKED | FAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A. Design | 10 | 10 | 0 | 0 | 0 | 0 |
| B. Owner decisions | 4 | 4 | 0 | 0 | 0 | 0 |
| C. Period matching | 8 | 8 | 0 | 0 | 0 | 0 |
| D. Growth computation | 8 | 8 | 0 | 0 | 0 | 0 |
| E. API | 6 | 6 | 0 | 0 | 0 | 0 |
| F. Frontend | 9 | 9 | 0 | 0 | 0 | 0 |
| G. Integrity and regression | 7 | 7 | 0 | 0 | 0 | 0 |
| H. Release | 4 | 3 | 0 | 1 | 0 | 0 |
| **Total** | **56** | **55** | **0** | **1** | **0** | **0** |

(Before the 2026-11-26 updates: 49 items, 10 PASS, 39 NOT STARTED; after the audit: 56 items, 13 PASS, 43 NOT STARTED; after implementation: 53 PASS, 3 NOT STARTED.)

## A. Design

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-A1 | Current implementation inspected | PASS | Periods, quarters, revisions, units, arithmetic, API and UI patterns recorded | Plan §1 | None | No |
| W3-A2 | Comparison types and matching | PASS | Annual YoY, QoQ, quarterly YoY with date rules, label checks, ambiguity, calendar and non-calendar years | Plan §2 | None | No |
| W3-A3 | Stand-alone vs YTD | PASS | Stand-alone only; no derivation; YTD-only cases stated | Plan §2.1 | None | No |
| W3-A4 | Growth and edge cases | PASS | WS4-D9 kept; every edge case listed; gaps routed to decisions | Plan §3 | None | No |
| W3-A5 | Architecture | PASS | Pure module and read-only service; no schema change; nothing stored | Plan §4 | None | No |
| W3-A6 | API contract and reasons | PASS | Shape, statuses, ranked reason codes with vi and en texts | Plan §5, §5.1 | None | No |
| W3-A7 | Frontend and tests | PASS | Selector, neutral indicators, states, disclosure, paging, mobile; test matrix | Plan §6, §8 | None | No |
| W3-A8 | Decision register | PASS | Ten decisions, each with context, options, recommendation, trade-offs, risk | Plan §10 | None | No |
| W3-A9 | Audit against `main` | PASS | Baseline, existing behaviour, findings with cases, decision-to-test map, recommendation | WS4_3_AUDIT.md (2026-11-26) | None | No |
| W3-A10 | Implementation specification | PASS | API contract, engine, matching algorithm, precedence, texts, UI, arithmetic, migration impact, fixtures with expected values, performance, compatibility, governance, acceptance criteria | Plan §12 (2026-11-26); fixture values checked against a `Fraction` oracle | W3-A9 | No |

## B. Owner decisions

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-B1 | Decisions W3-D1 to W3-D10 recorded | PASS | Each approved, changed or deferred in PRODUCT_DECISIONS | All ten approved by the owner on 2026-11-25 as proposed; recorded in PRODUCT_DECISIONS §2e | None | Yes |
| W3-B2 | Prerequisites decided | PASS | Owner decides whether AU-3 and AU-5 are fixed before or with WS4-3 | Owner authorised fixing AU-3, AU-4 and AU-5 before WS4-3 (2026-11-25). The fixes are on branch `fix/ws4-2-audit-au3-au4-au5` (not merged yet; see WS4_2_AUDIT.md). Update 2026-11-26: merged in PR #9 (`407ed63`) | None | Yes |
| W3-B3 | Go-ahead to implement | PASS | Owner authorises WS4-3 implementation | Owner message "Bắt đầu WS4-3" (2026-11-26); recorded in PRODUCT_DECISIONS §2e | W3-B1 | Yes |
| W3-B4 | Audit decisions | PASS | Owner decides proposed W3-D11 (mixed sample/real code) and the W3-D7 display threshold (plan §12.15) | Owner approved all §12.15 items as proposed on 2026-11-26 ("Duyệt như đề xuất"); recorded in PRODUCT_DECISIONS §2e | W3-A9 | Yes |

## C. Period matching

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-C1 | Annual YoY | PASS | Previous end within ±7 days of the current end − 1 year; flows also align on start − 1 day | backend `tests/test_comparison_api.py` (calendar FY, `test_annual_comparison_with_provenance`); backend `tests/test_comparisons.py` `test_annual_yoy`, `test_seven_day_window`, `test_flows_must_also_be_contiguous` (2026-11-26) | W3-B3 | No |
| W3-C2 | Quarterly QoQ | PASS | Q*n*−1 or prior Q4; flows on start − 1 day ±7; balance sheets 80–100 days earlier | backend `tests/test_comparison_api.py` `test_quarter_on_quarter_and_prior_q4` (flows and balance sheets); backend `tests/test_comparisons.py` 80/100/79/101-day boundaries (2026-11-26) | W3-B3 | No |
| W3-C3 | Quarterly YoY | PASS | Same quarter number, FY *t*−1, end − 1 year ±7 days | backend `tests/test_comparison_api.py` `test_quarter_year_on_year`; backend `tests/test_comparisons.py` `test_quarter_year_on_year` (2026-11-26) | W3-B3 | No |
| W3-C4 | Non-calendar years and leap days | PASS | FY ending 31 March; 29 Feb moved back to 28 Feb | backend `tests/test_comparison_api.py` `test_non_calendar_and_leap_day_years`; backend `tests/test_comparisons.py` `test_previous_year_moves_leap_day` (2026-11-26) | W3-C1 | No |
| W3-C5 | Ambiguity and missing periods | PASS | Two candidates → `ambiguous_previous_period`; none → `missing_previous_period`; never pick one | backend `tests/test_comparison_api.py` `test_ambiguous_previous_balance_sheet`, missing period in `test_annual_comparison_with_provenance`; backend `tests/test_comparisons.py` `test_two_candidates_are_ambiguous`, `test_fiscal_year_end_moved` (2026-11-26) | W3-C1 | No |
| W3-C6 | Label and date agreement | PASS | Disagreement → `period_mismatch` | backend `tests/test_comparison_api.py` `test_label_that_contradicts_dates`; backend `tests/test_comparisons.py` `test_label_and_dates_disagree`, `test_annual_label_must_be_previous_fiscal_year` (2026-11-26) | W3-C2 | No |
| W3-C7 | Granularity and scope isolation | PASS | Annual never vs quarter (incl. Q4 vs annual on the same date); scopes never mixed | backend `tests/test_comparison_api.py` `test_annual_and_q4_on_the_same_dates_never_pair`, `test_scopes_are_never_mixed` (2026-11-26) | W3-C1 | No |
| W3-C8 | Latest revision, no fallback | PASS | Latest revision of each side used and disclosed; a disputed, rejected or superseded latest revision is refused | backend `tests/test_comparison_api.py` `test_restated_previous_year_is_used_and_disclosed`, `test_bad_latest_revision_never_falls_back` (3 cases) (2026-11-26) | W3-C1 | No |

## D. Growth computation

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-D-1 | Formula `growth_abs_prior` v1 | PASS | (current − prior) ÷ \|prior\| exactly as WS4-D9 | backend `tests/test_comparisons.py` fixtures F1–F16 and 600 random pairs against a `Fraction` oracle (2026-11-26) | W3-B3 | No |
| W3-D-2 | Rounding | PASS | As decided in W3-D4; one rounding per output from the exact quotient | backend `tests/test_comparisons.py` F12a–F12d (ties half-up and half-even), oracle test (2026-11-26) | W3-B1 | No |
| W3-D-3 | Prior zero and sign change | PASS | `change_only` with exact absolute change | backend `tests/test_comparisons.py` F5, F8, F9, F10 (2026-11-26) | W3-D-1 | No |
| W3-D-4 | Current zero and negative bases | PASS | As decided in W3-D2 and W3-D3 | backend `tests/test_comparisons.py` F6, F7 (W3-D2), F3, F4 (negative bases) (2026-11-26) | W3-B1 | No |
| W3-D-5 | Fixed-point output | PASS | No exponent, no negative zero | backend `tests/test_comparisons.py` `test_no_negative_zero_and_no_exponent`; backend `tests/test_comparison_api.py` float trap and "E" check on every response (2026-11-26) | W3-D-1 | No |
| W3-D-6 | Reason precedence | PASS | Plan §5.1 order; all issues listed | backend `tests/test_comparisons.py` `test_precedence_lists_every_issue`, `test_rank_9_runs_only_when_nothing_else_applies`, isolation tests (W3-D11) (2026-11-26) | W3-D-1 | No |
| W3-D-7 | No float | PASS | Guard test; `mypy` clean | `tests/test_ratios.py::test_calculation_modules_never_use_float` covers the new modules; `mypy` strict clean (2026-11-26) | W3-D-1 | No |
| W3-D-8 | Exact 38-digit subtraction | PASS | Fixture F16 exact; no default-context arithmetic (audit A3-10) | backend `tests/test_comparisons.py` F16 (38 digits) and the random-pair test (2026-11-26) | W3-D-1 | No |

(Group D item ids carry a hyphen, `W3-D-n`, so they can't be confused with decisions `W3-Dn`.)

## E. API

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-E1 | Endpoint | PASS | `GET /companies/{id}/comparisons` with `type`, `metric`, `scope`, `fiscal_year`, paging | backend `tests/test_comparison_api.py` `test_filters_paging_and_errors` (2026-11-26) | W3-C1 | No |
| W3-E2 | Response model | PASS | Matches plan §5; decimals as strings or null | backend `tests/test_comparison_api.py` every test parses JSON with a float trap; `test_openapi_documents_comparisons` (2026-11-26) | W3-E1 | No |
| W3-E3 | Provenance | PASS | Both sides carry WS3 `source`, revision and period | backend `tests/test_comparison_api.py` `test_annual_comparison_with_provenance` (source page, link, revision, period on both sides) (2026-11-26) | W3-E1 | No |
| W3-E4 | No verification status | PASS | No `verification_status` on a comparison | backend `tests/test_comparison_api.py` `test_annual_comparison_with_provenance`, `test_openapi_documents_comparisons` (2026-11-26) | W3-E1 | No |
| W3-E5 | Validation and errors | PASS | 404 unknown company; 422 bad `type`, `metric`, `scope`, `limit` | backend `tests/test_comparison_api.py` `test_filters_paging_and_errors` (404; 422 for 8 bad parameter sets) (2026-11-26) | W3-E1 | No |
| W3-E6 | Docs and OpenAPI | PASS | ARCHITECTURE and README API tables; OpenAPI schema | ARCHITECTURE and README API tables updated; OpenAPI test (2026-11-26) | W3-E1 | No |

## F. Frontend

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-F1 | Section and selector | PASS | Three comparison types and scope, kept in the URL across reloads and the language switch | Route check (all three types, vi and en, `aria-current`); control links keep the other lists' pages (route check) (2026-11-26) | W3-E1 | No |
| W3-F2 | Neutral direction indicators | PASS | Arrow plus text; no colour-only or good/bad meaning (W3-D5) | Browser pass: arrows `aria-hidden`, no colour classes; route check checks the direction words (2026-11-26) | W3-B1 | No |
| W3-F3 | States | PASS | `change_only` and `not_comparable` show reasons; never 0 or a bare dash | Route check: every row on page 1 of each type shows its percentage or reason text, in vi and en (2026-11-26) | W3-E2 | No |
| W3-F4 | Disclosure and sources | PASS | Formula, both periods, revisions, links to exact pages | Browser pass: disclosure shows formula, full value, both periods, revisions and source pages; API test of sources (2026-11-26) | W3-E3 | No |
| W3-F5 | Paging | PASS | "Showing X of Y" with next/previous whenever `total` is larger | Route check: "Đang hiển thị 1–20 / 44" / "Showing 1–20 of 44" for the fictional company; existing `Pagination` (2026-11-26) | W3-E1 | No |
| W3-F6 | Language, accessibility, mobile | PASS | vi and en key parity; keyboard; 375 px with no sideways scroll | `i18n.test.ts` key parity; browser pass: keyboard through controls and disclosure, 375 px with `scrollWidth` 375 (2026-11-26) | W3-F1 | No |
| W3-F7 | Glossary | PASS | New terms added for the native-speaker review | GLOSSARY.md "Period comparison (WS4-3)" section; the native-speaker review itself stays open (2026-11-26) | W3-F3 | Yes (review) |
| W3-F8 | Seasonality and restated notes | PASS | QoQ seasonality note; restated note on the restated side (WS4-D9 §8.2; tests U6) | Route check (seasonality note only for quarter on quarter); browser pass (restated note on 5 rows of page 1) (2026-11-26) | W3-F1 | No |
| W3-F9 | Display limit | PASS | Threshold as decided in W3-B4; full value in the disclosure (test U7) | `api-core.test.ts` `percentBeyondLimit`, `percentText`; route check found "> 999,99%" for a fictional 89 900 % row (2026-11-26) | W3-B4 | No |

## G. Integrity and regression

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-G1 | No schema change | PASS | No migration; `alembic check` clean | `alembic check`: "No new upgrade operations detected" (isolated stack); no migration file added (2026-11-26) | W3-E1 | No |
| W3-G2 | Read-only and bounded | PASS | No writes; fixed query count | backend `tests/test_comparison_api.py` `test_read_only_and_bounded_queries` (no row count change; same query count for more years) (2026-11-26) | W3-E1 | No |
| W3-G3 | Fictional data only | PASS | Tests and Docker checks use fictional data; nothing under `data/` | Diff review: fixtures use example.test and TST tickers; nothing under `data/` changed (2026-11-26) | None | No |
| W3-G4 | Backend regression | PASS | All earlier tests green | Clean copy: ruff, `mypy` strict, `pytest` 379 passed; working tree 380 passed after one more test (2026-11-26) | W3-E1 | No |
| W3-G5 | Frontend regression | PASS | Lint, typecheck, tests, build green | Clean copy: lint, typecheck, `npm test` 35/35, production build, `npm audit` 0 (2026-11-26) | W3-F1 | No |
| W3-G6 | Isolated Docker and API ↔ UI | PASS | Route check online, offline and per comparison in vi and en | Isolated stack `atlasws43` (fresh volumes, ports 5463/8063/3063): route check online and offline passed (2026-11-26) | W3-F4 | No |
| W3-G7 | Stand-alone rule documented | PASS | VERIFICATION_WORKFLOW says quarterly figures must be printed stand-alone, never derived from YTD (audit A3-15) | VERIFICATION_WORKFLOW §7 rule added (2026-11-26) | None | No |

## H. Release

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-H1 | Checklists updated | PASS | This file, WS4_CHECKLIST (group G) and PHASE_2_CHECKLIST (P2-5.13) recounted | This file, WS4_CHECKLIST (WS4-G9) and PHASE_2_CHECKLIST (P2-5.13) recounted 2026-11-26 (2026-11-26) | G group | No |
| W3-H2 | Recorded owner review | NOT STARTED | The owner's review recorded on the PR before merge (AU-6) | PR record | W3-H1 | Yes |
| W3-H3 | PR and CI | PASS | Backend, Frontend, Docker green on head and merge | PR #10 opened at the owner's request; CI green on head `42f2f8a` (Backend, Frontend, Docker) and on merge `609864c` (Backend 380 passed, Frontend 35/35, Docker success) — [WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md) §3. Its dependency W3-H2 was **not** met: no recorded review before merge (2026-11-26) | W3-H2 | Yes (commit, PR) |
| W3-H4 | Merge | PASS | Merged by the owner | Merged 2026-11-26 04:47 UTC by the owner's account as `609864c`, identical to `42f2f8a`. Merged without a recorded review (W3-H2 NOT STARTED) (2026-11-26) | W3-H3 | Yes |
