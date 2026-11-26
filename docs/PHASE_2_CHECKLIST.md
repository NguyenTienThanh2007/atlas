# Phase 2 checklist: verified company discovery

The single source of truth for Phase 2 progress. Every status must match the codebase and the
evidence recorded here.

## Progress summary

| | |
| --- | --- |
| **Phase objective** | Turn the Phase 1 foundation into a usable discovery product backed by **at least 5 verified Vietnamese listed companies (stretch target 20–30)** across the 4 approved sectors, with evidence-backed financials and validation by real users |
| **Current status** | **IN PROGRESS: planning complete.** All product decisions A-1 to A-11 **approved** on 2026-11-23 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md)). A private 5-company pilot can start; **public display of real data waits on gate G1** (legal opinion), reported under Track B. Phase 1 capabilities re-verified. **Execution: CONDITIONAL GO (EX-1).** Merged to `main`: WS1 verification workflow (PR #3, `45ef0ca`), WS2 Vietnamese-first UI (PR #4, `78cf577`), WS3 per-figure sources (PR #5, `4be30b7`), WS4-1 metric dictionary 1.1.0 (PR #6, `105869f`); CI green on each merge (E-MAIN). WS4-2 ROE and ROA (PR #7, `2079101`) and its display fixes (PR #8, `8007fe2`); CI green on each merge (E-MAIN). Independent review: [WS4_2_AUDIT.md](WS4_2_AUDIT.md) (no CRITICAL/HIGH; AU-3 to AU-6 open). Next: WS4-3 period comparison, plan only ([WS4_3_IMPLEMENTATION_PLAN.md](WS4_3_IMPLEMENTATION_PLAN.md)). **Update 2026-11-26:** audit fixes AU-3, AU-4, AU-5 merged (PR #9, `407ed63`); WS4-3 period comparison merged (PR #10, `609864c`); CI green on both merges (E-MAIN). Neither PR has a recorded review (P2-8.11). Post-merge audit: [WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md); next steps: [PHASE_2_NEXT_STEPS.md](PHASE_2_NEXT_STEPS.md). |
| **Last verified** | 2026-11-26, `main` @ `609864c` (PR #10 merge): Backend 380 passed, Frontend 35/35, Docker success (E-MAIN). Earlier: 2026-11-25, `main` @ `8007fe2`; E-B/E-F (2026-11-23, `3660e5f`), E-WS1, E-WS2, E-WS3 |
| **Overall completion** | **32 / 83 items PASS (38.6%)**. BLOCKED and FAIL never count as complete |
| **Completed (PASS)** | 32 |
| **In progress** | 26 |
| **Not started** | 15 |
| **Blocked** | 10 |
| **Failed** | 0 |

| Section | Items | PASS | IN PROGRESS | NOT STARTED | BLOCKED | FAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1. Product scope and planning | 5 | 3 | 2 | 0 | 0 | 0 |
| 2. Data governance and provenance | 8 | 7 | 0 | 0 | 1 | 0 |
| 3. Verified company dataset | 9 | 0 | 1 | 8 | 0 | 0 |
| 4. Company discovery experience | 13 | 9 | 4 | 0 | 0 | 0 |
| 5. Financial intelligence and presentation | 17 | 4 | 4 | 0 | 9 | 0 |
| 6. Data quality and testing | 12 | 7 | 4 | 1 | 0 | 0 |
| 7. Product validation | 7 | 2 | 1 | 4 | 0 | 0 |
| 8. Engineering and release readiness | 12 | 0 | 10 | 2 | 0 | 0 |
| **Total** | **83** | **32** | **26** | **15** | **10** | **0** |

Scope changes: 2026-11-23, +2 items (P2-4.12, P2-4.13) added for the MVP scope approved in
A-3 and A-4. The total went from 81 to 83; no items were removed.
2026-11-24: P2-5.11, 5.12, 5.13, 5.15 and 5.17 moved NOT STARTED → IN PROGRESS because a written
proposal now exists (WS4 plan). Nothing moved to PASS; no formula is approved or implemented.
2026-11-25: P2-5.11, 5.12 and 5.17 moved IN PROGRESS → PASS with WS4-2 evidence, gathered on the branch
and confirmed by CI on the PR #7 merge (`2079101`).
2026-11-26: P2-5.13 moved IN PROGRESS → PASS with WS4-3 evidence, confirmed by CI on the PR #10 merge
(`609864c`). Counts recounted from the 83 item lines (32 PASS, 26 IN PROGRESS, 15 NOT STARTED,
10 BLOCKED, 0 FAIL); before: 31, 27, 15, 10, 0.

Percent complete = PASS ÷ total items. Counts are tallied from the item lines below. Re-count after
every update; don't estimate.

**Critical remaining work**

1. **Gate G1: legal opinion (B-1).** Commission the Vietnamese legal opinion on publicly
   displaying figures from mandatory disclosures (questions in
   [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) Q-1). It blocks all public display of real data
   (P2-2.3, P2-5.2 to P2-5.10).
2. **Gate G2: private 5-company pilot.** Choose the companies with the approved sectors (A-7) and
   selection criteria (A-11), curate them from their own audited annual reports, and measure hours per company.
   Needs a named second reviewer (Q-3).
3. **Open questions for the owner.** Q-3 (second reviewer) and Q-7 (hosting and budget) in
   [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md). All product decisions are approved. **Q-9 resolved
   2026-11-23:** round-1 threshold scaled to n = 10 (amendment AM-1 to A-9). **Q-4 resolved
   2026-11-23:** recruiting plan confirmed. **Q-2 resolved 2026-11-23:
   commercial intent.** G1 must therefore assess commercial
   use, storage, processing, display and redistribution rights per data source (PRODUCT_DECISIONS
   §4a).
4. **Verification workflow (P2-2.1, P2-2.5): done in WS1** ([VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md)). Applying it needs the Q-3 reviewer.
5. **Calculated metrics (P2-5.11, P2-5.12, P2-5.17).** ROE and ROA formulas, and a clear split
   between reported and calculated values. Proposed in
   [WS4_FINANCIAL_INTELLIGENCE_PLAN.md](WS4_FINANCIAL_INTELLIGENCE_PLAN.md); owner decisions
   WS4-D1 to WS4-D11 recorded 2026-11-24 (Q-5 resolved). Implementation waits on the owner's go-ahead.
   *Update 2026-11-26:* implemented and merged (WS4-2: PRs #7, #8; audit fixes: PR #9; WS4-3 period
   comparison: PR #10). Remaining WS4 work: missing-data states and bank applicability (WS4-4; see
   [PHASE_2_NEXT_STEPS.md](PHASE_2_NEXT_STEPS.md)).
6. **Product validation with real users (section 7).**

**Related documents:** [README](../README.md) ·
[Architecture](ARCHITECTURE.md) · [Development](DEVELOPMENT.md) ·
[Product strategy](PRODUCT_STRATEGY.md) · [Product decisions](PRODUCT_DECISIONS.md) ·
[Pilot selection criteria](PILOT_SELECTION_CRITERIA.md) ·
[WS4 plan](WS4_FINANCIAL_INTELLIGENCE_PLAN.md) · [WS4 checklist](WS4_CHECKLIST.md) ·
[Phase 0 checklist](PHASE_0_CHECKLIST.md) · [Phase 1 checklist](PHASE_1_CHECKLIST.md) ·
[Data rules, taxonomy, metric dictionary](../data/README.md) · [Data sources](../data/SOURCES.md)

## Status convention

| Status | Meaning |
| --- | --- |
| `NOT STARTED` | No work done for Phase 2 |
| `IN PROGRESS` | Partly done; the item says what is done and what remains |
| `PASS` | Done **and** verified. Evidence is recorded on the item |
| `BLOCKED` | Can't proceed; the item names the blocker (B-n) |
| `FAIL` | Was verified and does not meet the requirement; must be fixed |

Format: `- [ ] **[STATUS]** P2-x.y Description` followed by indented `Evidence:` / `Remaining:` /
`Blocked by:` lines. The checkbox is ticked (`[x]`) **only** for `PASS`.

**What counts as evidence for PASS:** a test command and its result, a source document plus a
verification record, an API response, a browser verification note, a reviewed implementation, or
written licensing confirmation. Code existing is not enough. Evidence carried over from Phase 1
is valid only when the code is unchanged (checked here: `git diff d858fbc 3660e5f` is empty) and
the tests are re-run.

**Evidence baseline used below (2026-11-23):**
- **E-B** (backend, `main` @ `3660e5f` from a `git archive` export): `uv run pytest` gave
  **87 passed**; `ruff check`, `ruff format --check` and `mypy` (strict) were clean;
  `alembic check` reported "No new upgrade operations detected".
- **E-F** (frontend, same export): `npm run lint` (0 issues), `npm run typecheck`, `npm test`
  (**8/8**) and `npm run build` all passed.
- **E-CI**: GitHub Actions on PR #2 head `d858fbc` passed for
  [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45037564694),
  [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45037564678) and
  [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45037564765).
- **E-WS1** (2026-11-23, Phase 2 workstream 1, approved EX-2): clean copy of the working tree (no `.venv`, `node_modules`, `.next`), fresh PostgreSQL 17: `uv sync --frozen`; `ruff check`, `ruff format --check`, `mypy` clean; `pytest` **170 passed**; `alembic upgrade head` → `check` ("No new upgrade operations detected") → `downgrade base` → `upgrade head` (`31b1317163eb`); `pip-audit` clean. Frontend `npm ci`, lint, typecheck, `npm test` 8/8, build, `npm audit` 0. Docker fresh volume: migrations to `31b1317163eb`, health 200, frontend 200, sample import OK, review of sample evidence refused, restart keeps data. Compatibility: upgrade/downgrade on a database holding Phase 1-era data left it unchanged; downgrade refused once a review existed. Not run on GitHub Actions at the time; CI after merge: E-MAIN.
- **E-WS3** (2026-11-24, workstream 3, branch `feat/ws3-per-figure-sources` from `main` @ `78cf577`): clean copy of the working tree: backend ruff/format/mypy clean, `pytest` **201 passed** (+31 in `tests/test_provenance.py`), `alembic check` clean (no migration), `pip-audit` clean; frontend `npm ci`, lint, typecheck, `npm test` **24/24**, build, `npm audit` 0. Isolated Docker stack (`atlasws3`, new volume, ports 5463/8063/3063) with fictional fixtures: route check online and offline, per-figure API-to-UI check in vi and en; browser pass desktop and 375×812. Not run on GitHub Actions at the time; CI after merge: E-MAIN.
- **E-WS2** (2026-11-23, workstream 2, approved by the owner): clean copy of the working tree: frontend `npm ci`, lint, typecheck, `npm test` **17/17**, production build (both languages partially prerendered, proxy registered); backend `pytest` **170 passed**, ruff/mypy clean, `alembic check` clean (no schema change). Isolated Docker stack: `scripts/check-routes.mjs` passed with the backend up and stopped; browser pass in both languages at desktop and 375×812 (layout, keyboard focus on the language switch, no console errors). Not run on GitHub Actions at the time; CI after merge: E-MAIN.
- **E-MAIN** (checked 2026-11-24 with `git fetch` and `gh`): PR #3 merged as `45ef0ca`
  ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45180859560),
  [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45180859516) success; Frontend
  not triggered by its path filter, and `git diff 3660e5f 45ef0ca -- frontend` is empty); PR #4
  merged as `78cf577`
  ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45185760407),
  [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45185760378),
  [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45185760569) success); PR #5
  merged as `4be30b7`
  ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45318642634): `201 passed`
  incl. migration round-trip;
  [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45318642611): tests 24, pass
  24; [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45318642530): stack healthy).
  PR #6 (WS4-1) merged as `105869f` on 2026-11-25, identical to its head `36b3794`
  ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45532503338): `224 passed`,
  `alembic check` "No new upgrade operations detected";
  [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45532503452): tests 25, pass
  25; [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45532503332): stack healthy).
  PR #7 (WS4-2) merged as `2079101`, identical to head `037a820`
  ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617789): `288 passed`,
  `alembic check` clean; [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617702):
  27/27; [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617848) success; PR-head
  runs also green). PR #8 (audit fixes AU-1, AU-2) merged as `8007fe2`, identical to head `0aa7977`
  ([Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45610139607): 28/28;
  [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45610139576) success; Backend not
  triggered by the path filter, no backend change).
  PR #9 (audit fixes AU-3, AU-4, AU-5) merged 2026-11-25 as `407ed63`, identical to head `6c01f11`
  ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669307): `314 passed`,
  `alembic check` clean; [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669447):
  31/31; [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669282) success).
  PR #10 (WS4-3) merged 2026-11-26 as `609864c`, identical to head `42f2f8a`
  ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757432716): `380 passed`,
  `alembic check` clean; [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757432592):
  35/35, build; [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757432573) success;
  PR-head runs also green). Checked 2026-11-26 ([WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md) §3).
  The PRs were opened and merged by the owner's account with no recorded GitHub review.
- **E-BR**: browser verification recorded in [PHASE_1_CHECKLIST.md](PHASE_1_CHECKLIST.md)
  sections 11–12 (2026-11-22, code `d858fbc`, identical to `main`).

---

## 1. Product scope and planning

- [x] **[PASS]** P2-1.1 Define target users (e.g. Vietnamese retail investors, foreign investors researching Vietnam, analysts), with the primary segment chosen.
  - Evidence: six segments analysed and ranked in [PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md) §4. Primary segment **C (Vietnamese investors learning to research listed companies)**, with E (foreign, English) second, **approved by the project owner Tiến Thành on 2026-11-23** ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-1).
- [ ] **[IN PROGRESS]** P2-1.2 Define the main investment discovery problems ATLAS solves, each grounded in user evidence or explicitly marked as an assumption.
  - Done: primary problem stated and labelled as a hypothesis (H1), with competitor facts cited ([PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md) §3, §5).
  - Done: positioning approved by the project owner on 2026-11-23 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-2).
  - Remaining: the problem itself (H1) is still a hypothesis; needs user evidence from round 1 interviews (P2-7.3).
- [ ] **[IN PROGRESS]** P2-1.3 Define core user journeys (e.g. find a company → understand its business → check its financials → see the sources).
  - Done: journeys J1–J4 with intent, steps, screens, data, success condition and friction ([PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md) §7).
  - Remaining: owner approval; validation in round 2 usability tests.
- [x] **[PASS]** P2-1.4 Define MVP scope and non-goals (non-goals already implied: no 3D world, no prices or trading, no investment advice).
  - Evidence: 17 features classified MUST / SHOULD / LATER / OUT OF SCOPE; MUSTs M1–M5 with problem, data, complexity, dependencies and acceptance criteria ([PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md) §6). **MVP = M1–M5, with price charts, news, portfolio, AI, relationships and 3D outside the MVP, approved by the project owner Tiến Thành on 2026-11-23** ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-3); Vietnamese-first UI approved the same day (A-4).
  - Note: A-5 (deferring 3D in the long-term vision) and the SHOULD features are separate decisions, not part of this item.
- [x] **[PASS]** P2-1.5 Define Phase 2 acceptance criteria and get the project owner's sign-off.
  - Evidence: acceptance criteria **approved by the project owner Tiến Thành on 2026-11-23** ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2a, A-10). Track A (product completion, AC-1 to AC-8): ≥5 verified companies (defined via A-11; stretch 20–30), figure-to-page traceability, reproducible data-quality checks, both research rounds documented whatever the outcome, journeys J1–J3, release gates, docs. Track B (public-launch readiness, LR-1 to LR-5) is reported separately below.

## 2. Data governance and provenance

- [x] **[PASS]** P2-2.1 Define the company data verification workflow: who reviews, what they check against which document, how the decision is recorded, and the two-person rule (if any).
  - Evidence: [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) §1–5. Roles curator and independent reviewer; decisions recorded in append-only `verification_reviews`; two-person rule enforced by PostgreSQL (`curator ≠ reviewer`, reviewer not a system name, `checked_against` required). Tests `test_reviewer_must_be_another_person[*]`, `test_raw_sql_review_is_held_to_the_same_rules`, `test_review_cli`. Phase 2 WS1 (approved EX-2, migration `31b1317163eb`), verified 2026-11-23 on a clean copy of the working tree: `pytest` **170 passed** (new `tests/test_verification.py`), ruff/mypy clean, migration up → check → down → up, Docker fresh start (E-WS1).
  - Note: the reviewer **person** is still open (**Q-3**); until appointed nothing can be verified.
- [x] **[PASS]** P2-2.2 Define source credibility tiers and evidence requirements per field (identity, ticker, sector, description, financials).
  - Evidence: tiers T1–T4 and the minimum tier per field in [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) §2 (T4/aggregators never accepted, A-6). Evidence is mandatory for every company and statement (`test_invalid_record_is_reported_and_others_still_import`), and every real figure needs its page (`test_real_figures_need_a_source_page_on_import`, `test_real_figures_need_page_and_reported_value`). Tier per field is applied by the reviewer, not checked automatically.
- [ ] **[BLOCKED]** P2-2.3 Document storage, display and redistribution permissions for every data source used.
  - Done: the state of knowledge is recorded in [data/SOURCES.md](../data/SOURCES.md); every source is `unknown`. Path approved: Vietnamese legal opinion = **gate G1** ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-6, questions in Q-1).
  - Blocked by: **B-1** until G1 returns.
- [x] **[PASS]** P2-2.4 Record source URL, document title, publication date and retrieval timestamp for every evidence item.
  - Evidence: `evidence` table columns `source_url`, `document_title`, `published_at`, `retrieved_at` (NOT NULL, `timestamptz`), plus `content_hash` (`backend/app/models.py`). Importer requires timezone-aware `retrieved_at` and rejects `published_at` later than `retrieved_at` (`backend/app/ingestion/schemas.py`). Tests `test_valid_import_creates_records_with_provenance` and `test_company_evidence_includes_provenance` pass (E-B). Exposed by `GET /api/v1/companies/{id}/evidence`.
- [x] **[PASS]** P2-2.5 Define verified, unverified, rejected and sample data states.
  - Evidence: states `unverified`, `verified`, `disputed`, `rejected` (new), `superseded`, `sample` and the allowed transitions in [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) §3, enforced by a database trigger. `test_transition_matrix[*]` covers all 25 (state, decision) pairs; `test_sample_evidence_can_never_be_reviewed[*]`, `test_evidence_cannot_be_inserted_in_a_reviewed_state[*]`, `test_status_and_content_cannot_be_updated_directly`, `test_stale_from_status_is_refused`, `test_imports_cannot_set_a_reviewed_state[*]`. Phase 2 WS1 (approved EX-2, migration `31b1317163eb`), verified 2026-11-23 on a clean copy of the working tree: `pytest` **170 passed** (new `tests/test_verification.py`), ruff/mypy clean, migration up → check → down → up, Docker fresh start (E-WS1).
- [x] **[PASS]** P2-2.6 Real and fictional records cannot be confused.
  - Evidence: `companies.is_sample`; sample sources may only use `verification_status = sample` and real sources may not; statements can't cross between sample and real companies. Tests `test_sample_and_real_data_never_mix`, `test_statement_for_sample_company_from_real_source_is_rejected` and `test_sample_fixture_imports_flagged_and_idempotently` pass (E-B). UI shows a "Sample data" badge in lists and a banner on the detail page (E-BR).
  - 2026-11-25 (audit AU-3, branch `fix/ws4-2-audit-au3-au4-au5`, not yet committed): the database now enforces this too. Migration `8de09b58f4c2` refuses any write that mixes sample and real evidence within a company, including direct SQL, and the calculation engine refuses mixed inputs (`backend/tests/test_sample_isolation.py`; full suite 314 passed on a clean copy).
  - 2026-11-26: merged in PR #9 (`407ed63`); Backend CI on the merge: 314 passed, `alembic check` clean (E-MAIN).
- [x] **[PASS]** P2-2.7 Support financial statement revisions and restatements.
  - Evidence: `revision` plus `supersedes_id` with CHECK `(revision = 1) = (supersedes_id IS NULL)`; append-only triggers on `financial_statements` and `financial_metrics` (migration `981ec5176312`). Tests `test_financial_history_is_append_only`, `test_statement_identity_and_revision_rules`, `test_restatement_is_a_new_revision_and_history_is_kept`, `test_changed_figures_are_a_conflict_not_an_overwrite` and `test_financial_statements_latest_revision_and_exact_values` pass (E-B).
- [x] **[PASS]** P2-2.8 Document data correction and review procedures, including how to correct company master data (today an import can only report a conflict; see Phase 1 L-3).
  - Evidence: [VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) §8 (curation errors, restatements, replaced documents, master data, wrong review decisions). History preservation tested: `test_reviews_are_append_only_and_history_is_kept`, `test_financial_history_is_append_only`. A *tooled* master-data update path is still future work (R-3).

## 3. Verified company dataset

Rule: if evidence or usage permission is unavailable, the item is **BLOCKED**. Never invent data
or claim verification without evidence. Under A-6, private curation for internal testing is
permitted; **publishing** real data waits on gate G1. Primary source is the company's own published
audited annual report; aggregators are never a source.

- [ ] **[IN PROGRESS]** P2-3.1 Establish the pilot target: choose 20–30 real listed companies across 3–4 sectors, with the selection criteria written down.
  - Done: **sectors and size approved** by the project owner on 2026-11-23 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-7): Banking & Financial Services, Consumer & Retail, Technology, Materials & Construction; 20–30 companies; first 5 = private pilot (gate G2).
  - Done: **selection criteria approved** by the project owner on 2026-11-23 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-11): [PILOT_SELECTION_CRITERIA.md](PILOT_SELECTION_CRITERIA.md) (eligibility E1–E8, ordering, composition rules, curation scope, audit-trail template).
  - Remaining: the long-list (checked against E1–E8 with evidence by a person) and the first-5 list confirmed by the owner. No company is named yet, by design.
  - G2 progress (2026-11-23, no names, per A-11 §5): candidate universe built from the official HOSE July-2026 VN30/VN100 constituent announcement (100 candidates). 7 priority candidates preliminarily assessed (56 criterion cells: 44 PASS, 0 FAIL, 3 UNKNOWN, 9 NOT REVIEWED; 5 candidates pass E1–E8 on a first, unreviewed check). A 5-company shortlist, confirmed by the owner on 2026-11-23, is held in the private workspace outside the repo. 0 companies verified (independent reviewer, Q-3, not appointed).
- [ ] **[NOT STARTED]** P2-3.2 Verify each company's legal identity and name against an authoritative source.
  - Unblocked for the **private 5-company pilot** by [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-6 (2026-11-23); public display waits on gate G1 (B-1).
- [ ] **[NOT STARTED]** P2-3.3 Verify ticker and exchange for each pilot company.
  - Unblocked for the **private 5-company pilot** by [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-6 (2026-11-23); public display waits on gate G1 (B-1). Exchange sites unreachable from our automated environment (B-3) can be checked manually by a person.
- [ ] **[NOT STARTED]** P2-3.4 Verify sector classification per the ATLAS taxonomy methodology (`data/README.md`), with evidence.
  - Unblocked for the **private 5-company pilot** by [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-6 (2026-11-23); public display waits on gate G1 (B-1).
- [ ] **[NOT STARTED]** P2-3.5 Collect business descriptions, each with evidence.
  - Unblocked for the **private 5-company pilot** by [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-6 (2026-11-23); public display waits on gate G1 (B-1). Descriptions are written in ATLAS's own words; no copied report text.
- [ ] **[NOT STARTED]** P2-3.6 Collect annual and quarterly financial statements where permitted.
  - Unblocked for the **private 5-company pilot** by [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-6 (2026-11-23); public display waits on gate G1 (B-1). Annual audited statements first (≥3 fiscal years, MVP M2); quarterly later. Two-person check on figures (D-6). Hours per company measured for gate G2.
- [ ] **[NOT STARTED]** P2-3.7 Validate reporting period, currency and unit for every imported statement.
  - Done (tooling): the importer validates period order, quarter range, currency format and metric units (E-B).
  - Unblocked for the **private 5-company pilot** by [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-6 (2026-11-23); public display waits on gate G1 (B-1).
- [ ] **[NOT STARTED]** P2-3.8 Track missing fields and missing reporting periods per company.
- [ ] **[NOT STARTED]** P2-3.9 Produce a data coverage report (companies × fields × periods; verified vs unverified).

**Dataset status:** 0 real companies, 0 verified. The only data is the fictional fixture
`data/seed/sample_companies.json` (3 companies, flagged as sample).

## 4. Company discovery experience

- [x] **[PASS]** P2-4.1 Company listing page.
  - Evidence: `frontend/src/app/companies/page.tsx` renders `GET /api/v1/companies` (E-BR). Build passes (E-F).
  - Path since WS2: `frontend/src/app/[lang]/companies/page.tsx`; re-checked in both languages by `scripts/check-routes.mjs` and the browser pass (E-WS2).
- [x] **[PASS]** P2-4.2 Search by company name and ticker.
  - Evidence: `test_search_and_filters` (13 cases, covering name, English name, ticker, and literal `%` and `_`) passes (E-B). Browser search for `sample2p` returned 1 result (E-BR).
- [x] **[PASS]** P2-4.3 Sector and exchange filters.
  - Evidence: `test_search_and_filters` sector and exchange cases (delisted listings excluded) pass (E-B). Browser sector filter verified (E-BR).
- [x] **[PASS]** P2-4.4 Pagination and stable sorting.
  - Evidence: `test_pagination_is_stable_and_complete` passes (E-B); `Pagination` component in `frontend/src/components/pagination.tsx`.
- [x] **[PASS]** P2-4.5 Company detail page.
  - Evidence: `frontend/src/app/companies/[id]/page.tsx`; `test_company_detail` passes (E-B); browser verified (E-BR).
  - Path since WS2: `frontend/src/app/[lang]/companies/[id]/page.tsx` (re-checked E-WS2, E-WS3).
- [ ] **[IN PROGRESS]** P2-4.6 Business overview.
  - Done: the `description` field is shown on the detail page.
  - Remaining: link each description to its evidence; real descriptions (blocked by P2-3.5).
- [x] **[PASS]** P2-4.7 Securities and exchange information.
  - Evidence: Listings table (ticker, exchange, type, status, listed and delisted dates); `GET /api/v1/securities/{id}`; tests `test_security_detail` and `test_list_item_shape_hides_internal_fields` pass (E-B). Two listings on two exchanges shown in the browser (E-BR).
- [ ] **[IN PROGRESS]** P2-4.8 Financial statement section.
  - Done: statements render with exact values, unit, period, source and verification status, and show a "restated (revision N)" label (E-BR, fictional data in an isolated database). API test `test_financial_statements_latest_revision_and_exact_values` passes (E-B).
  - Done (E-WS3): each figure shows its source document and page, and the as-reported value and scale.
  - Remaining: the section shows unverified statements too, labelled. Section 5 requires showing only verified-supported metrics, and that rule must be decided and implemented.
- [x] **[PASS]** P2-4.9 Source and evidence display.
  - Evidence: "Sources" section with data-source name, retrieval date (Vietnam time), verification status and usage rights; only http(s) URLs are links. Tests `test_company_evidence_includes_provenance` (E-B) and `formatDate` (E-F); browser verified (E-BR).
- [ ] **[IN PROGRESS]** P2-4.10 Loading, empty, error and not-found states.
  - Done: all four render (E-BR: skeleton during navigation, "No companies yet", per-page error panel with the backend stopped, not-found page for unknown ids).
  - WS2: unknown URLs now return HTTP **404** with the localized not-found page (catch-all route).
  - Remaining: unknown *record* ids on streamed detail routes still return HTTP 200 with the not-found page (Phase 1 L-4 / exit audit F-3).
- [x] **[PASS]** P2-4.11 Responsive desktop and mobile experience.
  - Evidence (E-WS2): at 375×812, all 12 page/language combinations (Discover, companies, company detail, sectors, watchlist, not-found × vi/en) have no horizontal scroll (`scrollWidth 375`), one `h1`, no unlabelled controls or unnamed links. Mobile menu opens and closes; desktop layouts checked; Vietnamese button labels kept on one line.
- [ ] **[IN PROGRESS]** P2-4.12 Vietnamese-first UI with English as second language (MVP M5, approved [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) A-4): all UI copy in Vietnamese, `lang` set correctly, the display font's `vietnamese` subset loaded (D-7).
  - Done (E-WS2): Vietnamese is the default at today's URLs (`<html lang="vi">`), English under `/en` (`lang="en"`); all UI copy, statuses, errors, empty/loading/not-found states and page titles in both languages; Fraunces and IBM Plex Sans load the `vietnamese` subset (browser: Fraunces Vietnamese ranges loaded); Vietnamese number and date formats; Vietnamese metric labels from the dictionary (`metric_name_vi`); language switch keeps page and query. Tests: `src/i18n/i18n.test.ts` (key parity, glossary coverage, no English UI copy in vi, units, error text, routing), `scripts/check-routes.mjs` (backend up and down). Glossary: [GLOSSARY.md](GLOSSARY.md).
  - Remaining: **native-speaker review of the glossary** (owner). Taxonomy descriptions exist only in English (shown as data with `lang="en"`); Vietnamese descriptions would need a taxonomy version bump.
- [x] **[PASS]** P2-4.13 Per-figure source links (MVP M2, approved A-3): every displayed financial figure reaches its source document in ≤2 clicks (D-3).
  - Evidence (E-WS3): API gives every metric a `source` (statement evidence + the figure's own `source_page`; `document_url` only for safe http(s) links) plus `reported_value`/`reported_scale` (`backend/tests/test_provenance.py`, 31 tests). The company page shows per figure "Nguồn: <document> · Trang N" linking to the document at `#page=N` in **one click**; unknown page ("Chưa có số trang nguồn") and non-linkable documents ("Liên kết nguồn không khả dụng") are stated, never invented (`frontend/src/lib/provenance.test.ts`). `scripts/check-routes.mjs` with `PROVENANCE_COMPANY_ID` matched every figure's rendered link and page to the API in vi and en for a fictional linkable company and the sample company. Browser: desktop and 375×812, keyboard focus and descriptive link labels, no console errors. Details: [WS3_CHECKLIST.md](WS3_CHECKLIST.md).
  - Limits: `#page=N` is honoured by browser PDF viewers, not by every document type; figures are only as verified as their evidence (Q-3 open, nothing verified).

## 5. Financial intelligence and presentation

Rule: only show metrics supported by verified source data, and always distinguish **reported**
values from **calculated** ones.

- [ ] **[IN PROGRESS]** P2-5.1 Define metric definitions and calculation formulas.
  - Done: 16 reported metrics defined, with Vietnamese names, statement type and unit, in `backend/app/reference/metric_dictionary.json` (documented in `data/README.md`).
  - Remaining: formulas for calculated metrics (ROE, ROA, growth), averaging conventions, and sign conventions.
  - 2026-11-24: per-metric gap analysis, proposed definitions, sign conventions and applicability in [WS4_FINANCIAL_INTELLIGENCE_PLAN.md](WS4_FINANCIAL_INTELLIGENCE_PLAN.md) §3. Owner approved definitions, bank applicability and a new `equity_parent` metric (WS4-D10, decision recorded 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d)); sign-convention field not approved. WS4-1 (merged 2026-11-25, PR #6, `105869f`, CI green, E-MAIN): dictionary **1.1.0** with vi/en definitions, bank / non-bank applicability and `equity_parent`, served at `GET /api/v1/metric-dictionary`; 23 new tests, backend `pytest` 224 passed (incl. `metric_name_en`); bank applicability derived from WS4-D1, D2, D4, D5; `equity_parent` rule WS4-D12. Owner approved all 17 definitions (2026-11-25); exit audit F-1 and F-2 resolved.
  - 2026-11-25 status: definitions done (merged); ROE, ROA, averaging and growth formulas approved (WS4-D1 to D3, D9). Still open: sign conventions (G-3 not approved). Stays IN PROGRESS.
- [ ] **[BLOCKED]** P2-5.2 Revenue (`net_revenue`).
  - Done: defined, importable, displayable.
  - Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.3 Gross profit (`gross_profit`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.4 Operating profit (`operating_profit`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.5 Net profit (`net_profit`, `net_profit_parent`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.6 Total assets (`total_assets`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.7 Total liabilities (`total_liabilities`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.8 Equity (`total_equity`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.9 Operating cash flow (`operating_cash_flow`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [ ] **[BLOCKED]** P2-5.10 EPS (`eps_basic`, unit `VND/share`). Defined and importable. Blocked by: **B-1** (public display waits on gate G1; pilot values depend on P2-3.6).
- [x] **[PASS]** P2-5.11 ROE: formula (e.g. net profit to parent ÷ average equity), calculation and tests. Not stored; derived at read time per `data/README.md`.
  - Done: options, proposed default and edge cases written (WS4 plan §4). Formula approved: WS4-D1, WS4-D3, decision recorded 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d).
  - Evidence (WS4-2, 2026-11-25, gathered on branch `feat/ws4-2-roe-roa` from `main` @ `105869f`, then merged as PR #7 `2079101` with Backend 288 passed, Frontend 27/27 and Docker CI success on head and merge; details in [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md)): backend `pytest` **288 passed** (+64), ruff/mypy clean, `alembic check` clean (no migration); frontend clean copy lint, typecheck, `npm test` 27/27, build; isolated Docker stack with a fictional bundle: route check online, offline and per calculated value in vi and en; browser desktop and 375×812. Re-verified by CI on merge (E-MAIN). Consolidated ROE = `net_profit_parent` ÷ average `equity_parent`, separate ROE = `net_profit` ÷ average `total_equity` (WS4-D1, D3, D12); `GET /api/v1/companies/{id}/calculated-metrics`.
  - Limits: every real input is unverified until Q-3, so results carry "Tính từ số liệu chưa kiểm chứng"; nothing is public before G1.
- [x] **[PASS]** P2-5.12 ROA: formula, calculation and tests.
  - Done: options, proposed default and edge cases written (WS4 plan §5). Formula approved: WS4-D2, WS4-D3, decision recorded 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d).
  - Evidence (WS4-2, 2026-11-25, gathered on branch `feat/ws4-2-roe-roa` from `main` @ `105869f`, then merged as PR #7 `2079101` with Backend 288 passed, Frontend 27/27 and Docker CI success on head and merge; details in [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md)): backend `pytest` **288 passed** (+64), ruff/mypy clean, `alembic check` clean (no migration); frontend clean copy lint, typecheck, `npm test` 27/27, build; isolated Docker stack with a fictional bundle: route check online, offline and per calculated value in vi and en; browser desktop and 375×812. Re-verified by CI on merge (E-MAIN). ROA = `net_profit` ÷ average `total_assets` per scope (WS4-D2, D3).
- [x] **[PASS]** P2-5.13 Financial period comparisons (year over year, quarter over quarter), only between comparable periods and scopes.
  - Done: comparability rules proposed (WS4 plan §8); approved as WS4-D9, decision recorded 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d).
  - Remaining: implementation; tests.
  - 2026-11-25: implementation plan and checklist written ([WS4_3_IMPLEMENTATION_PLAN.md](WS4_3_IMPLEMENTATION_PLAN.md), [WS4_3_CHECKLIST.md](WS4_3_CHECKLIST.md)); ten owner decisions W3-D1 to W3-D10 pending. Not implemented.
  - 2026-11-26: decisions W3-D1 to W3-D11 approved; audit [WS4_3_AUDIT.md](WS4_3_AUDIT.md). Implemented on branch `feat/ws4-3-period-comparison` (uncommitted): `GET /companies/{id}/comparisons`, company-page section; backend 380 passed, frontend 35/35, isolated Docker route check and browser pass. Stays IN PROGRESS until the PR has a recorded owner review, green CI and is merged.
  - Evidence (2026-11-26, post-merge): merged as PR #10 (`609864c`); CI on the merge: Backend 380 passed incl. matching, growth, reason and API tests, Frontend 35/35 and build, Docker success (E-MAIN). Year on year, quarter on quarter and same quarter last year; only same company, statement type, scope and granularity; ambiguous or mismatched periods refused. Verified against the code in [WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md) §2. The note above made a recorded owner review a condition; as for P2-5.11 and 5.12, that review is tracked by P2-8.11 (still NOT STARTED) and W3-H2, not by this item.
- [ ] **[IN PROGRESS]** P2-5.14 Currency and unit formatting.
  - Done: exact digit grouping from decimal strings, never floats (`formatDecimal`, unit test in E-F); unit shown next to each value.
  - Remaining: compact Vietnamese scales (tỷ / triệu), a locale decision, and negative-value styling.
  - 2026-11-24: display and rounding rules proposed (WS4 plan §10); approved as WS4-D8, decision recorded 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d); not implemented.
  - 2026-11-26: negative values now use the typographic minus (U+2212) everywhere (WS4-3 audit A3-7, PR #10). Remaining: compact Vietnamese scales and the locale decision.
- [ ] **[IN PROGRESS]** P2-5.15 Missing data handling (show "not reported", never zero; exclude from calculations).
  - Done: seven availability states proposed, with what today's schema can and cannot express (WS4 plan §7); vocabulary and Phase A approved as WS4-D6, decision recorded 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d). Phase B (explicit records, a schema change) not approved.
  - Remaining: implementation; tests.
- [ ] **[IN PROGRESS]** P2-5.16 Revision and restatement presentation.
  - Done: the latest revision is shown by default with a "restated" label; API `include_superseded=true` returns history (E-B, E-BR).
  - Remaining: a UI view of revision history and what changed.
- [x] **[PASS]** P2-5.17 Clearly distinguish reported values from calculated values in the API and UI (labels, formula disclosure, source).
  - Done: reported figures already carry document, page and verification status per figure (P2-4.13). API and UI proposal for calculated values (WS4 plan §9); approved as WS4-D7 and WS4-D11, decision recorded 2026-11-24 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2d).
  - Evidence (WS4-2, 2026-11-25, gathered on branch `feat/ws4-2-roe-roa` from `main` @ `105869f`, then merged as PR #7 `2079101` with Backend 288 passed, Frontend 27/27 and Docker CI success on head and merge; details in [WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md)): backend `pytest` **288 passed** (+64), ruff/mypy clean, `alembic check` clean (no migration); frontend clean copy lint, typecheck, `npm test` 27/27, build; isolated Docker stack with a fictional bundle: route check online, offline and per calculated value in vi and en; browser desktop and 375×812. Re-verified by CI on merge (E-MAIN). Calculated values have their own endpoint and page section ("Chỉ số tính toán (do ATLAS tính)"), formula text, inputs with page links, and an input-verification label; they never carry a verification status.

## 6. Data quality and testing

- [x] **[PASS]** P2-6.1 Schema validation.
  - Evidence: Pydantic input models with `extra="forbid"`; tests `test_invalid_record_is_reported_and_others_still_import`, `test_unreadable_bundle_fails_and_is_recorded[*]` and `test_invalid_metrics_are_rejected[*]` pass (E-B).
- [x] **[PASS]** P2-6.2 Data provenance validation.
  - Evidence: evidence required per record; `verified` must cite http(s); sample rules; data-source terms can't change through an import. Tests `test_sample_and_real_data_never_mix` and `test_changed_data_source_terms_fail_the_run` pass (E-B).
- [x] **[PASS]** P2-6.3 Duplicate detection.
  - Evidence: `test_duplicate_in_bundle_is_flagged` and `test_sample_fixture_imports_flagged_and_idempotently` (evidence not duplicated) pass (E-B).
- [x] **[PASS]** P2-6.4 Financial period validation.
  - Evidence: fiscal year named by its end year (non-calendar supported), quarter 80–100 days, year 360–371 days, balance sheet at one date, overlap rejected within the same company/type/scope/granularity while annual + quarterly and revisions coexist ([VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md) §7, boundaries documented). Tests `test_period_rules[*]`, `test_valid_periods_including_non_calendar_and_leap_years`, `test_overlap_rules`. Phase 2 WS1 (approved EX-2, migration `31b1317163eb`), verified 2026-11-23 on a clean copy of the working tree: `pytest` **170 passed** (new `tests/test_verification.py`), ruff/mypy clean, migration up → check → down → up, Docker fresh start (E-WS1).
  - Known limits: transitional fiscal periods rejected; quarter number not checked against months; overlap is importer-enforced (not a DB constraint).
- [x] **[PASS]** P2-6.5 Currency and unit validation.
  - Evidence: statement currency must be VND; required `amount_scale` ∈ dong / nghin_dong / trieu_dong, anything else rejected; exact conversion (60-digit context, raises on rounding) with `reported_value`, `reported_scale`, `source_page` kept and `value = reported_value × reported_scale` enforced by a DB CHECK; overflow rejected. Tests `test_amount_scales_convert_exactly[*]` (incl. 32-digit boundary and 0.000001 triệu), `test_per_share_and_share_counts_are_not_scaled`, `test_unsupported_scale_or_currency_is_rejected[*]`, `test_overflow_after_scaling_is_rejected`, `test_conversion_provenance_is_consistent[*]`. Phase 2 WS1 (approved EX-2, migration `31b1317163eb`), verified 2026-11-23 on a clean copy of the working tree: `pytest` **170 passed** (new `tests/test_verification.py`), ruff/mypy clean, migration up → check → down → up, Docker fresh start (E-WS1).
- [x] **[PASS]** P2-6.6 Decimal precision.
  - Evidence: `test_metric_values_round_trip_exactly[*]` (38 digits, −0.000001, 0.1+0.2, 10^15), `test_json_numbers_are_parsed_as_decimals_not_floats` and the API decimal-string assertion pass (E-B); `formatDecimal` unit test passes (E-F).
- [x] **[PASS]** P2-6.7 Restatement integrity.
  - Evidence: append-only triggers plus revision chain; `test_financial_history_is_append_only`, `test_restatement_is_a_new_revision_and_history_is_kept` and `test_revision_gap_and_unknown_company_are_reported` pass (E-B).
- [ ] **[IN PROGRESS]** P2-6.8 API tests.
  - Done: 34 API tests for the Phase 1 endpoints (`backend/tests/test_api.py`, E-B).
  - Done: WS3 added 31 per-figure provenance API and URL-safety tests (`backend/tests/test_provenance.py`); 201 backend tests pass on `main` (E-MAIN).
  - Done: WS4-1 added tests for `GET /api/v1/metric-dictionary` and its OpenAPI schema (`backend/tests/test_metric_dictionary.py`; merged in PR #6, E-MAIN).
  - Remaining: tests for Phase 2 endpoints (calculated metrics, comparisons, coverage) as they are built.
- [ ] **[IN PROGRESS]** P2-6.9 Frontend tests.
  - Done: 8 unit tests for the API client and formatting (E-F); 24 after WS2 and WS3 (i18n parity, routing, provenance links), passing on `main` (E-MAIN); 28 after WS4-2 and PR #8 (calculated-ratio labels, percent formatting), passing on `8007fe2`.
  - Remaining: page and component tests for states, search and filters.
- [ ] **[IN PROGRESS]** P2-6.10 Integration tests.
  - Done: the Docker workflow boots the full stack and checks health and frontend routes (E-CI).
  - Done: `npm run test:routes` (`frontend/scripts/check-routes.mjs`) checks routes online and offline and per-figure links against the API; run manually (E-WS2, E-WS3), not in CI.
  - Remaining: automated end-to-end browser tests of the core journeys.
- [ ] **[IN PROGRESS]** P2-6.11 Regression tests.
  - Done: full suites run on every PR (E-CI).
  - Remaining: a regression test for each Phase 2 bug fixed, and a pinned real-data fixture once permitted.
- [ ] **[NOT STARTED]** P2-6.12 Security review of Phase 2 changes (input handling, external links, dependency audit, secrets).

## 7. Product validation

Small pilots can't show product-market fit, and must not be reported as if they did.

- [x] **[PASS]** P2-7.1 Define pilot user profiles.
  - Evidence: pilot user profiles and recruiting plan **confirmed by the project owner Tiến Thành on 2026-11-23** ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) Q-4, §4b). Eligibility (interest in Vietnam's stock market, real need to evaluate listed companies, can describe their research process, adult and Vietnamese-speaking); profile categories (beginner or learning, at least 6 of 10; active; experienced where available); exclusions; channels and allocation (investor communities 5, RMIT 3, acquaintances 2; targets, not quotas); safeguards. Approved segment A-1.
  - Note: this plan supersedes PRODUCT_STRATEGY §10's recruitment criteria for round 1. Recruitment itself has **not started** (P2-7.3). The round-1 threshold at n = 10 was resolved via Q-9 (AM-1: ≥6 of 10 meets, ≤3 of 10 clearly below).
- [ ] **[IN PROGRESS]** P2-7.2 Define usability testing scenarios mapped to the core journeys (P2-1.3).
  - Done: scenarios S1–S4 mapped to J1–J4, plus round-1 interview guide ([PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md) §10).
  - Remaining: pilot company names in scenarios (after P2-3.1); dry run.
- [ ] **[NOT STARTED]** P2-7.3 Conduct interviews or usability sessions with real users (record the count and dates; no names without consent).
- [ ] **[NOT STARTED]** P2-7.4 Record feedback in a structured log.
- [ ] **[NOT STARTED]** P2-7.5 Identify and prioritise usability problems.
- [x] **[PASS]** P2-7.6 Define product success metrics, with how each is measured.
  - Evidence: metrics and qualitative pilot decision thresholds **approved by the project owner on 2026-11-23** ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2a, A-9): PB, TC, CF, CS, DS, UF, SUS (reference only), SV, RT (gated by G1), WTP (informational), each with how it's observed, plus Continue / Iterate / Pivot rules.
  - Note: measuring them happens under P2-7.3; RT waits on G1 and appropriate data access. Amended 2026-11-23 by AM-1: round-1 PB at n = 10 is ≥6 of 10 meets, ≤3 of 10 clearly below ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2b).
- [ ] **[NOT STARTED]** P2-7.7 Document product decisions and the evidence behind each.

## 8. Engineering and release readiness

These are release gates. They pass on the current baseline but must be re-verified on the Phase 2
release candidate, so they stay IN PROGRESS until then.

- [ ] **[IN PROGRESS]** P2-8.1 Backend lint and strict type checks. Baseline: clean (E-B).
- [ ] **[IN PROGRESS]** P2-8.2 Backend tests. Baseline: 87 passed (E-B); after WS1: 170 passed (E-WS1); after WS3: 201 passed, also on GitHub Actions for `4be30b7`; after WS4-1: 224 passed on GitHub Actions for `105869f` (E-MAIN); after WS4-2: 288 passed on GitHub Actions for `2079101` (E-MAIN); after PR #9: 314 on `407ed63`; after WS4-3: 380 on `609864c` (E-MAIN).
- [ ] **[IN PROGRESS]** P2-8.3 Frontend lint and type checks. Baseline: pass (E-F).
- [ ] **[IN PROGRESS]** P2-8.4 Frontend unit tests. Baseline: 8/8 (E-F); after WS2: 17/17 (E-WS2); after WS3: 24/24, also on GitHub Actions for `4be30b7`; after WS4-1: 25/25 on GitHub Actions for `105869f` (E-MAIN); after WS4-2: 27/27 on GitHub Actions for `2079101`; after PR #8: 28/28 on `8007fe2` (E-MAIN); after PR #9: 31/31 on `407ed63`; after WS4-3: 35/35 on `609864c` (E-MAIN).
- [ ] **[IN PROGRESS]** P2-8.5 Production build. Baseline: `next build` passes (E-F).
- [ ] **[IN PROGRESS]** P2-8.6 Docker clean build. Baseline: Docker workflow passed on `d858fbc` (E-CI).
- [ ] **[IN PROGRESS]** P2-8.7 Fresh database migration. Baseline: fresh volume migrated and seeded (Phase 1 checklist, section 2). 2026-11-25: fresh volume migrated to `8de09b58f4c2` on an isolated stack (branch `fix/ws4-2-audit-au3-au4-au5`, not yet committed). 2026-11-26: merged in PR #9 (`407ed63`); Docker CI on `407ed63` and `609864c` built and started the stack from a fresh volume; an isolated stack from `main` @ `609864c` migrated to `8de09b58f4c2` (WS4-3 checks).
- [ ] **[IN PROGRESS]** P2-8.8 Migration upgrade and downgrade tests. Baseline: `test_migrations_upgrade_downgrade_roundtrip` passes (E-B). 2026-11-25: `8de09b58f4c2` passes the round-trip, a step-down/up, and an in-transaction upgrade over existing data that keeps legitimate rows and refuses mixed ones (branch `fix/ws4-2-audit-au3-au4-au5`, not yet committed). 2026-11-26: merged in PR #9; the same tests pass in Backend CI on `407ed63` (314) and `609864c` (380).
- [ ] **[IN PROGRESS]** P2-8.9 GitHub Actions. Baseline: Backend, Frontend and Docker all passed on PR #2 (E-CI); and on the PR #4 to #8 merge commits (`78cf577`, `4be30b7`, `105869f`, `2079101`, `8007fe2`; Backend not triggered on `8007fe2`, a frontend-only change), and on `407ed63` (PR #9) and `609864c` (PR #10), with Backend and Docker on `45ef0ca` (E-MAIN). Remaining: re-run on the Phase 2 release candidate.
- [ ] **[IN PROGRESS]** P2-8.10 Documentation. Done: this checklist, the README Phase 2 section, PRODUCT_STRATEGY.md and PRODUCT_DECISIONS.md. Since then: VERIFICATION_WORKFLOW.md (WS1), GLOSSARY.md (WS2), WS3_CHECKLIST.md (WS3), WS4 plan and checklist (proposal). Remaining: docs for each Phase 2 feature. 2026-11-26: WS4-2 and WS4-3 plans, checklists and audits, [WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md), [PHASE_2_NEXT_STEPS.md](PHASE_2_NEXT_STEPS.md).
- [ ] **[NOT STARTED]** P2-8.11 Pull request review of the Phase 2 changes.
  - Note: PRs #3–#5 were merged by the owner's account with no recorded review; a review of the merged Phase 2 changes is still needed.
  - 2026-11-25: the same holds for PRs #6–#8 (all authored and merged by the owner's account, 0 reviews; `main` has no branch protection). An AI-assisted independent review of PR #7 exists ([WS4_2_AUDIT.md](WS4_2_AUDIT.md)) but is not a human review (audit AU-6).
  - 2026-11-26: the same holds for PR #9 (`407ed63`) and PR #10 (`609864c`): 0 review submissions, 0 review comments, 0 issue comments; green CI is not a review ([WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md) §4). Stays NOT STARTED.
- [ ] **[NOT STARTED]** P2-8.12 Release readiness review (all gates re-verified, blockers reported separately).

---

## Blockers

| ID | Blocker | Blocks | What unblocks it |
| --- | --- | --- | --- |
| B-1 | No confirmed permission to **publicly display** or redistribute company data and financials | P2-2.3, P2-5.2 to P2-5.10 (public display only; the private pilot is permitted under A-6) | **Gate G1:** a favourable Vietnamese legal opinion (A-6, Q-1), recorded in `data_sources` (`commercial_usage_status`, `terms_url`) |
| B-2 | No provider access: SSI FastConnect needs an SSI trading account and API keys | Only the later licensed-provider step (A-6 step 4); no longer blocks the pilot | Account, credentials and display rights, kept only in env vars or a secret manager |
| B-3 | Official portals unreachable from our automated environment (SSC portal: DNS failure; HNX: TLS error) | Automated checks only; the pilot uses manual retrieval by a person | Retry from another network, or manual retrieval |

## Gates (G1 and G2 approved under A-6; G3 under A-5)

| Gate | What | Passes when | Unlocks |
| --- | --- | --- | --- |
| G1 | Vietnamese legal opinion on storing and publicly displaying figures from mandatory disclosures (questions in [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) Q-1) | Written opinion is favourable and its conditions are recorded | Public display of real data (B-1); P2-2.3 |
| G2 | Private pilot: first 5 companies curated end to end from their own audited annual reports | 5 companies verified with two-person checks on figures, and hours per company recorded | Decision to scale to 20–30 companies (P2-3.1) |
| G3 | **Post-Phase 2.** Prerequisite for any 3D implementation (A-5) | (1) verified company relationship data exists; (2) a 2D relationship visualisation has shipped; (3) a 3D prototype shows measurable improvement over 2D for a specific user task; (4) an accessible 2D alternative stays available | 3D Discovery World implementation (long-term vision) |

## Track B: public-launch readiness (reported separately; not part of the completion count)

Approved under A-10. Phase 2 can complete as a **private pilot** while Track B is BLOCKED. Track B
statuses are never faked to make Phase 2 look complete, and they don't count toward the percentage
above.

| ID | Criterion | Status | Note |
| --- | --- | --- | --- |
| LR-1 | G1 passed: favourable written Vietnamese legal opinion, conditions recorded | BLOCKED | B-1; legal opinion not yet commissioned (Q-1). Scope is commercial use per Q-2 (resolved 2026-11-23) |
| LR-2 | Each data source's `commercial_usage_status` and terms recorded in `data_sources`, consistent with G1 | BLOCKED | Depends on LR-1 |
| LR-3 | Only data the opinion permits is displayed, with the attribution and linking it requires | BLOCKED | Depends on LR-1 |
| LR-4 | Public build contains no sample data (DS safeguards in place) | NOT STARTED | Verified by the AC-4 checks plus a build check |
| LR-5 | Hosting and budget decided (Q-7); privacy notice in place if analytics are used (D-9) | NOT STARTED | Owner decision |

**Track B summary:** 0 of 5 complete; 3 BLOCKED, 2 NOT STARTED.

## Risks

| ID | Risk | Mitigation |
| --- | --- | --- |
| R-1 | **The repo sits in an iCloud-synced `~/Documents`.** iCloud created conflict copies such as `frontend/src/app 2`, `.github/workflows 2`, `.git/index 2` and `.next/types/routes.d 2.ts`. The last one broke `npm run typecheck` in the working tree. **2026-11-23:** the copies were checked (empty folders, byte-identical files, a stale `.git/index` copy, build output) and removed. After that, `git fsck` was clean and lint, typecheck, `npm test` (8/8), build, ruff, mypy and pytest (87) all passed in the working tree. **Sync is still active, so copies can come back** | Move the repo out of iCloud-synced folders, or exclude it from sync. Before trusting a local check, run `find . -name '* [0-9]*'` outside `node_modules` and `.venv` |
| R-2 | Evidence is polymorphic and has no FK on `entity_id` (Phase 1 L-2) | Importer-enforced; add a periodic orphan check |
| R-3 | No reviewed path to correct company master data (Phase 1 L-3) | P2-2.8 |
| R-4 | HTTP status of not-found on streamed routes unverified (Phase 1 L-4) | P2-4.10 |
| R-5 | Unverified statements are currently displayed (labelled) | Decide under P2-4.8 and P2-5.x |

## Maintenance rules

1. Update an item whenever its task is implemented, tested or blocked, and record the evidence
   or blocker on the item.
2. Re-count the progress tables from the item lines after every meaningful change, and update
   **Last verified**.
3. Never mark PASS without evidence that meets the bar above, and never mark an existing feature
   PASS just because it exists.
4. Record new blockers (B-n) and risks (R-n) as they are found.
5. Don't delete unfinished items to raise the percentage. Descope only by a recorded product
   decision (P2-7.7) and keep the item marked as descoped.
6. Keep statuses consistent with the codebase. If a regression breaks a PASS item, set it to FAIL.
