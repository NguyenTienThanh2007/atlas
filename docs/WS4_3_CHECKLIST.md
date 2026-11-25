# WS4-3 checklist: financial period comparison

Acceptance checklist for [WS4_3_IMPLEMENTATION_PLAN.md](WS4_3_IMPLEMENTATION_PLAN.md). **Design approved,
implementation not started:** decisions W3-D1 to W3-D10 were approved on 2026-11-25; no WS4-3 code
exists, and implementation (W3-B3) is not authorised yet.

| | |
| --- | --- |
| Last verified | 2026-11-25, `main` @ `8007fe2` |
| Statuses | `NOT STARTED`, `IN PROGRESS`, `PASS`, `BLOCKED`, `FAIL` only |
| Parent items | WS4_CHECKLIST group G (WS4-G9 implemented and tested); PHASE_2_CHECKLIST P2-5.13 |

PASS in group A means the design is written in the plan. It does not mean the design is approved or
built.

## Summary (recounted from the item rows below)

| Group | Items | PASS | IN PROGRESS | NOT STARTED | BLOCKED | FAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A. Design | 8 | 8 | 0 | 0 | 0 | 0 |
| B. Owner decisions | 3 | 2 | 0 | 1 | 0 | 0 |
| C. Period matching | 8 | 0 | 0 | 8 | 0 | 0 |
| D. Growth computation | 7 | 0 | 0 | 7 | 0 | 0 |
| E. API | 6 | 0 | 0 | 6 | 0 | 0 |
| F. Frontend | 7 | 0 | 0 | 7 | 0 | 0 |
| G. Integrity and regression | 6 | 0 | 0 | 6 | 0 | 0 |
| H. Release | 4 | 0 | 0 | 4 | 0 | 0 |
| **Total** | **49** | **10** | **0** | **39** | **0** | **0** |

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

## B. Owner decisions

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-B1 | Decisions W3-D1 to W3-D10 recorded | PASS | Each approved, changed or deferred in PRODUCT_DECISIONS | All ten approved by the owner on 2026-11-25 as proposed; recorded in PRODUCT_DECISIONS §2e | None | Yes |
| W3-B2 | Prerequisites decided | PASS | Owner decides whether AU-3 and AU-5 are fixed before or with WS4-3 | Owner authorised fixing AU-3, AU-4 and AU-5 before WS4-3 (2026-11-25). The fixes are on branch `fix/ws4-2-audit-au3-au4-au5` (not merged yet; see WS4_2_AUDIT.md) | None | Yes |
| W3-B3 | Go-ahead to implement | NOT STARTED | Owner authorises WS4-3 implementation | Owner message | W3-B1 | Yes |

## C. Period matching

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-C1 | Annual YoY | NOT STARTED | Previous end within ±7 days of the current end − 1 year; flows also align on start − 1 day | DB tests | W3-B3 | No |
| W3-C2 | Quarterly QoQ | NOT STARTED | Q*n*−1 or prior Q4; flows on start − 1 day ±7; balance sheets 80–100 days earlier | DB tests | W3-B3 | No |
| W3-C3 | Quarterly YoY | NOT STARTED | Same quarter number, FY *t*−1, end − 1 year ±7 days | DB tests | W3-B3 | No |
| W3-C4 | Non-calendar years and leap days | NOT STARTED | FY ending 31 March; 29 Feb moved back to 28 Feb | DB tests | W3-C1 | No |
| W3-C5 | Ambiguity and missing periods | NOT STARTED | Two candidates → `ambiguous_previous_period`; none → `missing_previous_period`; never pick one | DB tests | W3-C1 | No |
| W3-C6 | Label and date agreement | NOT STARTED | Disagreement → `period_mismatch` | DB test | W3-C2 | No |
| W3-C7 | Granularity and scope isolation | NOT STARTED | Annual never vs quarter (incl. Q4 vs annual on the same date); scopes never mixed | DB tests | W3-C1 | No |
| W3-C8 | Latest revision, no fallback | NOT STARTED | Latest revision of each side used and disclosed; a disputed, rejected or superseded latest revision is refused | DB tests | W3-C1 | No |

## D. Growth computation

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-D-1 | Formula `growth_abs_prior` v1 | NOT STARTED | (current − prior) ÷ \|prior\| exactly as WS4-D9 | Unit tests vs `Fraction` oracle | W3-B3 | No |
| W3-D-2 | Rounding | NOT STARTED | As decided in W3-D4; one rounding per output from the exact quotient | Unit tests incl. ties | W3-B1 | No |
| W3-D-3 | Prior zero and sign change | NOT STARTED | `change_only` with exact absolute change | Unit tests | W3-D-1 | No |
| W3-D-4 | Current zero and negative bases | NOT STARTED | As decided in W3-D2 and W3-D3 | Unit tests | W3-B1 | No |
| W3-D-5 | Fixed-point output | NOT STARTED | No exponent, no negative zero | API tests | W3-D-1 | No |
| W3-D-6 | Reason precedence | NOT STARTED | Plan §5.1 order; all issues listed | Unit tests | W3-D-1 | No |
| W3-D-7 | No float | NOT STARTED | Guard test; `mypy` clean | Test run | W3-D-1 | No |

(Group D item ids carry a hyphen, `W3-D-n`, so they can't be confused with decisions `W3-Dn`.)

## E. API

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-E1 | Endpoint | NOT STARTED | `GET /companies/{id}/comparisons` with `type`, `metric`, `scope`, `fiscal_year`, paging | API tests | W3-C1 | No |
| W3-E2 | Response model | NOT STARTED | Matches plan §5; decimals as strings or null | API tests with a float trap | W3-E1 | No |
| W3-E3 | Provenance | NOT STARTED | Both sides carry WS3 `source`, revision and period | API tests | W3-E1 | No |
| W3-E4 | No verification status | NOT STARTED | No `verification_status` on a comparison | API test | W3-E1 | No |
| W3-E5 | Validation and errors | NOT STARTED | 404 unknown company; 422 bad `type`, `metric`, `scope`, `limit` | API tests | W3-E1 | No |
| W3-E6 | Docs and OpenAPI | NOT STARTED | ARCHITECTURE and README API tables; OpenAPI schema | Review, test | W3-E1 | No |

## F. Frontend

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-F1 | Section and selector | NOT STARTED | Three comparison types and scope, kept in the URL across reloads and the language switch | Browser pass | W3-E1 | No |
| W3-F2 | Neutral direction indicators | NOT STARTED | Arrow plus text; no colour-only or good/bad meaning (W3-D5) | Browser pass, review | W3-B1 | No |
| W3-F3 | States | NOT STARTED | `change_only` and `not_comparable` show reasons; never 0 or a bare dash | Unit tests, route check | W3-E2 | No |
| W3-F4 | Disclosure and sources | NOT STARTED | Formula, both periods, revisions, links to exact pages | Browser pass, route check | W3-E3 | No |
| W3-F5 | Paging | NOT STARTED | "Showing X of Y" with next/previous whenever `total` is larger | Browser pass | W3-E1 | No |
| W3-F6 | Language, accessibility, mobile | NOT STARTED | vi and en key parity; keyboard; 375 px with no sideways scroll | Tests, browser pass | W3-F1 | No |
| W3-F7 | Glossary | NOT STARTED | New terms added for the native-speaker review | GLOSSARY.md | W3-F3 | Yes (review) |

## G. Integrity and regression

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-G1 | No schema change | NOT STARTED | No migration; `alembic check` clean | CI | W3-E1 | No |
| W3-G2 | Read-only and bounded | NOT STARTED | No writes; fixed query count | DB test | W3-E1 | No |
| W3-G3 | Fictional data only | NOT STARTED | Tests and Docker checks use fictional data; nothing under `data/` | Diff review | None | No |
| W3-G4 | Backend regression | NOT STARTED | All earlier tests green | CI | W3-E1 | No |
| W3-G5 | Frontend regression | NOT STARTED | Lint, typecheck, tests, build green | CI | W3-F1 | No |
| W3-G6 | Isolated Docker and API ↔ UI | NOT STARTED | Route check online, offline and per comparison in vi and en | Command output | W3-F4 | No |

## H. Release

| ID | Item | Status | Acceptance criteria | Evidence | Dependencies | Owner approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-H1 | Checklists updated | NOT STARTED | This file, WS4_CHECKLIST (group G) and PHASE_2_CHECKLIST (P2-5.13) recounted | Diff | G group | No |
| W3-H2 | Recorded owner review | NOT STARTED | The owner's review recorded on the PR before merge (AU-6) | PR record | W3-H1 | Yes |
| W3-H3 | PR and CI | NOT STARTED | Backend, Frontend, Docker green on head and merge | CI links | W3-H2 | Yes (commit, PR) |
| W3-H4 | Merge | NOT STARTED | Merged by the owner | Merge commit | W3-H3 | Yes |
