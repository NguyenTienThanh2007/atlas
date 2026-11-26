# WS4-3 audit: period comparison, before implementation

**Status: AUDIT — Phase A only. No WS4-3 code exists; implementation is not authorised (W3-B3).**
This audit checks the approved WS4-3 design ([WS4_3_IMPLEMENTATION_PLAN.md](WS4_3_IMPLEMENTATION_PLAN.md),
decisions W3-D1 to W3-D10 in [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2e) against the code on
`main`. It changes no code, schema, data or decision. Fictional examples only.

| | |
| --- | --- |
| Audited | 2026-11-26 |
| Baseline | `main` = `origin/main` @ `407ed63` (PR #9 merge) |
| Method | Code reading of the files listed in §2; expected fixture results computed with the existing `rounded_quotient` and checked against an independent `Fraction` oracle (§5) |
| Result | **READY WITH CONDITIONS** (§7) |

## 1. Baseline verified

| Check | Evidence | Result |
| --- | --- | --- |
| Local `main` equals `origin/main` | `git rev-parse`: both `407ed6355df32ecebbe63c95e8f899cc4110947a` after a fast-forward from `8007fe2` | PASS |
| PR #9 on `main` | `gh pr view 9`: MERGED 2026-11-25 12:44 UTC, merge commit `407ed63`, head `6c01f11`; `git diff 6c01f11 407ed63` is empty, so the merged tree is the tree tested locally before the PR (backend 314 passed, frontend 31/31) | PASS |
| Migration `8de09b58f4c2` on `main` | `backend/migrations/versions/2026_11_25_1200-8de09b58f4c2_sample_real_isolation.py`, revises `31b1317163eb`; it is the head of the chain | PASS |
| CI on the merge commit | Backend, Frontend and Docker runs on `407ed63` all `success` ([backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669307), [frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669447), [docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669282)) | PASS |
| Recorded review on PR #9 | `reviews: []`; `main` has no branch protection (`gh api …/branches/main/protection` → 404 "Branch not protected") | AU-6 still open (§3, A3-13) |

No uncommitted work existed before this audit (`git status` clean on `fix/ws4-2-audit-au3-au4-au5`). The
audit documents are on a new branch, `docs/ws4-3-audit-plan`, cut from `main` @ `407ed63`.

## 2. Existing behaviour confirmed in code

| Property | Where | What the code does |
| --- | --- | --- |
| Sample/real isolation, database | Migration `8de09b58f4c2` | Triggers on `financial_statements`, `evidence`, `companies` and `securities` refuse any write that mixes a sample company with real evidence or the reverse (`check_violation`), with `FOR SHARE` locks on the company row |
| Sample/real isolation, engine | `calculations/ratios.py` `compute`; `calculations/service.py` `_company_mixed` | Independent of the triggers: any input whose classification differs from the company's, or any mixed statement of the company, gives `mixed_sample_and_real` and no verification label |
| Provenance per figure | `api/v1/schemas.py` `MetricSourceOut.for_figure` | Document title, a URL only when `linkable_url` accepts it, the figure's own `source_page`, the evidence status |
| Reported vs calculated | `CalculatedMetricOut` | `kind: "calculated"`, no `verification_status` on the result; `input_verification` describes the inputs (tests assert the absence) |
| Exact arithmetic | `ratios.py` | `Context(prec=100, traps=[Inexact])`; `rounded_quotient` rounds once from the exact quotient, half-even or half-up, never negative zero; `FixedDecimal` serialises with `format(d, "f")` |
| Pagination | `Page` (`items`, `total`, `limit`, `offset`); `components/pagination.tsx` (`param`, `anchor`, `showRange`) | Several paginated lists on one page, each with its own query parameter and "Đang hiển thị X–Y / Z" |
| Periods | `ingestion/schemas.py` `_check_period` | Annual flows 360–371 days, quarterly flows 80–100 days, balance sheets one date; fiscal year named by its end year; the quarter number is **not** checked against the months |
| Overlap and revisions | `ingestion/importer.py` `_overlapping`, `identity` | No overlapping periods within a company, type, scope and granularity; a revision keeps the period **end** but may change the start; latest = not superseded |
| Units | Importer | Amounts scaled to đồng at import; units `VND`, `VND/share`, `shares` from the dictionary; statement currency VND only |

## 3. Findings

Each finding has a fictional case. Classes: **D** = decision needed (not approved yet), **P** = plan
correction made in this task (no new decision), **R** = risk accepted with documentation, **X** =
process.

| ID | Class | Finding | Concrete case | Resolution |
| --- | --- | --- | --- | --- |
| A3-1 | **D** | The approved reason list (W3-D10, plan §5.1) has no code for mixed sample and real inputs, but the Phase B rules and the AU-3 engine defence require refusing them. Implementing W3-D10 literally would either compute such a comparison or refuse it with an unapproved code | A legacy row (written with triggers disabled) gives a real company one sample-evidence statement; a YoY pair through that statement | **Proposed W3-D11**: add `mixed_sample_and_real` at rank 0 with the WS4-2 texts (plan §12.4). Must be approved before WS4-3a |
| A3-2 | **D** | W3-D7 approves "a readable display limit" but no threshold | Prior 0.000001, current 1 → 99 999 900,00 % | **Proposed W3-D7 threshold**: absolute percentage above 999,99 % shows "> 999,99 %" or "< −999,99 %"; the full value is in the disclosure (plan §12.6). Owner confirms the number |
| A3-3 | P | WS4-D9 §8.2 (approved) requires a seasonality note on quarter-on-quarter comparisons; plan §6 omits it | Any QoQ table | Added to plan §12.5 and §12.6; texts join the glossary review |
| A3-4 | P | WS4-D9 §8.2 requires a "restated" note on the restated side; plan §6 puts revisions only in the disclosure | Previous year at revision 2 | Note shown in the row next to that side, reusing `company.restated` ("đã điều chỉnh (lần n)") |
| A3-5 | P | "One item per (current statement, metric)" with all 17 metrics (W3-D6) would emit rows for metrics a company never reports | A bank has no `gross_profit`; a company that doesn't print `equity_parent` (WS4-D12) | Rows only for metrics reported on at least one side (plan §12.3). W3-D6 still governs which metrics are eligible. Owner may object at plan review |
| A3-6 | P | Plan §6 says "Change from previous period"; approved W3-D3 says "Change versus previous period" | Section heading | The approved text is used |
| A3-7 | R | `formatDecimal` prints negatives with an ASCII hyphen; `formatFixed` uses U+2212 (AU-2). A comparison row would show both | Change −50 next to −100,00 % | Recommended in WS4-3d: `formatDecimal` also uses U+2212 (display only, every value; route check updated). If the owner prefers a narrower change, only comparison values use it |
| A3-8 | R | Annual YoY requires the previous statement labelled FY *t*−1. A 52/53-week year that ends across 1 January then has a date match with the wrong label | FY ends 2024-12-28, next FY ends 2026-01-03 (labelled FY2026) → previous labelled FY2024, expected FY2025 | `period_mismatch`, never paired. Documented; strict by W3-D9 |
| A3-9 | R | A revision may change the period start (identity uses the end only) | Revision 2 of a Q2 corrects the start date | Matching always uses the latest revision's dates; tested |
| A3-10 | R | Python's default 28-digit `Decimal` context silently rounds a 38-digit subtraction and prints an exponent | `Decimal("-99999999999999999999999999999999.999999") - Decimal("-0.000001")` gives `-1.000000000000000000000000000E+32`; the exact answer is `-99999999999999999999999999999999.999998` | All arithmetic through `_EXACT` (traps `Inexact`); test F16 (§5) |
| A3-11 | R | Through the importer, an ambiguous previous period can only arise for balance sheets (flows can't overlap, and each is ≥ 80 days long) | Two FY2024 balance sheets at 28 and 31 December | Flow ambiguity is tested with rows written directly to the test database |
| A3-12 | R | Unit or currency mismatch can't arise through the importer | — | Defensive check, tested with direct rows, as in WS4-2 |
| A3-13 | X | AU-6 continues: PRs #6 to #9 merged with no recorded review; `main` unprotected | — | WS4-3's PR carries a recorded owner review before merge (W3-H2) |
| A3-14 | R | The quarter number isn't checked against the months at import (P2-6.4) | A "Q3" with April–June dates | Caught as `period_mismatch` when paired |
| A3-15 | R | W3-D1 is enforced only by the length rule: a year-to-date quarter (> 100 days) can't be imported, but a curator could still type a derived quarter (YTD *n* − YTD *n*−1) as if printed | Q2 cash flow computed by hand from two YTD columns | Recommended addition to VERIFICATION_WORKFLOW in WS4-3e: quarterly figures must be printed as stand-alone in the document |
| A3-16 | R | The endpoint computes all comparisons of one company and type in memory, then pages | 10 years × 4 quarters × 3 types × 2 scopes = 240 statements | Bounded by one company's statements; fixed query count; `shortcut:` comment in the code |

**Defects that must be fixed in existing code before WS4-3: none.** The two D items are open
decisions, not defects.

## 4. Decision-to-test traceability

Test ids refer to plan §12.9 (F = arithmetic fixtures, M = matching fixtures, A = API, U = UI).

| Decision | Rule | Tests | Checklist |
| --- | --- | --- | --- |
| WS4-D9 | Same company, type, scope, granularity, unit, currency; latest revisions; growth = (current − prior) ÷ \|prior\|; prior 0 or sign change → no percentage; restated note; QoQ seasonality note | F1–F16, M1–M18, U5, U6 | W3-C1–C8, W3-D-1, W3-D-3, W3-F4, W3-F8 |
| W3-D1 | Stand-alone quarters only; no YTD derivation | M14; existing `tests/test_verification.py` case that rejects a 120-day quarter ("span") | W3-C2, W3-G3 |
| W3-D2 | Current zero is computed | F6, F7 | W3-D-4 |
| W3-D3 | Neutral wording, never "growth" | U1, U2 (texts), A9 (no `growth` wording in API names shown to users) | W3-F2 |
| W3-D4 | 10 dp half-even, 2 dp half-up, from exact `Decimal` | F12a–F12d, F13–F16, A6 | W3-D-2, W3-D-5, W3-D-8 |
| W3-D5 | Neutral colours; arrow plus text | U3, U4 | W3-F2 |
| W3-D6 | All 17 reported metrics; ROE/ROA not compared | A7, A8 | W3-E1 |
| W3-D7 | Display limit, full value in the disclosure | U7 (threshold as approved) | W3-F9 |
| W3-D8 | No charts | U8 (no chart element or library) | W3-F1 |
| W3-D9 | Matching rules of plan §2; ambiguity refused | M1–M13 | W3-C1–C7 |
| W3-D10 | Statuses, codes, precedence, texts | F5, F8–F10, M5, M6, M9, M13, M15–M18, A5, U5 | W3-D-6, W3-F3 |
| W3-D11 (proposed) | `mixed_sample_and_real` at rank 0 | M15 | W3-D-6, W3-B4 |

## 5. Expected arithmetic results (computed, not assumed)

Computed on 2026-11-26 with the existing `rounded_quotient` (denominator \|prior\|) and the exact
subtraction `_EXACT.subtract`; every value matched an independent `Fraction` oracle (script kept
outside the repository). The plan §12.9 table lists them.

## 6. Open risks and blockers

| Item | State | Effect |
| --- | --- | --- |
| W3-D11, W3-D7 threshold | Proposed | Block WS4-3a until decided |
| W3-B3 go-ahead | Not given | Blocks all WS4-3 code |
| AU-6 / A3-13 | Open | WS4-3 PR needs a recorded owner review |
| Q-3 independent reviewer | Open | Real values stay unverified; labels say so |
| G1 legal opinion | Open | No public display of real comparisons |
| Glossary native-speaker review | Pending | New WS4-3 terms join it |
| Q-7, Q-8 | Open | No effect on WS4-3 code |

**Update (2026-11-26):** the owner approved W3-D11 and the W3-D7 threshold (with A3-5 and A3-7) as
proposed (PRODUCT_DECISIONS §2e). Remaining: W3-B3, A3-13, and the open items Q-3, G1, Q-7, Q-8
and the glossary review.

## 7. Recommendation

**READY WITH CONDITIONS.** The code base supports WS4-3 without a migration: isolation, provenance,
exact arithmetic and pagination are in place and reusable. Conditions before WS4-3a starts:

1. The owner decides W3-D11 (A3-1) and the W3-D7 threshold (A3-2).
2. The owner authorises implementation (W3-B3).
3. The WS4-3 PR carries a recorded owner review before merge (A3-13).

**Update (2026-11-26):** condition 1 is met. Conditions 2 and 3 remain.

**Update (2026-11-26, later):** condition 2 is met (W3-B3) and WS4-3 is implemented (not committed).
Condition 3 (recorded owner review on the PR) remains. A3-7 (minus sign), A3-10 (exact
subtraction, fixture F16) and A3-15 (VERIFICATION_WORKFLOW rule) are done in that change.
