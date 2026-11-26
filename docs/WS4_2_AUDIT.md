# WS4-2 independent review (PR #7)

Audit of the ROE/ROA implementation, run on 2026-11-25. It is a record of evidence only and
changes no code, formula, decision or scope.

| | |
| --- | --- |
| PR | [#7](https://github.com/NguyenTienThanh2007/atlas/pull/7), head `037a820`, base `main` @ `105869f` |
| State found | **Already merged** on 2026-11-25 03:14:43 UTC by the owner's account, as `2079101`. The merge tree is identical to `037a820`. The audit was requested before merge, so it reviews merged code |
| Reviews on GitHub | 0 reviews, 0 comments |
| Diff | 27 files, all WS4-2 code, tests or docs. No secret patterns, no pilot names, no migration, no `models.py` or `data/seed` change |

## Evidence

| Check | Where | Result |
| --- | --- | --- |
| GitHub Actions on PR head `037a820` | Backend, Frontend, Docker | Success ([Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45537877885/job/138948865462), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45537877803/job/138948865076), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45537877765/job/138948865053)) |
| GitHub Actions on merge `2079101` | Backend (run 45538617789), Frontend (45538617702), Docker (45538617848) | Success; Backend log `288 passed`, `alembic check` clean; Frontend tests 27, pass 27 |
| Backend, local, `main` @ `2079101`, fresh PostgreSQL 17 | ruff, format, mypy, pytest, alembic, pip-audit | Clean; **288 passed**; `alembic check` clean; downgrade base → upgrade head OK; no known vulnerabilities |
| Frontend, local clean copy | eslint, tsc, tests, build, npm audit | Exit 0, exit 0, **27/27**, exit 0, 0 vulnerabilities |
| Independent oracle | 8 fictional companies (`TST1`–`TST8`), recomputed from the raw bundle with `fractions.Fraction`, compared with the API | **16/16 results identical** (status, reason, `value`, `percent`, `denominator_average`) |
| API edge cases | Isolated stack `atlasaudit7` | Non-UUID 422; unknown company 404; bad `scope` 422; `limit=101` 422; no `E` notation; no result carries `verification_status` |
| Route check | Same stack | Online, offline, and per calculated value (TST1, TST6) in vi and en: passed |
| Browser | Same stack | vi and en, desktop and 375 px: no horizontal scroll, safe external links (`noopener noreferrer`, `#page=7`), no unnamed links, no console errors |

The oracle covered these cases: a calculation in triệu đồng; repeating decimals; a half-up tie on a
negative percentage; a case where double rounding would differ; ratios of about 10^31 and about
10^-32; negative zero; a non-calendar year; a 7-day opening window; separate scope; and
`equity_parent` missing with `total_equity` present (refused, not substituted).

## Findings

No CRITICAL or HIGH findings.

| ID | Severity | Where | Finding | Fix (proposed, not applied) |
| --- | --- | --- | --- | --- |
| AU-1 | MEDIUM (fixed on branch) | `frontend/src/app/[lang]/companies/[id]/page.tsx:253` | A ratio that was **not** computed still shows "Tính từ số liệu chưa kiểm chứng" / "Calculated from unverified figures" next to its reason. Reproduce: company with `equity_parent` missing (TST6), FY2025 ROE row. The label says a calculation happened when none did | Show the verification label only when `status === "computed"` |
| AU-2 | MEDIUM (fixed on branch) | `frontend/src/lib/api-core.ts` `formatFixed`; page percentage | Negative percentages render with an ASCII hyphen (`-45,45%`). The approved display rule (WS4-D8, plan §10) says to use the minus sign `−` (U+2212) | Map a leading `-` to `−` in display formatting (string only), with a test |
| AU-3 | LOW | `docs/WS4_2_IMPLEMENTATION_PLAN.md:135, 296`; `backend/app/calculations/ratios.py` `_verification` | The docs say "database rules" stop sample and real data from mixing. In fact the importer enforces it (`importer.py:262, 389`); the database only checks evidence status on insert. If inputs were mixed by a direct SQL write, the result would be labelled `sample` and still computed | Correct the wording; optionally refuse mixed sample and non-sample inputs in `compute()` |
| AU-4 | LOW | `page.tsx:261` | The unit of the average denominator is hard-coded `"VND"`, not taken from the inputs. This is correct today because only VND is imported | Use the inputs' unit |
| AU-5 | LOW | `page.tsx:39` | The page fetches `limit: 40` with no paging and no "more" notice. A company with more than 10 annual years in both scopes would be cut off without warning. The statements section has the same pattern | Page through results or show that more exist |
| AU-6 | LOW (process) | PR #7, docs | The PR was merged without a recorded review (P2-8.11, W2-H2). Several docs still say "branch, uncommitted" | Record the owner's review; close out the docs to `2079101` |

## Fixes (2026-11-25, branch `fix/ws4-2-display-au1-au2` from `main` @ `2079101`; merged as PR #8, `8007fe2`)

| ID | Change | Evidence |
| --- | --- | --- |
| AU-1 | New `calculationLabel()` in `frontend/src/lib/api-core.ts`: only a computed ratio has an input-verification label; the company page uses it | Unit test "only a computed ratio shows an input-verification label"; route check now requires each label to appear exactly as often as the API has computed results with it; browser: TST6 FY2025 ROE shows only its reason, ROA keeps its label |
| AU-2 | `formatFixed` writes negative values with the minus sign U+2212 (WS4-D8) | Unit tests (`−5,00`, `−45.45`, no ASCII hyphen); browser: `−45,45%` (code point 2212) and `−3.13%` |

Verification of the fixes: frontend clean copy: eslint exit 0, tsc exit 0, `npm test` **28/28**,
build exit 0, `npm audit` 0. Isolated stack `atlasaufix` with the audit cases: route check passed
online, offline and per value for TST1, TST3, TST6 in vi and en; no console errors. Backend
unchanged. AU-3 to AU-6 are still open.

## Assessment

The financial results are correct, and the provenance, revision, verification and decimal rules
match the approved design. Two MEDIUM display defects remain and should be fixed before research
participants see ratios. Blockers that stay open: Q-3, G1, Q-7, Q-8, and the native-speaker review
of the glossary.

## Closeout (2026-11-25, `main` @ `8007fe2`)

The findings table above is kept as first written. This section records where each finding stands now.

| ID | Status | Evidence | Risk | Recommended action | Code change? |
| --- | --- | --- | --- | --- | --- |
| AU-1 | **FIXED** | PR #8 merged as `8007fe2` (head `0aa7977`, tree identical). CI on the merge: [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45610139607) 28/28, [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45610139576) success; on the head: Frontend and Docker success | None left | None | Done |
| AU-2 | **FIXED** | Same PR, CI and tests (`formatFixed` writes U+2212) | None left | None | Done |
| AU-3 | **OPEN, confirmed; raised to MEDIUM** | Probe on a throwaway database (scratch test, not in the repo): an evidence row with status `sample` and a balance sheet for a **real** company were inserted directly through the ORM, bypassing the importer. Both writes were accepted, and consolidated ROE for that real company was **computed** (`0.0909090909`) from a sample closing balance plus real numerator and opening, labelled `sample`. Permitted write paths can't do this: the importer checks `company.is_sample` against the source (`importer.py:262, 389`) and imported evidence status (`:166`); the review CLI only changes status, and sample evidence can never be reviewed; the API is read-only. No database constraint links a statement's evidence status to its company's `is_sample` | Only someone with direct database write access can create the mix. The result is then labelled `sample`, never `verified`, but it is still a number built from mixed data | (1) `compute()` refuses inputs that mix `sample` with non-sample statuses, using a new reason code such as `mixed_sample_and_real`. This is a code change plus a new reason code, so it needs owner approval. (2) Defence in depth: a database trigger on `financial_statements` insert requiring evidence status `sample` exactly when the company is a sample company. This is a migration and needs separate approval. The wording in the WS4-2 plan is already corrected (importer, not database) | Yes (both need approval) |
| AU-4 | **OPEN** | `page.tsx` writes the average's unit as `unitText(t, "VND")`. The data model already supports a derived unit: each input carries `unit` (from `financial_metrics.unit`), and `compute()` refuses inputs whose unit differs from their statement's currency (`unit_mismatch`). So when a result is computed, both denominator inputs share one unit | Low today: only VND can be imported. It would mislabel the unit if another currency were ever allowed | Take the unit from the `denominator_closing` input in the UI. Optionally add `denominator_unit` to the API (an additive field) | Yes (frontend, small) |
| AU-5 | **OPEN, wider than first reported** | The company page fetches statements with `limit: 20` and calculated metrics with `limit: 40`, and shows neither the API's `total` nor any "more" control. Statements: 3 types × 2 scopes × years plus quarters reaches 20 after about 3 years of annual statements alone. Calculated metrics: 2 formulas × 2 scopes × years reaches 40 after 10 years. The API supports `limit`/`offset` up to 100 with `total` | Financial history can disappear from the page without notice once data grows. No real data is loaded yet | Show "showing X of Y" whenever `total` is larger, plus a link to the next page (`?statements_page=`), or a year filter. Never truncate silently | Yes (frontend) |
| AU-6 | **OPEN (process)** | PRs #1 to #8 were all opened and merged by the owner's account, with 0 GitHub reviews and 0 comments; `main` has no branch protection (GitHub API: "Branch not protected"). This audit is an AI-assisted review, not a human or independent one | Merges are not reviews, so P2-8.11 and W2-H2 stay NOT STARTED | The owner records their own review of each merged workstream (for example as a PR comment), and later appoints a second reviewer (related to Q-3). GitHub can't require approval from the PR author's own account, so branch protection with required reviews only works once a second account exists. No external approval is claimed here | No (settings and process) |

## AU-3, AU-4, AU-5 fixes (2026-11-25, branch `fix/ws4-2-audit-au3-au4-au5` from `main` @ `8007fe2`, not yet committed)

The owner authorised these fixes, including the migration. The tables above are unchanged.

### AU-3: sample/real isolation (two independent layers)

**Classification:** a company is sample or real through `companies.is_sample`. Evidence is
"sample" exactly when `verification_status = 'sample'`. Every other status (unverified, verified,
disputed, rejected, superseded) is real; verification state and classification are different
things. The invariant is that every evidence row of a company (company, security and statement
evidence, including each statement's source evidence) carries its company's classification.

| Layer | What | Where |
| --- | --- | --- |
| 1. Database | Migration `8de09b58f4c2` adds triggers on `financial_statements` (insert/update), `evidence` (insert, plus update: classification can never change), `companies` (update of `is_sample` refused once the company has statements or evidence) and `securities` (update of `company_id` refused when its evidence would then mismatch). All raise `check_violation`. The checks take `FOR SHARE` on the company row, and a reclassification needs that row's exclusive lock, so concurrent writes serialise. Before creating the triggers, upgrade audits existing data: if anything violates the invariant it fails, listing statement ids only, and changes nothing. Downgrade drops the triggers and functions and changes no data | `backend/migrations/versions/2026_11_25_1200-8de09b58f4c2_sample_real_isolation.py` |
| 2. Calculation engine | Refuses any input whose classification differs from its company's, and refuses every result when any statement of the company mixes the two (new reason `mixed_sample_and_real`, rank 0; `input_verification` is `null` so no label hides the mix). Formulas and rounding are unchanged | `backend/app/calculations/ratios.py`, `service.py`; vi/en text in the frontend dictionaries |

Evidence (all in a throwaway database; nothing touches the owner's stack):

- `backend/tests/test_sample_isolation.py` covers:
  - Direct writes are refused through both the ORM and raw SQL: a statement with evidence of the
    other kind; mismatched statement-entity evidence; company and security evidence; raw SQL
    `UPDATE` of evidence status, of a statement's evidence and of `is_sample`; moving a security.
  - A company with no data can still be reclassified, and legitimate sample and real imports
    still work.
  - The upgrade audit refuses existing mixed data (shown with triggers disabled).
  - An in-transaction downgrade, insert and upgrade keeps legitimate data and refuses mixed data.
  - Two-connection concurrency: in both orders, the second writer waits on the lock and times out
    instead of slipping past.
  - With triggers disabled, legacy mixed data makes the API refuse every ratio with
    `mixed_sample_and_real`.
- `backend/tests/test_ratios.py`: mixed-input refusals, the company-level mix, and precedence
  (mixed first).
- `tests/test_models.py`: the helper `new_statement` used to create `unverified` evidence even for
  sample companies, which is exactly the mix now refused. It was corrected to match the company's
  classification.
- Clean copy on fresh PostgreSQL 17:
  - ruff, format and mypy clean; `pytest` **314 passed** (288 before).
  - `alembic upgrade head`, then `check` clean, then downgrade base and upgrade, then downgrade
    one step and upgrade: all fine. `pip-audit` reports no known vulnerabilities.
  - No committed test rows were left behind.
- Isolated Docker stack (`atlasau345`):
  - `psql` attempts to add sample company evidence to a real company, flip `is_sample`, or set an
    evidence status directly were each refused with the isolation or immutability error.
- The owner's running database was checked with a read-only transaction: revision `31b1317163eb`,
  0 companies, 0 mixed rows. The upgrade audit will pass there.

**Status: FIXED on the branch. All seven AU-3 acceptance criteria are met; merge pending.**

### AU-4: the denominator's unit comes from the inputs

`denominatorUnit()` (`frontend/src/lib/api-core.ts`) takes the single unit shared by a ratio's
denominator inputs. When the inputs carry no unit, or more than one, it returns nothing rather
than a guessed currency. The page no longer hard-codes `"VND"`. Data-model limit: the importer
accepts VND only, so other currencies can't reach the API today; the helper handles any unit
string (tested with `USD`).

Evidence: unit tests (VND, USD, no denominator input, empty unit, mismatched units). Browser:
"Bình quân mẫu số: 1.245 đồng" and "Average denominator: 1,245 VND". **Status: FIXED on the
branch.**

### AU-5: explicit server-side pagination

The statements and calculated-ratio sections are each paged on the server (20 per page) with their
own parameters, `statements_page` and `ratios_page`. Each list always shows "Đang hiển thị X–Y / N"
/ "Showing X–Y of N", with Previous/Next links that keep the other list's page and the language,
and an anchor back to the section. An invalid page value counts as page 1. A page past the end
says so ("Trang 9 không có mục nào (tổng cộng 50 mục)") and links back to the last page; it never
shows "no statements". The existing `Pagination` component gained these options and stays
backward compatible for the companies list. Navigation is a server render, so there are no
client requests that could finish out of order.

Evidence:
- Unit tests for `pageRange` (first, middle, last, empty, single page, past the end) and for the
  texts.
- The route check, on a fictional company with 51 statements and 50 ratios, passed online and
  offline, in vi and en, for: both ranges; page 2 of ratios showing the API's offset-20 items while
  statements stay on page 1; the statements Next link keeping `ratios_page`; past-the-end; and
  `abc` read as page 1.
- Browser:
  - Keyboard Enter on the ratios "Trang sau" link moved ratios to 21–40 while statements stayed
    21–40.
  - 375 px in English: "Showing 41–51 of 51" with no Next link, and "Page 9 has no items (50 in
    total)" linking back to page 3; no horizontal scroll; no console errors.
- Frontend clean copy: eslint, tsc, **31/31** tests, build, `npm audit` 0.

**Status: FIXED on the branch.**

### Still open

AU-6 (process: no recorded human review, no branch protection) stays open. Q-3, G1, Q-7, Q-8 and
the native-speaker glossary review are unchanged.

## Status update (2026-11-26, after merge)

The statuses above are kept as written. Since then:

| Finding | Status | Evidence |
| --- | --- | --- |
| AU-3 | **FIXED and merged** | PR #9 merged 2026-11-25 12:44 UTC as `407ed63` (identical to head `6c01f11`). Backend CI on the merge: `314 passed`, `alembic check` clean ([run](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669307)); migration `8de09b58f4c2` is the head on `main` |
| AU-4 | **FIXED and merged** | Same PR. Frontend CI on the merge: 31/31, build ([run](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669447)) |
| AU-5 | **FIXED and merged** | Same PR and Frontend run; Docker CI success ([run](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45616669282)) |
| AU-6 | **OPEN** | PR #9 and PR #10 (WS4-3, `609864c`) were also merged by the owner's account with 0 reviews and 0 comments; `main` is still unprotected ([WS4_3_POST_MERGE_AUDIT.md](WS4_3_POST_MERGE_AUDIT.md) §4) |

