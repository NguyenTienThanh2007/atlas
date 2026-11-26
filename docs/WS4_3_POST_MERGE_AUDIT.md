# WS4-3 post-merge audit

**Status: AUDIT — after merge. Docs only; no code, data, schema or GitHub setting changed.**
This audit checks what `main` contains after PR #10 against the WS4-3 plan, checklist, the
pre-implementation audit and the owner's decisions. It is an AI-assisted audit, **not** an
independent or human review.

| | |
| --- | --- |
| Audited | 2026-11-26 |
| `main` | `609864c27159d76599a90c663fc1c6d5072a38f6` (PR #10 merge), parent `407ed63` (PR #9 merge) |
| Feature commit | `42f2f8ae2c4f2b79670ef1438e744abe1cc0035b` |
| Result | Implementation matches the approved design; CI green; **no recorded review** (AU-6, W3-H2, P2-8.11 stay open) |

## 1. Kinds of evidence, kept apart

| Kind | Document or source | What it shows | What it does not show |
| --- | --- | --- | --- |
| Pre-implementation audit (historical) | [WS4_3_AUDIT.md](WS4_3_AUDIT.md), 2026-11-26, `main` @ `407ed63` | Design checked against the code before WS4-3; findings A3-1 to A3-16; READY WITH CONDITIONS | Anything about the implementation. Kept as written, with its own dated updates |
| Implementation evidence | [WS4_3_CHECKLIST.md](WS4_3_CHECKLIST.md) rows, gathered on branch `feat/ws4-3-period-comparison` before the commit | Local runs: clean-copy backend 379 passed (380 on the working tree), frontend 35/35, isolated Docker route check online and offline, browser desktop and 375 px | That GitHub ran the same; that anyone reviewed it |
| PR merge evidence | GitHub, PR #10 | Merged 2026-11-26 04:47:30 UTC by the owner's account (`NguyenTienThanh2007`); merge commit `609864c`; `git diff 42f2f8a 609864c` is empty | A review: 0 review submissions, 0 review comments, 0 issue comments |
| CI evidence | GitHub Actions on `42f2f8a` and `609864c` (§3) | Lint, types, tests, build and Docker health passed on the PR head and on the merge | Route check, browser checks (not in CI); independent review |
| Post-merge check (this audit) | §2, §6 | Code re-read on `main`; isolated stack confirmed to run `main`'s exact sources; route check re-run; language switch and past-the-end page checked | Human review |

## 2. Implementation verified on `main` (code read, not the PR text)

The working tree of `main` @ `609864c` was compared file by file with the sources running in the
isolated stack `atlasws43` (`backend/app`, `backend/migrations`, `frontend/src`,
`frontend/scripts`): identical.

| Property | Where on `main` | Verified by |
| --- | --- | --- |
| `annual_yoy` | `comparisons.py` `_candidate`, `expected_label` | Previous end within 7 days of the current end one year back; flows also contiguous (start − 1 day); label FY *t*−1. Tests `test_annual_yoy`, `test_seven_day_window`, `test_flows_must_also_be_contiguous`, API `test_annual_comparison_with_provenance`, `test_non_calendar_and_leap_day_years` |
| `quarterly_qoq` | same | Flows: previous end within 7 days of start − 1; balance sheets: 80–100 days earlier; label Q*n*−1 or prior Q4. Tests `test_quarter_on_quarter`, `test_balance_sheet_quarter_on_quarter[*]`, API `test_quarter_on_quarter_and_prior_q4` |
| `quarterly_yoy` | same | End within 7 days one year back; same quarter of FY *t*−1. Unit and API `test_quarter_year_on_year` |
| Granularity and scope | `_candidate` (annual vs quarter), `comparison_service.py` groups by (type, scope) | `test_annual_and_quarter_never_pair`, API `test_annual_and_q4_on_the_same_dates_never_pair`, `test_scopes_are_never_mixed` |
| Ambiguity refused | `match`: 2+ candidates → `ambiguous_previous_period`, `previous` null | `test_two_candidates_are_ambiguous`, API `test_ambiguous_previous_balance_sheet` |
| Label/date disagreement | `match` → `period_mismatch`, candidate shown, never used | `test_label_and_dates_disagree`, API `test_label_that_contradicts_dates` |
| Latest revision, no fallback | `service.py` `latest_statements` excludes any row a newer revision supersedes, whatever its status | API `test_restated_previous_year_is_used_and_disclosed`, `test_bad_latest_revision_never_falls_back[*]` (rejected, disputed, superseded) |
| Exact `Decimal` | `_EXACT.subtract`, `rounded_quotient` (shared with WS4-2), 100-digit context trapping `Inexact` | F1–F16 incl. 38-digit F16; 600 random pairs against a `Fraction` oracle; float guard covers the package |
| Zero prior, sign change | `compare`: prior 0 → `change_only` / `prior_zero`; opposite signs → `sign_change`; current 0 is computed (W3-D2) | F5–F10 |
| Mixed sample/real refused | `compare` (any side's class ≠ company's, or company mixed) plus database triggers from `8de09b58f4c2` | `test_mixed_sample_and_real_is_refused[*]`, API `test_mixed_legacy_data_is_refused` |
| Reason precedence | `RANK` (0–9), side order | `test_precedence_lists_every_issue`, `test_rank_9_runs_only_when_nothing_else_applies` |
| Per-figure provenance | `catalog.py` `_side`: `MetricSourceOut.for_figure` per side | API test checks page, link status and URL on both sides; UI disclosure uses `FigureSourceLine` |
| Pagination | API `limit`/`offset`/`total`; page uses `Pagination` with `comparisons_page`, `showRange` | Route check range "1–20 / 44"; past-the-end page shows "Trang 99 không có mục nào (tổng cộng 44 mục)" (checked in this audit) |
| vi/en parity | `vi.ts`, `en.ts` `company.comparison` | `i18n.test.ts` key parity in CI (35/35); route check in vi and en |
| Language switch keeps state | `Shell` keeps the query | Checked in this audit: `/companies/…?compare=quarterly_qoq&compare_scope=consolidated` links to the same query under `/en` |
| 375 px | stacked rows below 640 px | Browser pass before merge (`scrollWidth` 375); local only |
| Read-only, bounded | GET only; fixed query count | API `test_read_only_and_bounded_queries` |
| Input validation | `type` enum (required), `scope` enum, `metric` must be a dictionary code (≤ 64 chars), `fiscal_year` 1990–2200, `limit` 1–100; frontend keeps only valid `compare`/`compare_scope` | API `test_filters_paging_and_errors` (404 and 8 cases of 422) |

**No defect found in the merged code.** Differences between the plan text and the code, none of
which changes a result:

| ID | Difference | Effect | Proposed handling |
| --- | --- | --- | --- |
| PM-1 | Plan §12.4 gives `prior_zero` and `sign_change` no side ("—"); the code records `previous` and `current` | API `issues[].side` always has a value | Note in the plan (done, dated) |
| PM-2 | `issues[].period_end` is `null` when no previous statement matched; the plan doesn't say | Documented in the schema comment | Note in the plan (done, dated) |
| PM-3 | Display limit written "> 999,99%" (site percentage style); the approved W3-D7 text has a space before "%" | Cosmetic | **Owner to confirm**; recorded, not changed |
| PM-4 | W3-D11 says "with the WS4-2 vi/en texts"; the code uses the comparison wording "Không so sánh được: …" / "Not comparable: …" from plan §12.5 | Wording only | **Owner to confirm**; recorded, not changed |

## 3. CI evidence

| Commit | Workflow | Result | Detail from the log |
| --- | --- | --- | --- |
| `609864c` (merge, push) | [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757432716) | success | ruff and format clean; mypy "no issues found in 41 source files"; `380 passed`; `alembic check` "No new upgrade operations detected" |
| `609864c` | [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757432592) | success | `npm ci` "found 0 vulnerabilities"; lint; typecheck; tests pass 35, fail 0; "Compiled successfully" |
| `609864c` | [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757432573) | success | compose build; db, backend, frontend healthy; health and home page reachable |
| `42f2f8a` (PR head) | [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757230537), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757230494), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45757230524) | success, success, success | — |

No failed or skipped check runs. The legacy commit-status API reports `pending` with 0 statuses
for both commits; nothing uses it, so it is not a failure. CI does **not** run the route check or
any browser check; that evidence is local (§1).

## 4. Review-process evidence

| Check | Result |
| --- | --- |
| PR #10 review submissions | 0 (`gh api …/pulls/10/reviews`) |
| PR #10 review comments | 0 (`…/pulls/10/comments`) |
| PR #10 issue comments | 0 (`…/issues/10/comments`) |
| Review decision | none |
| `main` branch protection | none ("Branch not protected") |

CI success is not a code review. **W3-H2 stays NOT STARTED, AU-6 stays open, and P2-8.11 stays
NOT STARTED.** PRs #3 to #10 have all been merged by the owner's account without a recorded
review. This audit, like WS4_2_AUDIT.md, is AI-assisted and does not replace one.

## 5. Documentation reconciled (dated updates; earlier text kept)

| Document | Stale statement found | Update |
| --- | --- | --- |
| README.md | Status dated 2026-11-25 @ `8007fe2`; "WS4-3 … is a plan awaiting owner decisions"; "Period comparison … not built" | Status and WS4-3 lines brought to `609864c` |
| ROADMAP.md | "AU-3 … AU-5: on a branch, not yet committed"; "WS4-3 … implementation not started"; 31 / 83 | Phase 2 row brought to `609864c`; 32 / 83 |
| PHASE_2_CHECKLIST.md | Current status ends "Next: WS4-3 … plan only"; last verified `8007fe2`; P2-2.6, P2-8.7, P2-8.8 say "not yet committed"; P2-5.13 IN PROGRESS | Dated notes with PR #9 and PR #10 evidence; P2-5.13 → PASS (its criterion is met; the review gap stays with P2-8.11); counts recounted from the 83 item lines |
| PRODUCT_DECISIONS.md | §2e last says implementation authorised; no merge record. AU fixes authorised, no merge record | Dated implementation-status notes; PM-3 and PM-4 listed for the owner |
| WS4_CHECKLIST.md | WS4-G9 evidence "uncommitted"; last verified `8007fe2` | Dated merge evidence |
| WS4_3_CHECKLIST.md | "not committed"; W3-H3, W3-H4 NOT STARTED | W3-H3 and W3-H4 → PASS with CI and merge evidence, noting their dependency W3-H2 was not met; W3-H2 stays NOT STARTED |
| WS4_3_IMPLEMENTATION_PLAN.md | Top status "not committed" | Dated merge note; PM-1, PM-2 |
| WS4_2_AUDIT.md | AU-3, AU-4, AU-5 "FIXED on the branch … merge pending" | Dated note: merged in PR #9 (`407ed63`) with CI evidence; AU-6 still open and extended to PRs #9, #10 |
| WS4_3_AUDIT.md | — | **Not edited**: historical pre-implementation audit |

## 6. Commands run for this audit

```
git status --short; git branch --show-current; git rev-parse HEAD; git fetch origin
git rev-list --left-right --count HEAD...origin/main        # 0 1: local HEAD = PR head, main 1 ahead
git diff --stat 42f2f8a 609864c                             # empty
gh pr view 10 --json state,mergedAt,mergeCommit,headRefOid,reviews,comments,reviewDecision,mergedBy
gh api repos/NguyenTienThanh2007/atlas/pulls/10/{reviews,comments}; …/issues/10/comments
gh api repos/NguyenTienThanh2007/atlas/commits/<sha>/check-runs   # both commits
gh run view <id> --log                                      # counts quoted in §3
git archive 609864c … | diff -rq against the isolated stack sources   # identical
node scripts/check-routes.mjs (BASE_URL :3063, API_URL :8063, fictional TST7)   # passed
curl the language-switch link and ?comparisons_page=99      # §2
```

No test was re-run locally against `main` for this audit beyond the route check; the backend and
frontend suites on `main` are evidenced by CI (§3).
