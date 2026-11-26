# Phase 2: next steps after WS4-3

**Status: RECOMMENDATION (2026-11-26, `main` @ `609864c`). Requires owner decision.** Nothing here
is authorised or started. Progress figures come from [PHASE_2_CHECKLIST.md](PHASE_2_CHECKLIST.md),
recounted from its 83 item lines on 2026-11-26: **32 PASS, 26 IN PROGRESS, 15 NOT STARTED,
10 BLOCKED, 0 FAIL.**

## 1. Where Phase 2 stands

- **Software merged:** WS1 to WS3, WS4-1 (dictionary), WS4-2 (ROE, ROA), the WS4-2 audit fixes
  (PRs #8, #9) and WS4-3 (period comparison, PR #10). CI green on every merge.
- **Phase objective not yet reached:** 0 verified companies. The pilot (G2) needs a second
  reviewer (Q-3). Public display of real data needs the legal opinion (G1).
- **Process gap:** PRs #3 to #10 merged with no recorded review (AU-6, P2-8.11).

## 2. Candidate workstreams

"Claude" = work an AI assistant can do in the repository. "Human / external" = needs the owner or
someone outside.

| | Candidate | Phase 2 items | Depends on | Claude can do | Needs a human / external party | Risk if delayed |
| --- | --- | --- | --- | --- | --- | --- |
| A | **WS4-4: missing-data semantics and bank applicability** | WS4-F2, F3, F8, WS4-E2; P2-5.15 (and display of bank pilot companies) | Owner decisions on Phase B states (WS4-F7 deferred them) and on how a company is classified bank / non-bank; probably a schema change, which needs explicit approval | Plan, decision register, migration, engine, API, UI, tests (as for WS4-2 and WS4-3) | Owner decisions; approval of any migration | Banking is a proposed pilot sector (A-7). Without applicability, a bank shows "missing" where a metric does not apply, and "not reported" can't be stored at all (`value` is NOT NULL) |
| B | **P2-6.12 security review** | P2-6.12; supports P2-8.12 | None | An AI-assisted review of input handling, external links, dependency audit and secrets across the Phase 2 changes, with findings and fixes for approval | An independent human review if the owner wants P2-6.12 to rest on one; any GitHub setting | Low exposure today (no public deployment), but eight merged PRs were never reviewed |
| C | User research, round 1 | P2-7.3 to P2-7.5 | Owner's recruiting (Q-4 plan confirmed) | Session guide, log template, synthesis of notes the owner provides | **Owner** runs sessions with real people | H1 stays a hypothesis; features may miss the real problem |
| D | G2 reviewer and five-company verification | P2-3.x, G2 | **Q-3** (named second reviewer) | Curation tooling, checks, coverage report (P2-3.9) on fictional data; import of real data only once authorised | **Second reviewer**; the owner's curation of real filings | The phase objective (≥ 5 verified companies) can't be met |
| E | G1 legal opinion | P2-2.3, P2-5.2 to P2-5.10, Track B | Owner commissions it | Question list exists (Q-1); can tidy it | **Vietnamese lawyer** | All public display of real data stays blocked |
| F | Glossary native-speaker review | GLOSSARY.md (WS2, WS4-2, WS4-3 terms) | A native speaker | Prepare the term list and context | **Native speaker** | Wording errors in a Vietnamese-first product |
| G | Q-7 hosting and budget; Q-8 repository location | Track B LR-5; risk R-1 | Owner | Options and costs; a move checklist for Q-8 | **Owner** decides | Q-8: the repository stays in an iCloud-synced folder (sync conflicts) |

## 3. Recommendation

**Next engineering workstream: A, WS4-4 missing-data semantics and bank applicability**, started
the same way as WS4-3: a plan and decision register first, no code until the owner approves it.

Why A:

1. It is the remaining engineering prerequisite for the pilot. Banking is one of the proposed
   pilot sectors, and today a bank company would show ROE/ROA inputs and dictionary metrics as
   simply missing.
2. Its blockers are owner decisions, not external parties, so it can move now.
3. It touches the schema (a way to record "not reported", and a bank / non-bank classification),
   so it is better settled before real data is imported than after.

**Also recommended, small and independent: B, an AI-assisted security review (P2-6.12)**, clearly
labelled as not independent. It can run before or alongside A's planning. It would not close
P2-8.11, which needs a recorded review by a person.

**For the owner, in parallel (no engineering dependency):** record a review of PRs #9 and #10, or
of the Phase 2 changes so far (P2-8.11); appoint the Q-3 reviewer (unblocks D); start recruiting
for round 1 (C); commission G1 (E); and decide Q-7 and Q-8 (G).

## 4. Open blockers (unchanged by WS4-3)

| Item | Owner | Blocks |
| --- | --- | --- |
| G1 legal opinion | Owner / lawyer | Public display of real data (10 BLOCKED items) |
| Q-3 second reviewer | Owner | G2, any VERIFIED figure |
| AU-6 / P2-8.11 recorded review | Owner | Release readiness (P2-8.12) |
| Glossary native-speaker review | Owner / reviewer | Final Vietnamese wording |
| Q-7 hosting and budget, Q-8 repository location | Owner | Track B LR-5; risk R-1 |
| PM-3, PM-4 (WS4-3 wording) | Owner | Nothing; confirm or ask for a change |
