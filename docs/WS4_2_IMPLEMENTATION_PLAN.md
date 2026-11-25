# WS4-2: ROE and ROA implementation plan

**Status: DESIGN APPROVED and implementation authorised 2026-11-25. Implemented on branch
`feat/ws4-2-roe-roa` (uncommitted);** evidence in [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md). No code, schema, migration or data change is
part of this document. The formulas are already approved (WS4-D1, D2, D3, D7, D8, D11, D12 in
[PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d). This plan only says how to build them. It adds no
new formula, metric or decision; the few design choices that need the owner are listed in §12.

| | |
| --- | --- |
| Written | 2026-11-25 |
| Code inspected | `main` @ `105869f` (WS4-1 merged, PR #6) |
| Parent plan | [WS4_FINANCIAL_INTELLIGENCE_PLAN.md](WS4_FINANCIAL_INTELLIGENCE_PLAN.md) §4, §5, §9, §10, §13 (step WS4-2/3/4 for ROE and ROA) |
| Checklist | [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) |
| Phase 2 items | P2-5.11 (ROE), P2-5.12 (ROA), part of P2-5.17 (reported vs calculated) |

## 0. Approved rules this plan implements (unchanged)

| Rule | Source |
| --- | --- |
| Consolidated ROE = `net_profit_parent` ÷ average `equity_parent` | WS4-D1 |
| Separate ROE = `net_profit` ÷ average `total_equity` | WS4-D1 |
| ROA = `net_profit` ÷ average `total_assets`, banks and non-banks, per scope | WS4-D2 |
| Average = (opening + closing) ÷ 2; no opening balance → not computable | WS4-D3 |
| Annual statements only | WS4-D1, D2 |
| `equity_parent` only as reported; never derived, never replaced by `total_equity`; missing → consolidated ROE not computable | WS4-D12 |
| Calculated values have no verification status; never VERIFIED; labelled by their inputs; not computed if an input is disputed or rejected | WS4-D7 |
| Ratios shown as % with 2 decimals; rounding on decimal strings, never floats | WS4-D8 |
| Shown with an "unverified inputs" label in the private pilot; never public before G1 | WS4-D11 |
| Negative or zero denominator → not meaningful (`equity_not_positive`, `assets_not_positive`) | WS4 plan §4.3, §5.3 (approved with D1, D2) |
| Ratio rounded once, half-even, 10 decimal places in the API | WS4 plan §4.3 |
| Opening balance = end of FY *t*−1 (previous report or comparative column); period ends that move by more than 7 days → not computable | WS4 plan §4.3 |
| Latest revision of each input; restatements disclosed | WS4 plan §4.3 |

## 1. What exists today (inspected)

- `financial_statements`: one row per statement and revision; latest revision = no other row has
  `supersedes_id` pointing at it (same rule as `GET /companies/{id}/financial-statements` in
  `backend/app/api/v1/catalog.py`). Annual = `fiscal_quarter IS NULL`. Balance sheets have
  `reporting_period_start = reporting_period_end` (importer rule). Each statement has exactly one
  `source_evidence` row carrying the verification status.
- `financial_metrics.value`: `Numeric(38, 6)`, exact `Decimal`, full units; `unit` is `VND`,
  `VND/share` or `shares`; currency is VND only (importer).
- `MetricSourceOut.for_figure(evidence, page)` (`backend/app/api/v1/schemas.py`) already builds the
  per-figure provenance with safe links (WS3). WS4-2 reuses it unchanged.
- Exact arithmetic precedent: `Context(prec=60, traps=[Inexact])` in `backend/app/ingestion/importer.py`.
- Metric dictionary 1.1.0 (`metric_name_vi`, `metric_name_en`) supplies input labels.
- No calculated metric exists anywhere (`grep -rniwE "roe|roa"` finds only prose in the dictionary notes).
- Note: the request named `backend/app/schemas.py`; the API schemas actually live in
  `backend/app/api/v1/schemas.py`. There is no other schema module.

## 2. Calculation service architecture

```
GET /api/v1/companies/{id}/calculated-metrics
        │  (catalog.py: validate params, 404 for unknown company)
        ▼
app/calculations/service.py   load inputs: 2 queries, latest annual revisions only
        │                     (income statements + balance sheets, with metrics and evidence)
        ▼
app/calculations/ratios.py    pure functions, no database, no I/O
        │                     registry (frozen, versioned) + compute() with exact Decimal
        ▼
CalculatedMetricOut (schemas.py)   decimal strings or null; reason codes; inputs with WS3 source
```

- **`ratios.py` (pure):** the formula registry and `compute(formula, numerator, opening, closing)`.
  Takes plain values (Decimal, unit, evidence status); returns a result object. Fully unit-testable
  without a database.
- **`service.py` (read-only):** selects inputs for one company and builds one result per
  (fiscal year, scope, formula). Never writes, never caches, never commits.
- **Separation:** nothing is written to `financial_metrics` or any table. Reported figures keep
  their endpoint and shape; calculated values have their own endpoint and schema.
- **Size:** two new modules, one endpoint, one response schema, one frontend section. No new
  dependency.

## 3. Formula registry design

A tuple of frozen dataclasses in `ratios.py`. Changing a formula means a new `formula_version` and a
new owner decision; tests pin the registry.

| `code` | `formula_id` | `version` | Scope | Numerator (income statement, FY *t*) | Denominator (balance sheets, end of FY *t*−1 and FY *t*) |
| --- | --- | --- | --- | --- | --- |
| `roe` | `roe_parent_avg_equity` | 1 | consolidated | `net_profit_parent` | `equity_parent` |
| `roe` | `roe_separate_avg_equity` | 1 | separate | `net_profit` | `total_equity` |
| `roa` | `roa_avg_assets` | 1 | consolidated and separate (computed per scope) | `net_profit` | `total_assets` |

Each entry also holds: names (`name_vi` "Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE)" / `name_en`
"Return on equity (ROE)"; ROA likewise), formula text in vi and en, the non-positive reason
(`equity_not_positive` or `assets_not_positive`). The denominator code is fixed per entry: there is
no fallback list, so `total_equity` can never stand in for `equity_parent` (D12).

## 4. Input selection

For company *c*, scope *s*, fiscal year *t*. Every input is the **latest revision** of an
**annual** statement (`fiscal_quarter IS NULL`) of the same company and scope. "Latest" means no
other statement has `supersedes_id` pointing at it, the same rule as
`GET /companies/{id}/financial-statements`.

### 4.1 Matching algorithm

| Step | Input | Rule |
| --- | --- | --- |
| 1 | Income statement (numerator) | `statement_type = income_statement`, `fiscal_year = t`. The importer guarantees at most one latest annual income statement per company, scope and year, spanning 360–371 days |
| 2 | Closing balance sheet | `statement_type = balance_sheet`, `fiscal_year = t`, `reporting_period_end` **equal to** the income statement's `reporting_period_end`. Both come from the same annual report, so the dates must agree exactly |
| 3 | Expected opening date | *E* = income statement `reporting_period_start` − 1 day, i.e. the end of FY *t*−1 when the year runs without a gap |
| 4 | Opening candidates | `statement_type = balance_sheet`, `fiscal_year = t − 1` (never another year), same scope, and `reporting_period_end` within **±7 days of *E*** (the approved 7-day alignment rule, WS4 plan §4.3) |
| 5 | Opening choice | Exactly one candidate → use it. None → `missing_opening_balance`. More than one → `ambiguous_opening_balance` (not computed; ATLAS never picks one) |

Why this reconciles the approved rules:

- **"Opening = end of the preceding fiscal year":** step 4 requires the FY *t*−1 label and a date at
  the start of FY *t*, so a balance sheet of any other year can never be paired.
- **7-day rule:** a prior-year end that moved by up to 7 days (for example, a company closing on the
  last Friday of the year) still matches. A larger shift (a fiscal-year change) gives no candidate,
  so the result is `missing_opening_balance`.
- **Previous report or comparative column:** both are imported as a FY *t*−1 balance sheet. The
  importer's identity rule (company, type, scope, year, quarter, period end, revision) allows only
  one row per date and revision. A second document for the same date either matches the stored
  figures exactly (unchanged), or is a conflict, or must be imported as a restatement (a new
  revision). So at most one latest balance sheet can exist per date; step 5 only has to handle
  different dates inside the window.
- **Scope:** every query filters on the one scope, so consolidated and separate are never mixed.
- **Quarterly balance sheets** (`fiscal_quarter` 4 on the same date) are never candidates.

### 4.2 Evidence and revision semantics

Each statement's status is its `source_evidence.verification_status` (WS1). The latest revision is
taken as it is. **ATLAS never falls back to an older revision**, whatever the latest one's status.

| Status of a selected input | Used? | Effect on the result |
| --- | --- | --- |
| `verified` | Yes | Counts toward `all_verified` |
| `unverified` | Yes | Result is `some_unverified` |
| `sample` | Yes, only for a sample company | Result is `sample`. Database rules already stop sample and real records from mixing within one company, so a result can't combine them |
| `disputed` | **No** | `input_disputed_or_rejected`; not computed |
| `rejected` | **No** | `input_disputed_or_rejected`; not computed |
| `superseded` | **No** | `input_superseded`; not computed. The older revision is not used instead |

A statement that a newer revision replaced is never selected, even if that newer revision is
disputed or rejected: the result is then refused, not computed from the older figures.

## 5. Decimal and rounding rules (audited)

Audit on `main` @ `105869f`:

| Check | Finding |
| --- | --- |
| Input type | `financial_metrics.value` is `Numeric(38, 6)`, read as `Decimal`. OK |
| Average exactness | Inputs are below 10^32 with 6 decimals. The sum has at most 39 digits; halving adds at most one decimal (40 digits). `Context(prec=60, traps=[Inexact])` therefore always gives the exact average (checked: two values of 10^32 − 0.000001 and the half-unit case 0.0000015). **The average is never rounded** |
| JSON form | **Issue found.** Pydantic serialises `Decimal` with `str()`, which uses exponent notation for small or zero values with more than 6 decimals: `Decimal("0E-10")` → `"0E-10"`, `Decimal("1E-10")` → `"1E-10"`, `Decimal("-0E-10")` → `"-0E-10"`, `Decimal("5E-7")` → `"5E-7"` (checked 2026-11-25). Today's reported figures are not affected (always scale 6). Calculated values and averages would be |
| Frontend formatter | **Issue found.** `formatDecimal` accepts only plain digits (an exponent string is shown raw) and drops trailing zeros (`"18.30"` → `18,3`), so it can't show a fixed 2-decimal percentage |

Rules for WS4-2:

1. Arithmetic only with `Decimal` (no `float`, no `int()` on money). The ratio uses
   integer-valued `Decimal`s in an exact context (`prec=100`, `Inexact` trapped): with
   *N* = numerator × 10^7 and *D* = average × 10^7, the quotient and remainder of
   *N* × 10^10 ÷ *D* (`divmod`) are exact, and the rounding is decided from the remainder.
2. **One rounding per output:** `value` = 10 decimals, half-even (ties to even), from the exact
   quotient; `percent` = 2 decimals, half-up (ties away from zero, the same for negatives), also from
   the exact quotient, never from the rounded `value`.
3. The denominator is checked (≤ 0 → refused) **before** any division, so no division by zero can
   happen.
4. **Fixed-point JSON:** calculated decimals (`value`, `percent`, `denominator_average`) are
   serialised with `format(d, "f")`, always with their fixed number of decimals (`value` 10,
   `percent` 2, `denominator_average` 7). Negative zero is normalised to zero
   (`"-0.0000000000"` never appears).
5. **No browser arithmetic:** the frontend gets `percent` as a string such as `"18.30"` and only
   swaps the decimal separator and adds "%". A new `formatFixed` helper keeps the given decimals; it
   does not round, parse or compute.
6. A loss gives a negative ratio. Very large ratios (tiny positive denominator) are returned as
   they are, exactly, with no cap.

## 6. API response schema proposal

`GET /api/v1/companies/{id}/calculated-metrics?fiscal_year=&scope=` → `Page[CalculatedMetricOut]`,
ordered by fiscal year (newest first), scope, `code`. There is one result per formula for each
latest annual income statement; a year without one has no result. Unknown company → 404.

```json
{
  "code": "roe",
  "kind": "calculated",
  "formula_id": "roe_parent_avg_equity",
  "formula_version": 1,
  "name_vi": "Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE)",
  "name_en": "Return on equity (ROE)",
  "formula_text_vi": "Lợi nhuận sau thuế của cổ đông công ty mẹ ÷ bình quân vốn chủ sở hữu của cổ đông công ty mẹ đầu kỳ và cuối kỳ",
  "formula_text_en": "Net profit attributable to parent ÷ average of opening and closing equity attributable to owners of the parent",
  "fiscal_year": 2025,
  "scope": "consolidated",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "status": "not_computable",
  "reason": "missing_input",
  "value": null,
  "percent": null,
  "denominator_average": null,
  "inputs": [
    {"role": "numerator", "metric_code": "net_profit_parent", "metric_name_vi": "…", "metric_name_en": "…",
     "statement_id": "…", "revision": 1, "period_end": "2025-12-31", "value": "…", "unit": "VND",
     "reported_value": "…", "reported_scale": 1000000, "source": {"…": "WS3 MetricSourceOut"}}
  ],
  "issues": [
    {"code": "missing_input", "role": "denominator_closing", "metric_code": "equity_parent", "period_end": "2025-12-31"},
    {"code": "missing_opening_balance", "role": "denominator_opening", "metric_code": "equity_parent", "period_end": "2024-12-31"}
  ],
  "input_verification": "some_unverified"
}
```

Figures are elided on purpose: this shows the shape, not any company's numbers.

- `status` ∈ `computed`, `not_computable`. When computed, `reason` is `null` and `issues` is empty.
- `role` ∈ `numerator`, `denominator_opening`, `denominator_closing`.
- `inputs` lists every input that was found (computed or not), each with its WS3 `source`.
- `issues` lists **every** problem found, in precedence order; `reason` = `issues[0].code`.
- `input_verification` ∈ `all_verified`, `some_unverified`, `sample`, or `null` when no input was
  found. It describes the inputs only. There is no `verification_status` field on a calculated
  value, and no value is ever `verified`.

## 7. Provenance chain

Every computed value links back to three reported figures, each with: statement id and revision,
period end, the exact stored value, the as-reported value and scale, the document title, the safe
link and the page (WS3 `MetricSourceOut.for_figure`), and the evidence status. The formula id and
version identify the rule. Same inputs (same statement ids and revisions) → same output, so any
value can be recomputed by hand from the linked pages.

## 8. Reason codes and precedence

All issues are collected, then sorted by this precedence. `reason` is the first. Every reason
refuses the calculation (`value`, `percent` and `denominator_average` are `null`). Value checks
(rank 7) run only when no issue of rank 1–6 exists, because they need all three figures.

| Rank | `code` | Triggered by (role) | When | Refused | vi (proposed) | en (proposed) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `missing_input` | numerator, denominator_closing | Income statement, closing balance sheet, or the needed figure in either is absent. Includes `equity_parent` absent (D12); `total_equity` is never used instead | Yes | Không tính được: thiếu số liệu đầu vào ({chỉ tiêu}) | Not calculable: missing input ({metric}) |
| 2 | `missing_opening_balance` | denominator_opening | No opening candidate (§4.1), or the candidate lacks the denominator figure (D3) | Yes | Không tính được: thiếu số dư đầu kỳ | Not calculable: opening balance missing |
| 3 | `ambiguous_opening_balance` | denominator_opening | More than one opening candidate within ±7 days | Yes | Không tính được: có nhiều hơn một số dư đầu kỳ phù hợp | Not calculable: more than one possible opening balance |
| 4 | `input_disputed_or_rejected` | the input concerned | Its evidence is `disputed` or `rejected` (D7) | Yes | Không tính được: số liệu đầu vào đang xem xét lại hoặc bị loại | Not calculable: an input is under review or rejected |
| 5 | `input_superseded` | the input concerned | Its evidence is `superseded` | Yes | Không tính được: tài liệu nguồn đã được thay thế | Not calculable: a source document was superseded |
| 6 | `unit_mismatch` | the input concerned | Its unit is not its statement currency | Yes | Không tính được: đơn vị không khớp | Not calculable: units do not match |
| 7 | `equity_not_positive` | denominator_opening / closing (or the average) | ROE: opening, closing or average equity ≤ 0 | Yes ("not meaningful") | Không có ý nghĩa: vốn chủ sở hữu không dương | Not meaningful: equity is not positive |
| 7 | `assets_not_positive` | denominator_opening / closing (or the average) | ROA: opening, closing or average assets ≤ 0 | Yes ("not meaningful") | Không có ý nghĩa: tổng tài sản không dương | Not meaningful: total assets are not positive |

Ties within a rank are ordered by role: numerator, denominator_closing, denominator_opening. A
missing value is never treated as zero, and no input is ever substituted or estimated. Existing
glossary terms are reused ("Đang xem xét lại", "Bị loại").

## 9. Test matrix

All data fictional (`example.test`, `TST` tickers), created inside tests only.

| Area | Cases |
| --- | --- |
| Registry | Exactly three entries as in §3; ids and versions pinned; consolidated ROE denominator is `equity_parent` only |
| Exact arithmetic | Hand-checked ratios as exact strings; inputs near 10^32; opening + closing odd (average with 7 decimals, not rounded); repeating quotient (÷3, ÷7); a tie at the 11th decimal (half-even) and at the 3rd percent decimal (half-up); a case where rounding the 10-decimal `value` to 2 would differ from rounding the exact quotient; a tie on a negative ratio |
| JSON form | Zero numerator → `"0.0000000000"` and `"0.00"`; ratio 10^-10 → `"0.0000000001"`; tiny negative → no `"-0…"`; average with 7 decimals is fixed-point; no `E` anywhere in the response; JSON parsed with a float trap |
| Signs and size | Loss year → negative ROE; equity ≤ 0 at opening, closing or average (e.g. opening −10, closing +4); assets 0; tiny positive denominator → large exact ratio |
| Missing data | No income statement; missing numerator figure; missing closing balance sheet; `equity_parent` missing while `total_equity` present (refused, never substituted); no opening balance; opening present without the figure |
| Simultaneous issues | Numerator and opening both missing → `reason = missing_input`, both in `issues` in order; missing opening plus a rejected closing → `missing_opening_balance` first, both listed; rejected and superseded inputs together → `input_disputed_or_rejected` first; non-positive denominator not reported while another issue exists |
| Opening selection | Calendar FY; non-calendar FY (ends 31 March); opening dated within ±7 days → used; 8 days away → `missing_opening_balance`; two candidates in the window → `ambiguous_opening_balance`; a FY *t*−2 or FY *t* balance sheet near the date → never a candidate; quarterly balance sheet on the date → ignored; closing date differs from the income statement end → `missing_input` |
| Scope | Consolidated and separate computed independently; a separate opening balance never pairs with a consolidated closing; separate ROE uses `total_equity` |
| Revisions and evidence | Restated balance sheet → latest revision used and returned; each of `verified`, `unverified`, `sample` used with the right label; `disputed`, `rejected`, `superseded` on the latest revision → refused, and the older revision (with good evidence) is **not** used; reviews created through the WS1 path |
| Sample isolation | Sample company → `input_verification = sample`; real company results never include sample inputs (database rules) |
| API | Shape and OpenAPI; 404 unknown company; filters; pagination; no private fields; no `verification_status`; nothing written (row counts unchanged); fixed query count |
| Frontend | `formatFixed` keeps decimals (vi `18,30%`, en `18.30%`, `-5,00%`); every reason label in vi and en; key parity; no `Number()` or `parseFloat` on values; route check compares rendered percentages with the API strings |
| Regression | All 224 backend and 25 frontend tests stay green; WS3 provenance tests unchanged |
| Guard | The calculation modules contain no `float(` (test) |

## 10. Frontend presentation (vi / en)

- New section below the statements on the company page: **"Chỉ số tính toán (do ATLAS tính)"** /
  **"Calculated ratios (computed by ATLAS)"**, visually separate from reported figures.
- One row per (year, scope, ratio): name, value `18,30%` / `18.30%` from `percent` via `formatFixed`
  (keeps the 2 decimals; no arithmetic), and the label
  **"Tính từ số liệu chưa kiểm chứng"** / **"Calculated from unverified figures"** (or the verified
  or sample label).
- A disclosure **"Cách tính"** / **"How it's calculated"**: formula text, the three inputs with
  their values and WS3 source links to each page, the revision used.
- Not computable: the reason text from §8, never "0", never a bare dash.
- No arithmetic in the browser; only formatting of the API's strings (`formatDecimal` is not used for
  percentages because it drops trailing zeros). New strings go into both
  dictionaries (parity test) and into the glossary review (P2-4.12).

## 11. Security and data integrity

- Read-only endpoint; inputs validated (UUID path, `fiscal_year` 1990–2200, `scope` enum); unknown
  company 404.
- Fixed number of queries per request (no per-result query); bounded by the company's statement count.
- No writes, no caches, no background jobs; nothing stored, so no stale calculated values.
- Exact `Decimal` only; the response model types values as `Decimal`, serialised as strings.
- Provenance reuses WS3's `linkable_url` checks; no new URL handling; no private evidence fields.
- Sample and real data can't mix (existing database rules), and sample inputs are labelled `sample`.
- Display stays private-pilot only: no deployment exists, and public display waits on G1.

## 12. Design points (approved by the owner 2026-11-25)

| # | Choice | Proposal |
| --- | --- | --- |
| 1 | Endpoint | Separate `GET /companies/{id}/calculated-metrics`, keeping reported and calculated apart |
| 2 | Reason codes, precedence and texts | The eight codes, ranks and vi/en texts of §8, with every issue listed in `issues` |
| 3 | Number form | `value` = ratio with 10 decimals (half-even), `percent` = 2 decimals (half-up), both from the exact quotient, fixed-point strings, no exponent, no negative zero |
| 4 | Opening balance | FY *t*−1 annual balance sheet, same scope, latest revision, dated within ±7 days of the day before the period start; none → `missing_opening_balance`; several → `ambiguous_opening_balance`; closing must match the income statement's end date exactly |
| 5 | Evidence states | `verified`, `unverified`, `sample` used and labelled; `disputed`, `rejected`, `superseded` refused; never fall back to an older revision |
| 6 | Ratio names | "Tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE)" / "Tỷ suất lợi nhuận trên tổng tài sản (ROA)"; "Return on equity (ROE)" / "Return on assets (ROA)" |

## 13. Dependencies and blockers

| Item | State | Effect on WS4-2 |
| --- | --- | --- |
| WS4-D1, D2, D3, D7, D8, D11, D12 | Approved | Ready |
| Metric dictionary 1.1.0 with `equity_parent` | Merged (PR #6) | Ready |
| Owner review of this plan (§12) | Approved 2026-11-25 | Go-ahead to implement still pending |
| Glossary native-speaker review (P2-4.12) | Pending | New labels join the review; does not block code |
| Q-3 independent reviewer | Open | All real inputs stay unverified; results carry the unverified label |
| G1 legal opinion | Open | No public display of real results |
| Per-company bank / non-bank type | Not approved (schema change) | Not needed: ROE and ROA apply to both kinds |
| Real data | None in the repo | Tests use fictional data only |
| Q-7, Q-8 | Open | No effect on the code |

## 14. Implementation sequence (after owner approval)

1. **WS4-2a** `ratios.py`: registry and pure `compute()`, with exact-arithmetic unit tests.
2. **WS4-2b** `service.py`: input selection (latest annual revisions, date matching), with
   database tests for missing data, periods, scopes, revisions and verification.
3. **WS4-2c** Endpoint and `CalculatedMetricOut`, OpenAPI, API tests; docs (`ARCHITECTURE.md`, README).
4. **WS4-2d** Frontend section, `formatPercent`, vi/en strings, route check extension, browser pass
   (desktop and 375 px) on an isolated stack with fictional fixtures.
5. **WS4-2e** Full verification (backend, frontend, Docker), checklist update, owner review, PR.

No migration at any step. Growth (D9) and missing-data UI states (D6) are later WS4 steps, not WS4-2.
