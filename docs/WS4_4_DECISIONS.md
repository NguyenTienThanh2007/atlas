# WS4-4 decision register

**Status update (2026-11-26, later): WS4-4-D1 to D10 APPROVED by the owner as recommended
("Duyệt như đề xuất"); recorded in [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2f. Q-A and Q-C
answered; Q-B answered in part (finance companies need an accountant's view). Implementation is not
authorised.** The register below is kept as proposed; its "Status" column predates the approval.

**Status: PROPOSED — NONE APPROVED.** Written 2026-11-26 against `main` @ `9d44fb4`. Each decision
below needs the project owner's explicit approval before any WS4-4 code is written. Design:
[WS4_4_IMPLEMENTATION_PLAN.md](WS4_4_IMPLEMENTATION_PLAN.md).

## Decisions already approved and reused unchanged

| ID | What WS4-4 reuses | Source |
| --- | --- | --- |
| WS4-D4 | Bank scope: `net_interest_income`, ROE, ROA | PRODUCT_DECISIONS §2d |
| WS4-D5 | `net_revenue`, `gross_profit` not applicable for banks | same |
| WS4-D6 | Seven-state vocabulary; Phase A only; **Phase B not approved** | same |
| WS4-D7, D11 | Calculated values never verified; unverified-input label; private pilot only | same |
| WS4-D10 (G-2) | Dictionary applicability per kind; `unclassified` never means not applicable | same; implemented in dictionary 1.1.0 |
| WS4-D12 | `equity_parent` only when reported; never derived | same |
| WS1 rules | Two-person review: curator ≠ reviewer, reviewer is a person | VERIFICATION_WORKFLOW |
| G1, A-7 | No public display of real data; banking is a pilot sector | PRODUCT_DECISIONS |

No approved decision is reopened. WS4-4-D9 asks the owner to confirm how WS4-D6's "no schema
change" applies to a company-classification table (plan §1.7, C-1).

## Decisions needed

| ID | Decision | Options | Recommendation | Rationale | Consequences | Status |
| --- | --- | --- | --- | --- | --- | --- |
| WS4-4-D1 | Company classification model | A: column on `companies`; **B: append-only classification records with evidence and two-person review**; C: derive from sector; D: column + history | **B** | C is wrong for the taxonomy (`BANKING_FINANCIAL` includes securities firms, insurers, finance companies); A loses history and the importer can't update companies; D duplicates the truth | One new table and triggers (D9); every existing company starts unclassified | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D2 | Kinds and the unknown state | (a) `bank`, `non_bank`, unknown; **(b) also `other_financial`, for which no applicability claim is made**; (c) more granular kinds now | **(b)**; unknown = no current classification | The dictionary has two columns only; claiming non-bank rules for an insurer would be unsupported. Which kind a finance company gets needs an accountant (human dependency) | Insurers and securities firms show no "not applicable" until a later dictionary change | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D3 | Applying dictionary applicability per company | **The plan §3.1 table**: `not_applicable` only from a reviewed kind **and** a dictionary `not_applicable`; `unclassified` or unknown → no claim (absent = "not yet collected") | **As §3.1** | Keeps G-2's rule that unclassified is never N/A | Banks show many "not yet collected" lines for `unclassified` bank metrics (honest) | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D4 | `not_applicable` display, conflicts and calculations | (a) **Absent N/A metrics listed as "Không áp dụng"; importer refuses new figures for N/A metrics; existing conflicting rows flagged, not hidden; comparisons of such rows `metric_not_applicable`; defensive ROE/ROA code `input_not_applicable`**; (b) hide N/A metrics entirely | **(a)** | Hiding is less clear for learners; refusing at import prevents wrong data | Two new reason codes (changes the W3-D10 and WS4-2 code lists, ranks after the existing `missing_*`); no formula change | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D5 | Phase B: explicit `not_reported` records | (a) Keep not approved (WS4-D6 stands); **(b) approve the design of plan §5.2 for a later step, implementation after G2 measures curation hours**; (c) implement with Phase A | **(b)** | WS4-D6 deferred Phase B "after the pilot"; designing now avoids a second migration shape later, but the curation cost is unknown | Until implemented, absence stays "not yet collected"; no "not reported" text anywhere | PROPOSED — REQUIRES OWNER APPROVAL (WS4-D6 left Phase B unapproved) |
| WS4-4-D6 | `unavailable` state and sub-reasons | Sub-reasons `not_published`, `inaccessible`, `temporarily_unavailable` (with re-check date), `access_restricted` (never bypassed), `rights_restricted`; document-level record; Phase B | **Approve the vocabulary with D5's timing** | Distinguishes "the company didn't publish" from "ATLAS can't get it" | Same as D5 | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D7 | Curator / reviewer requirements | (a) **Classification and Phase B records need two people (curator ≠ reviewer, reviewer a person), like WS1; a classification stops counting if its evidence becomes `disputed` or `rejected`**; (b) curator only | **(a)** | Classification drives "not applicable" claims for every metric of a company; one person's error would spread | Nothing can be classified until the Q-3 reviewer exists (human dependency) | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D8 | Visibility | **Private pilot only, like all real data (G1, WS4-D11)**; sample companies visible as sample | **As stated** | No new public surface before G1 | — | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D9 | Migration and backward compatibility | (a) **Allow one additive migration for `company_classifications` (no change to existing tables or rows; downgrade drops it); confirm that WS4-D6's "no schema change" referred to missing-data records only**; (b) no schema change at all: Phase A without "not applicable" | **(a)** | Without a stored kind, WS4-D5 can never take effect | API changes are additive only; existing clients unaffected | PROPOSED — REQUIRES OWNER APPROVAL |
| WS4-4-D10 | Scope and acceptance | **Phase A as plan §5.1 (items 1–6) with the acceptance criteria in WS4_4_CHECKLIST.md; Phase B excluded** | **As stated** | Matches WS4-D6 | P2-5.15 can pass for Phase A only after its wording is reconciled (plan §1.7, C-2) | PROPOSED — REQUIRES OWNER APPROVAL |

## Open questions for the owner

| ID | Question | Linked |
| --- | --- | --- |
| Q-A | Does WS4-D6's "no schema change" also cover a classification table? | D9 |
| Q-B | Which kind do securities firms, insurers and finance companies get? (Accountant input advised) | D2 |
| Q-C | Must classification evidence be `verified`, or is the classification's own two-person review enough? | D7 |

## Human dependencies

- Q-3 second reviewer: needed before any real classification counts (D7).
- An accountant's view on the kinds of financial companies (D2).
- Glossary native-speaker review for the new texts.
- G1 for any public display (D8).
