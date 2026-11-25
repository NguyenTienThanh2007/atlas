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

## Fixes (2026-11-25, branch `fix/ws4-2-display-au1-au2` from `main` @ `2079101`, uncommitted)

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
