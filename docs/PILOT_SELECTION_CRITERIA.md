# Pilot company selection criteria (P2-3.1)

Status: **APPROVED** by the project owner Tiến Thành on 2026-11-23
([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-11). Changes to these criteria need a new recorded
decision.

Applies to the approved pilot ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-7): **20–30 companies**
across **Banking & Financial Services, Consumer & Retail, Technology, and Materials & Construction**.
The first **5** form the private pilot (gate G2, A-6).

**This document names no companies, by design.** Candidates are recorded only after a person has
checked them against the criteria below, with evidence.

## Principles

1. **Objective and repeatable.** Two reviewers applying these criteria to the same evidence should
   reach the same shortlist.
2. **Checkable from primary documents.** Every criterion can be checked from the company's own
   published reports or official exchange notices, the same documents the pilot curates from
   (A-6). No aggregator site is used.
3. **Serve the approved segment.** Learners start with well-known large companies (PRODUCT_STRATEGY
   §4, an assumption to confirm in interviews), so prefer those.
4. **Keep the first 5 simple; let the 20–30 exercise the edge cases.**

## 1. Eligibility (every candidate must pass all of these)

| # | Criterion | How to check (evidence to record) |
| --- | --- | --- |
| E1 | Listed on **HOSE or HNX**, status *listed* (not suspended, not delisted) on the selection date | Exchange listing notice or the company's own disclosure page, checked by a person; URL and date |
| E2 | Not under an exchange **warning, control or special-control** designation on the selection date | Exchange announcements; URL and date |
| E3 | **Primary business activity** fits one approved sector under the ATLAS taxonomy methodology (largest revenue source per the latest audited report) | Segment note or business description in the audited annual report; page or section |
| E4 | **Audited annual financial statements for at least the last 3 fiscal years** are published on the **company's own website** (investor relations) and can be downloaded | One URL per year; retrieval date; SHA-256 of each file |
| E5 | **Consolidated** statements are available for those years (or the company has no subsidiaries, recorded as such) | Statement cover page |
| E6 | Statements are in **VND** | Statement header |
| E7 | **Unqualified audit opinion** (*ý kiến chấp nhận toàn phần*) for each of the 3 years | Auditor's report page |
| E8 | **Annual report** (*báo cáo thường niên*) for the latest year is published, to source the business description | URL, retrieval date |

E2 and E7 apply to the private pilot and the 20–30 alike. Revisit them later, once the product can
explain warnings and qualified opinions to learners.

## 2. Ordering (who goes first among eligible candidates)

1. **Prominence:** constituents of the **VN30** index on the selection date, then other **VN100**
   constituents, then others. The source is the official index constituent announcement (URL, date).
   This is a proxy for "companies learners have heard of".
2. **Tie-breaker: interview signal.** Companies named unprompted by round-1 interviewees (PRODUCT_STRATEGY
   §10, question 5) rank higher. The tally is recorded without interviewee names.
3. **Tie-breaker: document quality.** Machine-readable PDFs (text, not scans) rank higher, because
   they make per-figure source references easier.

## 3. Composition rules

**First 5 (private pilot, gate G2):**
- **At least 1 company from each of the 4 sectors**, plus a fifth from any sector.
- **Exactly 1 bank.** Banks report on a different statement format (no gross profit; net interest
  income instead of revenue). One bank tests how ATLAS handles this, which informs open question
  Q-5, without making the whole pilot bank-specific.
- **Calendar fiscal years only** (year ending 31 December), so periods line up across companies.
- **Prefer companies with one listed security**, to keep the first pass simple.

**Full 20–30:**
- **5–8 companies per sector.** No sector exceeds 40% of the total.
- **At least 2 banks** and at least 1 non-bank financial company (e.g. securities or insurance).
- **At least 1 HNX-listed company**, so not everything is HOSE.
- **Include deliberately, if eligible:**
  - at least 1 company with a **non-calendar fiscal year**
  - at least 1 company that **moved exchange or changed ticker** (tests listing history)
  - at least 1 company with **more than one listed security**
  - at least 1 company with a **restated** prior-year figure (tests revisions)
- **No more than 2 companies from the same corporate group**, to avoid one group dominating a sector.

## 4. What is curated for each selected company

Matches MVP M1 and M2 ([PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md) §6):

| Area | Fields | Source |
| --- | --- | --- |
| Identity (M1) | Legal name, short name, English name (if published), tax code, website | Audited report cover page and notes; annual report |
| Listings (M1) | Ticker, exchange, security type, listing date | Exchange notice or annual report |
| Sector (M1) | ATLAS sector, with a one-line justification | Segment note (E3) |
| Business overview (M1) | 2–4 paragraphs **in ATLAS's own words**, no copied text | Annual report, audited report notes |
| Key financials (M2) | ≥3 fiscal years, consolidated: `net_revenue` (or `net_interest_income` for banks), `gross_profit` (not for banks), `operating_profit`, `profit_before_tax`, `net_profit`, `net_profit_parent`, `eps_basic`, `total_assets`, `total_liabilities`, `total_equity`, `cash_and_equivalents`, `operating_cash_flow` | Audited statements; **page number per figure** |

**"Not applicable" is different from "not reported".** A bank has no gross profit line; that is not
missing data. P2-5.15 must show the difference. Record "not applicable" explicitly during curation.

## 5. Selection record (template)

One row per **candidate considered**, including the rejected ones, so the selection can be audited.
Keep it in the private pilot workspace, not in this public repository, until gate G1 allows
publishing.

| Field | Example (format only) |
| --- | --- |
| Candidate | Legal name and ticker |
| Selection date | YYYY-MM-DD |
| E1 to E8 | pass / fail, each with URL, retrieval date and page |
| Prominence | VN30 / VN100 / other (source URL, date) |
| Interview mentions | count |
| Document quality | text PDF / scanned |
| Decision | selected (pilot 5 / full set) or rejected, with reason |
| Checked by / reviewed by | initials of curator and second reviewer (D-6) |
| Conflict of interest | Does the curator or reviewer hold this stock? (yes / no, recorded, not a reason to exclude) |

## 6. Process

1. The owner approves these criteria (A-11).
2. Build a long-list from official index constituent announcements, by sector.
3. Check E1–E8 for each candidate and fill in the selection record. A second person checks a sample
   of at least 20% of the rows.
4. Apply the ordering and composition rules to pick the first 5. The owner confirms the list.
5. Curate the 5 (gate G2) and record hours per company. Only then pick the remaining companies.
