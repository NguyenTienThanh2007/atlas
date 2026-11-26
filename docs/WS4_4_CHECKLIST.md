# WS4-4 checklist: missing-data semantics and bank applicability

Acceptance checklist for [WS4_4_IMPLEMENTATION_PLAN.md](WS4_4_IMPLEMENTATION_PLAN.md) and
[WS4_4_DECISIONS.md](WS4_4_DECISIONS.md). **Design written; no decision approved; implementation
not authorised.**

**Status update (2026-11-26, later):** the owner approved WS4-4-D1 to D10 as proposed
(PRODUCT_DECISIONS §2f). W4-B1 and W4-B3 PASS; W4-B2 IN PROGRESS (Q-B in part); W4-B4 (go-ahead)
NOT STARTED.

**Status update (2026-11-26, implementation):** W4-B4 given ("Bắt đầu WS4-4"); Phase A
implemented on branch `feat/ws4-4-phase-a` (uncommitted). Each PASS cites the test or check that ran.
Recorded review, PR/CI and merge (W4-H2 to W4-H4) are not done; W4-B2 waits on an accountant (Q-B).

| | |
| --- | --- |
| Last verified | 2026-11-26, branch `feat/ws4-4-phase-a` from `main` @ `9d44fb4`, uncommitted |
| Statuses | `NOT STARTED`, `IN PROGRESS`, `PASS`, `BLOCKED`, `FAIL` only |
| Parent items | WS4_CHECKLIST WS4-E2, F2, F3, F8, I6; PHASE_2_CHECKLIST P2-5.15 |

PASS in group A means the design is written. It does not mean it is approved or built.

## Summary (recounted from the item rows below)

| Group | Items | PASS | IN PROGRESS | NOT STARTED | BLOCKED | FAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A. Design | 8 | 8 | 0 | 0 | 0 | 0 |
| B. Owner decisions | 4 | 3 | 1 | 0 | 0 | 0 |
| C. Classification | 6 | 6 | 0 | 0 | 0 | 0 |
| D. Applicability and states | 6 | 6 | 0 | 0 | 0 | 0 |
| E. Calculation safety | 4 | 4 | 0 | 0 | 0 | 0 |
| F. API and UI | 6 | 6 | 0 | 0 | 0 | 0 |
| G. Integrity and regression | 5 | 5 | 0 | 0 | 0 | 0 |
| H. Release | 4 | 1 | 0 | 3 | 0 | 0 |
| **Total** | **43** | **39** | **1** | **3** | **0** | **0** |

(Before the 2026-11-26 approval: 8 PASS, 0 IN PROGRESS, 35 NOT STARTED; after it: 10, 1, 32.)

## A. Design

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-A1 | Current implementation inspected | PASS | Dictionary, companies, sectors, figures, calculations, UI facts recorded with the commit | Plan §1 (`main` @ `9d44fb4`) | None | No |
| W4-A2 | Contradictions recorded | PASS | Each with a proposed dated reconciliation, none silently fixed | Plan §1.7, §12 | None | No |
| W4-A3 | Classification alternatives | PASS | A–D compared on the eleven criteria; recommendation | Plan §2 | None | No |
| W4-A4 | Applicability rules | PASS | Every kind × dictionary value; API and UI behaviour | Plan §3 | None | No |
| W4-A5 | Seven states specified | PASS | Meaning, evidence, people, storage, visibility, API, UI, calculations, transitions, history | Plan §4 | None | No |
| W4-A6 | Phase A / B boundary | PASS | Phase A scope; Phase B design and alternatives; approval boundary | Plan §5 | None | No |
| W4-A7 | Calculation safety and data model | PASS | Per state and calculation; tables, constraints, concurrency, migration, rollback | Plan §6, §7 | None | No |
| W4-A8 | Test strategy and decision register | PASS | Test matrix; ten decisions with options and recommendation | Plan §8, WS4_4_DECISIONS.md | None | No |

## B. Owner decisions

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-B1 | Phase A decisions | PASS | WS4-4-D1 to D4, D7 to D10 approved, changed or rejected | D1 to D4 and D7 to D10 approved as recommended, 2026-11-26 ("Duyệt như đề xuất"); PRODUCT_DECISIONS §2f | W4-A8 | Yes |
| W4-B2 | Open questions answered | IN PROGRESS | Q-A, Q-B, Q-C answered | Done: Q-A (D9), Q-C (D7) answered; Q-B answered for securities firms and insurers (`other_financial`). Remaining: an accountant's view on finance companies and other non-bank credit institutions (human dependency); until then they are classified case by case by the two-person review | W4-A8 | Yes |
| W4-B3 | Phase B decision | PASS | WS4-4-D5, D6 decided (may stay unapproved) | D5, D6 decided 2026-11-26: Phase B design approved, implementation deferred until G2 measures curation hours; PRODUCT_DECISIONS §2f | W4-A8 | Yes |
| W4-B4 | Go-ahead to implement | PASS | Owner authorises Phase A implementation | Owner message "Bắt đầu WS4-4" (2026-11-26); recorded in PRODUCT_DECISIONS §2f | W4-B1 | Yes |

## C. Classification

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-C1 | Table and constraints | PASS | As plan §7.1: FKs restrict, append-only, chain unique, one first row per company | Migration `5c1f0a2b7e44`; backend `tests/test_classification.py` `test_classifications_are_append_only`, `test_one_linear_chain_per_company`; `alembic check` clean (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-B4 | No |
| W4-C2 | Two-person rule | PASS | curator ≠ reviewer; reviewer a person | backend `tests/test_classification.py` `test_two_person_rule[*]` (same person in other case and spacing, "AI", "system", blank basis) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-B4 | No |
| W4-C3 | Evidence and isolation | PASS | Evidence about the same company; sample/real must match | backend `tests/test_classification.py` `test_evidence_must_be_about_the_same_company`, `test_withdrawn_evidence_cannot_be_cited[*]`, `test_sample_and_real_classifications_never_mix` (raw legacy row), `test_sample_company_is_classified_with_sample_evidence` (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-B4 | No |
| W4-C4 | Unknown by default | PASS | No row → `unclassified`; nothing inferred from sector, name or ticker | backend `tests/test_classification.py` `test_classification_is_recorded_and_current`, `test_unclassified_company_marks_nothing_not_applicable`; `tests/test_api.py` list item shape (`unclassified` for a company in an energy sector) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-C1 | No |
| W4-C5 | Concurrency | PASS | Competing supersessions and first rows: one wins | backend `tests/test_classification.py` `test_concurrent_first_classifications_serialize` (two connections, lock timeout) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-C1 | No |
| W4-C6 | Migration round trip | PASS | Upgrade, downgrade, `alembic check`; existing rows untouched | `tests/test_migrations.py` round trip includes `5c1f0a2b7e44`; manual upgrade → downgrade −1 → upgrade on a throwaway database; isolated stack migrated a fresh volume to `5c1f0a2b7e44` (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-C1 | No |

## D. Applicability and states

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-D-1 | Effective applicability | PASS | All rows of plan §3.1; `unclassified` never N/A | backend `tests/test_classification.py` `test_effective_applicability_never_turns_unknown_into_not_applicable` (all 17 metrics × kinds; bank N/A exactly `net_revenue`, `gross_profit`) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-B1 | No |
| W4-D-2 | Absent metrics | PASS | `not_yet_collected` / `not_applicable` per statement; never 0 | backend `tests/test_classification.py` `test_bank_shows_not_applicable_only_where_the_dictionary_says_so`, `test_other_kinds[*]`; route check counts every state on the page (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-1 | No |
| W4-D-3 | Conflicting rows | PASS | Importer refuses; existing rows flagged | backend `tests/test_classification.py` `test_importer_refuses_figures_that_do_not_apply`, `test_conflicting_rows_are_flagged_and_not_compared`; CLI import in the isolated stack refused `net_revenue` for the fictional bank (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-1 | No |
| W4-D-4 | Real zero vs absence | PASS | 0 is `reported`; absence is a state | backend `tests/test_classification.py` `test_unclassified_company_marks_nothing_not_applicable` (a 0 is reported and listed as a figure, not absent) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-2 | No |
| W4-D-5 | Phase B states absent | PASS | No `not_reported` / `unavailable` produced or shown in Phase A | `AbsentMetricOut.state` allows only `not_yet_collected` / `not_applicable`; no "not reported" or "source not available" text in vi/en (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-2 | No |
| W4-D-6 | Invalid never stored | PASS | Existing import refusals still hold; nothing shown on the page | Existing import refusal tests unchanged and green (404 passed); invalid rows never reach the API (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | None | No |

## E. Calculation safety

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-E1 | ROE/ROA unchanged | PASS | Formulas, rounding, codes unchanged; WS4-2 suite green | WS4-2 suite unchanged and green; ranks renumbered without changing order; backend `tests/test_classification.py` `test_roe_roa_input_not_applicable_is_defensive` (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-1 | No |
| W4-E2 | Comparisons | PASS | `metric_not_applicable` if approved; WS4-3 suite green | backend `tests/test_classification.py` `test_conflicting_rows_are_flagged_and_not_compared`; WS4-3 suite green; isolated stack: fictional bank `net_revenue` `metric_not_applicable` (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-B1 | No |
| W4-E3 | Unknown never N/A | PASS | Unknown applicability gives `missing_*`, never N/A | backend `tests/test_classification.py` effective-applicability test (unknown never N/A); unclassified company: comparisons and ratios use only `missing_*` (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-1 | No |
| W4-E4 | Bank fixture | PASS | Fictional bank: revenue and gross profit N/A; ROE and ROA computed | backend `tests/test_classification.py` bank tests; isolated stack: fictional bank ROE 6.37 %, ROA 0.63 % computed, `gross_profit` "Không áp dụng"; route check (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-2 | No |

## F. API and UI

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-F1 | Additive API | PASS | `classification`, `absent_metrics`, `applicability_conflict`; nothing removed or renamed; OpenAPI | `classification` on `/companies` and `/companies/{id}`, `absent_metrics`, `applicability_conflict`; existing fields unchanged (`tests/test_api.py` shape test extended, not reduced) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-D-2 | No |
| W4-F2 | Company type shown | PASS | vi/en texts; unclassified note | Route check: company type and unclassified note in vi and en for a classified and an unclassified fictional company (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F1 | No |
| W4-F3 | State texts | PASS | "Chưa thu thập" / "Không áp dụng"; never 0 or dash | Route check: counts of "Chưa thu thập"/"Not yet collected", "Không áp dụng"/"Not applicable" and conflict warnings equal the API; browser pass (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F1 | No |
| W4-F4 | Language and parity | PASS | vi/en key parity; language switch keeps state | `i18n.test.ts` key parity and a WS4-4 text test (36/36) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F3 | No |
| W4-F5 | Accessibility and 375 px | PASS | Keyboard; no sideways scroll | Browser pass: desktop 1280 and 375 px (`scrollWidth` 375, no overflowing element) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F3 | No |
| W4-F6 | Glossary | PASS | New terms added for the review | GLOSSARY.md "Missing data and company type (WS4-4)"; the native-speaker review itself stays open (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F3 | Yes (review) |

## G. Integrity and regression

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-G1 | Fictional data only | PASS | Fixtures `example.test`, `TST`; nothing under `data/` | Fixtures use example.test and TST tickers; nothing under `data/` changed (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | None | No |
| W4-G2 | Backend regression | PASS | All earlier tests green (380 on `609864c`) | Clean copy: ruff, format, `mypy` strict, `pytest` 404 passed (380 earlier, 2 assertions updated for the additive field and one fixed extra query; 24 new), `alembic check` clean, pip-audit clean (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-C1 | No |
| W4-G3 | Frontend regression | PASS | All earlier tests green (35 on `609864c`), build | Clean copy: lint, typecheck, `npm test` 36/36, production build, `npm audit` 0 (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F1 | No |
| W4-G4 | Isolated Docker | PASS | Fresh volume; route check online and offline, vi and en | Isolated stack `atlasws44` (fresh volumes, ports 5463/8063/3063): route check online for two fictional companies and offline (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F3 | No |
| W4-G5 | Read-only endpoints | PASS | No writes from GET; fixed query count | Existing read-only and query-count tests green; company list: 4 fixed queries whatever the page size (`test_company_list_has_no_n_plus_one`) (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | W4-F1 | No |

## H. Release

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W4-H1 | Checklists updated | PASS | This file, WS4_CHECKLIST, PHASE_2_CHECKLIST recounted | This file, WS4_CHECKLIST and PHASE_2_CHECKLIST recounted (2026-11-26, branch `feat/ws4-4-phase-a`, uncommitted) | G group | No |
| W4-H2 | Recorded owner review | NOT STARTED | Review recorded on the PR before merge (AU-6) | PR record | W4-H1 | Yes |
| W4-H3 | PR and CI | NOT STARTED | Green on head and merge | CI links | W4-H2 | Yes |
| W4-H4 | Merge | NOT STARTED | Merged by the owner | Merge commit | W4-H3 | Yes |
