# WS4: Financial intelligence foundation (plan)

**Status: OWNER DECISIONS RECORDED 2026-11-24; NOT IMPLEMENTED.** The project owner decided
WS4-D1 to D11 on 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d; outcome per
decision in §12). Two parts were **not approved**: the sign-convention field (G-3, with G-5 to
G-9) and missing-data Phase B. No formula, dictionary change, schema change or API change has been
implemented; implementation needs the owner's go-ahead.

| | |
| --- | --- |
| Written | 2026-11-24 |
| Code inspected | `main` @ `4be30b7` (after PRs #3, #4, #5); WS4-1 merged as `105869f` (PR #6, 2026-11-25) |
| Phase 2 items served | P2-5.1, P2-5.11 to P2-5.17 ([PHASE_2_CHECKLIST.md](PHASE_2_CHECKLIST.md)) |
| Acceptance checklist | [WS4_CHECKLIST.md](WS4_CHECKLIST.md) |
| WS4-2 (ROE, ROA) | [WS4_2_IMPLEMENTATION_PLAN.md](WS4_2_IMPLEMENTATION_PLAN.md), [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md) |
| Preserved | A-1 to A-11, AM-1, EX-1 to EX-3 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md)); metric dictionary 1.0.0 unchanged (exit audit F-1, F-2 stay OPEN until the approved changes ship); Q-3, Q-7, Q-8 stay OPEN; G1 not passed. Q-5 resolved by WS4-D4 |

**Goal.** Make financial figures understandable, comparable and computable in a way that is exact,
transparent and checkable, without inventing numbers. ATLAS prefers an honest missing value over an
invented one.

**Non-goals.** No real data, no new metrics in production, no scraping, no public launch, no
investment advice, no price-based ratios (P/E, P/B need prices, which are out of the MVP under A-3).

---

## 1. Summary

All rows below were approved on 2026-11-24 as written, except where §12 says otherwise.

| Topic | Specification | Decision |
| --- | --- | --- |
| ROE | `net_profit_parent` ÷ average of opening and closing **equity attributable to the parent**, annual only. Needs one new reported metric; until then ROE is "not computable" for consolidated statements | WS4-D1, D3 |
| ROA | `net_profit` ÷ average of opening and closing `total_assets`, same scope, annual only. Same formula for banks | WS4-D2, D3 |
| Banks | Initial pilot needs: N/A marking of `net_revenue` and `gross_profit`, plus `net_interest_income`, ROE, ROA. NPL, provisions and credit growth come later | WS4-D4, D5 (Q-5) |
| Missing data | Seven availability states, separate from verification status. Phase A uses only what today's schema can prove | WS4-D6 |
| Calculated values | Computed at read time with exact `Decimal`, never stored, never labelled VERIFIED; they carry their inputs' provenance | WS4-D7 |
| Display | Exact value always available; display in tỷ đồng / triệu đồng with half-up rounding done on decimal strings | WS4-D8 |
| Comparison | Only same company, scope, statement type, granularity and currency; anything else refused or warned | WS4-D9 |

---

## 2. Existing implementation (audit)

What exists on `main` @ `4be30b7`, and what WS4 must stay compatible with.

### 2.1 Data model (`backend/app/models.py`)

| Field | Meaning today | WS4 relevance |
| --- | --- | --- |
| `financial_statements.statement_type` | `income_statement`, `balance_sheet`, `cash_flow` | Ratio inputs come from two statement types and must be paired |
| `reporting_period_start` / `_end` | Span for income and cash-flow; **one date** for balance sheets (start = end, importer rule) | Opening balance = balance sheet at the prior period end |
| `fiscal_year`, `fiscal_quarter` | Year named by the calendar year it ends in; quarter 1–4 or null (annual). Quarters span 80–100 days, so **quarterly figures are stand-alone quarters, not year-to-date** | Q4 is its own quarter; TTM needs four quarters |
| `scope` | `consolidated` or `separate` | Never mixed inside a ratio |
| `currency` | Format-checked; the importer accepts **VND only** | Cross-currency comparison cannot arise yet |
| `revision`, `supersedes_id` | Restatement = new revision; history append-only | Use latest revision; disclose revision used |
| `source_evidence_id` | One document per statement (non-null) | Provenance of every input |
| `financial_metrics.value` | `Numeric(38, 6)` full units, **NOT NULL** | A metric is either present with a value or has no row; there is no "null value" today |
| `reported_value`, `reported_scale` | As printed, scale ∈ {1, 1 000, 1 000 000}; DB CHECK `value = reported_value × reported_scale` | Display can always show the printed figure |
| `source_page` | Page of the figure; required for real figures (trigger) | Calculated values link to each input's page |
| `unit` | `VND`, `VND/share`, `shares` | Only `VND` amounts may enter ROE/ROA |
| Verification status | On the **evidence** row (`unverified`, `verified`, `disputed`, `rejected`, `superseded`, `sample`); changed only through append-only reviews with curator ≠ reviewer (WS1) | A statement's figures share their evidence's status |

### 2.2 Import and arithmetic (`backend/app/ingestion/`)

- Required `amount_scale` (dong, nghin_dong, trieu_dong); exact multiplication in a 60-digit context
  that raises on rounding; `|value| < 10^32` (`importer.py`).
- A metric must belong to the statement's type (`test_invalid_metrics_are_rejected`); per-share and
  share counts are never scaled (`test_per_share_and_share_counts_are_not_scaled`).
- Period rules and overlap per granularity (WS1, [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) §7).
- **Not checked:** signs (any sign is accepted), bank versus non-bank applicability, and accounting
  identities (for example assets = liabilities + equity). These are gaps, listed in §3.3.

### 2.3 API (`backend/app/api/v1/`)

- `GET /api/v1/companies/{id}/financial-statements` returns the latest revision by default
  (`include_superseded=true` for history), with filters `fiscal_year`, `statement_type`, `scope`.
- Each metric carries `value`, `reported_value`, `reported_scale` as JSON **strings** (never floats,
  `test_decimals_are_json_strings`), plus `source` (WS3): `evidence_id`, `document_title`,
  `document_url` (safe http(s) only), `link_status`, `page`, `verification_status`.
- No calculated metric, no comparison and no verification endpoint exists (reviews are CLI-only).

### 2.4 Frontend

- `formatDecimal` groups digits on the decimal **string**, locale-aware (vi `1.234,5`, en `1,234.5`),
  trims trailing zeros, never parses to a float (`frontend/src/lib/api-core.ts`).
- Company page shows each figure with its unit, an "as reported" line when scale > 1, and the
  per-figure source line (WS3). Negative values show a leading `-`. No compact scale (tỷ/triệu).
- Vietnamese is the default and English is under `/en` (WS2); metric labels come from `metric_name_vi`.

### 2.5 Compatibility constraints for WS4

1. Calculated values are derived at read time and never stored (dictionary `notes`, `data/README.md`).
2. Reported figures keep their WS3 `source` contract unchanged; calculated values add a new shape.
3. Verification stays two-person and append-only (WS1); WS4 adds no way to set a status.
4. All copy in both languages with key parity (WS2 test).
5. Exact decimals end to end; no `float` in Python, no `Number` arithmetic in JavaScript for money.

---

## 3. Metric dictionary review (16 metrics)

The dictionary (`backend/app/reference/metric_dictionary.json`, version 1.0.0) holds only `code`,
`name`, `name_vi`, `statement_type` and `unit` per metric. **Not changed by this document.**

### 3.1 Per-metric review

"Has" = present in the dictionary today. "Proposed" columns are suggestions for the owner.
Evidence required is the same for every row: the statement's source document (evidence row,
T1–T3 per [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) §2) and the page the figure is
printed on. Missing-data behaviour for every row: no row means "not yet collected", never zero (§7).

| Code | Vietnamese name (has) | English name (has) | Statement (has) | Unit (has) | Definition | Proposed sign convention | Reported / calculated | Non-bank | Bank (proposed) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `net_revenue` | Doanh thu thuần | Net revenue | income | currency | **Missing** | Normally ≥ 0; negative accepted only as printed, flagged for review | Reported | Applies | **Not applicable** (bank income statements have no net revenue line; mapping total operating income here would mislead) |
| `net_interest_income` | Thu nhập lãi thuần | Net interest income | income | currency | **Missing** | As printed; may be negative | Reported | Usually not applicable | Applies |
| `gross_profit` | Lợi nhuận gộp | Gross profit | income | currency | **Missing** | As printed; may be negative | Reported | Applies | **Not applicable** (WS4-D5) |
| `operating_profit` | Lợi nhuận thuần từ hoạt động kinh doanh | Operating profit | income | currency | **Missing** | As printed; loss negative | Reported | Applies | **Ambiguous**: bank forms show operating profit before and after credit-loss provisions; must be defined before use |
| `profit_before_tax` | Lợi nhuận trước thuế | Profit before tax | income | currency | **Missing** | Loss negative | Reported | Applies | Applies |
| `net_profit` | Lợi nhuận sau thuế | Net profit after tax | income | currency | **Missing** | Loss negative | Reported | Applies | Applies |
| `net_profit_parent` | Lợi nhuận sau thuế của cổ đông công ty mẹ | Net profit attributable to parent | income | currency | **Missing** | Loss negative | Reported | Consolidated only; for separate statements it does not exist (no subsidiaries are consolidated) | Consolidated only |
| `eps_basic` | Lãi cơ bản trên cổ phiếu | Basic earnings per share | income | currency_per_share | **Missing** | Loss negative | Reported (company-computed, not recomputed by ATLAS) | Applies | Applies |
| `total_assets` | Tổng tài sản | Total assets | balance | currency | **Missing** | > 0 | Reported | Applies | Applies |
| `total_liabilities` | Tổng nợ phải trả | Total liabilities | balance | currency | **Missing** | ≥ 0 | Reported | Applies | Applies |
| `total_equity` | Vốn chủ sở hữu | Total owners' equity | balance | currency | **Missing**. In consolidated statements it **includes non-controlling interests**, so it is not "equity of the parent" | Negative possible (accumulated losses) | Reported | Applies | Applies |
| `cash_and_equivalents` | Tiền và các khoản tương đương tiền | Cash and cash equivalents | balance | currency | **Missing** | ≥ 0 | Reported | Applies | **Ambiguous**: bank balance sheets split cash, central-bank deposits and interbank placements; must be defined |
| `shares_outstanding` | Số lượng cổ phiếu đang lưu hành | Shares outstanding | balance | shares | **Missing** (which date; treasury shares excluded?) | > 0, integer | Reported. Usually printed in the equity notes, not on the balance sheet face | Applies | Applies |
| `operating_cash_flow` | Lưu chuyển tiền thuần từ hoạt động kinh doanh | Net cash from operating activities | cash flow | currency | **Missing** | Inflow positive, outflow negative | Reported | Applies | Applies (not comparable with non-banks) |
| `investing_cash_flow` | Lưu chuyển tiền thuần từ hoạt động đầu tư | Net cash from investing activities | cash flow | currency | **Missing** | Inflow positive, outflow negative | Reported | Applies | Applies |
| `financing_cash_flow` | Lưu chuyển tiền thuần từ hoạt động tài chính | Net cash from financing activities | cash flow | currency | **Missing** | Inflow positive, outflow negative | Reported | Applies | Applies |

### 3.2 General sign rule (proposed)

Store the sign **as presented**: an amount printed in parentheses `(1.234)` is stored as `-1234`
(times the scale). Expenses shown as positive numbers stay positive. The curator records what the
document shows; ATLAS never flips signs to fit a formula. Formulas state which sign they expect.
**Not approved (G-3, 2026-11-24):** no sign field is added to the dictionary; this rule stays a
curation guideline only, and the question remains open.

### 3.3 Gaps found

| ID | Gap | Effect | Proposed fix (needs approval) |
| --- | --- | --- | --- |
| G-1 | No definitions (= exit audit F-1) | Learners and curators can't tell what a line includes | Add `definition_vi`, `definition_en` per metric |
| G-2 | No applicability (= F-2) | "Not applicable" can't be told from "missing" for banks | Add `applies_to` (`non_bank`, `bank`) |
| G-3 | No sign convention | A positive expense versus negative expense can't be checked | Add `sign` (`as_presented`, with expected range) and an importer warning, not a rejection |
| G-4 | `total_equity` includes non-controlling interests | ROE with `net_profit_parent` would divide parent profit by group equity | Add reported metric `equity_parent` (Vốn chủ sở hữu của cổ đông công ty mẹ) or `non_controlling_interests` |
| G-5 | No bank lines beyond net interest income | Bank analysis limited (Q-5) | See §6 |
| G-6 | No `kind` (reported versus calculated) | Calculated metrics need their own registry | Separate calculated-metric registry with formula id and version (§9) |
| G-7 | No reference to the report form line | Curators map lines by name only | Add an optional `form_line` reference filled by the curator from the actual form, never guessed |
| G-8 | No accounting-identity checks | A typo in assets or equity passes import | Optional importer warning when `total_assets ≠ total_liabilities + total_equity` beyond 0 tolerance |
| G-9 | `operating_profit` and `cash_and_equivalents` ambiguous for banks | Wrong mapping risk | Define for banks or mark not applicable |

Any of G-1 to G-9 is a dictionary version bump (proposed 1.1.0 for additive fields, 2.0.0 if a
definition changes meaning) and **requires owner approval** (WS4-D10). F-1 and F-2 stay OPEN
until then. **2026-11-24:** G-1, G-2 and G-4 approved; G-3 and G-5 to G-9 not approved.

---

## 4. ROE specification

**Status: APPROVED 2026-11-24 (WS4-D1, D3; `equity_parent` via D10 G-4). Not implemented.**

### 4.1 Options

| Option | Formula | When it fits | Problem |
| --- | --- | --- | --- |
| A | `net_profit_parent` ÷ average equity attributable to the parent | Consolidated groups with minority shareholders; the usual definition for listed-company analysis | Needs `equity_parent`, not in the dictionary (G-4) |
| B | `net_profit` ÷ average `total_equity` | Separate statements; or consolidated "whole group" view where both sides include minorities | Overstates or understates the return to the parent's shareholders when minorities are large |
| C | `net_profit_parent` (or `net_profit`) ÷ closing equity | Only one balance sheet is available | Distorted by capital raised or dividends paid during the year; biased versus A and B |
| Mixed (rejected) | `net_profit_parent` ÷ `total_equity` | Never | Numerator and denominator cover different owners. Must not be implemented |

### 4.2 Proposed default

- **Consolidated:** option A. Until `equity_parent` exists (WS4-D10), consolidated ROE is
  **not computable**, with the reason shown. Option B may be offered only as a separately named
  metric ("ROE toàn tập đoàn / group ROE") if the owner wants it.
- **Separate:** option B (`net_profit` ÷ average `total_equity`); there are no minorities.
- **Granularity:** annual statements only. Quarterly or trailing-twelve-month ROE is future scope.

Reason: A is the standard reading of "return to the company's shareholders", B is its exact
equivalent where minorities don't exist, and refusing C by default avoids a number that looks
precise but mixes timing.

### 4.3 Rules

| Case | Rule |
| --- | --- |
| Numerator | Income statement for fiscal year *t*, same company and scope, latest revision |
| Average equity | (equity at the end of FY *t*−1 + equity at the end of FY *t*) ÷ 2, both balance sheets of the same scope. Multi-point averages (quarterly balances) are not used in Phase A |
| Opening balance source | The balance sheet dated at the end of FY *t*−1, latest revision. It may come from the prior year's report or from the comparative column of the current report; the response states which document and revision |
| Missing opening balance | **Not computable** (`reason: missing_opening_balance`). Never fall back to closing equity silently |
| Missing `equity_parent` (WS4-D12) | Consolidated ROE **not computable** (`reason: missing_input`, naming `equity_parent`). `equity_parent` is never derived as total equity minus non-controlling interests, and `total_equity` is never substituted |
| Negative or zero equity | If opening, closing or average equity ≤ 0: **not meaningful** (`reason: equity_not_positive`). A loss with positive equity gives a negative ROE, shown as such |
| Scope change | Inputs must share scope. If FY *t*−1 exists only as separate and FY *t* as consolidated: not computable |
| Restatement | Use the latest revision of each input. If an input was restated, say so and show its revision number. History view recomputes from the revisions in force at the time only if requested |
| Fiscal-year change | If FY *t* is not 360–371 days (cannot happen today, the importer rejects it) or period ends differ from the prior year by more than 7 days: not computable |
| Precision | Exact `Decimal`, 60-digit context; ratio rounded once, half-even, to 10 decimal places in the API; display rounding per WS4-D8 |
| Verification | No VERIFIED label; show its inputs' statuses (§9) |

---

## 5. ROA specification

**Status: APPROVED 2026-11-24 (WS4-D2, D3). Not implemented.**

### 5.1 Options

| Option | Formula | Notes |
| --- | --- | --- |
| A | `net_profit` ÷ average `total_assets` | Both sides cover the whole group (assets are not split by owner). Common for banks too (often called ROAA) |
| B | `profit_before_tax` ÷ average `total_assets` | Removes tax differences; useful for comparing companies with tax incentives. A secondary metric |
| C | `net_profit_parent` ÷ average `total_assets` | Mismatch: parent-only profit over group assets. Not recommended |
| D | Any of the above ÷ closing `total_assets` | Only if the opening balance is missing; not the default |

### 5.2 Proposed default

Option A, same scope, annual only, for banks and non-banks alike. Option B as an optional second
metric if the owner wants it (WS4-D2). **Decided:** option A only.

### 5.3 Rules

Same rules as ROE §4.3 for period alignment, opening balance, restatements, scope and precision,
with: average total assets ≤ 0 → not computable (`reason: assets_not_positive`; zero or negative
assets indicate a data error and go to review). Consolidated and separate ROA are separate values
and never mixed or compared with each other.

---

## 6. Bank-specific metrics (Q-5)

**Q-5 resolved 2026-11-24 by WS4-D4 and D5:** the minimal scope of §6.3. **Owner review of WS4-1
(2026-11-24):** the bank column of the §3.1 table is *not* approved as a whole. Bank values come
only from D1, D2, D4 and D5 ([data/README.md](../data/README.md), metric dictionary); all others are
`unclassified`. Banking & Financial
Services is an approved pilot sector (A-7).

### 6.1 How bank statements differ

Vietnamese credit institutions report on their own forms (State Bank of Vietnam rules), not the
general corporate forms. The income statement starts from interest income and expense, then fee,
trading and other income, operating expenses, and credit-loss provisions. There is no "net revenue"
and no "cost of goods sold", so gross profit does not exist. Asset quality (NPL) is disclosed in
the notes, not on the statement face.

### 6.2 Candidates

| Metric | Source | Classification (proposed) | Note |
| --- | --- | --- | --- |
| Net interest income | Income statement face | **1. Required for initial pilot** (already in the dictionary) | Needs a definition and bank applicability |
| Gross profit | n/a | **1. Required: mark not applicable for banks** | Not zero, not missing: not applicable (WS4-D5) |
| Net revenue | n/a | **1. Required: mark not applicable for banks** | Same |
| ROE, ROA | Calculated | **1. Required** | Same formulas (§4, §5) |
| Interest income, interest expense | Income statement face | **2. Useful, optional** | Interest expense is printed as a deduction; sign convention must be explicit |
| Total operating income | Income statement face | **2. Useful, optional** | Bank analogue of a "top line"; never stored as `net_revenue` |
| Credit-loss provision expense | Income statement face | **2. Useful, optional** | Needed to define bank `operating_profit` (G-9) |
| Loans to customers (gross) | Balance sheet / notes | **4. Needs owner approval** | Input to credit growth |
| Credit growth | Calculated from loans to customers | **3. Future scope** | YoY rule from §8 once loans are collected |
| NPL ratio | Notes (loan classification groups) | **4. Needs additional data and owner approval** | Requires note-level curation; definition (groups 3–5 over total loans) to be confirmed against the notes |
| Capital adequacy (CAR) | Notes or regulatory disclosures | **3. Future scope** | Often outside the audited statements |

### 6.3 Recommendation

For the first pilot: dictionary definitions and bank applicability for the existing 16 metrics,
ROE and ROA for banks, and nothing else bank-specific. Decide the optional group after the first
bank has been curated and the hours are known (Q-3, G2).

---

## 7. Missing-data semantics

**Rule: a missing value is never zero and never enters a calculation.** WS4 proposes no schema
change; states that today's schema cannot prove are marked as such.

### 7.1 States

Availability is one dimension; verification (§9) is a separate one. A figure can be
`reported` and `unverified` at the same time.

| State | Meaning | Today's data can show it? | UI (vi / en, proposed) | In formulas |
| --- | --- | --- | --- | --- |
| `reported` | A row exists; the value is what the document prints, **including a real 0** | Yes (row present) | the value | Used |
| `not_reported` | The document was checked and has no such line | **No.** Needs an explicit record that someone looked (schema change) | "Không trình bày trong báo cáo" / "Not presented in the report" | Not computable |
| `not_applicable` | The metric does not apply to this kind of company (for example gross profit for a bank) | Only after the dictionary has applicability (G-2) and companies have a bank / non-bank type | "Không áp dụng" / "Not applicable" | Not computable; the ratio itself may be N/A |
| `not_yet_collected` | No statement for that period, or statement present without this metric and no "checked" record | Yes (absence of row or statement) | "Chưa thu thập" / "Not yet collected" | Not computable |
| `unavailable` | The document is not published or not obtainable | **No.** Needs a record per company and period | "Không có tài liệu nguồn" / "Source not available" | Not computable |
| `invalid` | The value failed validation | Rejected at import, so never stored; visible in ingestion-run errors | Not shown on the company page; listed in the coverage report (P2-3.9) | Never used |
| `pending_verification` | Present, evidence not yet verified | Yes (evidence status `unverified`) | existing status label (WS1/WS3) | Used, and the result says it rests on unverified inputs |

### 7.2 Phased proposal

- **Phase A (no schema change):** `reported`, `not_yet_collected`, `pending_verification`, and
  `not_applicable` once the dictionary carries applicability. Absence is always shown as "not yet
  collected", never as "not reported", because ATLAS can't prove someone checked.
- **Phase B (schema change, separate approval):** explicit `not_reported` and `unavailable`
  records with curator, document and page, append-only like reviews.

### 7.3 Effects

- **API:** reported figures stay as they are. Calculated values return `value: null` with a
  `status` and `reason` instead of a number. Absence is not invented as a row.
- **Frontend:** a dash or zero must never stand in for a missing value; show the state text.
- **Formulas:** any missing input makes the result not computable, with the missing input named.

---

## 8. Period comparison rules

**Status: APPROVED 2026-11-24 (WS4-D9, growth on |prior|). Not implemented.**

### 8.1 Comparable only when all of these match

Same company; same `statement_type`; same `scope`; same granularity (annual with annual, quarter
with quarter); same currency (VND only today); same unit; both latest revisions (or both from an
explicitly chosen history view).

| Comparison | Pair |
| --- | --- |
| FY vs FY (YoY) | FY *t* with FY *t*−1 |
| Quarter YoY | Q*n* of FY *t* with Q*n* of FY *t*−1 |
| QoQ | Q*n* with Q*n*−1 of the same FY; Q1 with Q4 of FY *t*−1 |

### 8.2 Refused or warned

| Case | Rule |
| --- | --- |
| Annual vs quarterly | Refused |
| Consolidated vs separate | Refused |
| Period end moved (fiscal-year change) by more than 7 days, or lengths differ beyond the importer's ranges | Refused |
| Fiscal year not the calendar year | Allowed within one company (named by end year). Across companies, a warning that period ends differ |
| Restated prior period | Allowed using the latest revisions, with a "restated" note on the side that was restated |
| Missing period | Not computable; never interpolated, never skipped to the next available year without saying so |
| Different currencies or units | Refused (cannot happen yet) |
| Bank vs non-bank | Cross-company comparison refused for metrics not applicable to one side; warned for the rest |
| Quarterly seasonality | QoQ shown with a note that quarters can be seasonal |

### 8.3 Growth formula

`growth = (current − prior) ÷ |prior|`, exact decimals.

- prior = 0 → not computable (`reason: prior_zero`).
- Sign change (loss to profit or back) → percentage "not meaningful"; show the absolute change only.
- Using `|prior|` versus `prior` is part of WS4-D9.

---

## 9. Reported versus calculated metrics

### 9.1 Reported (exists today)

From the document, with document, page, evidence and verification status per figure (WS3
`source`). Nothing to change.

### 9.2 Calculated (proposed)

| Property | Proposal |
| --- | --- |
| Where | Read-time service in the backend; never stored (dictionary notes) |
| Registry | A versioned calculated-metric registry, separate from the reported dictionary: `code`, `formula_id`, `formula_version`, names and formula text in vi and en, inputs, applicability |
| Arithmetic | Python `Decimal`, 60-digit context; inputs taken from `Numeric` columns, never floats; one final rounding (§4.3) |
| Output | Decimal string or `null`, never a JSON number |
| Reproducible | Same inputs (statement ids and revisions) → same output; inputs listed in the response |

Proposed API shape (illustrative, not implemented):

```json
{
  "code": "roe",
  "kind": "calculated",
  "formula_id": "roe_parent_avg_equity",
  "formula_version": "1",
  "formula_text": "net_profit_parent ÷ ((equity_parent[t−1] + equity_parent[t]) ÷ 2)",
  "fiscal_year": 2025,
  "scope": "consolidated",
  "value": "…",
  "status": "computed",
  "reason": null,
  "inputs": [
    {"metric_code": "net_profit_parent", "statement_id": "…", "revision": 1,
     "period_end": "2025-12-31", "value": "…", "source": {"…": "WS3 MetricSourceOut"}}
  ],
  "input_verification": "some_unverified"
}
```

Values are elided on purpose: this shows the shape only, not a figure for any company. `value` is
a decimal string with 10 decimal places, or `null` with a `reason`.

### 9.3 Verification semantics

A calculated value has **no verification status of its own** and is never labelled VERIFIED.
It carries `input_verification`: `all_verified`, `some_unverified`, `includes_disputed_or_rejected`
(then not computed), or `sample`. Proposed UI labels:

| `input_verification` | vi | en |
| --- | --- | --- |
| `all_verified` | Tính từ số liệu đã kiểm chứng | Calculated from verified figures |
| `some_unverified` | Tính từ số liệu chưa kiểm chứng | Calculated from unverified figures |
| `sample` | Dữ liệu mẫu | Sample data |

Each calculated value shows "Cách tính / How it's calculated" with the formula text and links to
each input's source page.

---

## 10. Units and number presentation

| Topic | Proposal (WS4-D8) |
| --- | --- |
| Storage | Unchanged: full units, exact, with the as-printed value and scale kept |
| Company amounts | Display in **tỷ đồng** (10^9) with 2 decimals by default (en: "VND bn"); triệu đồng when the absolute value is below 1 tỷ |
| Exact value | Always available next to the rounded one (tooltip or expand), plus the WS3 "as reported" line |
| Per share | `đồng/cổ phiếu` (`VND/share`), integer, never scaled |
| Share counts | Integer with grouping; optional "triệu cổ phiếu" in summaries only |
| Ratios | Percent with 2 decimals (`18,34%` vi, `18.34%` en) |
| Rounding | Half-up on the displayed digit, done on decimal strings (or `BigInt`), never `Number` |
| Negative | Minus sign `−` (U+2212), not parentheses; profit lines below zero labelled "lỗ / loss" in summaries |
| Never | Show a rounded figure as if it were the printed figure; drop the unit |

---

## 11. Testing strategy (for implementation, after approval)

| Layer | Must cover |
| --- | --- |
| Unit (backend) | Each formula with exact expected decimal strings; rounding boundaries; 32-digit inputs; negative numerator; zero, negative and missing denominator; sign change in growth |
| Unit (frontend) | Compact scale and rounding on strings (no float drift, e.g. 0.1 + 0.2 cases); vi/en formats; state labels; key parity |
| API | Response shape; `value` is a string or null; inputs and sources listed; reasons; OpenAPI contract; no private fields |
| Integration | Import fictional fixtures → API → page: computed, not computable, N/A, restated cases in both languages |
| Missing data | Absent row → `not_yet_collected`, never 0; N/A only via dictionary applicability |
| Period alignment | YoY, QoQ, Q1 vs prior Q4, non-calendar FY, refused pairs (annual vs quarter, scope mix) |
| Restatement | Latest revision used; revision disclosed; history view |
| Bank / non-bank | Bank fixture: gross profit N/A, ROE/ROA computed; non-bank unaffected |
| Regression | Existing 201 backend and 24 frontend tests stay green; WS3 provenance tests unchanged |

All test data fictional (`example.test`, `TST` tickers), flagged as sample where stored.

---

## 12. Owner decision register

Decided by the project owner on 2026-11-24, recorded in [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md)
§2d. The analysis below is kept as it was presented; each entry ends with the outcome.

### WS4-D1: ROE default formula

- **Current situation:** no ROE; `net_profit_parent` exists, `equity_parent` does not.
- **Options:** A parent profit ÷ average parent equity; B net profit ÷ average total equity;
  C closing equity.
- **Recommendation:** A for consolidated (needs WS4-D10), B for separate statements, annual only.
- **Trade-offs:** A is correct but needs one new curated line per balance sheet; B works now but is a
  "group" ROE.
- **Risks:** mixing parent profit with group equity (rejected option) gives a plausible wrong number.
- **If undecided:** no ROE is shown. P2-5.11 stays IN PROGRESS.
- **Outcome (2026-11-24):** Approved as recommended (option A consolidated, B separate, annual only).

### WS4-D2: ROA default formula

- **Current situation:** no ROA; all inputs exist.
- **Options:** net profit, profit before tax or parent profit ÷ average total assets; closing assets.
- **Recommendation:** net profit ÷ average total assets; PBT variant optional.
- **Trade-offs:** net profit is the familiar figure; PBT compares across tax regimes.
- **Risks:** parent-profit variant mismatches its denominator.
- **If undecided:** no ROA. P2-5.12 stays IN PROGRESS.
- **Outcome (2026-11-24):** Approved: net profit ÷ average total assets; no PBT variant.

### WS4-D3: Averaging convention

- **Current situation:** one balance sheet per date; opening balances may come from comparative columns.
- **Options:** (opening + closing) ÷ 2; closing only; average of five quarterly balances.
- **Recommendation:** (opening + closing) ÷ 2; not computable if opening is missing.
- **Trade-offs:** five-point averages are smoother but need all quarterly balance sheets.
- **Risks:** silent fallback to closing equity would change the meaning year to year.
- **If undecided:** neither ROE nor ROA can be implemented.
- **Outcome (2026-11-24):** Approved: (opening + closing) ÷ 2; not computable without the opening balance.

### WS4-D4: Banking metric scope (Q-5)

- **Current situation:** one bank-specific metric (`net_interest_income`); Q-5 open.
- **Options:** minimal (§6.3); minimal + optional group (interest income/expense, operating income,
  provisions); full (NPL, credit growth, CAR).
- **Recommendation:** minimal now; decide the rest after the first bank is curated.
- **Trade-offs:** more metrics are more useful for learners but add curation hours and note-level data.
- **Risks:** adding NPL before note-level curation is defined invites unverifiable figures.
- **If undecided:** the bank in the pilot shows only generic metrics, with gross profit and revenue
  wrongly appearing as "not yet collected" instead of "not applicable".
- **Outcome (2026-11-24):** Approved: minimal scope. **Q-5 resolved.**

### WS4-D5: Gross profit (and net revenue) for banks

- **Current situation:** no applicability field.
- **Options:** not applicable; map a bank line (e.g. total operating income) to it; leave missing.
- **Recommendation:** not applicable, for both `gross_profit` and `net_revenue`.
- **Trade-offs:** mapping would give a number but changes the metric's meaning between companies.
- **Risks:** a learner compares a bank's "revenue" with a retailer's.
- **If undecided:** shown as "not yet collected", which suggests data will come.
- **Outcome (2026-11-24):** Approved: not applicable for both `gross_profit` and `net_revenue`.

### WS4-D6: Missing-data states

- **Current situation:** present row or no row.
- **Options:** Phase A only (no schema change); Phase A + B (explicit records, a migration).
- **Recommendation:** approve the seven-state vocabulary and Phase A now; decide Phase B after the pilot.
- **Trade-offs:** Phase A can't say "not reported" honestly; Phase B adds curation work and a migration.
- **Risks:** labelling absence as "not reported" without proof would be an unsupported claim.
- **If undecided:** P2-5.15 stays IN PROGRESS; UI keeps hiding absent metrics.
- **Outcome (2026-11-24):** Approved: seven-state vocabulary and Phase A. Phase B not approved (decide separately).

### WS4-D7: Verification semantics of calculated metrics

- **Current situation:** only evidence rows have a status.
- **Options:** no own status + `input_verification` (recommended); inherit the weakest input status;
  a separate review of calculated values.
- **Recommendation:** no own status; derived label; never VERIFIED.
- **Trade-offs:** inheriting looks simpler but makes a calculation look reviewed when only inputs were.
- **Risks:** a VERIFIED badge on a ratio would claim a check that never happened.
- **If undecided:** calculated values cannot be shown.
- **Outcome (2026-11-24):** Approved: no own status, `input_verification` label, never VERIFIED.

### WS4-D8: Display precision and rounding

- **Current situation:** exact full-unit digits; no compact scale.
- **Options:** keep full units; tỷ đồng 2 decimals (recommended); match each document's printed scale.
- **Recommendation:** §10.
- **Trade-offs:** full units are exact but unreadable; matching the document varies by company.
- **Risks:** rounding with floats or hiding the exact value.
- **If undecided:** P2-5.14 stays IN PROGRESS with full-unit display.
- **Outcome (2026-11-24):** Approved as §10.

### WS4-D9: Period comparison rules

- **Current situation:** no comparisons.
- **Options:** §8 rules; looser rules with warnings only.
- **Recommendation:** §8 (refuse incompatible pairs; warn on cross-company period differences);
  growth on `|prior|`.
- **Trade-offs:** strict rules show fewer comparisons.
- **Risks:** a consolidated-versus-separate or annual-versus-quarter comparison misleads.
- **If undecided:** P2-5.13 stays IN PROGRESS.
- **Outcome (2026-11-24):** Approved: §8 rules, growth on `|prior|`.

### WS4-D10: Metric dictionary changes (exit audit F-1, F-2)

- **Current situation:** dictionary 1.0.0; F-1 and F-2 OPEN.
- **Options:** approve G-1 to G-9 together (1.1.0 / 2.0.0); approve per gap; defer.
- **Recommendation:** approve G-1, G-2, G-3, G-4 first (definitions, applicability, signs,
  `equity_parent`); the rest with WS4-D4.
- **Trade-offs:** each new metric adds curation work per statement.
- **Risks:** definitions written without review by an accountant may be wrong; proposed text should
  be checked by the owner or a delegate.
- **If undecided:** consolidated ROE stays not computable; banks can't be marked N/A.
- **Outcome (2026-11-24):** Approved: G-1, G-2, G-4. Not approved: G-3 and G-5 to G-9. G-4 and G-2 were added after the owner was shown that D1 needs `equity_parent` and D5 needs applicability.

### WS4-D11: Calculated metrics from unverified inputs in the private pilot

- **Current situation:** Q-3 open, so every real figure will be unverified for now.
- **Options:** show with the "unverified" label (private pilot only); hide until inputs are verified.
- **Recommendation:** show with the label in the private pilot; never publicly before G1.
- **Trade-offs:** hiding blocks research round testing; showing risks over-trust.
- **Risks:** a screenshot leaves the private pilot without its label.
- **If undecided:** calculated values are hidden whenever any input is unverified.
- **Outcome (2026-11-24):** Approved: shown with the unverified label in the private pilot only.

---

## 13. Implementation scope (after approval only)

| Step | Content | Depends on | Schema change |
| --- | --- | --- | --- |
| WS4-1 | Dictionary 1.1.0: definitions, applicability, new metrics as approved (G-1, G-2, G-4; no signs, G-3 not approved) | D4, D5, D10 | No (reference JSON only; the dictionary is not stored in the database). **Done:** merged 2026-11-25 (PR #6, `105869f`; Backend, Frontend, Docker CI success); definitions approved by the owner |
| WS4-2 | Calculated-metric registry and read-time service with exact `Decimal` | D1, D2, D3, D7 | No |
| WS4-3 | API endpoint for calculated metrics; OpenAPI | WS4-2 | No |
| WS4-4 | UI: calculated labels, formula disclosure, states, compact display | D6, D7, D8 | No |
| WS4-5 | Period comparisons | D9 | No |
| WS4-6 | Explicit "not reported" / "unavailable" records | D6 Phase B (**not approved**) | **Yes** (needs its own approval) |

*Note (2026-11-26):* the workstreams were delivered under different numbers from this table:
WS4-2 = calculated-metric registry, service, API and UI for ROE/ROA (rows WS4-2 to WS4-4 above);
WS4-3 = period comparisons (row WS4-5); WS4-4 = missing-data semantics and bank applicability,
Phase A ([WS4_4_IMPLEMENTATION_PLAN.md](WS4_4_IMPLEMENTATION_PLAN.md)). Row WS4-6 (explicit records)
is WS4-4 Phase B, design approved, not built. The table above is kept as written.

### Exit criteria for WS4 implementation

1. Every implemented formula matches an approved decision, with its id and version in the response.
2. No missing value appears as zero; tests prove it.
3. No float in any financial calculation (Python and JavaScript); tests with 32-digit inputs.
4. Calculated values are never labelled VERIFIED.
5. All WS1, WS2, WS3 tests still pass; CI green.
6. Fictional fixtures only; no real figures in the repository.
7. [WS4_CHECKLIST.md](WS4_CHECKLIST.md) recounted with no FAIL.

---

## 14. Risks and dependencies

| ID | Risk or dependency | Effect |
| --- | --- | --- |
| WR-1 | Q-3 (no reviewer) | All real inputs stay unverified; calculated values carry the unverified label |
| WR-2 | G1 (no legal opinion) | Nothing real is shown publicly, calculated or reported |
| WR-3 | Bank scope limited to the minimal set (D4) | Learners see no asset-quality metrics for banks yet |
| WR-4 | Definitions not reviewed by an accountant | A wrong definition would mislead learners |
| WR-5 | Opening balances from comparative columns create a second balance sheet for the same date | Must be imported as the same statement (or a revision), never a parallel one; check against the overlap rules before curation starts |
| WR-6 | Glossary native-speaker review pending | New Vietnamese labels add to that review |
