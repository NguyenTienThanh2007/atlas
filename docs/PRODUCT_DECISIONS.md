# ATLAS product decisions

Decision log for Phase 2 product direction. Rationale lives in
[PRODUCT_STRATEGY.md](PRODUCT_STRATEGY.md), referenced as §n. Project owner: **Tiến Thành**.
Created 2026-11-23.

**Approval status: all decisions A-1 to A-11 approved** by Tiến Thành on 2026-11-23. Everything else is still a
recommendation. Claude Code recommends; only the project owner approves. When a decision is
approved, record the date and approver on its row and update
[PHASE_2_CHECKLIST.md](PHASE_2_CHECKLIST.md).

## 1. Decisions recommended by Claude Code

These are within engineering and product practice. They follow from the evidence and constraints,
and can be reversed by the owner at any time.

| ID | Decision | Rationale |
| --- | --- | --- |
| D-1 | Distinguish **fact / assumption / hypothesis** in all product documents; don't act on a hypothesis before it is tested | Prevents strategy built on unverified claims (§2) |
| D-2 | **No real data is published until gate G1** (legal view on the data path) passes | B-1; trust is the core of the positioning (§12 risk 1) |
| D-3 | Every displayed financial figure must link to its source document; missing values show as "not reported", never zero | Core differentiator and data-integrity rule (§6 M2) |
| D-4 | Reported and calculated values are always visually and semantically distinct; calculated formulas are shown | Phase 2 rule; trust (§8) |
| D-5 | Verify the **first 5 companies end to end and measure effort** before committing to 20–30 (gate G2) | Verification cost is unknown (§9, §12 risk 2) |
| D-6 | Two-person verification for financial figures in the pilot | Errors hurt trust disproportionately (§12 risk 8) |
| D-7 | Load Fraunces' `vietnamese` subset and set the correct `lang` (a small fix, scheduled for P2 engineering) | Fraunces is loaded `latin`-only today; Vietnamese headings would fall back to another font (§8) |
| D-8 | Pre-register validation thresholds before testing, and make no product-market-fit claims | Avoids reading results to fit the plan (§10) |
| D-9 | Analytics, if added, are opt-in and privacy-respecting, with no third-party ad trackers | Fits the trust positioning; nothing exists today |

## 2. Decisions requiring project owner approval

| ID | Decision proposed | Why it needs the owner | Recommendation / status |
| --- | --- | --- | --- |
| A-1 | **Primary segment: C, Vietnamese investors learning to research listed companies**; E (foreign, English) second | Sets product direction | ✅ **APPROVED** by Tiến Thành, 2026-11-23 (§4) |
| A-2 | **Positioning:** understandable, checkable company profiles with per-figure provenance (§5) | Brand and direction | ✅ **APPROVED** by Tiến Thành, 2026-11-23. The positioning's underlying problem (H1) and the value of provenance (H2) are still hypotheses to validate (§10) |
| A-3 | **MVP = M1–M5** (§6). Price charts, news, portfolio, AI, relationships and 3D are out of the MVP | Scope | ✅ **APPROVED** by Tiến Thành, 2026-11-23. The SHOULD features (ratios, comparison, watchlist, glossary) are not part of this approval |
| A-4 | **Vietnamese-first UI**, with English second. This changes the current English-first UI | Reverses the current direction | ✅ **APPROVED** by Tiến Thành, 2026-11-23. Rationale: the approved primary segment (A-1) reads Vietnamese; the current UI is English-only (`lang="en"`) |
| A-5 | **3D world:** no 3D in Phase 2; Discovery World kept as the long-term vision; implementation only after gate G3 (verified relationship data, 2D relationship visualisation shipped, 3D measurably better than 2D on a named task, accessible 2D alternative kept) | Changes the long-term vision's emphasis | ✅ **APPROVED** by Tiến Thành, 2026-11-23 (as revised; details in §2a) |
| A-6 | **Data path (approved sequence):** (1) **now:** private pilot: curate the first 5 companies from their own published audited annual reports, for internal usability testing only, nothing published, and measure hours per company (**gate G2**); (2) **in parallel:** get a Vietnamese legal opinion on storing and publicly displaying figures from mandatory disclosures (**gate G1**; questions in Q-1); (3) **if G1 is favourable:** publish figures with links to the source filings, business descriptions in ATLAS's own words, no copied report text or PDFs; (4) **later, for scale:** licensed provider, only with public-display rights and per-figure document references in the contract. Never source from aggregators (CafeF, Vietstock, Simplize…) | Legal and financial exposure; possible cost | ✅ **APPROVED** by Tiến Thành, 2026-11-23. Basis (not legal advice): Circular 96/2020/TT-BTC Art. 10 requires public companies to disclose audited annual financial statements; legal commentary on IP Law Art. 15 says pure figures are outside copyright protection (law version to be confirmed by the legal opinion) |
| A-7 | **Pilot sectors and size:** 3–4 sectors (proposed: Banking & Financial Services, Consumer & Retail, Technology, Materials & Construction), 20–30 large companies, selection criteria in P2-3.1 | Product focus | ✅ **APPROVED** by Tiến Thành, 2026-11-23: the four sectors and a size of 20–30 companies. The selection criteria and the company list are still to be written (P2-3.1); the first 5 form the private pilot (G2, A-6) |
| A-8 | **Monetization:** core profiles, key financials and source transparency stay free (the core only, not every future advanced feature); no paid tier, ads or payments in Phase 2; interest researched via interviews and one clearly non-functional signal; paid launch needs legal clearance, commercial data rights, willingness-to-pay evidence and a Vietnamese legal/tax review | Business model | ✅ **APPROVED** by Tiến Thành, 2026-11-23 (as revised; details in §2a) |
| A-9 | **Validation:** qualitative pilot decision thresholds (not market estimates): task completion (≥8 of 10), comprehension of figures and sources, verified-vs-sample distinction, perceived usefulness; SUS 68 as a reference only; Continue / Iterate / Pivot rules; 14-day return gated by G1 | They decide continue / pivot | ✅ **APPROVED** by Tiến Thành, 2026-11-23 (as revised; details in §2a) · **Amended 2026-11-23 by AM-1 (§2b):** round-1 PB at n = 10 |
| A-10 | **Phase 2 acceptance:** Track A product completion (≥5 verified companies per A-11 definition, stretch 20–30; figure-to-page traceability; reproducible data-quality checks; both research rounds documented whatever the outcome; J1–J3; release gates). Track B public-launch readiness reported separately. A private pilot can complete Phase 2 | Defines "done" for Phase 2 | ✅ **APPROVED** by Tiến Thành, 2026-11-23 (as revised; details in §2a) |
| A-11 | **Pilot company selection criteria** in [PILOT_SELECTION_CRITERIA.md](PILOT_SELECTION_CRITERIA.md): eligibility E1–E8 (HOSE/HNX listed, no exchange warning, sector fit, ≥3 years of audited consolidated VND statements with an unqualified opinion on the company's own site, annual report available), VN30/VN100 ordering, composition rules (first 5: one per sector plus one, exactly 1 bank, calendar fiscal years) | Determines which real companies ATLAS shows first | ✅ **APPROVED** by Tiến Thành, 2026-11-23. Next: build the long-list (step 2 of its process); the owner confirms the first-5 list |

## 2a. Decision proposals for owner review: A-5, A-8, A-9, A-10

Prepared 2026-11-23. **All four approved by Tiến Thành on 2026-11-23, as revised.** Labels: **[F]** research finding or repository
fact, with a source (refs at the end of this file); **[A]** assumption; **[R]** recommendation. Each
proposal is evaluated against ATLAS's current constraints:

| Constraint | Current state [F] |
| --- | --- |
| Technical | Next.js 16 + FastAPI + PostgreSQL; catalogue API and UI exist; no auth, payments, analytics or 3D; no relationship model in the schema |
| Data access | 0 real companies. Private 5-company pilot allowed (A-6, gate G2); **public display waits on the legal opinion (G1)** |
| Target customer | Segment C, Vietnamese investors learning to research listed companies (A-1); willingness to pay assumed low [A] |
| Resources | Effectively one person [A] across product, data verification, engineering and research (PRODUCT_STRATEGY §12 risk 9); no stated budget (Q-7) |

### A-5: 3D world prioritisation and timing

*Revised 2026-11-23 per project owner direction. Status: ✅ **APPROVED** by Tiến Thành, 2026-11-23.*

**Proposed decision [R]**
1. **No 3D implementation in Phase 2.**
2. **The Discovery World stays ATLAS's long-term product vision.** Deferring 3D does not drop the concept.
3. **Gate G3 must pass before any 3D implementation starts.** All four conditions are required:
   1. **Verified company relationship data exists** (e.g. ownership or group links), with evidence, under the same verification standard as financial data.
   2. **A 2D relationship visualisation has shipped**, as the baseline.
   3. **A 3D prototype shows a measurable improvement over the 2D baseline for a specific, named user task** (e.g. "find all companies in the same group"). The improvement is measured as fewer errors or less time, with an equal or better ease rating. Because samples will be small, the result is a qualitative product decision, not a statistical claim (see A-9).
   4. **An accessible 2D alternative stays available** for every capability the 3D view offers.

**Research findings**
- [F] The repository has no 3D world, no relationship data and no relationship schema.
- [F] None of the reviewed competitors' feature lists mention 3D. CafeF offers a 2D "sector map" (PRODUCT_STRATEGY R8, §3.2).
- [F] Perception research is task-dependent. In a 2026 dissertation, 3D heat maps gave more accurate ratio estimates than 2D, while bar-chart accuracy did not differ by chart type [Ref V4]. 3D helped when the third dimension carried data.

**Assumptions**
- 3D adds mobile performance and accessibility cost [A].
- The approved segment's first questions ("what does it do, are the numbers right") don't need spatial navigation [A, tested indirectly by A-9].

**Evaluation**

| Dimension | Assessment |
| --- | --- |
| Tech | Feasible later (e.g. WebGL), but a new rendering stack with its own testing and performance work |
| Data | No relationship data exists; public display of it would also wait on G1 |
| Customers | Doesn't address segment C's core problem |
| Resources | Would compete with data verification, the bottleneck |

**Risks:** the vision's visible signature is absent for a while. Mitigation: keep the *world* metaphor
in 2D navigation and copy (sectors as regions), and plan a relationship-data spike after Phase 2.

**Alternatives**
- *3D now as a hook:* rejected. No data to show, and it takes effort from the bottleneck.
- *Abandon 3D:* rejected. It's the owner's long-term vision, and evidence shows 3D can help when it encodes data.
- *2D relationship map first:* adopted as G3 condition 2.

**If approved:** record G3 in the Phase 2 checklist as a post-Phase-2 gate; no Phase 2 status changes.

### A-8: Initial monetization strategy

*Revised 2026-11-23 per project owner direction. Status: ✅ **APPROVED** by Tiến Thành, 2026-11-23.*

**Proposed decision [R]**
1. **The core stays free:** company profiles, key financials and source transparency. "Free" applies to this **core only**. It does **not** commit every future advanced feature to being free.
2. **Phase 2 has no paid tier, no advertising and no payment implementation.** No payment details are collected.
3. **Premium interest may be researched** through interviews and a **clearly non-functional interest signal**: one visibly labelled "coming later, not available" element. It only records interest, never implies a purchase, and collects nothing beyond the click.
4. **Any paid launch requires all four of these:**
   1. legal clearance (G1, including commercial use)
   2. valid commercial rights to the data used by the paid feature
   3. evidence of willingness to pay (A-9 interest signals plus interview evidence)
   4. a Vietnamese legal and tax review for selling subscriptions

**Research findings**
- [F] Individual subscription list prices: FireAnt 120k–480k VNĐ/month (12-month terms; list 149k–599k); Simplize Professional 599k VNĐ/month; TradingView US$12.95–199.95/month (billed annually); institutional FiinPro-X 10.9M VNĐ per user per month (PRODUCT_STRATEGY R1, R3, R9, R12).
- [F] CafeF is free and ad-supported (R8).
- [F] Data-feed prices aren't published ("contact us"; R10), and SSI terms aren't published (`data/SOURCES.md`).
- [F] The repository has no auth or payment system.

**Assumptions**
- Segment C's willingness to pay is low [A].
- Paid demand emerges as users mature toward segment B: more companies, longer history, comparisons, alerts on new filings [A].
- Competitor prices are interview anchors only, not evidence of what anyone would pay ATLAS.

**Evaluation**

| Dimension | Assessment |
| --- | --- |
| Tech | Payments and accounts would be new subsystems, and premature |
| Data | Premium depth needs more verified or licensed data than the pilot has. Some features, such as export, may count as redistribution |
| Customers | C is the funnel, B the likely payer [A] |
| Resources | No build cost in Phase 2 |

**Known costs:** legal opinion (G1, fee unknown); verification hours (measured at G2); hosting (small at
pilot scale [A]); future data licences (unknown).

**Risks**
- No revenue for 6+ months [A] (Q-2).
- The interest signal could confuse testers. Mitigation: one element, labelled non-functional before it's clicked.
- Price anchoring in interviews could bias answers. Mitigation: open questions first.

**Alternatives**
- *Paywall now:* rejected. No depth to sell and no commercial rights.
- *Advertising:* rejected. Conflicts with trust and needs scale.
- *B2B dataset licensing:* deferred until redistribution rights are clear (after G1).
- *Sponsorship or donations:* deferred until there are users.

### A-9: Product validation metrics and thresholds (revises PRODUCT_STRATEGY §10)

*Revised 2026-11-23 per project owner direction. Status: ✅ **APPROVED** by Tiến Thành, 2026-11-23.*

**Scope statement.** These are **qualitative pilot decision thresholds**: rules for deciding what the
team does next. They are **not statistically representative market estimates**, and they don't
measure market size, adoption or product-market fit. A sample of 8–10 people can reveal problems
and give directional signals. It cannot prove a hypothesis about the wider market.

**Observed findings (research) [F]**
- NN/g: a first study with five participants found about 85% of usability problems, and several small tests beat one large one [V1].
- NN/g: the 5-user guideline "only applies to qualitative" studies; quantitative studies usually need **more than 30** participants [V2].
- MeasuringU: average task completion is **78%** across about 1,100 tasks, and the average SUS score is **68** across 500 datasets [V3].
- No ATLAS user data exists yet. Every threshold below is a pre-registered expectation, not an observation.

**Assumptions [A]**
- Recruits meeting the PRODUCT_STRATEGY §10 criteria represent segment C well enough for directional signals.
- Moderated-session behaviour approximates real use, so unprompted actions count more than ratings.
- Return visits reflect value only when access is effortless.

**Recommendations [R]: measures and thresholds**

> **Amended by AM-1 (§2b, 2026-11-23):** round 1 has n = 10; PB meets at ≥6 of 10 and is clearly below at ≤3 of 10.

Round 1: n = 8 problem interviews. Round 2: n = 10 moderated usability sessions, at least 5 of them new
people, run in a private test environment.

| ID | Measure | How observed | Meets threshold | Clearly below |
| --- | --- | --- | --- | --- |
| PB | **Problem exists** (round 1) | Coded interview notes | ≥5 of 8 describe confusion or distrust about company data unprompted | ≤2 of 8 |
| TC | **Task completion**, scored per task: S1 understand a company, S2 explore a sector, S3 check a figure's source | Completed without help, observer sheet | ≥8 of 10 for each task (reference: 78% average [V3]) | ≤5 of 10 on any task |
| CF | **Comprehension of financial figures** | Participant explains what a shown figure means, including its period and unit (e.g. net profit to parent, FY, tỷ đồng) | ≥8 of 10 correct | ≤5 of 10 |
| CS | **Comprehension of sources** | Participant states where a figure comes from (document, page) and how fresh it is (verified date) | ≥8 of 10 correct | ≤5 of 10 |
| DS | **Can tell verified data from sample data** | Shown one verified record and one labelled sample record in the test environment, participant says which is real and why | 10 of 10 correct. **Any participant who believes sample data is real triggers a mandatory label fix before any public release** | — |
| UF | **Perceived usefulness** | Rating 1–5, "How useful would this be for researching a company?", with the reason recorded | Median ≥4 | Median ≤2 |
| SUS | **SUS** | Standard questionnaire after the session | **Reference only:** compared with the average of 68 [V3]. A score well below 68 prompts investigation; it's not an automatic pass or fail | — |
| SV | **Sources are valued** (supports positioning, A-2) | Unprompted source opens during tasks, plus a top-2 rank of 5 features | ≥5 of 10 do either | ≤2 of 10 |
| RT | **Return interest** | Voluntary use within 14 days, opt-in | **Gated:** run only after G1 legal clearance and with appropriate data access; until then, record stated intent, clearly labelled | — |
| WTP | **Premium interest** (informs A-8, not a continue/pivot rule) | Names a specific paid feature, plus the non-functional interest signal | Recorded and reported; no threshold drives Phase 2 decisions | — |

**Continue / Iterate / Pivot.** These rules say what the signals justify *doing next*. They don't
say what has been proven.

| Signal pattern | Next action | What it does **not** show |
| --- | --- | --- |
| PB met; TC, CF, CS met; DS 10 of 10; UF median ≥4 | **Continue:** proceed to scale the pilot, subject to G2 and A-10 | That the market wants ATLAS, or that people will pay |
| Any of TC, CF, CS or UF between the two thresholds, DS below 10 of 10, or SUS well below the reference | **Iterate:** fix the issues found, then run another small round (≈5 users [V1]) on the changed areas | That the direction is wrong |
| PB clearly below | **Pivot candidate:** re-examine the segment (A-1) before building further; consider segment E. Owner decision | That segment C has no need. It shows we didn't find it in 8 interviews |
| SV clearly below while PB is met | **Pivot candidate, emphasis only:** lead with understanding, keep sources as hygiene. Owner decision | That sources don't matter for trust |
| UF clearly below in two consecutive rounds | **Pivot candidate:** revisit the MVP scope (A-3). Owner decision | — |

**Measurement and ethics:** an observer sheet and session notes, with consent. No names in the repo;
recordings stay outside it. The verified-vs-sample task (DS) runs only in the **test environment**,
never in the pilot dataset (see A-10, AC-3).

**Risks:** small samples give false confidence (mitigation: counts, repeat rounds, and the
"what it does not show" column); recruitment bias; moderator bias (mitigation: a written script, and
a second observer if possible).

**Alternatives**
- *Survey only:* rejected. Stated and revealed behaviour differ.
- *Quantitative study with more than 30 participants:* deferred. Valid, but costly at this stage [V2].
- *A product-market-fit survey:* rejected. The pilot can't support such a claim.

### A-10: Phase 2 acceptance criteria

*Revised 2026-11-23 per project owner direction. Status: ✅ **APPROVED** by Tiến Thành, 2026-11-23.*

**Proposed decision [R]:** Phase 2 is judged on **two separate tracks**. **Track A, product completion**, decides whether
Phase 2 is done. **Track B, public-launch readiness**, is reported separately and may stay BLOCKED
without preventing Phase 2 from completing as a private pilot.

**Definition: verified company.** A company counts as **verified** only when all of these hold:
1. It was selected under the approved criteria ([PILOT_SELECTION_CRITERIA.md](PILOT_SELECTION_CRITERIA.md), A-11). It passes E1–E8, with recorded evidence (URL, retrieval date, page), and for the first 5 it follows the composition rules.
2. Every field in criteria §4 is curated: identity, listings, sector, a business overview in ATLAS's own words, and key financials for ≥3 fiscal years, with "not applicable" recorded explicitly.
3. **Every financial figure has passed a two-person check** (D-6): two independent entries agree, and both match the source page.
4. Its selection record (criteria §5) is complete, including both reviewers and the conflict-of-interest note.
5. Its evidence rows carry `verification_status = verified` only after steps 1–4. Anything less stays `unverified`.

**Track A: product completion (all required)**

| ID | Criterion | Reproducible evidence |
| --- | --- | --- |
| AC-1 | MVP **M1–M5** implemented and meeting their acceptance criteria (PRODUCT_STRATEGY §6), on pilot data | Tests plus browser verification in the checklist |
| AC-2 | **At least 5 verified companies** (definition above). **20–30 is a stretch target**, reported but not required | Verification log; selection records (kept private) |
| AC-3 | **Traceability:** every displayed financial figure traces to an **official source and page**: the company's own published audited report or official disclosure, with URL, retrieval date, SHA-256 of the file, and page number. The pilot dataset contains no sample records | Automated check (AC-4). **Note:** the evidence model has no page field today [F, `backend/app/models.py`], so adding one is an implementation task (P2-4.13) |
| AC-4 | **Reproducible data-quality checks**, run by documented commands with recorded output. They must confirm: (a) every displayed figure has evidence with a URL and page; (b) the two independent entries reconcile with **zero differences**; (c) re-importing the pilot bundle changes nothing; (d) no sample records exist in the pilot dataset; (e) periods, currency and units validate; (f) no "not applicable" value is shown as zero | Command output in the checklist |
| AC-5 | **Both research rounds completed and documented, regardless of outcome:** round 1 (n ≥ 8) and round 2 (n ≥ 8) run under A-9; an anonymised summary and the Continue / Iterate / Pivot decision recorded (P2-7.7) | Summary doc; decision record |
| AC-6 | **Journeys J1–J3** reach the A-9 task-completion thresholds (TC) in the latest round. If they don't, Phase 2 is not complete until a follow-up small round meets them, **or** the owner records a decision to close Phase 2 with the gap documented | Round results |
| AC-7 | **Engineering release gates** P2-8.1–8.9 pass on the release candidate; no open CRITICAL or HIGH defects | Command output; CI links |
| AC-8 | **Docs and checklist current:** every item PASS, or BLOCKED or descoped by a recorded owner decision | Checklist |

**Track B: public-launch readiness (separate; may be BLOCKED)**

| ID | Criterion |
| --- | --- |
| LR-1 | **G1 passed:** a favourable written Vietnamese legal opinion, with its conditions recorded |
| LR-2 | Each data source's `commercial_usage_status` and terms are recorded in `data_sources`, consistent with G1 |
| LR-3 | Only data the opinion permits is displayed, with the attribution and linking it requires |
| LR-4 | The public build contains no sample data (DS safeguards in place) |
| LR-5 | Hosting and budget decided (Q-7); privacy notice in place if any analytics are used (D-9) |

**Phase 2 outcomes**

| Outcome | Condition |
| --- | --- |
| **Complete, public** | Track A complete and Track B complete |
| **Complete, private pilot** | Track A complete; Track B BLOCKED by legal or data-rights issues, reported separately, never faked |
| **Not complete** | Any Track A criterion open, with no owner decision recorded |

**Research findings [F]**
- Phase 1 set the precedent of reporting software completion separately from data blockers (PHASE_1_CHECKLIST).
- Verification effort per company has never been measured; G2 exists to measure it (A-6).
- Engineering gates pass on the current baseline (PHASE_2_CHECKLIST E-B, E-F, E-CI), but must be re-run on the release candidate.
- G1 depends on an outside party, so ATLAS doesn't control its timing.
- The evidence model has no page-number field today.

**Assumptions [A]:** Track A with a minimum of 5 companies is achievable in about 90 days for one
person; that holds only because the minimum is 5. Two-person verification is available (reviewer to
be named, Q-3).

**Risks**
- AC-6 can hold Phase 2 open. Mitigation: follow-up small rounds, or a recorded owner decision.
- The 5 vs 20–30 change lowers the visible ambition of Phase 2.
- Page-level traceability adds a schema change.

**Alternatives**
- *20–30 companies plus a public launch required:* rejected. It depends on G1 and unknown effort.
- *Software-only criteria:* rejected. They ignore validation.
- *Require positive research results:* rejected. That incentivises bending the evidence; AC-5 requires running and recording.

**If approved:** P2-1.5 becomes PASS; the Phase 2 objective line changes to "≥5 verified companies
(stretch 20–30)"; Track B is added to the checklist as a separately reported section.

## 2b. Amendments to approved decisions

Amendments are recorded here. The original approved text in §2 and §2a stays as approved, with a
pointer to the amendment.

### AM-1: amends A-9. Round-1 problem threshold at n = 10

**Approved by the project owner Tiến Thành on 2026-11-23** (resolves Q-9, which arose from Q-4's C-1).

| Measure | A-9 as approved (n = 8) | **Amended for round 1 at n = 10** |
| --- | --- | --- |
| PB: problem exists (round 1) | Meets: ≥5 of 8. Clearly below: ≤2 of 8 | **Meets: ≥6 of 10. Clearly below: ≤3 of 10** |

- **Between the thresholds** (4 or 5 of 10), A-9's Continue / Iterate / Pivot rule applies unchanged:
  it's an **Iterate** signal, not a pass or a failure.
- **Reason:** the confirmed recruiting plan (Q-4) sets round 1 at 10 participants. The A-9 counts
  were stated for 8.
- **Scope:** PB in round 1 only. The other A-9 measures were already stated for n = 10 (round 2), and
  their wording, A-9's qualitative-pilot scope statement and the "what it does not show" limits are
  unchanged.
- **If round 1 ends with a different number of participants** (e.g. allocation adjustments under Q-4),
  this amendment does not cover it. The owner records how to score **before** scoring.
- A-10 AC-5 ("round 1 n ≥ 8") is satisfied by 10. No change.

## 2c. Execution approvals

New records only. No earlier decision is changed. These are recorded so Phase 2 work can be
traced to the owner's approval.

| ID | Date | Approval | Boundaries |
| --- | --- | --- | --- |
| EX-1 | 2026-11-23 | **Phase 2 execution: CONDITIONAL GO** by the project owner, after the Phase 1 exit audit (CONDITIONAL PASS) | Only tasks not blocked by G1, data rights, Q-3 or a pending owner approval. Phase 1 exit result unchanged. No public launch, charging, subscriptions or redistribution of restricted data. No commit/push/merge/release/deploy without separate authorization. Metric dictionary (F-1, F-2), Q-7 and Q-8 need explicit approval |
| EX-2 | 2026-11-23 | **Workstream 1 approved**, including its Alembic migration: curation-ready verification and validation | Append-only reviews; curator ≠ reviewer in the database; no verification without an independent review; transitions defined and tested; local-only review tool with no public API; overlap rules per granularity; exact unit conversion with provenance; `source_page` required for real figures only; one migration, tested up/down/up; no changes to F-1/F-2, real data, private evidence, A-11 or hosting. Implemented as migration `31b1317163eb` ([VERIFICATION_WORKFLOW.md](VERIFICATION_WORKFLOW.md)) |
| EX-3 | 2026-11-23 | **Workstream 2 approved**: Vietnamese-first interface (P2-4.12) after WS1 closure | Vietnamese default at existing URLs, English under `/en`; maintainable dictionaries; read-only `metric_name_vi` from the existing metric dictionary (no dictionary or schema change); tests for language rendering and existing behaviour. No changes to F-1/F-2, real data, private evidence, A-11, hosting; no commit/push/merge/deploy without authorization |

## 2d. Financial intelligence decisions (WS4)

New records only; no earlier decision is changed. Decided by the project owner on 2026-11-24 after
reviewing [WS4_FINANCIAL_INTELLIGENCE_PLAN.md](WS4_FINANCIAL_INTELLIGENCE_PLAN.md) §12, each
choosing the plan's recommended option except where stated. **These approve specifications, not
implementation:** no code, dictionary, schema or API change is made by recording them, and
implementation still needs the owner's go-ahead (EX-1 rules).

| ID | Decision | Approved option | Notes |
| --- | --- | --- | --- |
| WS4-D1 | ROE default | Consolidated: `net_profit_parent` ÷ average equity attributable to the parent (`equity_parent`). Separate: `net_profit` ÷ average `total_equity`. Annual statements only | The mixed form `net_profit_parent` ÷ `total_equity` is rejected. Formula id `roe_parent_avg_equity` / `roe_separate_avg_equity`, version 1 |
| WS4-D2 | ROA default | `net_profit` ÷ average `total_assets`, same scope, annual only, banks and non-banks | No pre-tax variant for now |
| WS4-D3 | Averaging | (opening + closing) ÷ 2 from the FY *t*−1 and FY *t* year-end balance sheets | Missing opening balance → not computable; no fallback to closing |
| WS4-D4 | Bank metric scope (**resolves Q-5**) | Minimal: `net_interest_income`, ROE, ROA for banks | NPL, provisions, credit growth, CAR and the optional bank lines stay future scope, to be revisited after the first bank is curated |
| WS4-D5 | Gross profit and net revenue for banks | **Not applicable** | Needs dictionary applicability (G-2, approved under D10) |
| WS4-D6 | Missing-data states | The seven-state vocabulary, implemented as **Phase A** only (no schema change) | Phase B (explicit "not reported" / "unavailable" records, a migration) not approved; to be decided separately |
| WS4-D7 | Verification of calculated values | No status of their own; never VERIFIED; `input_verification` label; not computed if any input is disputed or rejected | — |
| WS4-D8 | Display and rounding | Tỷ đồng (VND bn) with 2 decimals, triệu đồng below 1 tỷ; ratios as % with 2 decimals; half-up rounding on decimal strings; minus sign `−`; exact and as-reported values kept available | — |
| WS4-D9 | Period comparison | Strict rules of plan §8 (incompatible pairs refused, cross-company period differences warned); growth = (current − prior) ÷ \|prior\|; prior 0 or sign change → no percentage | — |
| WS4-D10 | Metric dictionary changes (exit audit F-1, F-2) | **Approved:** G-1 (vi/en definitions), G-2 (bank / non-bank applicability), G-4 (new reported metric `equity_parent`, Vốn chủ sở hữu của cổ đông công ty mẹ). **Not approved:** G-3 (sign convention field) and G-5 to G-9 | G-4 was added on the owner's confirmation after the conflict with D1 was pointed out; G-2 was added together with D4/D5. F-1 and F-2 stay OPEN until the dictionary version is actually changed and the definition text has been checked by the owner or a delegate |
| WS4-D11 | Calculated values from unverified inputs | Shown with the "Tính từ số liệu chưa kiểm chứng" label in the **private pilot only**; never public before G1 | — |
| WS4-D12 | `equity_parent` source rule (owner review of WS4-1, 2026-11-24) | Recorded **only** when the statement explicitly reports the line. Never derived as total equity minus non-controlling interests; `total_equity` is never substituted. If it is missing, consolidated ROE is not calculable (missing input); source page and reported value are kept as for every figure | The owner accepts that many Vietnamese consolidated statements may not present the line, so consolidated ROE may often be not calculable |

**Bank applicability as implemented in dictionary 1.1.0** (owner review of WS4-1, 2026-11-24).
This is not a separate decision; every value follows from the decisions above:

| Bank value | Metrics | Follows from |
| --- | --- | --- |
| `not_applicable` | `net_revenue`, `gross_profit` | WS4-D5 |
| `applicable` | `net_interest_income` | WS4-D4 |
| `applicable` | `net_profit`, `total_assets` | Inputs of bank ROA (WS4-D2: banks and non-banks; WS4-D4) |
| `applicable` | `net_profit_parent`, `equity_parent` | Inputs of consolidated bank ROE (WS4-D1, WS4-D4) |
| `applicable` | `net_profit`, `total_equity` | Inputs of separate-statement bank ROE (WS4-D1, WS4-D4) |
| `unclassified` | All other metrics | No approved decision. Never inferred from accounting practice or from the planning document alone; never read as "not applicable" |

The owner also approved, in the same review, the English name **"Total equity"** for `total_equity`
(was "Total owners' equity"), to avoid confusion with equity attributable to owners of the parent.

**Implementation status (2026-11-25):** WS4-D10 and WS4-D12 are implemented in metric dictionary
1.1.0, merged as PR #6 (`105869f`, Backend, Frontend and Docker CI success). The owner approved all
17 definitions. No other §2d decision is implemented yet (WS4-2 onward). Records above unchanged.

**WS4-2 design approval (2026-11-25).** The project owner approved all six design points of
[WS4_2_IMPLEMENTATION_PLAN.md](WS4_2_IMPLEMENTATION_PLAN.md) §12 as written: (1) a separate
`GET /companies/{id}/calculated-metrics` endpoint; (2) the eight reason codes, their precedence and
vi/en texts, with every issue listed; (3) `value` 10 decimals half-even and `percent` 2 decimals
half-up, both from the exact quotient, as fixed-point strings; (4) opening balance = FY *t*−1 annual
balance sheet, same scope, latest revision, within ±7 days, `ambiguous_opening_balance` when several,
closing on the exact date; (5) `verified` / `unverified` / `sample` used, `disputed` / `rejected` /
`superseded` refused, no fallback to older revisions; (6) the ROE and ROA names. This implements the
approved formulas (WS4-D1 to D3, D7, D8, D11, D12) and changes none of them. It is **not** a
go-ahead to implement; that is a separate approval.

**WS4-2 go-ahead (2026-11-25).** The project owner authorised WS4-2 implementation ("Start WS4-2").
One addition made during implementation: each listed `issue` also carries the metric's Vietnamese
and English names (`metric_name_vi`, `metric_name_en`) so the "missing input (…)" text can name it.
Codes, precedence and texts are unchanged.

## 3. Rejected alternatives

| Alternative | Why rejected |
| --- | --- |
| **Segment A (general retail) first** | Needs realtime market data and competes with FireAnt's free tier on its strengths (§4) |
| **Segment B (fundamental investors) first** | Needs data breadth and history (competitors offer 15–20 years) that ATLAS can't license or verify yet (§3.2, §4) |
| **Segments D/F (professionals, institutions) first** | Require complete coverage, SLAs and sales (FiinPro-X is 10.9M VNĐ per user per month for coverage ATLAS doesn't have) |
| **Breadth-first: hundreds of unverified companies** | Abandons the trust differentiator; imported unverified data would look like every other site |
| **3D world as the core value** | No relationship data to show; no evidence it helps a user task; high cost (§6) |
| **AI research assistant in the MVP** | Hallucination conflicts with the trust positioning; FireAnt, FiinGroup and WiData already ship AI (§3.2) |
| **Price charts and news in the MVP** | Licensing cost; incumbents are strong; not the learner's core question |
| **Advertising revenue** | Conflicts with trust; needs scale (§9) |
| **Setting a subscription price now** | No evidence of ATLAS-specific willingness to pay; competitor prices are anchors, not proof (§9) |

## 4. Open questions

| ID | Question | Who / how to answer |
| --- | --- | --- |
| Q-1 | Is it lawful to store and display figures taken from companies' published audited reports on a public website, and on what terms? Specifically: (a) public and commercial display of figures from mandatory disclosures; (b) database or compilation and unfair-competition constraints; (c) exchange and SSC portal terms of use versus the same files on company sites; (d) attribution, linking and caching of source PDFs; (e) personal project versus commercial product | Owner, with a Vietnamese legal opinion (**gate G1**, approved under A-6) |
| Q-2 | Is ATLAS intended as a commercial product or a personal / portfolio project in the next 6 months? This changes the licensing needs and the legal questions under G1 | ✅ **RESOLVED 2026-11-23: COMMERCIAL INTENT.** Decided by the project owner Tiến Thành; details in §4a |
| Q-3 | What are the realistic verification hours per company, including the business overview? Who is the second reviewer for financial figures (D-6)? | Measured at gate G2; reviewer named by owner |
| Q-4 | Can the owner recruit 10–15 interviewees matching the §10 criteria, and through which channels? | ✅ **RESOLVED 2026-11-23: recruiting plan confirmed by the project owner Tiến Thành** (§4b). C-1 split out as Q-9 |
| Q-5 | Should banks get their own metric set (net interest income, NPL ratio) in the MVP, given Banking is a proposed pilot sector? | ✅ **RESOLVED 2026-11-24: minimal bank scope** (net interest income, ROE, ROA; gross profit and net revenue not applicable; NPL and other bank metrics later). Decided by the project owner; recorded as WS4-D4 and WS4-D5 (§2d) |
| Q-6 | Should English (segment E) launch together with Vietnamese, or later? | Owner, after round 1 |
| Q-7 | Which hosting setup for a public pilot, and what is the budget? | Owner |
| Q-8 | Move the repository out of the iCloud-synced `~/Documents` folder? (Phase 2 risk R-1) | Owner |
| Q-9 | **Round-1 threshold at n = 10 (from Q-4, C-1):** how does A-9's problem threshold PB ("≥5 of 8 meets; ≤2 of 8 clearly below") apply when round 1 has 10 participants? Option (a): scale to ≥6 of 10 meets, ≤3 of 10 clearly below. Option (b): keep A-9's counts unchanged. Either requires a recorded amendment to A-9 | ✅ **RESOLVED 2026-11-23: option (a), scale to n = 10.** Decided by the project owner Tiến Thành; recorded as amendment AM-1 to A-9 (§2b) |

## 4a. Resolved questions

### Q-2: commercial or personal? Resolved 2026-11-23: COMMERCIAL INTENT

**Decision.** The project owner, Tiến Thành, approved a **commercial product direction** for ATLAS
from Phase 2 onward. ATLAS is developed as a **potential commercial investment-discovery product**.

**Rationale (as recorded).** This is the owner's product direction. It resolves the open question
that determined the legal scope of gate G1 and the licensing needs under A-6 and A-8, so the legal
review can be scoped once, for commercial use, instead of being repeated later.

**What it does *not* authorise:**
- immediate **public launch** (still gated by G1 and Track B, A-10)
- **paid subscriptions** (still governed by A-8's four conditions)
- **company formation**
- **commercial redistribution of third-party data**

Phase 2 stays focused on MVP development and the **private pilot** (A-6, A-10 Track A).

**Implications**
1. **The G1 legal review must explicitly assess, for each relevant data source, rights to
   commercial use, storage, processing, display and redistribution.** This adds scope to the review
   described in Q-1. Q-1 itself stays open and unchanged.
2. **Any data source without sufficiently clear rights stays restricted until reviewed.** This
   matches D-2 (nothing published before G1) and the importer default `commercial_usage_status =
   unknown` (`data/SOURCES.md`).
3. **A-8's paid-launch conditions are unchanged.** Commercial intent satisfies none of them on its
   own: legal clearance, commercial data rights, willingness-to-pay evidence and a Vietnamese
   legal/tax review are all still required.
4. **The later licensed-provider step (A-6 step 4)** must negotiate terms that cover commercial use
   and public display.

**Risks**
- **Legal scope and cost grow.** A commercial-use opinion is broader than a personal-use one [A].
- **Stricter outcome.** Sources acceptable for personal use may be restricted for commercial use,
  which could delay G1 or leave it unfavourable and keep Track B BLOCKED longer [A].
- **Expectation pressure.** "Commercial" can be misread as permission to launch or charge.
  Mitigation: the explicit non-authorisations above.

**Unchanged:** open questions Q-1 and Q-3 to Q-8, and decisions A-1 to A-11.

## 4b. Confirmed answers

### Q-4: user research recruiting plan. Status: RESOLVED 2026-11-23, confirmed by the project owner

Recorded 2026-11-23 from the project owner's recruiting constraints and **confirmed as proposed by
the project owner Tiến Thành on 2026-11-23**. The confirmation covers the target, channels,
allocation, eligibility (including item 4), the profile-mix minimum, avoid rules, safeguards and the
handling of C-2 and C-3. C-1 offered two options, so it was resolved separately as Q-9 (option (a),
AM-1).
No one has been recruited, contacted or interviewed yet.

**Target:** 10 participants for the first research round (round 1, problem interviews; A-9).

**Available channels and suggested allocation.** These are targets, not mandatory quotas.

| Channel | Suggested target | Notes |
| --- | ---: | --- |
| Investor communities | 5 | Largest share; most likely to include active and experienced investors |
| RMIT student network | 3 | Likely beginners or people learning to invest |
| Friends and personal acquaintances | 2 | Bias safeguards below apply |
| **Total** | **10** | |

If a channel can't supply enough **qualified** participants, the allocation may be adjusted. Each
adjustment is documented in the tracking table with its reason.

**Eligibility (all required)**
1. Interested in Vietnam's stock market.
2. Has a **real need** to discover, understand or evaluate listed companies.
3. Can describe their current investment research process.
4. *Confirmed addition:* an adult (self-confirmed 18+) who can take part in
   Vietnamese. Interviews and the product are Vietnamese-first (A-4).

**Profile mix (aim for, not quota)**

| Category | Description |
| --- | --- |
| Beginner / learning | New to investing or learning to research companies. This is the approved primary segment C (A-1) |
| Active individual | Invests regularly on their own account |
| Experienced | Several years of investing; recruit where available |

*Confirmed:* at least 6 of 10 from Beginner / learning, so round 1 mainly
tests the approved segment C.

**Avoid (bias)**
- Recruiting only close friends.
- People who already know the ATLAS concept well, including anyone who has seen these documents or a demo.
- *From PRODUCT_STRATEGY §10, confirmed:* finance professionals (segment D).

**Safeguards**
- Explain the research purpose before participation; participation is **voluntary**, and people may stop at any time.
- Collect **no unnecessary personal or financial information**.
- **Never ask** for account credentials, portfolio holdings or sensitive financial details.
- **Do not present ATLAS as investment advice.**
- Record only: a participant code (P01–P10), channel, profile category, consent given (yes/no) and session date. **No names or contact details** in this repository; anything identifying stays outside it.
- Keep **targets** clearly separate from **actual** recruits (table below).
- **Never fabricate recruitment or interview results.**

**Tracking: targets vs actual**

| Channel | Target | Qualified and recruited (actual) | Interviews done (actual) | Adjustments (reason) |
| --- | ---: | ---: | ---: | --- |
| Investor communities | 5 | 0 | 0 | — |
| RMIT student network | 3 | 0 | 0 | — |
| Friends and acquaintances | 2 | 0 | 0 | — |
| **Total** | **10** | **0** | **0** | Recruitment not started |

**Consistency with approved decisions.** Recorded here; no approved text is changed.

| # | Point | Approved text | Handling |
| --- | --- | --- | --- |
| C-1 | **Round size** | A-9: "Round 1: n = 8", with the problem threshold PB "≥5 of 8 … ≤2 of 8". A-10 AC-5: round 1 "n ≥ 8" | 10 satisfies AC-5. **Resolved via Q-9 (2026-11-23): option (a)**, scale proportionally (≥6 of 10 meets, ≤3 of 10 clearly below). Recorded as amendment AM-1 to A-9 (§2b) |
| C-2 | **Friends** | PRODUCT_STRATEGY §10 excluded "friends of the founder (bias)"; A-9 assumes recruits meet the §10 criteria | **Confirmed:** allow up to 2 **acquaintances**, not close friends. Exclude anyone familiar with the ATLAS concept. Tag them by channel and report their responses separately, so they never decide a threshold on their own |
| C-3 | **Experience** | §10 required under 3 years of experience; A-1's segment is learners | **Confirmed:** include experienced investors only where available. Tag by category. Score A-9 thresholds on the full round **and** show segment C separately |

**Status:** Q-4 resolved on 2026-11-23. C-1 resolved via Q-9 on 2026-11-23 (AM-1). This plan supersedes the recruitment criteria in PRODUCT_STRATEGY §10 for round 1.

## References for A-6

- Circular 96/2020/TT-BTC on information disclosure:
  https://thuvienphapluat.vn/van-ban/Chung-khoan/Circular-96-2020-TT-BTC-providing-guidelines-on-disclosure-of-information-on-securities-market-460833.aspx?tab=1 ·
  original: https://vbpl.vn/FileData/TW/Lists/VBPQ/Attachments/146048/VanBanGoc_96-2020-TT-BTC.pdf
- IP Law Art. 15 (subjects not protected by copyright), commentary:
  https://thuvienphapluat.vn/hoi-dap-phap-luat/doi-tuong-khong-thuoc-pham-vi-bao-ho-quyen-tac-gia-21491.html ·
  https://luatvietnam.vn/tin-phap-luat/3-doi-tuong-khong-duoc-bao-ho-quyen-tac-gia-230-30625-article.html
- These are secondary sources, read for orientation only. The legal opinion (G1) decides.

## References for §2a (verified 2026-11-23)

| Ref | Source |
| --- | --- |
| V1 | NN/g, "Why You Only Need to Test with 5 Users": https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/ |
| V2 | NN/g, "How Many Test Users in a Usability Study?" (qualitative vs quantitative): https://www.nngroup.com/articles/5-test-users-qual-quant/ |
| V3 | MeasuringU, "10 Benchmarks for User Experience Metrics" (78% completion, SUS 68): https://measuringu.com/?p=138, and completion-rate note https://measuringu.com/?p=82 |
| V4 | Wiederich (2026), "Perception of 3D Data Visualizations", University of Nebraska–Lincoln, abstract only: https://digitalcommons.unl.edu/dissunl/486 |

Searched but **not cited**: a 2024 MDPI bar-chart study and a Tableau 3D-pie paper. Both returned
HTTP 403 and couldn't be checked.
