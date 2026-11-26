# WS4-4: Missing-data semantics and bank applicability — design

**Status update (2026-11-26, implementation): Phase A implemented on branch `feat/ws4-4-phase-a`
(uncommitted) as designed: migration `5c1f0a2b7e44`, `classify` CLI, `classification`,
`absent_metrics`, `applicability_conflict`, importer refusal, `metric_not_applicable` and
`input_not_applicable`. Phase B not implemented (D5, D6). Choices made while building: the company
list now runs 4 fixed queries (one for the page's classifications); ROE/ROA and comparison ranks
were renumbered to insert the new codes without changing the order of existing codes; the
classification's `source` has `page: null` because the record has a `basis` text, not a page
column. Evidence per item in [WS4_4_CHECKLIST.md](WS4_4_CHECKLIST.md).**

**Status update (2026-11-26, later): decisions WS4-4-D1 to D10 APPROVED by the owner as proposed
(PRODUCT_DECISIONS §2f). Phase B design approved, its implementation deferred (D5, D6).
Implementation of Phase A is not authorised yet and has not started.** Original status follows:

**Status: DESIGN — REQUIRES OWNER REVIEW. Not implemented, not authorised.** This document changes
no code, model, migration, dictionary value or data. Decisions it needs are in
[WS4_4_DECISIONS.md](WS4_4_DECISIONS.md); acceptance items in [WS4_4_CHECKLIST.md](WS4_4_CHECKLIST.md).

| | |
| --- | --- |
| Written | 2026-11-26 |
| Commit inspected | `main` @ `9d44fb4be755bda90aae2379e98c324761188edf` (PR #11 merge; contains PRs #9, #10, #11) |
| Working tree | Clean before this task; documents written on branch `docs/ws4-4-design` (uncommitted) |
| Phase 2 items | P2-5.15 (missing data); bank display for the pilot (A-7 sector); WS4-F2, F3, F8, WS4-I6 |

**Labels used on every statement:** **[F]** verified fact (checked in the code or documents at the
commit above) · **[A]** owner-approved decision · **[P]** proposal · **[Q]** open question ·
**[H]** human dependency.

**Naming.** [F] The WS4 plan's §13 used "WS4-4" for a UI step and "WS4-6" for explicit records.
The workstreams actually delivered are numbered differently (WS4-1 dictionary, WS4-2 ROE/ROA,
WS4-3 comparisons). In this document **WS4-4 = missing-data semantics and bank applicability**.
[P] A dated note in the WS4 plan should record the renumbering (§12).

---

## 1. What exists today

### 1.1 Metric dictionary (`backend/app/reference/metric_dictionary.json`)

- [F] Version `1.1.0`, 17 metrics. Each has `applicability: {non_bank, bank}`, values
  `applicable` / `not_applicable` / `unclassified`, both keys required with no default
  (`MetricApplicability` in `ingestion/reference.py`; tests
  `test_applicability_is_explicit_and_as_approved`, `test_applicability_has_no_default[*]`).
- [F] Every bank value matches the owner-approved basis (PRODUCT_DECISIONS §2d note, data/README):

| Metric | Bank | Non-bank | Basis |
| --- | --- | --- | --- |
| `net_revenue`, `gross_profit` | `not_applicable` | `applicable` | [A] WS4-D5 |
| `net_interest_income` | `applicable` | `unclassified` | [A] WS4-D4; non-bank: no decision |
| `net_profit`, `total_assets` | `applicable` | `applicable` | [A] bank ROA inputs (WS4-D2, D4) |
| `net_profit_parent`, `equity_parent` | `applicable` | `applicable` | [A] consolidated bank ROE inputs (WS4-D1, D4) |
| `total_equity` | `applicable` | `applicable` | [A] separate bank ROE input (WS4-D1, D4) |
| `operating_profit`, `profit_before_tax`, `eps_basic`, `total_liabilities`, `cash_and_equivalents`, `shares_outstanding`, `operating_cash_flow`, `investing_cash_flow`, `financing_cash_flow` | `unclassified` | `applicable` | [A] no decision for banks; non-bank column approved (WS4 plan §3.1) |

- [F] Nothing in the code reads `applicability` except the dictionary endpoint
  (`GET /api/v1/metric-dictionary`) and its tests. `unclassified` is not mapped to anything.

### 1.2 Companies and sectors

- [F] `companies` has `legal_name`, `short_name`, `english_name`, `tax_code`, `description`,
  `website`, `sector_id`, `is_sample`, `last_verified_at`, timestamps. **No bank / non-bank field.**
- [F] Sector taxonomy 1.0.0 (`sector_taxonomy.json`): `BANKING_FINANCIAL` is described as
  "Commercial banks, securities firms, insurers, consumer finance and other financial
  intermediaries". **A sector cannot tell a bank from a securities firm or an insurer.**
- [F] The importer never updates a stored company: any different field, sector or `is_sample` is a
  `conflict` (`importer.py` `_apply_company`). There is no path to change a company's attributes
  after import.
- [F] `CompanyOut` / `CompanyListItem` expose sector, securities and the fields above; no kind.
- [F] Company evidence rows exist (`evidence.entity_type = 'company'`), with WS1 verification
  reviews (append-only, curator ≠ reviewer, reviewer must be a person — `verification_reviews`
  check constraints).

### 1.3 Financial figures

- [F] `financial_metrics.value` is `NUMERIC(38,6) NOT NULL`; one row per (statement, metric)
  (`uq_metric_per_statement`); `source_page` required for real figures (trigger
  `financial_metrics_provenance`); `financial_statements` and `financial_metrics` are append-only
  (`atlas_reject_history_change`); restatements are new revisions (`supersedes_id`).
- [F] A row means a reported figure, including a real zero. Absence of a row proves nothing about
  the document.
- [F] Invalid input is rejected at import and never stored; the reason is kept in
  `ingestion_runs.issues` (JSONB). No API exposes ingestion runs.
- [F] Evidence status (`unverified`, `verified`, `disputed`, `rejected`, `superseded`, `sample`) is
  on the statement's evidence, separate from availability.
- [F] Sample/real isolation is enforced by triggers (`8de09b58f4c2`) on statements, evidence,
  companies (`is_sample` immutable once data exists) and securities, and again in the engines.

### 1.4 Calculations and comparisons

- [F] ROE/ROA (`calculations/ratios.py`, `service.py`): a missing input gives `missing_input`,
  `missing_opening_balance` or `ambiguous_opening_balance`; disputed/rejected/superseded inputs are
  refused; no fallback to older revisions; `mixed_sample_and_real` ranks first.
- [F] Comparisons (`comparisons.py`, `comparison_service.py`): rows only for metrics reported on at
  least one side; `missing_current_value`, `missing_previous_value`, `missing_previous_period`.
- [F] All ROE/ROA inputs are `applicable` for both bank and non-bank, so `not_applicable` can never
  be an ROE/ROA input under dictionary 1.1.0.

### 1.5 Frontend

- [F] The company page lists each statement's **present** metrics only; absent metrics are not
  shown at all (`app/[lang]/companies/[id]/page.tsx`). Calculated ratios and comparisons show
  reason texts. No "not applicable" or "not yet collected" text exists in `vi.ts` / `en.ts` today.

### 1.6 Decisions that already govern this work

| ID | Content | Status |
| --- | --- | --- |
| WS4-D4 | Minimal bank scope: `net_interest_income`, ROE, ROA | [A] 2026-11-24 |
| WS4-D5 | `net_revenue`, `gross_profit` not applicable for banks | [A] 2026-11-24 |
| WS4-D6 | Seven-state vocabulary; **Phase A only, no schema change**; Phase B not approved | [A] 2026-11-24 |
| WS4-D7, D11 | Calculated values never verified; unverified-input label; private pilot only | [A] 2026-11-24 |
| WS4-D10 (G-2) | Dictionary applicability per kind, `unclassified` ≠ not applicable | [A] 2026-11-24, implemented (PR #6) |
| WS4-D12 | `equity_parent` only when the statement reports it; never derived | [A] 2026-11-24 |
| A-7 | Banking & Financial Services is a pilot sector | [A] 2026-11-23 |

### 1.7 Contradictions found

| ID | Finding | Proposed handling |
| --- | --- | --- |
| C-1 | [F] WS4 plan §7.1 says `not_applicable` needs "companies [to] have a bank / non-bank type", but WS4-D6 approved Phase A as "no schema change". A company kind is a schema change, so Phase A as approved **cannot** show `not_applicable` | [P] Decide the classification store separately (WS4-4-D1, D9). D6 is not reopened: its "no schema change" is read as covering explicit missing-data records only — the owner should confirm that reading |
| C-2 | [F] P2-5.15's title says "show 'not reported'", but under WS4-D6 Phase A absence must never be shown as "not reported" | [P] Dated note on P2-5.15: Phase A acceptance is "not yet collected / not applicable, never zero"; "not reported" needs Phase B |
| C-3 | [F] WS4-F3's "Remaining: dictionary applicability implemented (WS4-B6)" is stale: B6 is PASS; the real gap is the per-company kind | [P] Dated note on WS4-F3 |
| C-4 | [F] The dictionary has only two kinds (`bank`, `non_bank`) but the pilot sector also contains securities firms, insurers and finance companies, whose statements also differ from the general corporate forms | [Q] Which kind do they get? (§2.4, WS4-4-D2) |
| C-5 | [F] WS4 plan §13 numbering differs from the delivered WS4-x workstreams | [P] Dated note (§12) |

---

## 2. Workstream A — company classification

### 2.1 Requirements

- Values: **bank**, **non-bank**, and **unclassified** (unknown). Unknown is the default and must be
  representable without a row being invented.
- Evidence-backed: a classification cites a document (the company's own disclosure or licence
  information) like every other ATLAS record.
- Never guessed from the sector, ticker or name. A diversified financial group is not a bank
  because it owns one.
- Changes are traceable: old classifications stay; a change says what it replaced.
- Sample/real isolation holds.
- [P] Two-person reviewed under WS1 before the classification can drive "not applicable".

### 2.2 Alternatives

| | A. `company_kind` column on `companies` | B. Versioned classification records with evidence and review | C. Derive from sector | D. Hybrid: column + history table |
| --- | --- | --- | --- | --- |
| Correctness | Good if set correctly | Good | **Wrong:** `BANKING_FINANCIAL` includes securities firms, insurers, finance companies [F] | Good |
| Auditability | Weak: who set it and from which document is not recorded; `companies.updated_at` only | Strong: evidence, curator, reviewer, time per row | None beyond the sector's evidence | Strong in the history table; the column can drift from it |
| History | Lost on update (and the importer refuses updates [F], so changing it needs a new write path anyway) | Append-only rows with `supersedes_id`, like statement revisions | Sector changes would silently re-classify | Kept, but two sources of truth |
| Importer impact | New optional field in `CompanyIn`; conflict rules for changes | Separate record type in the bundle (or a curator command), not a company field | None | Both |
| API compatibility | Additive field | Additive field on `CompanyOut` (derived current value) | None | Additive field |
| Frontend | Read one field | Read one field; history optional | — | Read one field |
| DB constraints | Enum + default `unclassified` | Enum, FK to company and evidence, append-only trigger, unique chain, review checks, isolation trigger | — | All of B plus keeping the column in sync (trigger) |
| Migration | Small (one column) | One table, triggers; no change to existing rows | None | Largest |
| Reviewer workflow | None unless added | Same two-person rule as WS1 (`curator ≠ reviewer`, reviewer is a person) | None | As B |
| Unknown | Default value | **No current row** = unclassified | Impossible to express | Default value |
| Change review and trace | No | Yes | No | Yes |

### 2.3 Recommendation [P]

**Option B: an append-only `company_classifications` record, with evidence and a two-person
review, and no column on `companies`.** The current classification is derived (latest row in the
chain); "no row" means unclassified.

- Correct and honest: unknown is the absence of a reviewed claim, the same way absence of a metric
  row is "not yet collected".
- Auditable and reversible: a wrong classification is corrected by a new row that supersedes it,
  never by an update.
- One source of truth (D's column would need a sync trigger and could disagree).
- Cost: one table, its triggers and a read join. Accepted.

Rejected: C (provably wrong for this taxonomy), A (no audit trail, and the importer has no update
path), D (duplication without benefit at pilot scale).

### 2.4 Kinds for other financial companies [Q]

The dictionary has `bank` and `non_bank` columns only [F]. Securities firms, insurers and finance
companies may report on forms that differ from both (WS4 plan §6.1 describes only banks). Options:

1. Classify them `non_bank` → would claim, for example, that `gross_profit` *applies* to an insurer.
2. Classify them `bank` → would claim bank rules apply.
3. **[P] Recommended:** add a third kind, `other_financial`, for which **no applicability claim is
   made** (every metric behaves as `unclassified`) until the dictionary gains a column for it
   (a later dictionary change, separate approval).

[H] Which kind a non-bank credit institution (for example a finance company) belongs to needs an
accountant's confirmation; ATLAS must not decide it from the name.

---

## 3. Workstream B — applying dictionary applicability per company

### 3.1 Effective applicability [P]

`effective(company, metric)` is computed at read time, never stored:

| Company classification (current, reviewed) | Dictionary value for that kind | Effective applicability | Meaning for an absent figure | Meaning for a present figure |
| --- | --- | --- | --- | --- |
| `bank` | `applicable` | `applicable` | `not_yet_collected` | `reported` |
| `bank` | `not_applicable` | `not_applicable` | `not_applicable` | **conflict** (§3.3) |
| `bank` | `unclassified` | `unknown` | `not_yet_collected` | `reported` |
| `non_bank` | `applicable` | `applicable` | `not_yet_collected` | `reported` |
| `non_bank` | `not_applicable` | `not_applicable` | `not_applicable` | **conflict** (§3.3) |
| `non_bank` | `unclassified` | `unknown` | `not_yet_collected` | `reported` |
| `other_financial` (if approved) | any | `unknown` | `not_yet_collected` | `reported` |
| unclassified (no current row; or, if WS4-4-D7 so decides, a current row whose evidence is disputed or rejected) | any | `unknown` | `not_yet_collected` | `reported` |

Rules: `unknown` never becomes `not_applicable`; `not_applicable` comes only from a reviewed
classification **and** a dictionary value of `not_applicable`; an absent figure is never zero.

### 3.2 API behaviour [P] (all additive; no field removed or renamed)

| Endpoint | Change |
| --- | --- |
| `GET /companies`, `GET /companies/{id}` | New `classification`: `{kind: "bank" | "non_bank" | "other_financial" | "unclassified", classified_at, evidence: {…WS3 source…} | null}`. `unclassified` when no reviewed row. Never inferred |
| `GET /companies/{id}/financial-statements` | Each statement gains `absent_metrics`: `[{metric_code, metric_name_vi, metric_name_en, state: "not_yet_collected" | "not_applicable", applicability_basis: "dictionary_bank" | "dictionary_non_bank" | null}]` for dictionary metrics of that statement type with no row. Present metrics gain `applicability_conflict: bool` (§3.3). Existing fields unchanged |
| `GET /metric-dictionary` | Unchanged (already serves applicability) |
| `GET /companies/{id}/calculated-metrics` | Unchanged formulas and codes. ROE/ROA inputs are applicable for both kinds [F], so no new reason is needed in Phase A |
| `GET /companies/{id}/comparisons` | Unchanged in Phase A except one defensive reason (§3.3) |
| Sample companies | Same rules; their classification rows must use sample evidence (isolation trigger extended) |

### 3.3 A reported figure for a metric that does not apply [P]

Possible only through data entered before classification, or a wrong classification. Rules:

- Importer: refuse a new figure whose effective applicability is `not_applicable`
  (`invalid`: "metric not applicable to this company kind").
- Existing rows are never deleted (append-only). The API marks them `applicability_conflict: true`;
  the UI shows the value with a warning "Chỉ tiêu không áp dụng cho loại doanh nghiệp này — cần kiểm
  tra lại" / "This metric does not apply to this kind of company — needs checking".
- Comparisons of such a metric: `not_comparable` with a new reason `metric_not_applicable`
  (rank after `unit_or_currency_mismatch`, before rank 9). This changes the W3-D10 code list, so it
  needs approval (WS4-4-D4).

### 3.4 UI behaviour [P] (vi first, en at `/en`)

| Case | vi | en |
| --- | --- | --- |
| Classification shown in the company facts | "Loại doanh nghiệp: Ngân hàng / Không phải ngân hàng / Tổ chức tài chính khác / Chưa phân loại" | "Company type: Bank / Non-bank / Other financial / Not classified" |
| Absent, `not_yet_collected` | "Chưa thu thập" | "Not yet collected" |
| Absent, `not_applicable` | "Không áp dụng", with the visible note "theo phân loại doanh nghiệp đã kiểm tra" | "Not applicable", with "based on the reviewed company classification" |
| Unclassified company | Note under the statements: "Doanh nghiệp chưa được phân loại, nên ATLAS không đánh dấu chỉ tiêu nào là không áp dụng." | "This company isn't classified yet, so ATLAS marks no metric as not applicable." |

Never a dash or 0 for an absent figure. Absent rows are listed after the present ones, muted, and
kept in both languages (key parity test). Texts join the glossary review [H].

---

## 4. Workstream C — the seven states

Availability is one dimension; verification status is another [A] (WS4-D6, WS4 plan §7.1).

| | `reported` | `not_yet_collected` | `pending_verification` | `not_applicable` | `not_reported` | `unavailable` | `invalid` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Meaning | Row exists; value as printed, incl. 0 | No confirmed figure; says nothing about the document | A reported figure whose evidence is not `verified` | Metric does not apply to the company's reviewed kind | Curator checked the document; the line is not presented | The document was not published or could not be obtained | A submitted figure failed validation |
| Phase | Exists [F] | A | Exists [F] (as evidence status) | A (needs classification store, §2) | **B** | **B** | Exists [F] (ingestion runs) |
| Evidence required | Statement evidence + page [F] | None (absence) | Evidence status | Reviewed classification + dictionary rule | Statement evidence (the document checked) + pages checked | Attempt record: URL or channel tried, date, outcome | Ingestion issue |
| Created by | Importer | Derived | Importer (`unverified`) | Derived | Curator | Curator | Importer (refusal) |
| Reviewed by | WS1 reviewer | — | WS1 reviewer moves it to `verified` | Classification reviewer (two-person) | Second person (WS1 rule) | Second person | — |
| Stored | Yes | No | Yes (evidence) | No (derived) | Yes (new record) | Yes (new record) | Run log only |
| Visibility | Private pilot; public only after G1 [A] | Same | Same, with label [A] | Same | Same | Same | Coverage report / curator tools only, never on the company page |
| API | Figure | `absent_metrics[].state` | Figure's `source.verification_status` | `absent_metrics[].state` | Phase B: `absent_metrics[].state = "not_reported"` with record | Phase B: statement-level `availability` | Not exposed |
| UI vi / en | value | "Chưa thu thập" / "Not yet collected" | existing status label | "Không áp dụng" / "Not applicable" | "Không trình bày trong báo cáo" / "Not presented in the report" [P] (WS4 plan §7.1 proposal; D6 approved the vocabulary, not the texts) | "Không có tài liệu nguồn" / "Source not available" [P] (same), plus sub-reason | — |
| In ROE/ROA | Used (unless disputed/rejected/superseded) [F] | Not computable [F] | Used with label [A] | Not computable (`input_not_applicable`, §6) | Not computable | Not computable | Never |
| In comparisons | Used [F] | Not comparable [F] | Used with label [F] | No row / `metric_not_applicable` (§3.3) | Not comparable | Not comparable | Never |
| Transitions | New revision supersedes; review changes evidence status [F] | → `reported` (import), → `not_reported` / `unavailable` (Phase B record) | → `verified` / `disputed` / `rejected` (WS1) | Changes only when a new classification supersedes the old | → superseded by a later record or by a `reported` figure in a new revision | → superseded when the document is obtained | Resubmission creates a new run |
| History | Append-only [F] | — | `verification_reviews` [F] | Classification chain | Append-only records with `supersedes_id` | Same | Run log [F] |

### 4.1 `unavailable` sub-reasons [P] (Phase B)

| Code | Meaning | Note |
| --- | --- | --- |
| `not_published` | The company did not publish the document for that period | Evidence: where it was looked for and when |
| `inaccessible` | Published but could not be retrieved (broken link, removed) | Re-check later |
| `temporarily_unavailable` | Expected to appear (late filing) | Expires; re-check date required |
| `access_restricted` | Behind a login or paywall ATLAS has no right to use | **Never bypassed** |
| `rights_restricted` | Obtainable, but terms forbid ATLAS's use | Links to G1 / source terms (Q-2) |

---

## 5. Workstream D — Phase A and Phase B

### 5.1 Phase A [A] scope as approved, plus the classification store [P]

1. Company classification (§2) — **needs WS4-4-D1 and D9** because it is a schema change (C-1).
2. Effective applicability (§3.1) computed at read time from the dictionary.
3. `absent_metrics` with `not_yet_collected` / `not_applicable` on statements (§3.2).
4. UI states (§3.4); never 0 or a dash; the unclassified note.
5. Importer refusal of figures for not-applicable metrics (§3.3) and the conflict flag.
6. Calculation and comparison safety (§6) — mostly already true [F]; tests added.
7. No `not_reported`, no `unavailable` (WS4-D6 [A]).

If WS4-4-D1 is **not** approved, Phase A can still deliver items 3 (with `not_yet_collected` only),
4 and 6, and show no "not applicable" anywhere; banks' `net_revenue` would then read "not yet
collected" (the risk WS4-D4 described).

### 5.2 Phase B [P] — separate approval required (WS4-D6 did not approve it)

Two records, because the claims differ in scope:

| | `metric_not_reported` (metric level) | `source_availability` (document level) |
| --- | --- | --- |
| Refers to | One `financial_statements` row (the document that was checked, specific revision) + `metric_code` | Company, `statement_type`, `scope`, granularity, `fiscal_year`, `fiscal_quarter`, period dates (no statement exists) |
| Evidence | The statement's evidence; `pages_checked` (int array, ≥ 1 for real data) | Attempt: `source_url` or channel, `attempted_at`, `sub_reason` (§4.1), optional `recheck_after` |
| People | `curator`, `reviewer` (≠ curator, a person), `checked_against` | Same |
| History | Append-only; `supersedes_id`; one current record per key (partial unique index) | Same |
| Ends when | A later revision reports the metric (the record stays as history of that revision) | A statement for that period is imported |

Alternatives considered for Phase B:

| Option | Verdict |
| --- | --- |
| Make `financial_metrics.value` nullable with a `state` column | Rejected: breaks "a row is a reported figure" [F], every calculation's assumption, and the append-only history of existing rows |
| A JSON list of "not presented" items on the evidence row | Rejected: no constraints, no per-item review, not queryable |
| One generic `metric_availability` table for both states | Possible, but `unavailable` has no statement to point at; two records keep constraints simple |
| **Two records as above** | **Recommended** |

---

## 6. Workstream E — calculation safety

| State of an input | ROE / ROA | Annual YoY | Quarterly QoQ | Quarterly YoY |
| --- | --- | --- | --- | --- |
| `reported`, verified or unverified | Used; `input_verification` label [F] | Used [F] | Used [F] | Used [F] |
| `reported`, disputed / rejected / superseded evidence | Refused, no fallback [F] | Refused [F] | Refused [F] | Refused [F] |
| `reported`, sample/real mismatch | Refused, rank 0 [F] | Refused, rank 0 [F] | same | same |
| `not_yet_collected` | `missing_input` / `missing_opening_balance` [F] | `missing_current_value` / `missing_previous_value` / `missing_previous_period` [F] | same | same |
| `not_applicable` | Cannot occur under dictionary 1.1.0 (all inputs applicable for both kinds) [F]; [P] defensive reason `input_not_applicable` if a future dictionary changes that | No row; if a conflicting row exists → `metric_not_applicable` [P] | same | same |
| unknown applicability | Treated as applicable-but-absent (`missing_*`), never as N/A [P] | same | same | same |
| `not_reported` (Phase B) | [P] `input_not_reported` (replaces `missing_input` for that input) | [P] `current_not_reported` / `previous_not_reported` | same | same |
| `unavailable` (Phase B) | [P] `source_unavailable` | [P] `source_unavailable` | same | same |
| `invalid` | Never stored, so never an input [F] | same | same | same |

- Formulas, rounding and existing reason codes are unchanged [A] (WS4-D1 to D3, D9, W3-D4).
- [P] New codes (`input_not_applicable`, `metric_not_applicable`, Phase B codes) slot into the
  existing precedence **after** the corresponding `missing_*` rank, so existing results keep their
  first reason. Any new code needs owner approval (WS4-4-D4, D5).
- Provenance stays attached to every reported input [F]; absent inputs carry no source.

---

## 7. Workstream F — data model and migration impact (proposal only; no migration written)

### 7.1 Phase A: `company_classifications`

| Column | Type | Rule |
| --- | --- | --- |
| `id` | uuid PK | — |
| `company_id` | uuid FK → companies, `ON DELETE RESTRICT` | — |
| `kind` | enum `company_kind` (`bank`, `non_bank`, `other_financial`) | No `unclassified` value: absence of a current row is unclassified |
| `evidence_id` | uuid FK → evidence | Evidence must be about this company (`entity_type = 'company'`, same company); sample/real class must match the company (extend `atlas_isolate_*`) |
| `basis` | text, non-empty | What the document says (e.g. "licensed as a commercial bank, p. 3") |
| `curator`, `reviewer` | varchar(120) | Same checks as `verification_reviews`: present, different, reviewer is a person |
| `supersedes_id` | uuid FK → company_classifications, nullable, **unique** | Chain; `(supersedes_id IS NULL)` allowed once per company (partial unique index on `company_id WHERE supersedes_id IS NULL`) |
| `decided_at` | timestamptz, `clock_timestamp()` | — |

- Append-only trigger (reuse `atlas_reject_history_change`).
- Current = the row no other row supersedes. Concurrency: two curators superseding the same row →
  the unique index rejects the second; inserting the first row twice → the partial unique index
  rejects it. The insert takes `FOR SHARE` on the company row, like the isolation triggers.
- [Q] Whether the evidence must itself be `verified` before the classification counts, or the
  classification's own two-person review is enough (WS4-4-D7).
- Indexes: `(company_id, decided_at)`.
- Existing rows: none; every existing company stays unclassified. No backfill, no guess.
- Downgrade: drop table, triggers and enum; no other data touched. Rollback risk: none for existing
  data; classifications entered after upgrade are lost on downgrade (documented).
- API compatibility: additive `classification` object.

### 7.2 Phase B (only if approved): `metric_not_reported`, `source_availability`

Columns as §5.2; both append-only with the chain/partial-unique pattern above; FKs `RESTRICT`;
sample/real isolation extended (record class must match the company, as for statements);
`pages_checked` positive integers, required for real data (like `source_page`); no `NUMERIC`
values are stored, so `NUMERIC(38,6)` exactness is unaffected. Upgrade creates empty tables;
downgrade drops them.

### 7.3 Things that must not change

`financial_metrics.value NOT NULL`, append-only history, WS1 review rules, isolation triggers,
`NUMERIC(38,6)`, existing response fields, approved formulas and reason codes.

---

## 8. Workstream G — test strategy (fictional fixtures only: `example.test`, `TST` tickers)

| Area | Cases |
| --- | --- |
| Seven states | Each state produced and displayed; `invalid` never stored; `not_reported` / `unavailable` absent in Phase A (no such text rendered) |
| Kind × applicability | All 8 rows of §3.1 for an absent and a present figure; `unclassified` dictionary value never yields `not_applicable` |
| Unknown classification | No row → `unknown`; a superseded row never counts; evidence disputed/rejected → `unknown` if D7 says so |
| Bank / non-bank fixtures | Fictional bank: `net_revenue`, `gross_profit` "not applicable"; ROE/ROA computed; `operating_profit` "not yet collected". Fictional non-bank: unaffected. Fictional insurer (if `other_financial` approved): no N/A anywhere |
| Sample / real | Sample classification needs sample evidence; mixed refused by the database and the API |
| Evidence status | Classification evidence `disputed` / `rejected` → classification no longer counts (if D7 says so) |
| Missing rows vs zero | A real 0 is `reported` and computes; an absent row is never 0 (API string null, UI text) |
| Source unavailable / restricted (Phase B) | Each sub-reason; `access_restricted` never fetched |
| Revisions | Restatement adds a figure → state `reported`; Phase B record bound to the old revision stays history |
| Reviewer separation | curator = reviewer refused; reviewer "system"/"ai" refused |
| Concurrency | Two supersessions of one row: one wins; two first rows: one wins (two connections, as in `test_sample_isolation.py`) |
| Calculation refusal | Each new reason code and its rank; existing codes unchanged (WS4-2 and WS4-3 suites green) |
| Comparison refusal | `metric_not_applicable` for a conflicting row |
| API | Additive shape; OpenAPI; old clients' fields unchanged; pagination unchanged; float trap |
| Frontend | vi/en key parity; states never 0 or dash; 375 px; keyboard; route check per absent metric |
| Migration | Round trip (upgrade/downgrade) for the classification table; Phase B tables only if approved |

---

## 9. Implementation sequence (after approval only)

1. **WS4-4a** — classification table, triggers, model, tests (needs D1, D7, D9).
2. **WS4-4b** — curator path to add a classification (CLI like `review`), fixture support.
3. **WS4-4c** — effective applicability, `absent_metrics`, `classification` in the API; importer
   refusal and conflict flag (needs D3, D4).
4. **WS4-4d** — UI states, texts, route check, browser pass (needs D8).
5. **WS4-4e** — verification, docs, checklists, PR with a recorded review.
6. **Phase B** — only after a separate approval (D5, D6); its own plan.

## 10. Risks and open questions

| ID | Item | Label |
| --- | --- | --- |
| R-1 | Classifying a financial group or finance company wrongly | [H] accountant input; [P] two-person review; `other_financial` |
| R-2 | Absent metrics shown as a long list of "not yet collected" for banks (many `unclassified` bank values) | [P] accept: honest; revisit when the dictionary classifies more bank metrics |
| R-3 | Reviewer (Q-3) not appointed: no classification can be reviewed, so every company stays unclassified | [H] Q-3 |
| R-4 | New Vietnamese texts | [H] glossary native-speaker review |
| R-5 | Phase B curation hours | [Q] measure in G2 first |
| Q-A | Does WS4-D6's "no schema change" also forbid the classification table? (C-1) | [Q] owner |
| Q-B | Kind for securities firms, insurers, finance companies (C-4) | [Q] owner; [H] accountant |
| Q-C | Must classification evidence be verified, or is the classification's own review enough? | [Q] owner (D7) |

## 11. Not in scope

New metrics, dictionary value changes, sign conventions (G-3), NPL/CAR (WS4-D4 future scope),
real data, public display (G1).

## 12. Proposed dated reconciliations (not made here)

- WS4 plan §13: note that delivered workstream numbers differ (C-5).
- WS4-F3: note that the remaining gap is the per-company kind (C-3).
- P2-5.15: note the Phase A reading of "not reported" (C-2).
