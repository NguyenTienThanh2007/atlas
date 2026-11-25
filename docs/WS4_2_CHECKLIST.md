# WS4-2 checklist: ROE and ROA

Acceptance checklist for [WS4_2_IMPLEMENTATION_PLAN.md](WS4_2_IMPLEMENTATION_PLAN.md). Formulas are
approved (WS4-D1 to D3, D7, D8, D11, D12), the design is approved and implementation was authorised
(2026-11-25). Merged as PR #7 (`2079101`); display fixes AU-1 and AU-2 merged as PR #8 (`8007fe2`).

| | |
| --- | --- |
| Last verified | 2026-11-25, `main` @ `8007fe2` |
| Statuses | `NOT STARTED`, `IN PROGRESS`, `PASS`, `BLOCKED`, `FAIL` only |
| Parent items | WS4_CHECKLIST WS4-C7 (ROE implemented), WS4-D-7 (ROA implemented), WS4-H9 (calculated values in API and UI), WS4-I2 to I10 (tests) |

PASS in group A means the design is written in the plan. Other PASS items rest on this evidence
(2026-11-25, gathered on branch `feat/ws4-2-roe-roa` from `main` @ `105869f` before merge; CI
re-ran them on the PR head and the merge commit, see **CI** below):

- **BT:** fresh PostgreSQL 17: `ruff check`, `ruff format --check`, `mypy` clean; `pytest` **288
  passed** (+37 in `tests/test_ratios.py`, +27 in `tests/test_calculated_metrics.py`);
  `alembic upgrade head` + `alembic check` clean.
- **FT:** clean copy of `frontend/`: lint, typecheck, `npm test` 27/27, build, `npm audit` 0.
- **DK:** isolated Docker stack `atlasws42` with a fictional bundle (TST1, `example.test`): FY2025
  ROE `15.00`, ROA `4.21`; FY2024 `missing_opening_balance`; route check online, offline and per
  calculated value in vi and en passed.
- **BR:** browser, desktop and 375×812, vi and en.
- **CI:** PR #7 head `037a820`: [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45537877885), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45537877803), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45537877765) success. Merge `2079101`: [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617789) (`288 passed`, `alembic check` clean), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617702) (27/27), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617848) success.
- **Post-merge (2026-11-25):** the independent review [WS4_2_AUDIT.md](WS4_2_AUDIT.md) found no CRITICAL or HIGH issue; AU-1 and AU-2 (display) were fixed in PR #8 (`8007fe2`). AU-3 (sample/real isolation, database triggers plus an engine check), AU-4 (unit from inputs) and AU-5 (pagination) are fixed on branch `fix/ws4-2-audit-au3-au4-au5`, not yet committed. AU-6 is open.

## Summary (recounted from the item rows below)

| Group | Items | PASS | IN PROGRESS | NOT STARTED | BLOCKED | FAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A. Design | 10 | 10 | 0 | 0 | 0 | 0 |
| B. Owner review | 2 | 2 | 0 | 0 | 0 | 0 |
| C. Formula registry and exact computation | 8 | 8 | 0 | 0 | 0 | 0 |
| D. Input selection | 11 | 11 | 0 | 0 | 0 | 0 |
| E. API | 6 | 6 | 0 | 0 | 0 | 0 |
| F. Frontend | 6 | 6 | 0 | 0 | 0 | 0 |
| G. Integrity and regression | 6 | 6 | 0 | 0 | 0 | 0 |
| H. Release | 4 | 3 | 0 | 1 | 0 | 0 |
| **Total** | **53** | **52** | **0** | **1** | **0** | **0** |

## A. Design

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-A1 | Service architecture | PASS | Pure computation separated from read-only input loading; nothing stored | Plan §2 | None | No |
| W2-A2 | Formula registry | PASS | Three versioned entries matching D1, D2; no fallback denominator | Plan §3 | None | No |
| W2-A3 | Input selection rules | PASS | Same company, scope, annual, latest revision; closing matched by exact date; opening = FY t−1 within ±7 days, exactly one candidate | Plan §4.1 | None | No |
| W2-A4 | API schema | PASS | Decimal strings or null; status, reason, inputs, missing inputs, input verification; no verification status | Plan §6 | None | No |
| W2-A5 | Provenance chain | PASS | Each input carries statement, revision, exact and as-reported values, WS3 source | Plan §7 | None | No |
| W2-A6 | Reason mapping | PASS | Eight codes with rank, triggering role, refusal, vi and en text; all issues listed; no zero or substitution | Plan §8 | None | No |
| W2-A7 | Test matrix | PASS | Cases for arithmetic, signs, missing data, periods, scope, revisions, verification, API, UI, regression | Plan §9 | None | No |
| W2-A8 | Security and integrity | PASS | Read-only, validated, bounded queries, exact Decimal, no new URL handling | Plan §11 | None | No |
| W2-A9 | Evidence and revision semantics | PASS | Behaviour for verified, unverified, sample, disputed, rejected, superseded; no fallback to older revisions; sample isolation | Plan §4.2 | None | No |
| W2-A10 | Decimal and rounding audit | PASS | Exact average; one rounding per output from the exact quotient; fixed-point JSON; no browser arithmetic; findings recorded | Plan §5 (two issues found: exponent notation in JSON, trailing-zero loss in `formatDecimal`) | None | No |

## B. Owner review

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-B1 | Plan design choices confirmed | PASS | Owner confirms or changes the six points in plan §12 | Owner approved all six points on 2026-11-25; recorded in PRODUCT_DECISIONS §2d ("WS4-2 design approval") | None | Yes |
| W2-B2 | Go-ahead to implement | PASS | Owner authorises WS4-2 implementation | Owner message "Start WS4-2" (2026-11-25); recorded in PRODUCT_DECISIONS §2d | W2-B1 | Yes |

## C. Formula registry and exact computation

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-C1 | Registry implemented | PASS | Exactly the three entries of plan §3; frozen; pinned by a test | `backend/tests/test_ratios.py` `test_registry_is_exactly_the_approved_formulas`; backend `pytest` 288 passed (BT) | W2-B2 | No |
| W2-C2 | Exact average | PASS | `(opening + closing) / 2` in a 60-digit context that traps inexact results | `backend/tests/test_ratios.py` `test_average_is_exact_never_rounded` (values near 10^32, half-unit average `0.0000015`) | W2-C1 | No |
| W2-C3 | Single-rounding ratio | PASS | 10 decimals half-even from an exact integer-valued quotient (`divmod`); a case where double rounding would differ is tested | `backend/tests/test_ratios.py` `test_one_rounding_from_the_exact_quotient[*]` (15 cases against an exact `Fraction` oracle), `test_percent_is_not_derived_from_the_rounded_value` | W2-C1 | No |
| W2-C4 | Display percent | PASS | 2 decimals half-up (ties away from zero, also for negatives) from the exact quotient, never from `value` (D8) | `backend/tests/test_ratios.py` `test_ties_follow_their_rounding_rule` (`3.13`, `-3.13`), oracle cases | W2-C1 | No |
| W2-C5 | Non-positive denominator | PASS | Opening, closing or average ≤ 0 → `equity_not_positive` / `assets_not_positive`; loss gives a negative ratio | `backend/tests/test_ratios.py` `test_non_positive_equity_is_not_meaningful[*]`, `test_non_positive_assets_use_their_own_reason`, `test_loss_gives_a_negative_ratio`; `backend/tests/test_calculated_metrics.py` `test_negative_equity_is_not_meaningful` | W2-C1 | No |
| W2-C6 | No float | PASS | No `float` in calculation modules; guard test | `backend/tests/test_ratios.py` `test_calculation_modules_never_use_float`; `mypy` strict clean | W2-C1 | No |
| W2-C7 | Reason precedence | PASS | All issues collected and ordered by plan §8 rank and role; `reason` = first issue; value checks only when ranks 1–6 are clear | `backend/tests/test_ratios.py` `test_simultaneous_issues_are_all_listed_in_precedence_order`, `test_issue_ties_are_ordered_by_role`; `backend/tests/test_calculated_metrics.py` `test_missing_numerator_and_opening_are_both_listed` | W2-C1 | No |
| W2-C8 | Fixed-point serialisation | PASS | `value` 10, `percent` 2, `denominator_average` 7 decimals via `format(d, "f")`; no exponent; no negative zero | `backend/tests/test_calculated_metrics.py` `test_zero_profit_is_a_fixed_point_zero`; every API test asserts no `E-`/`E+` and parses JSON with a float trap; oracle checks no `-0` | W2-C1 | No |

## D. Input selection

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-D1 | Latest annual revisions only | PASS | Superseded revisions and quarterly statements never used | `backend/tests/test_calculated_metrics.py` `test_latest_revision_is_used_and_disclosed`, `test_quarterly_and_closing_balance_sheets_are_never_the_opening` | W2-C1 | No |
| W2-D2 | Opening and closing matching | PASS | Closing = income statement end date exactly; opening = FY t−1 annual balance sheet within ±7 days of start − 1 day; non-calendar FY works; 8-day shift → `missing_opening_balance` | `backend/tests/test_calculated_metrics.py` `test_seven_day_window[*]` (0 and 7 days used, 8 days refused), `test_non_calendar_fiscal_year`, `test_closing_must_match_the_income_statement_end` | W2-D1 | No |
| W2-D3 | Scope isolation | PASS | Consolidated and separate computed independently | `backend/tests/test_calculated_metrics.py` `test_scopes_are_never_mixed`, `test_separate_roe_uses_total_equity` | W2-D1 | No |
| W2-D4 | No substitution | PASS | `equity_parent` missing with `total_equity` present → consolidated ROE `missing_input` | `backend/tests/test_calculated_metrics.py` `test_equity_parent_is_never_replaced_by_total_equity` | W2-D1 | No |
| W2-D5 | Missing opening balance | PASS | No result is computed without it | `backend/tests/test_calculated_metrics.py` `test_missing_opening_balance_prevents_calculation`, `test_opening_without_the_figure` | W2-D2 | No |
| W2-D6 | Evidence status | PASS | Disputed or rejected → not computed; superseded → `input_superseded`; labels `all_verified` / `some_unverified` / `sample` | `backend/tests/test_calculated_metrics.py` `test_bad_latest_revision_never_falls_back[*]`, `test_all_verified_inputs`, `test_sample_company_results_are_labelled_sample` (reviews through the WS1 `record_review` path); `backend/tests/test_ratios.py` `test_refused_evidence_states[*]` | W2-D1 | No |
| W2-D7 | Bounded queries | PASS | Fixed number of queries per request | `backend/tests/test_calculated_metrics.py` `test_read_only_and_bounded_queries` (same query count with more years) | W2-D1 | No |
| W2-D8 | Read-only | PASS | No rows written by the service or endpoint | `backend/tests/test_calculated_metrics.py` `test_read_only_and_bounded_queries` (row counts unchanged; no INSERT, UPDATE or DELETE during the request) | W2-D1 | No |
| W2-D9 | Ambiguous opening balance | PASS | Two candidates in the window → `ambiguous_opening_balance`; ATLAS never picks one | `backend/tests/test_calculated_metrics.py` `test_two_candidates_are_ambiguous` | W2-D2 | No |
| W2-D10 | No fallback to older revisions | PASS | Latest revision disputed, rejected or superseded → refused even when an older revision has good evidence | `backend/tests/test_calculated_metrics.py` `test_bad_latest_revision_never_falls_back[*]` (verified revision 1 not used when revision 2 is rejected, disputed or superseded) | W2-D1 | No |
| W2-D11 | Never another year or scope | PASS | FY t−2 or FY t balance sheets near the date and other-scope balance sheets are never candidates | `backend/tests/test_calculated_metrics.py` `test_quarterly_and_closing_balance_sheets_are_never_the_opening`, `test_scopes_are_never_mixed`. A wrongly labelled annual balance sheet can't be imported at those dates (annual period rule), so the FY *t*−1 label check is defence in depth | W2-D2 | No |

## E. API

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-E1 | Endpoint | PASS | `GET /companies/{id}/calculated-metrics`, filters, pagination, 404 | `backend/tests/test_calculated_metrics.py` `test_filters_pagination_and_404` | W2-D1 | No |
| W2-E2 | Response model | PASS | Matches plan §5; values are strings or null | `backend/tests/test_calculated_metrics.py` `test_consolidated_roe_and_roa` and all API tests (float trap) | W2-E1 | No |
| W2-E3 | Provenance in response | PASS | Every input has WS3 `source`; no private fields | `backend/tests/test_calculated_metrics.py` `test_every_input_carries_its_provenance` | W2-E1 | No |
| W2-E4 | No verification status | PASS | No result carries `verification_status` or "verified" | `backend/tests/test_calculated_metrics.py` `test_consolidated_roe_and_roa`, `test_all_verified_inputs`, `test_openapi_documents_calculated_metrics` | W2-E1 | No |
| W2-E5 | OpenAPI | PASS | Schema documented | `backend/tests/test_calculated_metrics.py` `test_openapi_documents_calculated_metrics` (value typed as string) | W2-E1 | No |
| W2-E6 | Docs | PASS | ARCHITECTURE.md API table, README | `docs/ARCHITECTURE.md` (module table, API table), `README.md` API table | W2-E1 | No |

## F. Frontend

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-F1 | Calculated section | PASS | Separate from reported figures, in vi and en | Browser pass (BR): section "Chỉ số tính toán (do ATLAS tính)" / "Calculated ratios (computed by ATLAS)" below the statements | W2-E1 | No |
| W2-F2 | Percent formatting | PASS | `formatFixed` keeps the API's decimals (vi `18,30%`, en `18.30%`, `-5,00%`); no `Number()`, `parseFloat` or rounding in the browser | `frontend/src/lib/api-core.test.ts` "fixed-point values keep their decimals"; browser shows `15,00%` / `15.00%` | W2-E2 | No |
| W2-F3 | Labels | PASS | Input-verification labels and every reason text in both languages; key parity | `frontend/src/i18n/i18n.test.ts` "every calculation reason and input label has text in both languages"; key parity test | W2-E2 | No |
| W2-F4 | Formula disclosure | PASS | Formula text and input links to the source pages | Browser (BR): formula text, average and three inputs with source links to page 7; route check (DK) compares every percentage and reason with the API in vi and en | W2-F1 | No |
| W2-F5 | Accessibility and mobile | PASS | Keyboard, labelled controls, no horizontal scroll at 375 px | Browser (BR): 375×812 `scrollWidth` 375 in vi and en with all disclosures open; Tab reaches "Cách tính" with a 2 px focus outline; no unnamed links; no console errors | W2-F1 | No |
| W2-F6 | Glossary | PASS | New terms added to GLOSSARY.md for the native-speaker review | `docs/GLOSSARY.md` "Calculated ratios (WS4-2)"; notes the "kiểm chứng" / "xác minh" choice for the review | W2-F3 | Yes (review) |

## G. Integrity and regression

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-G1 | No schema change | PASS | No migration; `alembic check` clean | No file under `backend/migrations`, no `models.py` change; `alembic upgrade head` + `alembic check`: "No new upgrade operations detected" | W2-E1 | No |
| W2-G2 | No stored calculations | PASS | `financial_metrics` unchanged by requests | `backend/tests/test_calculated_metrics.py` `test_read_only_and_bounded_queries` | W2-D8 | No |
| W2-G3 | Fictional data only | PASS | Test data only `example.test` / `TST`; nothing under `data/` added | Test data only inside tests (`example.test`, `TST`); the Docker check used a fictional bundle in the scratchpad, not the repo; no change under `data/` | None | No |
| W2-G4 | Backend regression | PASS | All existing backend tests green | backend `pytest` 288 passed (BT); ruff and mypy clean | W2-E1 | No |
| W2-G5 | Frontend regression | PASS | All existing frontend tests, lint, typecheck, build green | Clean copy (FT): `npm ci`, lint exit 0, typecheck exit 0, `npm test` 27/27, build exit 0, `npm audit` 0 | W2-F1 | No |
| W2-G6 | Isolated Docker check | PASS | Fresh stack; route check online and offline; calculated values match the API in vi and en | Isolated stack `atlasws42` (new volume, ports 5463/8063/3063) (DK): route check online, offline, and with `PROVENANCE_COMPANY_ID` (figures and calculated values) passed | W2-F4 | No |

## H. Release

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W2-H1 | Checklists updated | PASS | This file, WS4_CHECKLIST (C7, D-7, H9, I2–I10) and PHASE_2_CHECKLIST (P2-5.11, 5.12, 5.17) recounted | This file, WS4_CHECKLIST and PHASE_2_CHECKLIST updated and recounted (2026-11-25) | G group | No |
| W2-H2 | Owner review of the change | NOT STARTED | Owner reviewed results and labels | Not done. PR #7 was merged by the owner's account with no recorded review; a merge is not a review (audit AU-6). Needs an owner review note | W2-H1 | Yes |
| W2-H3 | PR and CI | PASS | PR opened on request; Backend, Frontend, Docker green | PR #7; CI success on head `037a820` and merge `2079101` (see **CI**) | W2-H2 | Yes (commit, PR) |
| W2-H4 | Merge | PASS | Merged by the owner | Merged 2026-11-25 03:14:43 UTC as `2079101`; follow-up display fixes merged as PR #8 (`8007fe2`) | W2-H3 | Yes |
