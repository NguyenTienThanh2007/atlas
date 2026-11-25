# Phase 2 readiness

## Status update (2026-11-25, verified on `main` @ `8007fe2`)

Execution started on 2026-11-23 under the owner's **CONDITIONAL GO** (EX-1,
[PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2c). The assessment below is kept as written on
2026-11-23; this section records what changed since.

| Workstream | PR | Merge commit | CI on the merge commit (Backend / Frontend / Docker) | Checklist effect |
| --- | --- | --- | --- | --- |
| WS1 verification workflow and figure provenance (EX-2) | #3 | `45ef0ca` | [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45180859560) and [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45180859516) success; Frontend not triggered (path filter, no `frontend/` change) | P2-2.1, P2-2.2, P2-2.5, P2-2.8, P2-6.4, P2-6.5 PASS |
| WS2 Vietnamese-first UI (EX-3) | #4 | `78cf577` | [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45185760407), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45185760378), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45185760569) success | P2-4.11 PASS; P2-4.12 IN PROGRESS (glossary review) |
| WS3 per-figure source transparency | #5 | `4be30b7` | [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45318642634) (201 passed), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45318642611) (24/24), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45318642530) success | P2-4.13 PASS |
| WS4-1 metric dictionary 1.1.0 (WS4-D10, D12) | #6 | `105869f` | [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45532503338) (224 passed), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45532503452) (25/25), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45532503332) success | P2-5.1 progress; Phase 1 exit audit F-1, F-2 resolved |
| WS4-2 ROE / ROA | #7 | `2079101` | [Backend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617789) (288 passed), [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617702) (27/27), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45538617848) success | P2-5.11, 5.12, 5.17 PASS ([WS4_2_CHECKLIST.md](WS4_2_CHECKLIST.md)) |
| WS4-2 audit fixes AU-1, AU-2 | #8 | `8007fe2` | [Frontend](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45610139607) (28/28), [Docker](https://github.com/NguyenTienThanh2007/atlas/actions/runs/45610139576) success; Backend not triggered (no backend change) | Display only ([WS4_2_AUDIT.md](WS4_2_AUDIT.md)); AU-3 to AU-6 open |
| Audit fixes AU-3 (sample/real isolation, migration `8de09b58f4c2`), AU-4, AU-5 | not opened | none | local only: backend 314 passed, frontend 31/31, isolated Docker and browser ([WS4_2_AUDIT.md](WS4_2_AUDIT.md)) | Branch `fix/ws4-2-audit-au3-au4-au5`, not yet committed; owner authorised |
| WS4-3 period comparison | none | none | n/a (design only) | Decisions W3-D1 to W3-D10 approved 2026-11-25 ([PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md) §2e); implementation not authorised, not started |

PRs #3 to #8 were opened and merged by the owner's account; GitHub records no separate review
(P2-8.11 stays NOT STARTED). Checklist: **31 / 83 PASS** (recounted from item lines).

**Unchanged blockers:** Q-3 (no independent reviewer, so nothing can be VERIFIED), G1 (no legal
opinion, so nothing real can be published), Q-7 (hosting and budget), Q-8
(repo in iCloud, R-1), glossary native-speaker review (P2-4.12). Engineering completion is not
permission to launch. Q-5 (bank metrics) was resolved on 2026-11-24 by WS4-D4 and D5.

## Assessment of 2026-11-23 (before execution)

Date: 2026-11-23. Assessed after the [Phase 1 exit audit](PHASE_1_EXIT_AUDIT.md) (CONDITIONAL PASS).
The detailed plan, gates, Track B and risks live in [PHASE_2_CHECKLIST.md](PHASE_2_CHECKLIST.md).
This page only judges whether execution can start.

**Recommendation: READY WITH BLOCKERS.** The private pilot work can start once the owner approves
execution: curation workflow, Vietnamese UI, interview round 1. **No company can become VERIFIED**
until the Q-3 reviewer is appointed, and **nothing can be published** until G1.

## Product readiness

| Check | State |
| --- | --- |
| A-1 to A-11 | All approved, unchanged |
| AM-1 (amends A-9, n = 10) | Intact |
| Q-2, Q-4, Q-9 | Resolved, unchanged |
| Q-3 (second reviewer) | **Open.** No reviewer named |
| Pilot shortlist | Five companies, owner-confirmed 2026-11-23. Names kept in the private workspace (A-11 §5) |
| Verification status | All five **unverified** |

## Data readiness

| Check | State |
| --- | --- |
| Private G2 package | Present outside the repo; 23/23 SHA-256 sums verify |
| Selection criteria E1–E8 | Unchanged (file hash matches the approved version) |
| Owner decisions recorded privately | Hosts linked from investor pages accepted as "own website"; one company's audit Emphasis of Matter accepted |
| Data rights | Uncertain, held for G1. No commercial rights assumed |
| Private evidence in the public repo | None |

## Execution readiness

| Check | State | Where |
| --- | --- | --- |
| Scope (Track A, AC-1 to AC-8) | Clear | PHASE_2_CHECKLIST §1, A-10 |
| G1 / G2 dependencies | Documented | PHASE_2_CHECKLIST "Gates", [ROADMAP](ROADMAP.md) |
| Research-round method | Documented (A-9, AM-1, Q-4) | PRODUCT_STRATEGY §10, PRODUCT_DECISIONS |
| Verification workflow | Documented (criteria §6; two-person checks) | PILOT_SELECTION_CRITERIA |
| Hosting and budget | Open (Q-7, LR-5) | PHASE_2_CHECKLIST Track B |

## Blockers and open items before or during execution

1. **Q-3:** appoint the second reviewer. This blocks VERIFIED status.
2. **G1:** commission the legal opinion. This blocks public display (Track B).
3. **Metric definitions and bank applicability** (exit audit F-1, F-2; Q-5): needed before figures
   are shown to learners. Each is a versioned dictionary change needing owner approval.
4. **Q-7** hosting/budget, and **Q-8** moving the repo out of iCloud (R-1).

Phase 2 is not complete and has not been started. Execution waits on explicit owner approval.
(Superseded the same day by EX-1, the owner's conditional go; see the status update above.)
