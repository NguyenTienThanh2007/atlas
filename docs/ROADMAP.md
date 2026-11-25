# Roadmap

Three things are tracked separately and must not be confused: **software completion**, **data
verification** (real companies checked against their own documents) and **public-launch readiness**.

| Phase / gate | What it delivers | Status (2026-11-25, `main` @ `105869f`) |
| --- | --- | --- |
| **Phase 0** – repository foundation | Monorepo, Docker Compose, FastAPI + Next.js skeleton, CI | Complete ([checklist](PHASE_0_CHECKLIST.md)) |
| **Phase 1** – financial data foundation | Domain model, migrations, reference data, import framework with provenance, catalogue API, companies and sectors UI | Software complete; exit audit **CONDITIONAL PASS** ([audit](PHASE_1_EXIT_AUDIT.md)). 0 real companies |
| **Phase 2** – verified company pilot | ≥5 verified companies (stretch 20–30) in 4 sectors, M1–M5 MVP, Vietnamese-first UI, user research | Planning complete (A-1 to A-11 approved). **Execution in progress** under a conditional go (EX-1). Merged to `main`: WS1 verification workflow (PR #3, `45ef0ca`), WS2 Vietnamese-first UI (PR #4, `78cf577`), WS3 per-figure sources (PR #5, `4be30b7`), WS4-1 metric dictionary 1.1.0 (PR #6, `105869f`); CI green on each. WS4-2 ROE/ROA: implemented on a branch, uncommitted ([WS4 plan](WS4_FINANCIAL_INTELLIGENCE_PLAN.md), [WS4-2 plan](WS4_2_IMPLEMENTATION_PLAN.md)). 31 / 83 items PASS ([checklist](PHASE_2_CHECKLIST.md), [readiness](PHASE_2_READINESS.md)) |
| **G1** – legal and data rights | Vietnamese legal opinion on storing and publicly displaying figures from disclosures, incl. commercial use (Q-2) | Not commissioned. Blocks public display only |
| **G2** – five-company pilot | First 5 companies curated from their own audited reports, two-person checked, hours recorded | Shortlist owner-confirmed (kept private, A-11 §5); **0 verified**; reviewer (Q-3) not appointed |
| **Track B** – public-launch readiness | LR-1 to LR-5: G1 passed, source terms recorded, permitted display only, no sample data in public build, hosting/budget | 0 of 5 complete (3 BLOCKED, 2 NOT STARTED) |
| **G3** – 3D world | 3D Discovery World, only after verified relationships exist and demand is shown (A-5) | Deferred |

Phase 2 can finish as a **private pilot** while Track B is blocked. Nothing is published before G1.
Engineering progress is not launch permission: open owner items are Q-3 (reviewer), Q-7 (hosting and
budget), Q-8 (repo out of iCloud) and the glossary native-speaker review. Q-5 resolved 2026-11-24 (WS4-D4).
