# WS4 checklist: financial intelligence foundation

Acceptance checklist for [WS4_FINANCIAL_INTELLIGENCE_PLAN.md](WS4_FINANCIAL_INTELLIGENCE_PLAN.md).
WS4-1 (metric dictionary 1.1.0) is merged (PR #6). WS4-2 (ROE, ROA) is merged (PR #7, `2079101`),
with display fixes AU-1 and AU-2 merged in PR #8 (`8007fe2`). WS4-2 has its own
checklist: [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md).

| | |
| --- | --- |
| Last verified | 2026-11-25, `main` @ `8007fe2` (PRs #7 and #8 merged, CI green) |
| Statuses | `NOT STARTED`, `IN PROGRESS`, `PASS`, `BLOCKED`, `FAIL` only |
| Owner approval | "Yes" means the item can't pass until the project owner decides (decision ids WS4-D1 to D11 in the plan, §12) |

**How to read PASS here.** In groups C, D, E, F, G and H, PASS on a "written" item means the
specification is written in the plan. It does **not** mean it is implemented. Approval items pass
only on a recorded owner decision (2026-11-24, PRODUCT_DECISIONS §2d); no implementation item passes.

## Summary (recounted from the item rows below)

| Group | Items | PASS | IN PROGRESS | NOT STARTED | BLOCKED | FAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A. Existing architecture audit | 5 | 5 | 0 | 0 | 0 | 0 |
| B. Metric dictionary | 8 | 5 | 3 | 0 | 0 | 0 |
| C. ROE | 7 | 7 | 0 | 0 | 0 | 0 |
| D. ROA | 7 | 7 | 0 | 0 | 0 | 0 |
| E. Banking | 5 | 4 | 1 | 0 | 0 | 0 |
| F. Missing-data semantics | 8 | 5 | 2 | 1 | 0 | 0 |
| G. Period comparison | 9 | 8 | 0 | 1 | 0 | 0 |
| H. Reported vs calculated | 9 | 9 | 0 | 0 | 0 | 0 |
| I. Testing strategy | 10 | 8 | 1 | 1 | 0 | 0 |
| J. Approval and implementation readiness | 7 | 7 | 0 | 0 | 0 | 0 |
| **Total** | **75** | **65** | **7** | **3** | **0** | **0** |

No item is BLOCKED. The open items are implementation and tests, which wait on the owner's
go-ahead to implement, plus the parts the owner did not approve (G-3 sign field, missing-data
Phase B), which stay IN PROGRESS as open questions.

## A. Existing architecture audit

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-A1 | Existing metrics audited | PASS | All 16 dictionary metrics reviewed for name, statement, unit, sign, applicability | Plan §3.1 against `metric_dictionary.json` 1.0.0 | None | No |
| WS4-A2 | Existing APIs audited | PASS | Statement endpoint, filters, revision default, decimal strings and WS3 `source` described | Plan §2.3; `backend/app/api/v1/catalog.py`, `schemas.py` | None | No |
| WS4-A3 | Existing financial models audited | PASS | `value`, `reported_value`, `reported_scale`, `source_page`, period, scope, revision, verification status explained | Plan §2.1; `backend/app/models.py` | None | No |
| WS4-A4 | WS1/WS2/WS3 compatibility assessed | PASS | Constraints WS4 must keep are listed | Plan §2.5 | None | No |
| WS4-A5 | Gaps documented | PASS | Each gap has an effect and a proposed fix | Plan §3.3 (G-1 to G-9) | None | No |

## B. Metric dictionary

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-B1 | Definitions | PASS | Every metric has an approved vi and en definition in the dictionary | All 17 metrics have `definition_vi` and `definition_en` (dictionary 1.1.0), tested by `backend/tests/test_metric_dictionary.py` (non-empty, glossary statement terms, "as presented"); owner approved all 17 texts (2026-11-25); merged as PR #6 (`105869f`, 2026-11-25); Backend CI 224 passed, Frontend 25/25, Docker healthy | WS4-D10 | Yes |
| WS4-B2 | Vietnamese and English names | IN PROGRESS | Names present for all 16 and reviewed by a native speaker | Done: names in 1.0.0. Remaining: native-speaker review (same as P2-4.12) | Glossary review | Yes |
| WS4-B3 | Units | PASS | Each metric has a unit; only currency amounts are scaled | `test_per_share_and_share_counts_are_not_scaled`, `test_amount_scales_convert_exactly[*]`; Backend CI on `105869f` (224 passed) | None | No |
| WS4-B4 | Statement types | PASS | A metric is accepted only on its statement type | `test_invalid_metrics_are_rejected` ("belongs to balance_sheet"), `test_equity_parent_belongs_to_the_balance_sheet`; Backend CI on `105869f` | None | No |
| WS4-B5 | Sign conventions | IN PROGRESS | Each metric has a recorded sign convention | Done: proposal plan §3.1, §3.2. **G-3 not approved** on 2026-11-24, so no dictionary field; open | WS4-D10 | Yes |
| WS4-B6 | Applicability (bank / non-bank) | PASS | Each metric says where it applies | Explicit `applicability {non_bank, bank}`, no default; bank values derived from WS4-D1, D2, D4, D5 and confirmed in the owner's review (PRODUCT_DECISIONS §2d note); pinned by `test_applicability_is_explicit_and_as_approved`, `test_bank_classifications_come_only_from_decisions`, `test_applicability_has_no_default[*]`; served at `GET /api/v1/metric-dictionary`; merged as PR #6 (`105869f`, 2026-11-25); Backend CI 224 passed, Frontend 25/25, Docker healthy. Per-company bank / non-bank type is WS4-F3 | WS4-D4, D5, D10 | Yes |
| WS4-B7 | Reported / calculated classification | IN PROGRESS | Reported dictionary and calculated registry are separate and versioned | Done: all 16 are reported (dictionary notes); registry approved via D7 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d). Remaining: registry implementation | WS4-D7 | Yes |
| WS4-B8 | Dictionary version change approved and recorded | PASS | Owner decision recorded in PRODUCT_DECISIONS; F-1, F-2 closed there | WS4-D10 recorded (PRODUCT_DECISIONS §2d) and implemented with G-1, G-2, G-4 only; merged as PR #6 (`105869f`, 2026-11-25); Backend CI 224 passed, Frontend 25/25, Docker healthy; exit audit F-1 and F-2 marked RESOLVED in the post-audit note of PHASE_1_EXIT_AUDIT.md | WS4-D10 | Yes |

## C. ROE

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-C1 | Formula options documented | PASS | At least: parent profit ÷ average equity, net profit ÷ average equity, closing equity; plus the rejected mixed form | Plan §4.1 | None | No |
| WS4-C2 | Default formula proposed | PASS | One default with reasons, marked PROPOSED | Plan §4.2 | None | No |
| WS4-C3 | Period rules written | PASS | Numerator period, opening/closing balance dates, annual only | Plan §4.3 | None | No |
| WS4-C4 | Missing-data rules written | PASS | Missing opening balance → not computable, no silent fallback | Plan §4.3, including WS4-D12: missing `equity_parent` → consolidated ROE not computable; never derived, never `total_equity` | None | No |
| WS4-C5 | Edge cases written | PASS | Negative/zero equity, scope change, restatement, fiscal-year change, precision | Plan §4.3 | None | No |
| WS4-C6 | Owner approval recorded before implementation | PASS | Decision recorded with formula id and version | WS4-D1, D3 and D10 (G-4) recorded, [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d; formula ids `roe_parent_avg_equity`, `roe_separate_avg_equity`, version 1 | WS4-D1, D3, D10 | Yes |
| WS4-C7 | ROE implemented and tested | PASS | Matches the approved formula; tests in §11 pass | Registry entries `roe_parent_avg_equity` and `roe_separate_avg_equity` v1; WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | WS4-C6 | Yes |

## D. ROA

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-D-1 | Formula options documented | PASS | Net profit, PBT and parent profit ÷ average assets; closing assets | Plan §5.1 | None | No |
| WS4-D-2 | Default formula proposed | PASS | One default with reasons, marked PROPOSED; bank applicability stated | Plan §5.2 | None | No |
| WS4-D-3 | Period rules written | PASS | Same alignment as ROE | Plan §5.3, §4.3 | None | No |
| WS4-D-4 | Missing-data rules written | PASS | Missing opening assets → not computable | Plan §5.3, §4.3 | None | No |
| WS4-D-5 | Edge cases written | PASS | Zero/negative assets, consolidated vs separate, restatements | Plan §5.3 | None | No |
| WS4-D-6 | Owner approval recorded before implementation | PASS | Decision recorded with formula id and version | WS4-D2, D3 recorded, [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d | WS4-D2, D3 | Yes |
| WS4-D-7 | ROA implemented and tested | PASS | Matches the approved formula; tests in §11 pass | Registry entry `roa_avg_assets` v1 per scope; WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | WS4-D-6 | Yes |

(Group D item ids carry a hyphen, `WS4-D-n`, so they can't be confused with decisions `WS4-Dn`.)

## E. Banking

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-E1 | Bank-specific gap analysis | PASS | Differences from non-bank statements and each candidate's source listed | Plan §6.1, §6.2 | None | No |
| WS4-E2 | Net interest income treatment | IN PROGRESS | Definition, sign and applicability approved | Done: required for the pilot (D4) and definition approved in principle (G-1). Remaining: sign convention (G-3 not approved), definition text | WS4-D4, D10 | Yes |
| WS4-E3 | Gross profit (and net revenue) applicability | PASS | Bank treatment approved | WS4-D5 recorded: not applicable for `gross_profit` and `net_revenue`, [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d | WS4-D5 | Yes |
| WS4-E4 | NPL and other candidates classified | PASS | Each candidate in one of the four classes | Plan §6.2 | None | No |
| WS4-E5 | Q-5 decision recorded | PASS | Owner decision recorded in PRODUCT_DECISIONS; Q-5 closed there | Q-5 marked RESOLVED in PRODUCT_DECISIONS §4 (WS4-D4, D5) | WS4-D4 | Yes |

## F. Missing-data semantics

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-F1 | Zero vs missing | PASS | Rule written: a real 0 is `reported`; absence is never 0 and never enters a formula. Today's schema can't store a null value (`value` NOT NULL) | Plan §7; `backend/app/models.py` | None | No |
| WS4-F2 | Not reported | IN PROGRESS | State defined and expressible in data | Done: defined (plan §7.1). Remaining: needs an explicit record; **Phase B not approved** (D6), so open | WS4-D6 | Yes |
| WS4-F3 | Not applicable | IN PROGRESS | State defined and derivable | Done: defined; G-2 and D5 approved. Remaining: dictionary applicability implemented (WS4-B6) | WS4-D5, D6, D10 | Yes |
| WS4-F4 | Not yet collected | PASS | Defined and derivable from today's data (no row or statement) | Plan §7.1, §7.2 | None | No |
| WS4-F5 | Invalid | PASS | Defined: rejected at import, never stored, reported by ingestion runs | Plan §7.1; `test_invalid_metrics_are_rejected` | None | No |
| WS4-F6 | Pending verification | PASS | Defined as a verification state, separate from availability | Plan §7.1; WS3 per-figure `verification_status` | None | No |
| WS4-F7 | Owner approval of states | PASS | Vocabulary and Phase A approved; Phase B decided separately | WS4-D6 recorded: vocabulary and Phase A approved; Phase B not approved, [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d | WS4-D6 | Yes |
| WS4-F8 | Implemented and tested | NOT STARTED | Tests in plan §11 "Missing data" pass | Test run, CI | WS4-F7 | Yes |

## G. Period comparison

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-G1 | FY rule written | PASS | FY *t* with FY *t*−1, same company, scope, type | Plan §8.1 | None | No |
| WS4-G2 | Quarter rule written | PASS | Quarter with quarter only; stand-alone quarters | Plan §8.1, §2.1 | None | No |
| WS4-G3 | YoY written | PASS | Annual and quarterly YoY pairs; growth formula and zero/sign-change cases | Plan §8.1, §8.3 | None | No |
| WS4-G4 | QoQ written | PASS | Including Q1 vs prior Q4; seasonality note | Plan §8.1, §8.2 | None | No |
| WS4-G5 | Scope matching written | PASS | Consolidated vs separate refused | Plan §8.2 | None | No |
| WS4-G6 | Restatement handling written | PASS | Latest revisions; restated side noted | Plan §8.2 | None | No |
| WS4-G7 | Fiscal-year alignment written | PASS | Non-calendar years; period-end shift > 7 days refused; cross-company warning | Plan §8.2 | None | No |
| WS4-G8 | Owner approval | PASS | Rules and growth formula approved | WS4-D9 recorded (growth on \|prior\|), [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d | WS4-D9 | Yes |
| WS4-G9 | Implemented and tested | NOT STARTED | Tests in plan §11 "Period alignment" pass | Test run, CI | WS4-G8 | Yes |

## H. Reported vs calculated

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-H1 | API contract proposal | PASS | Shape with value as string or null, status, reason, inputs, formula id and version | Plan §9.2 | None | No |
| WS4-H2 | UI labels proposal | PASS | vi and en labels for calculated values and input verification | Plan §9.3 | None | No |
| WS4-H3 | Formula disclosure | PASS | Formula text shown with each calculated value | Plan §9.2, §9.3 | None | No |
| WS4-H4 | Provenance chain | PASS | Each input carries its WS3 `source` (document, page, status) | Plan §9.2 | None | No |
| WS4-H5 | Decimal precision | PASS | Exact `Decimal`, one final rounding, no float in Python or JavaScript | Plan §4.3, §9.2, §10 | None | No |
| WS4-H6 | Verification semantics proposal | PASS | Calculated values have no own status and are never VERIFIED | Plan §9.3 | None | No |
| WS4-H7 | Display and rounding proposal | PASS | Scales, decimals, rounding mode, negatives, exact value kept | Plan §10 | None | No |
| WS4-H8 | Owner approval | PASS | Verification semantics, display rules and pilot display of unverified inputs approved | WS4-D7, D8, D11 recorded, [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d | WS4-D7, D8, D11 | Yes |
| WS4-H9 | Implemented and tested | PASS | API and UI tests in plan §11 pass | `GET /api/v1/companies/{id}/calculated-metrics` and the company-page section; WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | WS4-H8 | Yes |

## I. Testing strategy

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-I1 | Test strategy documented | PASS | Each layer and case family listed | Plan §11 | None | No |
| WS4-I2 | Unit tests | PASS | Formulas with exact expected strings | `backend/tests/test_ratios.py` (37); WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | Implementation | No |
| WS4-I3 | API tests | PASS | Shape, strings, reasons, OpenAPI | `backend/tests/test_calculated_metrics.py` (27) incl. OpenAPI; WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | Implementation | No |
| WS4-I4 | Integration tests | PASS | Fixture → API → page in vi and en | Isolated Docker stack with a fictional bundle: route check compares API and page in vi and en (DK); WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | Implementation | No |
| WS4-I5 | Decimal precision tests | PASS | 32-digit inputs; no float drift | Exact `Fraction` oracle, values near 10^32, fixed-point JSON checks; WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | Implementation | No |
| WS4-I6 | Missing-data tests | IN PROGRESS | Absence never 0; N/A only via dictionary | Done: absence is never zero and stops the calculation (`missing_input`, `missing_opening_balance`), WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101`. Remaining: showing the D6 states for reported figures in the UI (later WS4 step) | Implementation | No |
| WS4-I7 | Period alignment tests | PASS | Valid and refused pairs | ±7-day window, non-calendar year, closing date, quarterly exclusion tests; WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | Implementation | No |
| WS4-I8 | Restatement tests | PASS | Latest revision used and disclosed | `test_latest_revision_is_used_and_disclosed`, `test_bad_latest_revision_never_falls_back[*]`; WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | Implementation | No |
| WS4-I9 | Bank / non-bank tests | NOT STARTED | Bank fixture N/A cases; non-bank unchanged | Test run | Implementation | No |
| WS4-I10 | Regression tests | PASS | Existing backend (201) and frontend (24) suites green after WS4 | All earlier tests still pass: backend 288 (224 before WS4-2), frontend 27 (25 before); WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | Implementation | No |

## J. Approval and implementation readiness

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-J1 | All owner decisions identified | PASS | Each has situation, options, recommendation, trade-offs, risks, effect if undecided | Plan §12 (WS4-D1 to D11) | None | No |
| WS4-J2 | No unapproved formulas implemented | PASS | No ROE/ROA or other calculated metric in code | Only the approved formulas exist: the registry is pinned by `test_registry_is_exactly_the_approved_formulas` (WS4-D1, D2, D3); no growth or other ratio is implemented. WS4-2, verified on branch `feat/ws4-2-roe-roa` before merge (2026-11-25; see [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) BT/FT/DK/BR) and merged as PR #7 (`2079101`) with Backend 288 passed, Frontend 27/27, Docker success on both PR head `037a820` and merge `2079101` | None | No |
| WS4-J3 | No unauthorized schema changes | PASS | No new migration or model change | `git diff 4be30b7 105869f -- backend/migrations backend/app/models.py` is empty; Backend CI on `105869f`: `alembic check` "No new upgrade operations detected". 2026-11-25: the audit fix AU-3 adds migration `8de09b58f4c2` (triggers only, no table or column change), explicitly authorised by the owner (branch `fix/ws4-2-audit-au3-au4-au5`, not yet committed) | None | No |
| WS4-J4 | No real financial data added | PASS | No figures, company names or tickers of real companies in the repo changes | Diff adds no figures to `data/`; test values are fictional (`example.test`, `TST`) and exist only inside tests; pilot names absent (A-11 §5) | None | No |
| WS4-J5 | WS4 implementation scope defined | PASS | Steps, dependencies, schema impact | Plan §13 | None | No |
| WS4-J6 | Exit criteria documented | PASS | Measurable exit criteria | Plan §13 | None | No |
| WS4-J7 | Owner review of the WS4 specification | PASS | Owner has reviewed the plan and recorded decisions WS4-D1 to D11 (approve, change or defer each) | All eleven decisions recorded 2026-11-24, [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d (D10 partly approved: G-3, G-5 to G-9 not approved) | None | Yes |
