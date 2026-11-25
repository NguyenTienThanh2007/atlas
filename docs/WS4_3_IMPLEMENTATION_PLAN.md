# WS4-3: Financial period comparison plan

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
