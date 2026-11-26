# Verification workflow

How a real fact becomes **verified** in ATLAS. This page covers checklist items P2-2.1, P2-2.2,
P2-2.5 and P2-2.8, plus the import rules from P2-6.4 and P2-6.5. It was implemented in Phase 2
workstream 1 (migration `31b1317163eb`, approved by the owner on 2026-11-23).

Nothing here names a reviewer. The second reviewer is an open owner decision (**Q-3**). Until a
real person is appointed, nothing can be verified, because the database refuses it.

## 1. Roles and the two-person rule

| Role | Who | Does |
| --- | --- | --- |
| **Curator** | The person who prepares a record from the source document | Writes the import bundle: every figure with its page, the document's amount scale, and the evidence (URL, retrieval time, SHA-256) |
| **Reviewer** | A **different, independent human** (Q-3) | Re-checks the record against the same document and records a decision |

These rules are enforced by PostgreSQL, so they hold whatever client writes to the database:

- `curator ≠ reviewer`, compared without case or surrounding spaces.
- The reviewer can't be a name the system uses for itself: `system`, `atlas`, `auto`,
  `automated`, `automatic`, `bot`, `import`, `importer`, `ingestion`, `claude`, `ai`.
- Every review must say what was checked (`checked_against`: document and page).
- Nothing can be **inserted** as `verified`. Evidence starts as `unverified` (real) or `sample`
  (fixture), and only a review changes its state.

The database can't prove two names belong to two different people. Appointing an independent
reviewer is an owner responsibility (Q-3, PRODUCT_DECISIONS D-6).

## 2. What is checked, against which document (P2-2.2)

The source tiers, from most to least authoritative:
1. **T1:** regulator (SSC) or exchange (HOSE, HNX) notices.
2. **T2:** the company's audited financial statements.
3. **T3:** the company's annual report and investor-relations pages.
4. **T4:** third parties. **T4 is never accepted.** Aggregators are never a source (A-6).

| Field | Required evidence (minimum tier) | Reviewer checks |
| --- | --- | --- |
| Legal name, tax code | T2 cover/notes (or T1) | Exact spelling, NFC Vietnamese |
| Ticker, exchange, listing status | T1 | Status on the selection date (criteria E1, E2) |
| Sector | T2 segment note, or T3 business description | Largest revenue source per the taxonomy methodology (E3) |
| Business description | T3 or T2 | Written in ATLAS's own words; no copied text |
| Each financial figure | T2, with **page number** | Value as printed, the document's amount scale, period, scope (consolidated/separate), currency |

## 3. States and transitions (P2-2.5)

States of `evidence.verification_status`:

| State | Meaning |
| --- | --- |
| `unverified` | Imported, not yet reviewed (the only state a real import can create) |
| `verified` | An independent reviewer confirmed it against the document |
| `disputed` | A reviewer found a problem; it needs resolving |
| `rejected` | A reviewer found it wrong or unsupported |
| `superseded` | Replaced by newer evidence or a restatement; kept for history |
| `sample` | Fictional fixture data. It can never be reviewed and never become anything else |

These are the only transitions a review can record. Anything else is refused by the database.

| From → to | `verified` | `rejected` | `disputed` | `unverified` | `superseded` |
| --- | :-: | :-: | :-: | :-: | :-: |
| `unverified` | ✅ | ✅ | ✅ | — | ✅ |
| `disputed` | ✅ | ✅ | — | ✅ | ✅ |
| `verified` | — | — | ✅ | — | ✅ |
| `rejected` | — | — | — | ✅ (reopen) | — |
| `superseded` | — | — | — | — | — |
| `sample` | — | — | — | — | — |

A `verified` record can't be rejected directly; it is disputed first. Each review states the
`from_status` it saw. If the record has changed since, the review is refused, so two reviewers
can't silently overwrite each other.

## 4. Review history

`verification_reviews` can only be appended to: UPDATE and DELETE are refused by a trigger. A
changed decision is a new row, so the full history stays. Evidence that has reviews can't be
deleted (foreign key `RESTRICT`), and evidence content is immutable. To correct a source, record
new evidence.

| Column | Meaning |
| --- | --- |
| `evidence_id` | The evidence reviewed |
| `from_status`, `decision` | The state seen and the state chosen |
| `curator`, `reviewer` | Two different people |
| `checked_against` | Document and page(s) checked |
| `notes` | Optional reasoning |
| `reviewed_at` | Set by the database |

When a review verifies a company's or security's evidence, the database sets that record's
`last_verified_at` to the review time.

## 5. Recording a review (local only)

There is **no API** for reviews; the public API is read-only (a test checks this). Reviews are
recorded on the operator's machine:

```bash
cd backend
uv run python -m app.ingestion review <evidence-id> \
  --from unverified --decision verified \
  --curator "<curator>" --reviewer "<independent reviewer>" \
  --checked-against "Audited consolidated FS 2025, p. 6–9" [--notes "…"]
uv run python -m app.ingestion reviews <evidence-id>     # history, oldest first
```

`--curator`, `--reviewer` and `--checked-against` have no defaults. The command exits 0 when the
review is recorded. It exits 1 when the database refuses it (and says which rule), or 2 when an
argument is missing.

## 6. Financial figures: page, scale and exact conversion

Each real figure must carry the **page** of its source document. The statement must declare how
the document prints amounts:

| `amount_scale` | Meaning | Factor |
| --- | --- | --- |
| `dong` | đồng | 1 |
| `nghin_dong` | nghìn đồng (thousands) | 1,000 |
| `trieu_dong` | triệu đồng (millions) | 1,000,000 |

- There is no default. Any other value, such as `ty_dong` or `"1000"`, is rejected rather than
  guessed.
- Statement currency must be **VND**. Adding a currency means adding its scale names too.
- **Only currency amounts are scaled.** Per-share figures (`eps_basic`) and share counts are
  printed in units in Vietnamese statements and are stored as reported (scale 1).
- Each figure stores `value` (full units), `reported_value` (as printed), `reported_scale` and
  `source_page`. The database enforces `value = reported_value × reported_scale` exactly, and
  `reported_scale ∈ {1, 1000, 1000000}`.
- **Real** figures need `source_page` and the as-reported value (importer and database trigger).
  Fictional sample figures don't.
- Arithmetic is exact: a 60-digit decimal context that raises on any rounding. Values that don't
  fit `NUMERIC(38,6)` after scaling (|value| ≥ 10³²) are rejected.
- The original currency is the statement's `currency`. No currency conversion ever happens.
- The figure's document is the statement's `source_evidence` (URL, retrieval time, SHA-256).
  Together with `source_page`, that links each figure to an exact page.

## 7. Reporting periods (P2-6.4)

- **Fiscal year naming:** a fiscal year is named after the calendar year it **ends** in, so
  non-calendar years work. A July 2025 – June 2026 year is FY2026.
  - An annual period must end in `fiscal_year`.
  - A quarter must end in `fiscal_year` or the year before (Q1 of FY2026 ends 30 Sep 2025).
- **Span:** an income or cash-flow period lasts **80–100 days** (quarter) or **360–371 days**
  (year), counting both end dates. A leap year (366) is fine.
- **Balance sheets** are a position at one date: `reporting_period_start` = `reporting_period_end`.
- **Overlap:** a statement is rejected as a `conflict` if another stored statement overlaps its
  period and has the same company, statement type, scope **and granularity** (annual vs
  quarterly).
  - Annual and quarterly statements of the same year may cover the same months.
  - Revisions of the same statement (same fiscal year, quarter and period end) are not overlaps.
  - Consolidated and separate statements are independent.
  - Ranges are inclusive, so two periods sharing a day overlap.
- **Not supported yet:** transitional fiscal periods, such as a 6- or 15-month year after a
  company changes its year-end. They are rejected and would need an explicit, reviewed exception.
  The quarter number isn't checked against the months, because that needs the company's
  year-end, which isn't stored yet.
- **Stand-alone quarters only (W3-D1, 2026-11-26):** a quarterly income or cash-flow figure must be
  printed in the document for that quarter alone ("Quý này"). Never type a figure derived by
  subtracting two year-to-date ("Lũy kế từ đầu năm") columns: that would be a calculated figure
  recorded as reported. If only year-to-date figures are printed, import no quarter for it.

The overlap check runs in the importer, not as a database constraint. Two imports running at the
same moment could both pass; imports are run one at a time by a curator.

## 8. Corrections (P2-2.8)

| Situation | Procedure |
| --- | --- |
| A stored figure is wrong in our data (curation error) | Dispute the evidence (review `→ disputed`), then reject it. Import the corrected statement as revision N+1. History is kept (append-only statements and metrics) |
| The company restated its figures | Import revision N+1 with the new document as evidence. Mark the old evidence `superseded` by review |
| A source document was replaced | Record new evidence (evidence is immutable). Supersede the old evidence by review |
| Company master data is wrong (name, tax code, sector) | Imports report this as a `conflict` and never overwrite (Phase 1 L-3). The fix is a reviewed correction: dispute → reject the old evidence, then a deliberate, reviewed database change with new evidence. A tooled update path is future work |
| A review decision was wrong | Record a new review (for example `verified → disputed`). Reviews are never edited |

## 8a. Company classification (WS4-4, 2026-11-26)

A company counts as a **bank**, **non-bank** or **other financial company** (securities firm,
insurer and similar; no applicability claim is made for these) only through a reviewed record.
Never decide it from the sector, ticker or name: the Banking & Financial Services sector also holds
securities firms, insurers and finance companies. A finance company or other non-bank credit
institution is decided case by case from its own documents (an accountant's view is pending, Q-B).

```
uv run python -m app.ingestion classify <company-id> --kind bank|non_bank|other_financial \
    --evidence <company-evidence-id> --basis "what the document says, page" \
    --curator "…" --reviewer "…" [--supersedes <classification-id>]
```

- The evidence must be about that company and must not be disputed, rejected or superseded; a
  sample company uses sample evidence.
- Curator and reviewer are two different people, as for reviews (§1).
- Records are never edited. A correction is a new record with `--supersedes`; there is one chain
  per company and its last record counts.
- If the cited evidence is later disputed or rejected, the company is shown as unclassified again.
- Once a company is a bank or non-bank, the importer refuses figures for metrics the dictionary
  marks `not_applicable` for that kind. Figures stored earlier stay and are flagged on the page.

## 9. Migration behaviour (`31b1317163eb`)

- **Upgrade:**
  - Adds `verification_reviews`, the `rejected` state, the figure provenance columns and the
    triggers.
  - Existing rows are untouched. Their statuses are kept, including any pre-existing `verified`
    row, and their provenance columns are `NULL`. The new requirements apply only to rows
    inserted afterwards.
- **Downgrade:** refuses to run if any review, `rejected` evidence or figure provenance exists, so
  history is never silently discarded. Otherwise it restores the previous schema exactly.
- **Verified:** upgrade → `alembic check` → downgrade → upgrade on a clean database and on a
  database holding Phase 1-era data (sample fixture, a legacy `verified` row, a figure without
  provenance). The data was unchanged after each step, and the downgrade was refused once a
  review existed.
