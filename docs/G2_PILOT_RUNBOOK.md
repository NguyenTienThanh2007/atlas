# G2 pilot runbook: five-company private pilot

How to curate, check and time the first 5 real companies (gate G2, PRODUCT_DECISIONS A-6, D-5, D-6).
**Prepared 2026-11-26. Not started:** no real company has been curated, imported or verified.
Nothing here marks anything VERIFIED. Only an independent reviewer's recorded review does.

**No company names in this file, by design.** The owner's request of 2026-11-26 named five
tickers. They are not written here: this repository is public, and A-11 §5 keeps the pilot list in
the private workspace until G1 allows publishing. Put the names, the selection record, bundles, PDFs
and time logs in the private workspace. Never put them in `data/` or anywhere else in this repo.

Rules this runbook follows (not repeated here):
- [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md): roles, states, CLI, corrections.
- [PILOT_SELECTION_CRITERIA.md](PILOT_SELECTION_CRITERIA.md): E1–E8, the composition rules, what
  is curated.
- [WS4_4_DECISIONS.md](WS4_4_DECISIONS.md): classification.

## 0. Before the first company (all must be true)

| # | Precondition | Owner | Status 2026-11-26 |
| --- | --- | --- | --- |
| P0-1 | The five companies are confirmed by the owner and recorded in the private selection record (A-11 §5 template), with E1–E8 evidence | Owner | Shortlist confirmed 2026-11-23 (private); this request's five must match it. The owner checks this privately |
| P0-2 | Composition check: one company from each of the 4 sectors plus one more, **exactly 1 bank**, calendar fiscal years | Owner | Not checked in this repo (names are private) |
| P0-3 | An independent reviewer is appointed (Q-3). The curator and the reviewer are two different people | Owner | **Open.** Without this, nothing can become VERIFIED |
| P0-4 | Database roles are separated (SEC-01), so the two-person rule can't be skipped with one password | Owner approves, then engineering | **Open** |
| P0-5 | If testers use any machine other than the host: access control (SEC-02) | Owner (Q-7) | **Open.** Localhost-only use needs nothing |
| P0-6 | A **separate pilot database** (its own Compose project and volume). The sample fixture is never imported there | Engineering | Not created |
| P0-7 | The private workspace has folders for each company's documents, bundle, worksheets and time log | Curator | Not checked (outside the repo) |
| P0-8 | Conflict-of-interest line filled for the curator and the reviewer for each company (A-11 §5) | Curator, reviewer | Not started |

## 1. Per-company workflow (in order)

1. **Start the clock** (§7). Log every session.
2. **Collect evidence** (§2). Download each document from the company's own site or the
   regulator or exchange. Never use aggregators (A-6). Record the URL, retrieval time and SHA-256.
3. **Write the bundle** in the private workspace.
   - Data source: `source_type: company_disclosure`, `access_method: manual`,
     `commercial_usage_status: unknown`. Public access is not a licence.
   - Evidence: `verification_status: unverified` (the only state an import allows), with an
     `https://` `source_url`. Never use `file://` (SEC-03).
   - Statements: `amount_scale` as printed, and a `source_page` on **every** figure.
4. **Import into the pilot database:**
   `uv run python -m app.ingestion import <private path>/bundle.json`. Exit 0, or 2 with the issues
   listed. Fix the bundle and re-import; imports are idempotent.
5. **Classify the company** (§4), using the CLI's `classify` command with a different reviewer. Do
   this before importing more figures: after it, figures for metrics that don't apply are refused.
6. **Reconcile figures with their pages** (§5): the curator first, then the reviewer independently.
7. **Two-person verification** (§3). The reviewer records one review per evidence record. Anything
   that doesn't reconcile becomes `disputed`, never `verified`.
8. **Handle conflicts and corrections** (§6).
9. **Stop the clock.** Total the hours by activity (§7).
10. **Done for this company** only when all of the following hold:
    - every identity, listing and figure evidence record is `verified` by the reviewer;
    - every figure reconciles to its page;
    - the classification is recorded;
    - the hours are logged.

    This is A-10's definition of a verified company. A company with any `unverified`, `disputed`
    or `rejected` evidence is **not** verified, and must be reported that way.

## 2. Evidence collection checklist (curator, per company)

| ✓ | Item | Minimum tier | Record |
| --- | --- | --- | --- |
| ☐ | Audited consolidated financial statements, ≥3 fiscal years, unqualified opinion | T2 | URL, retrieval time, SHA-256, opinion page |
| ☐ | Annual report (business description, segments) | T3 | URL, retrieval time, SHA-256 |
| ☐ | Exchange listing notice or status (ticker, exchange, listing date, no warning) | T1 | URL, retrieval date, page or screenshot reference |
| ☐ | Legal name and tax code, from the audited report's cover page or notes | T2 | Page |
| ☐ | Sector justification: the largest revenue source from the segment note | T2/T3 | Page, one line |
| ☐ | Bank or non-bank evidence for the classification (business licence or the statement format) | T2/T1 | Page and a quote of the relevant line, in the private worksheet only |
| ☐ | The document is a text PDF or a scan (affects effort) | — | Yes/no |
| ☐ | No aggregator, no third-party copy, no cached mirror | — | Confirmed |

## 3. Two-person verification checklist (reviewer, per evidence record)

The reviewer works from the **same documents** (SHA-256 matches), not from the curator's notes.

| ✓ | Check |
| --- | --- |
| ☐ | I am not the curator, and my conflict-of-interest line is filled in |
| ☐ | The document's SHA-256 matches the evidence record |
| ☐ | The source is the company's own site, or the regulator or exchange (not T4) |
| ☐ | Each figure: value as printed, the **page**, the document's amount scale, the period (start and end), the scope (consolidated or separate), VND |
| ☐ | Signs are right (losses negative); restated comparatives are not mixed with the original figures |
| ☐ | Identity fields match exactly (NFC Vietnamese spelling) |
| ☐ | Record the decision: `uv run python -m app.ingestion review <evidence-id> --from unverified --decision verified\|disputed\|rejected --curator "<curator>" --reviewer "<reviewer>" --checked-against "<document>, p. N–M"` |
| ☐ | For `disputed` or `rejected`: `--notes` says what is wrong and where |

## 4. Company classification review

| ✓ | Check |
| --- | --- |
| ☐ | The kind is decided from the company's own documents, **never** from the sector, ticker or name (WS4-4-D1) |
| ☐ | `bank` only for a licensed credit institution that reports in the bank format. Securities firms and insurers are `other_financial`. Finance companies are decided case by case (Q-B partly open) |
| ☐ | The cited evidence is about this company and is not disputed, rejected or superseded (the database checks this) |
| ☐ | `--basis` says what the document says and on which page |
| ☐ | Curator and reviewer differ: `uv run python -m app.ingestion classify <company-id> --kind bank\|non_bank\|other_financial --evidence <company-evidence-id> --basis "…, p. N" --curator "…" --reviewer "…"` |
| ☐ | Exactly 1 company of the five is `bank` (P0-2) |

## 5. Source-page and figure reconciliation (worksheet template)

Keep one sheet per company, in the private workspace. The curator fills the left columns and the
reviewer the right ones, each without seeing the other's value first.

| Metric code | Fiscal year | Scope | Page | Printed value | Amount scale | Curator value (VND) | Reviewer value (VND) | Match? | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `net_revenue` | YYYY | consolidated | N | as printed | `trieu_dong` | … | … | yes / no | |

After import, compare the sheet with the API:
`GET /api/v1/companies/{id}/financial-statements`. Each figure's `source.page`, `reported_value` and
`reported_scale` must equal the sheet. Any difference means dispute the evidence (§6).

Absent metrics:
- The page shows "not yet collected" or "not applicable" (Phase A).
- If the curator checked the document and the line truly isn't there, note "checked, not reported,
  p. N" **in the private sheet**. Phase B records don't exist yet.
- These notes are the evidence WS4-4-D5 needs to decide on Phase B.

## 6. Conflicts and corrections

| Situation | Action (procedures in VERIFICATION_WORKFLOW §8) |
| --- | --- |
| Curator and reviewer values differ | Review `→ disputed` with notes. Both re-read the page. A curation error leads to a corrected bundle as revision N+1; then reject the old evidence |
| The import reports a `conflict` on master data | Never overwrite. Dispute, then reject the old evidence; a reviewed correction with new evidence |
| The company restated a figure | Import revision N+1 citing the new document; supersede the old evidence by review |
| The importer refuses a figure as "does not apply" | Check the classification first. If the classification is wrong, record a superseding classification; never force the figure in |
| The reviewer is unavailable | The record stays `unverified`. Never self-review |
| A suspected sample/real mix-up | Stop. The database refuses it; report the error text. Never use `session_replication_role` |

## 7. Time tracking (per company, private log)

G2 exists to measure effort before committing to 20–30 companies (D-5).

| Date | Person (role) | Activity | Start | End | Minutes | Note |
| --- | --- | --- | --- | --- | --- | --- |
| YYYY-MM-DD | initials (curator/reviewer) | collect · bundle · import · classify · reconcile · review · correct | hh:mm | hh:mm | n | |

Report per company: the total hours, hours by activity, and curator versus reviewer hours. Also
report the number of disputes and corrections, and whether the documents were text or scans. Report
the totals in this repo **without names** (for example "company 1–5"), as done for G2 progress in
PHASE_2_CHECKLIST P2-3.1.

## 8. What this runbook does not authorise

- It does not start the pilot. The owner starts it once P0-1 to P0-8 are met.
- It does not publish anything. Nothing is published before G1.
- It does not add real data to this repository or to any shared or public database.
- It does not implement Phase B.
- It does not mark any company VERIFIED without the reviewer's recorded reviews.
