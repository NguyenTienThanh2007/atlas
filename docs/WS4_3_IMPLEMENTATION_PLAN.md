# WS4-3: Financial period comparison plan

**Status update (2026-11-26, after merge): merged as PR #10 (`609864c`, feature commit `42f2f8a`),
CI green on head and merge. No recorded review (W3-H2). Two details the code settles that §12 left
open: `prior_zero` is recorded on the `previous` side and `sign_change` on the `current` side
(§12.4 shows "—"); an issue's `period_end` is `null` when no previous statement matched. See
[WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md) (PM-1 to PM-4).**

**Status update (2026-11-26, implementation): implemented as specified in §12 on branch
`feat/ws4-3-period-comparison`, not committed. No migration. Evidence per item in
[WS4_3_CHECKLIST.md](WS4_3_CHECKLIST.md). Two small presentation choices made during
implementation: the limit text follows the site's percentage style without a space ("> 999,99%");
the mixed-data text uses the comparison wording of §12.5 ("Không so sánh được: …").**

**Status update (2026-11-26, later): the owner approved the §12.15 items as proposed (W3-D11, the
W3-D7 threshold, A3-5, A3-7; PRODUCT_DECISIONS §2e). Implementation (W3-B3) is still not
authorised.**

**Status update (2026-11-26): audited against `main` @ `407ed63` ([WS4_3_AUDIT.md](WS4_3_AUDIT.md)).
§12 adds the implementation specification; where §12 differs from §§2–9 it says so, and §12
governs. Two items need the owner before implementation: proposed decision W3-D11 and the W3-D7
display threshold (§12.15). Implementation is still not authorised and has not started.** Earlier
status lines follow, kept as written:

**Status update (2026-11-25): decisions W3-D1 to W3-D10 APPROVED by the owner as proposed below
([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2e). Implementation is not authorised and has not
started.** The original status line follows, kept as written:

**Status: PLAN — REQUIRES OWNER REVIEW. Not implemented.** This document changes no code, schema,
migration, data or decision. It builds on the approved rule WS4-D9 (plan §8 of
[WS4_FINANCIAL_INTELLIGENCE_PLAN.md](WS4_FINANCIAL_INTELLIGENCE_PLAN.md)). Every new choice is marked
**PROPOSED — REQUIRES OWNER APPROVAL** and gathered in §10.

| | |
| --- | --- |
| Written | 2026-11-25 |
| Code inspected | `main` @ `8007fe2` (WS4-2 PR #7 and the display fixes in PR #8 merged) |
| Approved basis | WS4-D9 (comparison rules, growth on \|prior\|), WS4-D8 (display), WS4-D6 (missing data, Phase A), WS4-D7 (no verification status on calculated values), WS4-D12 (`equity_parent` only as reported) |
| Phase 2 item | P2-5.13 (period comparisons) |
| Checklist | [WS4_3_CHECKLIST.md](WS4_3_CHECKLIST.md) |

## 1. What exists today (inspected)

| Area | Fact | Effect on WS4-3 |
| --- | --- | --- |
| Periods | `fiscal_year` is named by the year the period ends in; `fiscal_quarter` is 1–4 or null (annual). Annual flows span 360–371 days; quarterly flows span 80–100 days (`backend/app/ingestion/schemas.py`). Balance sheets are one date | Quarterly flows are always **stand-alone quarters**. Year-to-date (6-month, 9-month) figures can't be imported, so ATLAS never holds them |
| Quarter numbers | The importer does not check the quarter number against the months (a known limit of P2-6.4) | Matching uses **dates**; labels must agree with dates, otherwise the pair is refused |
| Overlap and identity | Overlapping periods are refused within one company, type, scope and granularity; there is one row per period end and revision; restatements are new revisions | At most one latest statement per period; "comparative column" and "previous report" can't coexist as two rows |
| Revisions | Latest = not superseded by `supersedes_id` (`catalog.py`, `calculations/service.py`) | Reuse that rule; never fall back to an older revision (same as WS4-2) |
| Evidence status | On the statement's evidence (WS1); sample/real separation is enforced by the importer, not the database (audit AU-3) | Same refusal rules as WS4-2; AU-3's fix should land first or with WS4-3 |
| Units | `VND`, `VND/share`, `shares`; statement currency VND only | Compare only the same metric, unit and currency |
| Arithmetic | WS4-2 has exact `Decimal` helpers (`rounded_quotient`, exact average) and fixed-point JSON (`FixedDecimal`) | Reuse; no new numeric code style |
| API pattern | Read-only endpoints, `Page` with `total`; WS3 `MetricSourceOut` for provenance | Reuse |
| UI | Company page sections; `formatDecimal`, `formatFixed` (U+2212 minus); pagination gap AU-5 | The comparison section must show totals and paging from the start |

## 2. Comparison types

All three compare the **same company, metric, statement type, scope, unit and currency**, using the
**latest revision** of each statement. Annual is compared with annual only, quarter with quarter only.

| Type | Current | Previous | Matching rule (PROPOSED — REQUIRES OWNER APPROVAL, refines WS4-D9 §8.1) |
| --- | --- | --- | --- |
| `annual_yoy` | Annual statement, FY *t* | Annual statement, FY *t*−1 | Previous `reporting_period_end` within **±7 days** of the current end moved back one year (29 Feb → 28 Feb). For income and cash-flow statements, the previous period must also end within ±7 days of the current start − 1 day |
| `quarterly_qoq` | Quarter Q*n* of FY *t* | The immediately preceding quarter: Q*n*−1 of FY *t*, or Q4 of FY *t*−1 for Q1 | Flows: previous end within ±7 days of the current start − 1 day. Balance sheets (a single date): previous end between 80 and 100 days before the current end. In both cases the labels must agree (Q*n*−1, or Q4 of *t*−1) |
| `quarterly_yoy` | Quarter Q*n* of FY *t* | Q*n* of FY *t*−1 | Previous end within ±7 days of the current end moved back one year; same quarter number |

- **Calendar and non-calendar years:** both work, because matching uses dates and the fiscal year is
  named by its end year (e.g. a FY2025 that ends 31 March 2025).
- **Fiscal-year change:** a shift of more than 7 days, or a transitional period, leaves no previous
  period → `missing_previous_period`. Two candidates in the window → `ambiguous_previous_period`.
  ATLAS never picks one.
- **Label and date disagree** (e.g. a "Q3" whose dates fit Q2) → `period_mismatch`, refused.
- **Balance sheets:** compared at the period end. A Q4 balance sheet and an annual balance sheet on
  the same date belong to different granularities and are never compared with each other.

### 2.1 Stand-alone quarters and year-to-date (YTD)

Vietnamese quarterly reports often print both "Quý này" (this quarter) and "Lũy kế từ đầu năm"
(year to date) columns for the income statement, and the cash-flow statement is often printed as
**year to date only**.

| Case | Rule |
| --- | --- |
| Stand-alone quarter printed | Curators import that column; it is the only quarterly flow ATLAS stores |
| Only YTD printed (typical for quarterly cash flow) | **Not importable today** (the period would be longer than 100 days). There is no comparison, and the result says `missing_current_value` or `missing_previous_period` |
| Deriving a quarter as YTD(*n*) − YTD(*n*−1) | **Not done.** That would be a calculated figure presented as reported. See **W3-D1** for the options |

## 3. Growth formula and edge cases

WS4-D9 (approved) fixes the formula: `growth = (current − prior) ÷ |prior|`, exact; prior = 0 → no
percentage; sign change → no percentage, absolute change only. The plan keeps that unchanged.

| Case | Example (fictional) | Result under WS4-D9 | Gap needing a decision |
| --- | --- | --- | --- |
| Prior positive | 100 → 120 | `growth` 0.2, 20.00 % | — |
| Prior positive, current lower | 100 → 80 | −20.00 % | — |
| Prior negative, current more negative | −100 → −150 | (−150 + 100) ÷ 100 = −50.00 % | Wording: this reads as "value fell 50 % of the prior's size", not "the loss grew". See **W3-D3** |
| Prior negative, current less negative | −100 → −50 | +50.00 % | Same wording issue: +50 % here means the loss **narrowed** |
| Prior zero | 0 → 30 | No percentage (`prior_zero`); absolute change +30 shown | — |
| Current zero, prior non-zero | 50 → 0 | (0 − 50) ÷ 50 = −100.00 % | Is a move to exactly zero a "sign change"? D9 doesn't say. See **W3-D2** |
| Sign change | −40 → 60, or 60 → −40 | No percentage (`sign_change`); absolute change shown | — |
| Missing current or previous value | — | Not comparable; reason given; never zero | — |
| Restated prior | Prior revision 2 | Computed from the latest revisions, with a "restated (revision 2)" note | — |
| Very small prior | 0.000001 → 1 | Exact; about 99 999 900 % | Display cap or not: **W3-D7** |
| Precision | — | Not specified by D9 | Rounding of the growth value and percentage: **W3-D4** |

Absolute change = `current − prior`, exact, in the metric's unit, shown with the WS4-D8 display rules.

## 4. Architecture (no schema change)

```
GET /api/v1/companies/{id}/comparisons
        │ catalog.py: validate params, 404
        ▼
app/calculations/comparison_service.py   read-only: latest revisions of all statement types and
        │                                 both granularities in a fixed number of queries
        ▼
app/calculations/comparisons.py          pure: pair matching on dates, growth with exact Decimal,
        │                                 reason codes in a fixed precedence; reuses rounded_quotient
        ▼
PeriodComparisonOut (schemas.py)          fixed-point strings or null; WS3 sources for both sides
```

Nothing is written to `financial_metrics` or any other table. The registry gets one entry,
`growth_abs_prior` version 1, implementing WS4-D9.

## 5. API contract proposal

`GET /api/v1/companies/{id}/comparisons?type=annual_yoy|quarterly_qoq|quarterly_yoy&metric=&scope=&fiscal_year=&limit=&offset=`
→ `Page[PeriodComparisonOut]`, with one item per (current statement, metric) and a `total`.

```json
{
  "kind": "comparison",
  "type": "annual_yoy",
  "formula_id": "growth_abs_prior",
  "formula_version": 1,
  "metric_code": "net_revenue",
  "metric_name_vi": "Doanh thu thuần",
  "metric_name_en": "Net revenue",
  "statement_type": "income_statement",
  "scope": "consolidated",
  "unit": "VND",
  "currency": "VND",
  "current": {"fiscal_year": 2025, "fiscal_quarter": null, "period_start": "2025-01-01", "period_end": "2025-12-31",
              "value": "…", "statement_id": "…", "revision": 1, "source": {"…": "WS3 MetricSourceOut"}},
  "previous": {"fiscal_year": 2024, "fiscal_quarter": null, "period_start": "2024-01-01", "period_end": "2024-12-31",
               "value": "…", "statement_id": "…", "revision": 2, "source": {"…": "WS3 MetricSourceOut"}},
  "absolute_change": "…",
  "growth_value": "…",
  "growth_percent": "…",
  "status": "computed",
  "reason": null,
  "issues": [],
  "input_verification": "some_unverified"
}
```

Figures are elided on purpose; this shows the shape only.

- `status`: `computed` (growth and change), `change_only` (absolute change only: `prior_zero` or
  `sign_change`), or `not_comparable` (nothing computed).
- `previous` is `null` when no previous period matched.
- `input_verification` follows WS4-D7 and AU-1: it describes the inputs, and the UI shows it only
  for `computed` and `change_only`.
- Decimals are fixed-point strings, never numbers (`FixedDecimal`).

### 5.1 Reason codes and precedence (PROPOSED — REQUIRES OWNER APPROVAL)

| Rank | Code | Triggered by | Status | vi (proposed) | en (proposed) |
| --- | --- | --- | --- | --- | --- |
| 1 | `missing_current_value` | The current statement lacks the metric | not_comparable | Không so sánh được: kỳ này không có số liệu | Not comparable: no value for this period |
| 2 | `missing_previous_period` | No previous statement matches (§2) | not_comparable | Không so sánh được: không có kỳ trước phù hợp | Not comparable: no matching previous period |
| 3 | `ambiguous_previous_period` | More than one candidate | not_comparable | Không so sánh được: có nhiều hơn một kỳ trước phù hợp | Not comparable: more than one possible previous period |
| 4 | `period_mismatch` | Quarter label and dates disagree | not_comparable | Không so sánh được: số quý và ngày của kỳ không khớp | Not comparable: quarter label and dates disagree |
| 5 | `missing_previous_value` | The previous statement lacks the metric | not_comparable | Không so sánh được: kỳ trước không có số liệu | Not comparable: no value for the previous period |
| 6 | `input_disputed_or_rejected` | Either side's evidence | not_comparable | Không so sánh được: số liệu đang xem xét lại hoặc bị loại | Not comparable: a figure is under review or rejected |
| 7 | `input_superseded` | Either side's evidence | not_comparable | Không so sánh được: tài liệu nguồn đã được thay thế | Not comparable: a source document was superseded |
| 8 | `unit_or_currency_mismatch` | Unit or currency differs | not_comparable | Không so sánh được: đơn vị hoặc tiền tệ khác nhau | Not comparable: different unit or currency |
| 9 | `prior_zero` | Previous value is 0 | change_only | Không tính được tỷ lệ thay đổi: kỳ trước bằng 0 | No percentage: the previous value is zero |
| 9 | `sign_change` | One value is negative and the other positive | change_only | Không tính tỷ lệ thay đổi khi số liệu đổi dấu | No percentage: the value changed sign |

Every issue found is listed in `issues`, and `reason` is the first one. Rank-9 checks run only when
nothing from ranks 1–8 applies. Scope never mismatches: the queries filter by one scope.

## 6. Frontend proposal (vi first, en at `/en`)

- **Section:** "So sánh giữa các kỳ (do ATLAS tính)" / "Period comparison (computed by ATLAS)",
  separate from reported figures and from ROE/ROA.
- **Selector:** a segmented control with three options: "Năm so với năm trước" / "Year on year",
  "Quý so với quý trước" / "Quarter on quarter", "Quý so với cùng kỳ năm trước" / "Same quarter last
  year". It writes a query parameter (`?compare=annual_yoy`), so the choice survives a reload and the
  language switch. A scope filter (Hợp nhất / Riêng) follows the same pattern.
- **Table (desktop):** one row per metric. Columns: current period and value, previous period and
  value, absolute change, change %. On mobile (375 px) each metric becomes a stacked card with the
  same fields; nothing scrolls sideways.
- **Direction indicator:** a neutral arrow (▲ up, ▼ down, = unchanged) **plus text** ("tăng" /
  "giảm" / "không đổi"; "up" / "down" / "unchanged"). **No green or red** and no good/bad wording,
  because a rise isn't always good (debt, expenses), and colour is never the only signal (W3-D5).
- **Wording:** "Thay đổi so với kỳ trước" / "Change from previous period", not "tăng trưởng" /
  "growth", especially for negative bases (W3-D3).
- **States:** `change_only` shows the absolute change plus the reason text; `not_comparable` shows
  the reason. Neither ever shows a 0 or a bare dash.
- **Disclosure:** "Cách tính" / "How it's calculated" shows the formula text, both values with their
  periods, revisions ("đã điều chỉnh (lần n)") and WS3 source links to the exact pages.
- **Paging:** show "Đang hiển thị X / Y" / "Showing X of Y" with next/previous links whenever
  `total` exceeds the page (fixes AU-5's pattern for this section).
- **Charts:** not in WS4-3. A table is accessible and exact; charts can come later (W3-D8).
- **Numbers:** no arithmetic in the browser; `formatFixed` for percentages (U+2212 minus) and
  `formatDecimal` for values, as in WS4-2.

## 7. Security and integrity

- Read-only GET; validated params (`type` enum, `metric` must be in the dictionary, `scope` enum,
  `fiscal_year` range, `limit` ≤ 100); 404 for an unknown company.
- A fixed number of queries per request (statements with metrics and evidence loaded together),
  independent of the number of years.
- No writes, no caching, no stored comparisons; exact `Decimal` only; no `float` (guard test, as in
  WS4-2).
- Provenance reuses WS3 `linkable_url`. No new URL handling.

## 8. Test strategy (fictional fixtures only: `example.test`, `TST` tickers)

| Area | Cases |
| --- | --- |
| Calendar / non-calendar | Calendar FY; FY ending 31 March; leap-day year end moved back one year |
| Annual matching | ±7-day window (0, 7 and 8 days); fiscal-year change → `missing_previous_period`; two candidates → ambiguous |
| Quarterly matching | Q2 vs Q1; Q1 vs prior Q4; quarterly YoY; balance-sheet QoQ at 80 and 100 days; label/date disagreement → `period_mismatch`; annual vs Q4 never paired |
| Stand-alone vs YTD | Only stand-alone quarters are compared; no derivation from YTD; a cash flow with no quarterly row → reason, not zero |
| Scope | Consolidated and separate never mixed |
| Units, currency | Defensive `unit_or_currency_mismatch` with a row written directly in a test |
| Restatements | Latest revision of either side used and disclosed; a rejected latest revision → refused, no fallback |
| Missing values | Current missing; previous missing; never zero |
| Zero and negative priors | `prior_zero` → `change_only` with exact change; negative bases (both directions); current zero (per W3-D2) |
| Sign change | Both directions → `change_only` |
| Precision | Exact `Fraction` oracle; 32-digit values; ties at the rounding digits; no double rounding; fixed-point JSON (no `E`, no `-0`) |
| API | Shape, OpenAPI, filters, pagination and `total`, 404/422, no `verification_status`, read-only and query count |
| UI | vi and en texts and key parity; neutral arrow plus text; `formatFixed` minus sign; states never show 0; 375 px with no sideways scroll; keyboard through the selector and disclosures |
| API ↔ UI | Route check compares every rendered comparison with the API in vi and en |
| Regression | All earlier backend (288) and frontend (28) tests stay green |

## 9. Implementation sequence (after approval)

0. **Prerequisite (recommended):** fix AU-3 (refuse mixed sample/real inputs) and AU-5 (paging
   pattern), because WS4-3 reuses both paths.
1. **WS4-3a:** pure `comparisons.py`: matching and growth, with oracle unit tests.
2. **WS4-3b:** `comparison_service.py`: loading and pairing, with database tests.
3. **WS4-3c:** endpoint, schema, OpenAPI, API tests, docs.
4. **WS4-3d:** frontend section, selector, paging, vi/en strings, route check, browser pass.
5. **WS4-3e:** full verification (backend, frontend, Docker), checklists, owner review, PR.

No migration at any step.

## 10. Owner decision register (none approved when written; all ten approved 2026-11-25, see PRODUCT_DECISIONS §2e)

| ID | Context | Options | Recommendation | Trade-offs | Risk if undecided | Approval |
| --- | --- | --- | --- | --- | --- | --- |
| W3-D1 | Quarterly figures printed only year to date (typical for quarterly cash flow) | (a) Not supported: compare only stand-alone quarters; (b) derive quarter = YTD(*n*) − YTD(*n*−1) as a **calculated** figure with its own label; (c) store YTD as a new granularity (schema change) | **(a)** now; revisit after the pilot | (a) gives fewer quarterly cash-flow comparisons; (b) and (c) give more data but add a calculated layer or a migration | Curators might enter derived figures as if reported | Required |
| W3-D2 | Current value exactly zero, prior non-zero | (a) Compute (50 → 0 = −100 %; −50 → 0 = +100 %); (b) treat as a sign change → `change_only` | **(a)**: zero has no sign | (a) shows ±100 %, which is mathematically correct; (b) hides it | Inconsistent results between implementers | Required |
| W3-D3 | Wording for negative bases (losses), where \|prior\| makes "+" mean "moved up" | (a) Neutral "Thay đổi so với kỳ trước" / "Change from previous period" plus direction text; (b) "Tăng trưởng" / "Growth"; (c) special wording for loss metrics | **(a)** | (a) is accurate but less familiar; (b) misleads on losses | A learner reads "+50 %" on a loss as a bigger loss | Required |
| W3-D4 | Precision of growth (D9 is silent) | (a) Same as ratios: `growth_value` 10 decimals half-even, `growth_percent` 2 decimals half-up, both from the exact quotient; `absolute_change` exact; (b) other | **(a)**, consistent with WS4-D8 and WS4-2 | — | Inconsistent rounding across features | Required |
| W3-D5 | Visual semantics | (a) Neutral arrow plus text, no colour meaning; (b) green/red | **(a)** | (a) is less "dashboard-like" but never implies good or bad | Implying that higher debt is good | Required |
| W3-D6 | Which metrics | (a) All 17 reported dictionary metrics (EPS and share counts included, in their own units); (b) a subset; (c) also ROE/ROA changes in percentage points | **(a)**; ROE/ROA comparison later | (c) needs its own rule (points, not %) | Scope creep | Required |
| W3-D7 | Very large percentages (tiny prior) | (a) Show the exact value; (b) cap the display (e.g. "> 999,99 %") with the exact value in the disclosure | **(b)** | (b) avoids absurd headline numbers but adds one display rule | Misleading headline figures | Required |
| W3-D8 | Charts | (a) Table only in WS4-3; (b) table and chart | **(a)** | Less visual; charts need their own accessibility and design work | — | Required |
| W3-D9 | Matching details of §2 (±7 days applied per type; 80–100 days for balance-sheet QoQ; label/date agreement; ambiguity refused) | (a) As §2; (b) looser | **(a)** | Strict rules show fewer comparisons | Wrong pairs | Required |
| W3-D10 | Reason codes, texts and statuses of §5.1, including `change_only` | (a) As §5.1; (b) changes | **(a)** | — | Inconsistent UI and API | Required |

WS4-D9 is **not redefined**. W3-D2, W3-D3, W3-D4 and W3-D9 fill gaps D9 left open; the others are
design choices.

## 11. Dependencies and blockers

| Item | State | Effect |
| --- | --- | --- |
| W3-D1 to W3-D10 | Pending | Block implementation |
| AU-3 (mixed sample/real), AU-5 (paging) | Open | Recommended before or with WS4-3 |
| Q-3 independent reviewer | Open | All real values stay unverified; labels say so |
| G1 legal opinion | Open | No public display of real comparisons |
| Glossary native-speaker review | Pending | New terms join the review |
| Q-7, Q-8 | Open | No effect on the code |
| AU-6 (no recorded reviews) | Open | WS4-3's PR should carry a recorded owner review before merge |

## 12. Implementation specification (added 2026-11-26, after the audit)

Written after [WS4_3_AUDIT.md](WS4_3_AUDIT.md). It refines §§2–9 without changing WS4-D9 or
W3-D1 to W3-D10. Items marked **PROPOSED — REQUIRES OWNER APPROVAL** are gathered in §12.15.

### 12.0 What changed against §§2–9

| Where | Change | Why |
| --- | --- | --- |
| §5.1 | Rank 0 `mixed_sample_and_real` added (**PROPOSED**, W3-D11) | Audit A3-1: isolation must refuse, and W3-D10 has no code for it |
| §6 | Heading text "Change versus previous period" (approved W3-D3), not "from" | A3-6 |
| §6 | QoQ seasonality note; "restated" note next to the restated side | WS4-D9 §8.2, already approved (A3-3, A3-4) |
| §6 | Display limit 999,99 % (**PROPOSED** threshold for W3-D7) | A3-2 |
| §5 | Rows only for metrics reported on at least one side; `direction` field; issue `side` | A3-5; one place decides direction |
| §8 | Regression baseline is now backend 314 and frontend 31 (`main` @ `407ed63`) | PR #9 |
| §9 step 0 | Done: AU-3, AU-4 and AU-5 merged in PR #9 | — |
| §11 | W3-D1 to W3-D10 approved; AU-3 and AU-5 closed | PRODUCT_DECISIONS §2e, PR #9 |

### 12.1 API contract

`GET /api/v1/companies/{id}/comparisons`

| Parameter | Rule | Error |
| --- | --- | --- |
| `type` | Required: `annual_yoy`, `quarterly_qoq` or `quarterly_yoy` | 422 if missing or other |
| `scope` | Optional: `consolidated` or `separate`; absent = both | 422 |
| `metric` | Optional: one of the 17 dictionary codes | 422 for any other code (including `roe`, `roa`) |
| `fiscal_year` | Optional, 1990–2200: filters the **current** side | 422 |
| `limit`, `offset` | As every list: `limit` 1–100, default 20; `offset` ≥ 0 | 422 |
| `{id}` | Unknown company | 404 |

Response `Page[PeriodComparisonOut]`. Order: current `period_end` newest first, then statement type
(income statement, balance sheet, cash flow), scope (consolidated, separate), then dictionary
order of the metric. `total` counts every row before paging.

```json
{
  "kind": "comparison",
  "type": "quarterly_qoq",
  "formula_id": "growth_abs_prior",
  "formula_version": 1,
  "formula_text_vi": "(Kỳ này − kỳ trước) ÷ |kỳ trước|",
  "formula_text_en": "(current − previous) ÷ |previous|",
  "metric_code": "net_revenue",
  "metric_name_vi": "Doanh thu thuần",
  "metric_name_en": "Net revenue",
  "statement_type": "income_statement",
  "scope": "consolidated",
  "unit": "VND",
  "current":  {"statement_id": "…", "fiscal_year": 2025, "fiscal_quarter": 2, "period_start": "2025-04-01",
               "period_end": "2025-06-30", "revision": 1, "value": "120.000000", "reported_value": "…",
               "reported_scale": 1, "source": {"…": "MetricSourceOut"}},
  "previous": {"statement_id": "…", "fiscal_year": 2025, "fiscal_quarter": 1, "period_start": "2025-01-01",
               "period_end": "2025-03-31", "revision": 2, "value": "100.000000", "reported_value": "…",
               "reported_scale": 1, "source": {"…": "MetricSourceOut"}},
  "status": "computed",
  "reason": null,
  "issues": [],
  "absolute_change": "20.000000",
  "growth_value": "0.2000000000",
  "growth_percent": "20.00",
  "direction": "up",
  "input_verification": "some_unverified"
}
```

Values are those of fixture F1 (§12.9), fictional.

- `previous` is `null` when no previous statement is accepted or shown. For `period_mismatch` it is
  the candidate that disagreed, so the reader sees which period it was; nothing is computed from it.
- A side's `value`, `reported_value`, `reported_scale` and `source` are `null` when that statement
  lacks the metric. `source` is the WS3 `MetricSourceOut` of that figure.
- `status`: `computed`, `change_only` or `not_comparable`. `growth_value` and `growth_percent` are
  non-null only for `computed`; `absolute_change` and `direction` for `computed` and `change_only`.
- `direction`: `up`, `down` or `unchanged` (sign of `absolute_change`), else `null`.
- `issues`: `{code, side: "current" | "previous", metric_code, period_end}`, ordered by §12.4;
  `reason` = `issues[0].code`.
- `input_verification`: `all_verified`, `some_unverified` or `sample` from the evidence of the sides
  with a value (WS4-D7); `null` when a side is mixed (as WS4-2). Never a `verification_status` on
  the comparison itself.
- Decimals are fixed-point strings (`FixedDecimal`); `absolute_change` has 6 decimals,
  `growth_value` 10, `growth_percent` 2.

### 12.2 Engine design

| File | Content |
| --- | --- |
| `backend/app/calculations/comparisons.py` (new, pure) | `ComparisonType`, `ReasonCode`, `RANK`; `Period` (type, fiscal year, quarter, start, end); `previous_year(d)`; `match(kind, current, pool)` → (previous or none, issue or none); `Side` (value, unit, currency, status, period end); `compare(current, previous, issues, *, company_is_sample, company_mixed)` → outcome. Reuses `rounded_quotient`, `_EXACT`, `VALUE_PLACES`, `PERCENT_PLACES` from `ratios.py` |
| `backend/app/calculations/service.py` | `_latest_annual` becomes `latest_statements(db, company_id, quarterly: bool)` returning every type of one granularity; WS4-2 keeps filtering the types it needs in Python (it already does). `_company_mixed` is reused unchanged |
| `backend/app/calculations/comparison_service.py` (new) | `comparisons(db, company_id, kind, scope, metric, fiscal_year)`: loads once, groups by (type, scope), matches, builds rows |
| `backend/app/calculations/ratios.py` | `_verification` takes statuses instead of `Figure`s so both modules share it; no formula or rounding change |
| `backend/app/api/v1/schemas.py`, `catalog.py` | `ComparisonSideOut`, `ComparisonIssueOut`, `PeriodComparisonOut`; the endpoint |

Registry entry: `growth_abs_prior` version 1 = WS4-D9. Changing it needs a new version and a new
owner decision. Nothing is stored or cached.

### 12.3 Period-matching algorithm

```
previous_year(d)   = d with year − 1; 29 February → 28 February
pool               = latest revisions with the current statement's company, type, scope and
                     granularity (annual: fiscal_quarter null; quarterly: not null), current excluded
flow               = income statement or cash flow; balance sheet = one date
within(a, b)       = |a − b| ≤ 7 days

annual_yoy:     candidate if within(p.end, previous_year(c.end))
                and (balance sheet or within(p.end, c.start − 1 day))
                label must be: p.fiscal_year = c.fiscal_year − 1
quarterly_qoq:  flow:          candidate if within(p.end, c.start − 1 day)
                balance sheet: candidate if 80 ≤ (c.end − p.end) in days ≤ 100
                label must be: (c.fiscal_year, c.quarter − 1), or (c.fiscal_year − 1, 4) when c.quarter = 1
quarterly_yoy:  candidate if within(p.end, previous_year(c.end))
                label must be: (c.fiscal_year − 1, c.quarter)

0 candidates      → missing_previous_period, previous = null
2 or more         → ambiguous_previous_period, previous = null (never pick one)
1, label differs  → period_mismatch, previous = that candidate (shown, not used)
1, label agrees   → matched
```

Rows: for each current statement, one row per dictionary metric reported on the current statement
or, when matched, on the previous one. A metric neither side reports has no row. With `metric`
given, only that metric. ROE and ROA are never rows (W3-D6).

### 12.4 Statuses and reason precedence

Order: rank, then side (current before previous). Every issue is listed; ranks 9 run only when no
rank 0–8 issue exists.

| Rank | Code | Side | Status |
| --- | --- | --- | --- |
| 0 | `mixed_sample_and_real` (**PROPOSED**, W3-D11): a side's evidence classification differs from the company's, or the company has mixed statements | either | not_comparable |
| 1 | `missing_current_value` | current | not_comparable |
| 2 | `missing_previous_period` | previous | not_comparable |
| 3 | `ambiguous_previous_period` | previous | not_comparable |
| 4 | `period_mismatch` | previous | not_comparable |
| 5 | `missing_previous_value` | previous | not_comparable |
| 6 | `input_disputed_or_rejected` | either | not_comparable |
| 7 | `input_superseded` (evidence status) | either | not_comparable |
| 8 | `unit_or_currency_mismatch`: the two sides' units or currencies differ, or a currency metric's unit isn't its statement's currency | either | not_comparable |
| 9 | `prior_zero` | — | change_only |
| 9 | `sign_change` | — | change_only |

Ranks 1–9 of §5.1 are unchanged; only rank 0 is new (proposed). A newer revision whose evidence is
disputed, rejected or superseded is refused; the older revision is never used instead.

### 12.5 Vietnamese and English text

Reason texts are those of §5.1 (approved, W3-D10). New texts below join the glossary review.

| Key | vi | en |
| --- | --- | --- |
| Section title | So sánh giữa các kỳ (do ATLAS tính) | Period comparison (computed by ATLAS) |
| Section note | ATLAS so sánh số liệu báo cáo khi bạn xem; kết quả không phải số liệu doanh nghiệp công bố và không được lưu lại. | ATLAS compares reported figures when you view them; results aren't figures the company published and aren't stored. |
| Type: `annual_yoy` | Năm so với năm trước | Year on year |
| Type: `quarterly_qoq` | Quý so với quý trước | Quarter on quarter |
| Type: `quarterly_yoy` | Quý so với cùng kỳ năm trước | Same quarter last year |
| Scope filter | Tất cả / Hợp nhất / Riêng | All / Consolidated / Separate |
| Change column (W3-D3) | Thay đổi so với kỳ trước | Change versus previous period |
| Percent column | Thay đổi (%) | Change (%) |
| Direction | ▲ tăng / ▼ giảm / = không đổi | ▲ up / ▼ down / = unchanged |
| Seasonality (QoQ only, WS4-D9) | Số liệu quý có thể chịu ảnh hưởng mùa vụ, nên quý này khác quý trước không nhất thiết là xu hướng. | Quarterly figures can be seasonal, so a change from the previous quarter isn't necessarily a trend. |
| Restated (reused) | đã điều chỉnh (lần *n*) | restated (revision *n*) |
| No value on a side | Không có số liệu | No value |
| Display limit (W3-D7) | > 999,99 % / < −999,99 % | > 999.99% / < −999.99% |
| Disclosure | Cách tính; Giá trị đầy đủ: *percent* % (tỷ lệ *value*) | How it's calculated; Full value: *percent*% (ratio *value*) |
| Labels (reused from WS4-2) | Tính từ số liệu đã kiểm chứng / chưa kiểm chứng; Dữ liệu mẫu | Calculated from verified / unverified figures; Sample data |
| `mixed_sample_and_real` (reused, **PROPOSED** W3-D11) | Không so sánh được: dữ liệu mẫu và dữ liệu thật bị trộn lẫn | Not comparable: sample and real data are mixed |
| Pagination label | Phân trang so sánh giữa các kỳ | Period comparison pages |
| Empty | Chưa có báo cáo nào để so sánh theo cách này. | No statements to compare this way yet. |

### 12.6 UI placement and interaction

- **Place:** company page, a new section `id="comparisons"` after the calculated ratios (ROE/ROA)
  and before the sources. Server-rendered; no client JavaScript.
- **Controls:** two groups of links (`nav` with an accessible name; the active link has
  `aria-current="page"`): type (three options, default `annual_yoy` when `compare` is absent or
  invalid) and scope. Query parameters `compare`, `compare_scope`, `comparisons_page`. A control
  link keeps `statements_page` and `ratios_page` and drops `comparisons_page`; the language switch
  keeps all of them.
- **Table:** one semantic `<table>`: metric, current period and value, previous period and value,
  change, change (%). Below 640 px each row is a stacked block with the header text shown per cell,
  so nothing scrolls sideways at 375 px.
- **Direction:** the arrow is `aria-hidden`; the word next to it carries the meaning. Neutral text
  colour for every direction; no green, red or good/bad wording (W3-D5).
- **States:** `change_only` shows the change and the reason in the percent cell; `not_comparable`
  shows the reason across both cells. A missing side shows "Không có số liệu" / "No value". Never a
  0 or a bare dash.
- **Display limit:** when the integer part of `growth_percent` has more than three digits, the cell
  shows the limit text; the disclosure shows the full percentage and the ratio.
- **Notes:** the seasonality note under the controls for `quarterly_qoq`; the restated note next to a
  side with revision > 1.
- **Disclosure:** `<details>` per row: formula text, both periods and revisions, both values with
  WS3 source links to the exact pages (reuses `FigureSourceLine`).
- **Paging:** the existing `Pagination` with `param="comparisons_page"`, `anchor="comparisons"`,
  `showRange`, 20 per page.
- **Numbers:** no arithmetic in the browser. `formatFixed` for percentages; `formatDecimal` for
  values and changes, with U+2212 for negatives (audit A3-7, recommended).
- **No charts** (W3-D8).

### 12.7 Exact arithmetic and rounding

```
change  = _EXACT.subtract(current, prior)        # never the default 28-digit context (audit A3-10)
prior = 0                       → change_only, prior_zero
current < 0 < prior or prior < 0 < current → change_only, sign_change   # zero has no sign (W3-D2)
otherwise growth_value   = rounded_quotient(change, |prior|, 10, "even")
          growth_percent = rounded_quotient(_EXACT.multiply(change, 100), |prior|, 2, "up")
absolute_change = change quantised to 6 decimals (exact: inputs have 6); 0 is always "0.000000"
```

Inputs are `Numeric(38, 6)` below 10^32, so every step fits the 100-digit context; `Inexact` raises
instead of rounding. No `float` anywhere (guard test extended to the new modules).

### 12.8 Migration impact

None. No table, column, index, trigger or constraint changes; `alembic check` stays clean. The
existing index `ix_statements_company_period` covers the company filter.

### 12.9 Test fixtures and expected results (fictional)

Arithmetic, computed with the existing `rounded_quotient` and checked against an independent
`Fraction` oracle on 2026-11-26 (audit §5). Values are đồng unless noted.

| ID | Prior | Current | Status, reason | Change | Ratio | Percent |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | 100 | 120 | computed | 20 | 0.2000000000 | 20.00 |
| F2 | 100 | 80 | computed | −20 | −0.2000000000 | −20.00 |
| F3 | −100 | −150 | computed | −50 | −0.5000000000 | −50.00 |
| F4 | −100 | −50 | computed | 50 | 0.5000000000 | 50.00 |
| F5 | 0 | 30 | change_only, `prior_zero` | 30 | — | — |
| F6 | 50 | 0 | computed (W3-D2) | −50 | −1.0000000000 | −100.00 |
| F7 | −50 | 0 | computed (W3-D2) | 50 | 1.0000000000 | 100.00 |
| F8 | −40 | 60 | change_only, `sign_change` | 100 | — | — |
| F9 | 60 | −40 | change_only, `sign_change` | −100 | — | — |
| F10 | 0 | 0 | change_only, `prior_zero`; direction `unchanged` | 0 | — | — |
| F11 | 0.000001 | 1 | computed; display limit applies | 0.999999 | 999999.0000000000 | 99999900.00 |
| F12a | 200 | 200.01 | computed; percent tie, half-up | 0.01 | 0.0000500000 | 0.01 |
| F12b | 200 | 199.99 | computed; negative tie, away from zero | −0.01 | −0.0000500000 | −0.01 |
| F12c | 20000 | 20000.000005 | computed; ratio tie 2.5 → 2 (half-even) | 0.000005 | 0.0000000002 | 0.00 |
| F12d | 20000 | 20000.000003 | computed; ratio tie 1.5 → 2 (half-even) | 0.000003 | 0.0000000002 | 0.00 |
| F13 | 9 × 10^31 | 1 × 10^31 | computed; 32-digit values | −8 × 10^31 | −0.8888888889 | −88.89 |
| F14 | 3 | 4 | computed; non-terminating | 1 | 0.3333333333 | 33.33 |
| F15 | 3 | 5 | computed; non-terminating | 2 | 0.6666666667 | 66.67 |
| F16 | −0.000001 | −99999999999999999999999999999999.999999 | computed; 38-digit exact subtraction | −99999999999999999999999999999999.999998 | −99999999999999999999999999999999999998.0000000000 | −9999999999999999999999999999999999999800.00 |

Every computed result is also checked in the API as a fixed-point string: no exponent, no "-0".

Matching (dates inclusive; "BS" = balance sheet; all fictional):

| ID | Type | Current | Pool | Expected |
| --- | --- | --- | --- | --- |
| M1 | annual_yoy | FY2025 flow 2025-01-01..2025-12-31 | FY2024 2024-01-01..2024-12-31 | matched |
| M2 | annual_yoy | FY2025 flow 2024-04-01..2025-03-31 | FY2024 2023-04-01..2024-03-31 | matched (non-calendar) |
| M3 | annual_yoy | FY2024 flow 2023-03-01..2024-02-29 | FY2023 2022-03-01..2023-02-28 | matched (29 Feb → 28 Feb) |
| M4 | annual_yoy | FY2025 BS 2025-12-31 | FY2024 BS 2024-12-24 / 2024-12-23 | matched at 7 days; `missing_previous_period` at 8 |
| M5 | annual_yoy | FY2026 flow 2025-04-01..2026-03-31 | FY2024 2024-01-01..2024-12-31 (year-end moved) | `missing_previous_period` |
| M6 | annual_yoy | FY2025 BS 2025-12-31 | FY2024 BS 2024-12-28 and 2024-12-31 | `ambiguous_previous_period` |
| M7 | quarterly_qoq | Q2 FY2025 flow 2025-04-01..2025-06-30; Q1 FY2025 2025-01-01..2025-03-31 | Q1 FY2025; Q4 FY2024 2024-10-01..2024-12-31 | Q2 ↔ Q1 matched; Q1 ↔ prior Q4 matched |
| M8 | quarterly_qoq | Q2 FY2025 BS 2025-06-30 | Q1 BS at 80, 100, 79 and 101 days earlier (one per test) | matched at 80 and 100; `missing_previous_period` at 79 and 101 |
| M9 | quarterly_qoq | "Q3" FY2025 flow 2025-04-01..2025-06-30 | Q1 FY2025 2025-01-01..2025-03-31 | `period_mismatch`, previous shown |
| M10 | quarterly_yoy | Q2 FY2025 2025-04-01..2025-06-30 | Q2 FY2024 2024-04-01..2024-06-30; then the same dates labelled Q3 | matched; then `period_mismatch` |
| M11 | annual_yoy / quarterly_yoy | Annual and Q4 BS both at 2025-12-31 | Annual and Q4 BS both at 2024-12-31 | annual ↔ annual and Q4 ↔ Q4 only |
| M12 | annual_yoy | FY2025 consolidated | FY2024 separate only | `missing_previous_period` |
| M13 | annual_yoy | FY2025 | FY2024 revision 1 and revision 2 | revision 2 used and disclosed with the restated note; with revision 2's evidence rejected → `input_disputed_or_rejected`, never revision 1 |
| M14 | quarterly_qoq | Q1 FY2026 cash flow | Q4 FY2025 cash flow absent (only year to date printed) | rows with `missing_previous_period`; no value derived |
| M15 | annual_yoy | Real company with a legacy sample-evidence statement (triggers disabled in the test) | — | `mixed_sample_and_real`, `input_verification` null |
| M16 | annual_yoy | Previous unit `VND/share` for a currency metric (direct row) | — | `unit_or_currency_mismatch` |
| M17 | annual_yoy | Previous evidence disputed; then superseded | — | `input_disputed_or_rejected`; `input_superseded` |
| M18 | annual_yoy | Current has `net_revenue`, previous lacks it; previous has `gross_profit`, current lacks it | — | `missing_previous_value`; `missing_current_value` |

API (A) and UI (U):

| ID | Check |
| --- | --- |
| A1 | Response shape and OpenAPI schema of §12.1 |
| A2 | 404 unknown company; 422 for missing or bad `type`, bad `scope`, unknown `metric` (incl. `roe`), `limit` 0 or 101, `fiscal_year` 1989 |
| A3 | Filters `scope`, `metric`, `fiscal_year`; paging with `total`; offset past the end returns no items and the same `total` |
| A4 | Both sides carry statement id, revision, period and WS3 source with the exact page |
| A5 | `reason` = `issues[0].code`; all issues listed in §12.4 order |
| A6 | A trap that fails on any `float` in the response; fixed-point strings |
| A7 | Every dictionary metric can appear; ROE and ROA never do |
| A8 | No `verification_status` on a comparison; `input_verification` per §12.1 |
| A9 | Read-only: no row count changes; query count fixed for 1 and 10 years of data |
| U1 | vi and en key parity for every new text (existing parity test) |
| U2 | Section texts follow W3-D3; the word "tăng trưởng" / "growth" is not shown |
| U3 | Arrow `aria-hidden` plus a direction word; same colour class for all directions |
| U4 | Keyboard: controls and disclosures reachable and operable; visible focus |
| U5 | `change_only` and `not_comparable` rows show reason texts, never 0 or a bare dash |
| U6 | Seasonality note only for `quarterly_qoq`; restated note on the side with revision > 1 |
| U7 | Display limit at the approved threshold; full value in the disclosure |
| U8 | No chart element or chart library |
| U9 | 375 px: no horizontal scroll; desktop table readable |
| U10 | Route check: every rendered comparison equals the API in vi and en; paging links keep the other lists' pages |

### 12.10 Performance

Per request: company, mixed check, one statements query with metrics (`selectinload`) and evidence
(`joinedload`): a fixed number of queries, whatever the number of years (test A9). Pairing groups
statements by (type, scope) and looks only within a group, so work grows with the number of a
company's statements. All rows of one company and type are built, then sliced; a `shortcut:` comment
names that limit (one company has at most a few hundred statements). The company page gets one more
API call, made in parallel with the others; paging keeps the rendered table at 20 rows.

### 12.11 Backward compatibility

New endpoint and new response models only. Existing endpoints, response shapes, ROE/ROA formulas,
rounding and their tests are unchanged; `_latest_annual` and `_verification` are refactored with
WS4-2's tests as the guard. Existing URLs keep working; new query parameters are optional. If A3-7
is accepted, negative reported values display with U+2212 instead of a hyphen (display only).

### 12.12 Security and data governance

- Read-only GET; parameters validated (§12.1); no new URL handling (WS3 `linkable_url`).
- No writes, caching or stored comparisons; no `float`.
- Sample and real stay isolated: database triggers (`8de09b58f4c2`) plus the engine check (rank 0).
- A comparison is never `VERIFIED`; `input_verification` describes the inputs only.
- No YTD conversion; no inferred values; no fallback to older revisions.
- Fictional fixtures only (`example.test`, `TST` tickers); nothing under `data/`; no real company,
  ticker or private G2 evidence in code, tests or docs.
- Isolated Docker stack and ports for checks; the user's stack and volumes are not touched.

### 12.13 Measurable acceptance criteria

1. F1–F16 produce exactly the values in §12.9, and an oracle property test agrees on at least 500
   random fictional pairs.
2. M1–M18 give exactly the expected match or reason.
3. A1–A9 and U1–U10 pass.
4. Backend: `ruff format --check`, `ruff check`, `mypy` strict, full `pytest` (≥ 314 earlier tests
   plus the new ones, 0 failures), `alembic check` clean, `pip-audit` clean.
5. Frontend: lint, `tsc`, `node --test` (≥ 31 earlier plus new), production build, `npm audit` 0.
6. Isolated Docker stack from a fresh volume: migrations to head, health checks, route check online
   and offline in vi and en, browser pass at desktop and 375 px.
7. No migration file added; no file under `data/` changed.
8. Checklists recounted from item rows; nothing marked PASS without its evidence.

### 12.14 Expected changed files (after approval)

Backend: `app/calculations/comparisons.py` (new), `app/calculations/comparison_service.py` (new),
`app/calculations/service.py`, `app/calculations/ratios.py` (shared helper only),
`app/api/v1/schemas.py`, `app/api/v1/catalog.py`, `tests/test_comparisons.py` (new),
`tests/test_comparison_api.py` (new), `tests/test_ratios.py` (float guard).
Frontend: `src/lib/api-core.ts` (types, display-limit helper, minus sign), `src/lib/api-core.test.ts`,
`src/components/period-comparison.tsx` (new), `src/app/[lang]/companies/[id]/page.tsx`,
`src/i18n/vi.ts`, `src/i18n/en.ts`, `scripts/check-routes.mjs`.
Docs: ARCHITECTURE, README (API tables), GLOSSARY, VERIFICATION_WORKFLOW (A3-15), this plan,
WS4_3_CHECKLIST, WS4_CHECKLIST, PHASE_2_CHECKLIST.

### 12.15 Items for the owner before implementation

| ID | Item | Proposal | Status |
| --- | --- | --- | --- |
| W3-D11 | Mixed sample and real inputs (audit A3-1) | Add `mixed_sample_and_real` at rank 0, status `not_comparable`, with the WS4-2 texts; `input_verification` null | **PROPOSED — REQUIRES OWNER APPROVAL** |
| W3-D7 threshold | Display limit value (audit A3-2) | Above 999,99 % in absolute value: "> 999,99 %" / "< −999,99 %"; full value in the disclosure; API unaffected | **PROPOSED — REQUIRES OWNER APPROVAL** |
| A3-7 | Minus sign for reported values | U+2212 in `formatDecimal` (site-wide display) | Recommendation; owner may narrow it to comparisons |
| A3-5 | Row generation | Rows for metrics reported on at least one side | Plan detail within W3-D6; owner may object |
| W3-B3 | Go-ahead to implement | — | Not given |

**Update (2026-11-26):** W3-D11, the W3-D7 threshold, A3-5 and A3-7 were approved as proposed by
the owner (PRODUCT_DECISIONS §2e). The "PROPOSED" marks in §12.0–§12.6 now read as approved.
W3-B3 is still not given.
