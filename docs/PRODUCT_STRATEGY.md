# ATLAS product strategy (P2.1)

Status: **all product decisions A-1 to A-11 approved by the project owner Tiến Thành on 2026-11-23.**
Where this strategy and an approved decision differ, the decision wins. Notable revisions: A-9
replaces §10's thresholds, A-10 sets the acceptance criteria (≥5 verified companies, stretch 20–30),
and A-5 defers 3D behind gate G3. Decisions are tracked in
[PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md), and progress in
[PHASE_2_CHECKLIST.md](PHASE_2_CHECKLIST.md). Prepared 2026-11-23.

Evidence labels used throughout:

| Label | Meaning |
| --- | --- |
| **[F]** | Verified fact, with a reference number (§13) to a page read on 2026-11-23, or a fact about this repository |
| **[A]** | Assumption: believed true but not verified |
| **[H]** | Hypothesis: must be tested in the validation plan (§10) before it guides spending |

---

## 1. Executive summary

- **Who first:** Vietnamese individual investors who are **learning to research listed companies on
  fundamentals**, and who want to understand what a company does and whether its numbers can be
  trusted, starting with well-known large companies. (Segment C, which borders segment B; see §4.)
- **The problem:** existing tools are built around prices, charts and dense data tables. The data
  sources behind the numbers are rarely shown on the page **[F, R1, R6, R8]**, and deeper data
  sits behind paywalls **[F, R1, R3]**. A learner can find numbers but can't easily understand
  them or check where they came from.
- **The product bet:** *understandable and checkable*. ATLAS should offer a small set of verified
  company profiles. Each one gets a plain-language business overview and the key reported
  financials, and **every figure links to the exact filing it came from**. This is the one thing
  ATLAS already does structurally (Phase 1 provenance model) and that competitors' public pages,
  as read, do not.
- **The MVP is narrow:** at least 5 (stretch 20–30) verified large companies in the 4 approved sectors (A-10), a Vietnamese-first UI,
  key financials with sources, and sector browsing. No prices, no news, no AI, no 3D, no accounts.
- **3D is not the core value.** It earns a place only once relationship data exists (supplier,
  ownership and group links), and only if it answers a question better than a list or table does.
  Until then it is deferred (§6).
- **Monetization is not tested in the first 90 days beyond interviews.** Competitors already price
  individual subscriptions at about 120k–599k VNĐ per month **[F, R1, R3]**, so willingness to pay
  exists in the market. Whether anyone would pay *ATLAS* for anything is unknown.
- **The biggest risk is data rights, not engineering.** No permission to store or display company
  data exists yet (Phase 2 blocker B-1). The first 2 weeks must produce an owner decision and a
  legal view on the data path. Engineering on real data depends on it.

## 2. Research methodology

1. **Repository review:** README, ARCHITECTURE, DEVELOPMENT, Phase 1 and 2 checklists,
   `data/README.md`, `data/SOURCES.md`. Current state is confirmed from code, not assumed.
2. **Competitor review:** official pages of Simplize, FireAnt, 24HMoney, Vietstock, CafeF,
   FiinGroup (FiinPro-X, API/DataFeed), WiData (formerly WiChart) and TradingView, read on
   2026-11-23. Only what the pages state is recorded. Where a page didn't load or didn't state
   something, the comparison says "not found".
3. **Market facts:** official or press sources citing official bodies (FTSE Russell / LSEG; press
   citing VSDC), each opened and read.
4. **No user research has been done yet.** Every statement about user needs is therefore an
   assumption or hypothesis until the interviews in §10 happen.

Limits: no paid accounts were used, so paid features are described as advertised. Several sites
render mostly client-side, so some pages were only partly readable (noted per row). No usage,
revenue or market-share figures for competitors were found, and none are given.

## 3. Market and competitors

### 3.1 Market facts

| Fact | Source |
| --- | --- |
| 14,384,902 securities trading accounts at 31 Oct 2026, of which 14,331,814 domestic and 53,088 foreign **[F]** | Thời báo Tài chính Việt Nam, citing VSDC **[R15]**. Accounts are not unique people; one person may hold several |
| FTSE Russell: Vietnam to be reclassified from Frontier to Secondary Emerging, effective 21 Sep 2026, subject to an interim review in March 2026 **[F]** | LSEG / FTSE Russell press release, 7 Oct 2025 **[R16]** |
| Over 3 million investors, as claimed by FireAnt **[F: the claim exists]** | FireAnt homepage **[R4]**. A self-reported figure, unverified |

No reliable figure was found for how many investors use fundamental research tools, so none is given.

### 3.2 Competitor comparison

| Product | Target (as stated) | Core offer | Financial data presentation | Sources shown on page? | Published pricing |
| --- | --- | --- | --- | --- | --- |
| **Simplize** **[R1, R2]** | Individual investors | "Simple" investing: valuation, analysis, charts of complex data | Up to 20 years of statements (paid); 2 years free | Not found on pages read | Free Basic; Professional **599k VNĐ/month** or 5,988k VNĐ/year |
| **FireAnt** **[R3, R4]** | Vietnamese investors broadly; top tier for brokers, analysts, fund managers | Whole market in one account: realtime quotes, charts, screener, community, AI Copilot | Free: last 5 years, key items; paid: all periods | No external data vendor named; 66,000+ broker reports aggregated | Free; Thiết yếu 120k, Chuyên nghiệp 320k, Cao cấp 480k VNĐ/month (12-month terms) |
| **24HMoney** **[R5]** | Not stated | News, community and personalised feed | Not found | Not found | Not found |
| **Vietstock** **[R6, R7]** | Investors, learners (paid courses), businesses | News, financial data, screener, export; DataFeed for businesses | Financial statements under "Truy xuất dữ liệu" | Generic only ("from reliable sources") | Paid tiers exist (Basic to Premium) but prices not shown on the page read; courses priced separately |
| **CafeF** **[R8]** | General public | Free financial news and data portal, ad-supported | Company data pages, announcements | Generic disclaimer: data "tổng hợp từ các nguồn đáng tin cậy", for reference | Free (ads) |
| **FiinGroup FiinPro-X** **[R9, R10]** | Institutions (brokers, funds, banks, universities); individuals | Lawful, comprehensive financial data platform, bond portal, API/DataFeed, MCP for AI | 3,600+ companies, 15+ years, 200 indicators | Names upstream sources (SSC, exchanges, SBV, GSO…) at the data-feed level | **10.9M VNĐ per user per month** (platform); API/feed: "contact us" |
| **WiData** (formerly WiChart) **[R11]** | Not stated | Company and industry data, dashboards, screener, MCP connection for AI | Business results, advanced charts | Not found | Not found |
| **TradingView** **[R12–R14]** | Global traders | Charting platform; covers HOSE, HNX, UPCOM tickers | Financials tabs exist, but **HOSE:FPT showed no fundamentals data** when fetched | n/a | Free; paid $12.95–$199.95 per month (billed annually) |

### 3.3 What this means for ATLAS

- **[F] The market is crowded on data breadth, prices, charts, screeners, community and now AI.**
  A startup can't win on breadth against FiinGroup (3,600+ companies, 15+ years) or on realtime
  and community against FireAnt.
- **[F] No product reviewed shows, on the page, which filing a specific number came from.** At most
  they carry generic "reliable sources" disclaimers or vendor-level source lists. **[H]** Some
  users care about this enough to choose a product for it. That is untested.
- **[A] Local platforms are Vietnamese-first and dense; global platforms are thin on Vietnamese
  fundamentals** (the TradingView FPT example, a single observation).
- **[H] The open position is depth of understanding plus verifiability for a small set of
  companies, rather than breadth.**

## 4. Customer segmentation

| Segment | Main problems [A] | Existing alternatives [F] | Use frequency [A] | Willingness to pay [H] | Acquisition [A] | Product requirements | Early-stage fit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A. Vietnamese retail investors (general)** | Fast market info, tips, prices, community | FireAnt, CafeF, broker apps | Daily, price-driven | Low to medium; proven for realtime and tools | Expensive: dominant incumbents | Realtime prices, charts, news: all need licensed market data | ✗ Poor |
| **B. Long-term fundamental investors** | Deep history, comparisons, valuation, trustworthy numbers | Simplize (paid), Vietstock, FiinPro | Weekly | Medium; competitors charge for exactly this | Moderate: niche communities | 10+ years, hundreds of companies, ratios, export: heavy data licensing | △ Later |
| **C. New investors learning about listed companies** | "What does this company actually do? Are these numbers real? What do they mean?" | Same tools as A and B, built for experts; free tiers are limited | Weekly at first; drops off if not engaged | Low **[H]** | **Reachable [A]**: Vietnamese learning communities; local recruiting assumed possible | Plain-language profiles, key metrics explained, sources visible, Vietnamese UI. **Works with 20–30 companies** | ✓ **Best** |
| **D. Professional analysts** | Complete, fast, exportable, API | FiinPro-X (10.9M VNĐ per user per month), terminals | Daily | High, but only for complete coverage | Hard: sales-led, need for trust and coverage | Full coverage, history, Excel/API, SLAs | ✗ Not achievable |
| **E. Foreign investors researching Vietnam** | English-language, trustworthy understanding of Vietnamese companies; more relevant after FTSE reclassification **[F, R16]** | TradingView (thin fundamentals for HOSE:FPT **[F]**), broker research, local sites in Vietnamese | Episodic | Medium to high **[H]** | Hard: global, fragmented; data redistribution abroad adds licensing risk | English profiles, sources, translated statements | △ **Strong second** |
| **F. Financial institutions / B2B** | Data feeds, integration | FiinGroup API/DataFeed, Vietstock DataFeed | Continuous | High | Very hard: long sales cycles, compliance | Licensed, complete, SLA-backed data | ✗ Out |

**Ranking:** C > E > B > A > D > F.

**Recommendation: segment C as the one primary initial segment**, with E (English) designed in from
the start so it can be switched on later at low cost.

Why C:
1. **Its needs match what a small verified dataset can deliver.** Learners start with
   well-known large companies, and 20–30 verified profiles can serve them. B and D cannot be served
   without breadth.
2. **Its main pain, understanding and trust, is where ATLAS's provenance model is a real
   advantage**, not price or speed.
3. **It's reachable for validation now.** **[A]** The founder can reach Vietnamese learning
   communities and run 10–15 interviews in Vietnamese within weeks. Confirm under PRODUCT_DECISIONS Q-4.

Why not the others first:
- **A:** needs realtime market data and competes head-on with FireAnt and its free tier.
- **B:** the natural upgrade path from C, and where payment is proven, but it needs data breadth
  ATLAS can't license or verify yet. It would be competing with Simplize on Simplize's terms.
- **D and F:** require completeness, SLAs and sales. They're out of reach for an unfunded
  early-stage product.
- **E:** attractive and timely, but harder to reach, harder to interview, and it adds
  cross-border data-rights questions. Keep it second, using the same verified data in English.

Not chosen for sounding attractive: E and B have higher willingness to pay **[H]**. C was chosen
because it can be served and validated with what ATLAS can actually build and verify in 90 days.

## 5. Core problem and value proposition

**Primary problem [H]:** a new investor looking at a listed company can't quickly understand *what
the business does and how it performs* **and** trust that the figures they see are correct. The
tools they use are built for traders and experts, hide where the data comes from, and put depth
behind paywalls.

**Why alternatives fall short [F + H]:** the reviewed products put their effort into breadth,
prices, charts, screeners and AI. Sources appear only as generic disclaimers **[F]**. Whether that
actually stops learners is **[H]** and is tested in §10.

**What ATLAS offers:**
1. A **plain-language business overview** per company, in Vietnamese, with sources.
2. **Key reported financials**, each figure linked to the exact filing and retrieval date, with a
   verification status.
3. **Clear distinction** between reported and calculated values, and between verified and
   unverified data. Sample data is never presented as real.
4. **Sector context:** which companies sit together, and why.

**Why users would return [H]:** to look up the next company they hear about, and to check new
annual or quarterly results with their sources. **Why they would recommend it [H]:** "the one place
where you can see where every number comes from". **What could make them pay [H]:** depth once
they mature into segment B (more companies, more history, comparisons, alerts). That is not part of
the MVP.

**Positioning statement:**

> For **Vietnamese investors learning to research listed companies**, ATLAS helps them
> **understand what a company does and how it is performing** by giving **plain-language company
> profiles where every financial figure links to the official document it came from**, unlike
> **price- and chart-focused platforms whose data sources are not shown**, because **ATLAS is built
> on an evidence and verification model where provenance is part of every record**.

## 6. Product scope and MVP

| Feature | Class | Rationale |
| --- | --- | --- |
| Company discovery (search, sector and exchange filters) | **MUST** | Exists (Phase 2 checklist P2-4.1–4.4 PASS); needs a Vietnamese UI |
| Company profiles (business overview, listings) | **MUST** | The core of the value proposition |
| Sector exploration | **MUST** | Exists; add plain-language sector explanations |
| Financial statements: key reported metrics with per-figure sources | **MUST** | The core differentiator |
| Source transparency and data-status labels | **MUST** | Partly exists (sources section, sample badge); must become per-figure |
| Vietnamese-first UI (English kept as a second language) | **MUST** | The segment is Vietnamese; the current UI is English (`lang="en"`) **[F]** |
| Financial ratios (margins, ROE, ROA), labelled as calculated | SHOULD | High learning value, but needs formulas and verified inputs first (P2-5.11–5.17) |
| Company comparison (2–3 companies, same sector) | SHOULD | Natural next learning step; depends on comparable verified data |
| Watchlist / "save for later" (browser-local, no account) | SHOULD | Supports return visits without building auth |
| Glossary / "what this metric means" | SHOULD | Cheap and high-value for learners; could be folded into the metric display |
| Personalised discovery | LATER | Needs accounts and usage data |
| AI-assisted company research | LATER | Hallucination conflicts directly with the trust positioning. Revisit only with answers grounded in cited sources |
| Company and sector relationships | LATER | No relationship data exists; needs its own sourcing and verification |
| 3D investment world | LATER | Only useful once relationships exist, and only if user tests show it beats a 2D map or table for a real task |
| News and announcements | LATER | Content licensing; incumbents cover it well |
| Price charts | OUT OF SCOPE (MVP) | Needs licensed market data; incumbents are strong; not the learner's core question |
| Portfolio tracking | OUT OF SCOPE | Different job; broker apps already do it |

### MUST-have details

**M1. Verified company profiles**
- *User problem:* "What does this company do?"
- *Value:* understanding in under 2 minutes **[H]**.
- *Data:* legal name, short name, tickers and exchanges, sector, a 2–4 paragraph business
  overview, website. Each with evidence (annual report or company disclosure).
- *Complexity:* low engineering (fields exist); **high data effort** (writing and verifying the
  overview).
- *Dependencies:* B-1 data rights decision; verification workflow (P2-2.1); a `rejected` state
  (P2-2.5, schema change).
- *Acceptance:* at least 5 (stretch 20–30, per A-10) pilot companies each have a profile with ≥1 `verified` evidence item per
  field group. The overview cites its source. No unverified field is presented as verified.

**M2. Key reported financials with per-figure provenance**
- *User problem:* "How is it doing, and can I trust this number?"
- *Value:* trust plus learning.
- *Data:* a minimum set from the existing dictionary (revenue, gross profit, operating profit, net
  profit to parent, total assets, total liabilities, equity, operating cash flow, EPS) for **at
  least 3 fiscal years**, annual first. Quarterly comes later. Each value carries its document,
  page or section, and retrieval date.
- *Complexity:* medium. The schema exists. Needed: per-figure source display, a "not reported"
  state, Vietnamese scale formatting (tỷ đồng), banking-specific line items.
- *Dependencies:* B-1; P2-3.6; P2-5.14 and P2-5.15.
- *Acceptance:* every displayed number has a one-click path to its source. Missing values show as
  "not reported", never zero. Values match the source exactly (spot-check of 100% of pilot figures
  by a second reviewer).

**M3. Discovery and sector exploration**
- *User problem:* "Which companies are in banking, and which one should I read about?"
- *Data:* the existing taxonomy plus Vietnamese sector explanations.
- *Complexity:* low (exists).
- *Acceptance:* journeys J1 and J2 (§7) completed by ≥80% of test users without help **[H threshold]**.

**M4. Source transparency and data-status labels**
- *User problem:* "Is this real, and how fresh is it?"
- *Data:* the existing evidence model.
- *Complexity:* low to medium.
- *Acceptance:* every profile shows its verification status and last-verified date. Sample data
  is never mixed with pilot data in production.

**M5. Vietnamese-first UI**
- *User problem:* the target users read Vietnamese.
- *Complexity:* medium (copy, i18n, fonts).
- *Dependencies:* owner approval (changes the current English-first direction).
- *Acceptance:* all UI copy is in Vietnamese with English available; `lang` is set correctly; the
  display font loads its Vietnamese subset (§8).

## 7. Core user journeys

| # | Intent | Steps | Screens | Data | Success | Likely friction |
| --- | --- | --- | --- | --- | --- | --- |
| **J1** Understand a company I've heard of | "I heard about [company]; what is it?" | Search name or ticker → open profile → read overview → scan key financials → open a source | Search/list, company profile | Profile, overview, 3-year key metrics, evidence | Explains the business in their own words; finds latest net profit and its source | Ticker vs name confusion; jargon; only 20–30 companies covered (an "not covered yet" state is needed) |
| **J2** Explore a sector | "What banks are listed? How do they differ?" | Sectors → a sector → companies → profile | Sectors, sector detail, profile | Taxonomy explanations, company list | Names 2–3 companies in the sector and one difference between them | ATLAS taxonomy ≠ official classification; this must be explained |
| **J3** Check a number | "Is this revenue figure right?" | Figure → source link → original document (page or section) | Profile, source panel | Per-figure evidence | Reaches the original document in ≤2 clicks and confirms the number | Dead links on company sites; PDF without page anchors |
| **J4** Compare two companies (SHOULD) | "Which of these two is more profitable?" | Profile → compare → pick second company | Comparison view | Same metrics and periods for both | Correctly states which has higher net profit and margin | Different fiscal years, units, or banking vs non-banking line items |

The original prompt's "save the company for later" step belongs to the SHOULD watchlist and is
tested after the MUSTs.

## 8. UX and design direction

Keep the existing identity (dark navy and charcoal, brass accent, Fraunces plus IBM Plex Sans) and
shift the emphasis from atmosphere to **reading and checking numbers**.

- **Hierarchy:** company name, then one-sentence business summary, then key metrics, then sources.
  Answer "what is it / how is it doing / is it true" above the fold.
- **Data density:** medium. Learners need fewer columns than analysts: 3–5 years, about 9 core
  metrics, with expandable detail. Don't copy terminal density.
- **Numbers:** tabular figures, right-aligned, Vietnamese scales (e.g. "12.345 tỷ đồng") with the
  exact value on hover or expand. Signs and colours for negatives, never colour alone. Exact values
  are already preserved from decimal strings **[F: `formatDecimal`]**.
- **Typography: one fix needed.** Fraunces is loaded with the `latin` subset only, although it offers
  `vietnamese` **[F: `frontend/src/app/layout.tsx`, next/font data]**. Vietnamese headings would
  fall back to another font. Load the `vietnamese` subset and set `lang="vi"`.
- **Colour and contrast:** current text colours pass WCAG AA on both backgrounds. The lowest is
  muted text on charcoal at **5.71:1**; mist on ink is 14.05:1 **[F: computed]**. Keep status
  colours (ok, warn, bad) for data status only. Consider a light theme for long reading sessions
  **[H]**.
- **Charts:** small, honest, and always backed by a table. Bar charts for annual values (zero
  baseline), no 3D charts, no dual axes. Mark calculated values (e.g. ROE) differently from
  reported ones, and show their formulas.
- **Trust UI:** a source icon on every figure, a "Verified on [date]" stamp, a sample-data banner
  (exists), and an explicit "not reported" state.
- **Mobile:** the profile and key metrics must work at 375px (the list already does **[F]**); tables
  scroll horizontally inside their own container, never the whole page.
- **Motion:** none beyond state changes.

## 9. Business model

| Model | Assessment |
| --- | --- |
| Free tier | **Required** to reach learners; competitors all have one **[F]** |
| Premium individual | Proven in the market (120k–599k VNĐ/month list prices **[F, R1, R3]**). For ATLAS, **[H]** only once segment-B depth exists |
| Professional research | Needs coverage like FiinPro-X; not realistic |
| B2B / API licensing of the verified dataset | **[H]** Interesting (verified plus provenance), but ATLAS may have **no right to redistribute** source data (B-1). Would need legal clarity first |
| Institutional | Out of reach early on |
| Advertising | Used by CafeF **[F]**; conflicts with trust positioning and needs traffic. Not recommended |

**Initial monetization hypothesis [H]:** keep the core (profiles, key financials, sources) free.
Later, test a premium tier for maturing learners covering more companies and history, comparisons,
alerts on new filings, and export. **No pricing is set now.** Experiments after validation:
1. A "fake door" premium button that measures clicks only and charges nothing.
2. Van Westendorp-style price questions in interviews, using competitors' **list prices as anchors,
   not as ATLAS's willingness to pay**.

**Costs and operational risks:**
- **Verification labour per company.** Unknown: measure the hours per company during the pilot
  (P2-3.x) before planning scale.
- **Data licensing cost.** Unknown: FiinGroup feed pricing is "contact us" **[F, R10]**, and SSI
  terms aren't published **[F, data/SOURCES.md]**.
- **Hosting.** Small at this scale.
- **Legal exposure** if data rights are wrong.
- **Quarterly re-verification load** as new reports are published.

## 10. Validation plan

**Interviews and tests: 10–15 people, in two rounds.**
1. **Round 1, problem interviews:** 8 people, weeks 2–4. No product needed.
2. **Round 2, usability tests:** 8–10 people, weeks 9–11, on pilot data. Some can repeat from round 1.

**Recruitment criteria:**

> **Superseded for round 1 by the confirmed recruiting plan (Q-4, 2026-11-23):**
> [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md#4b-confirmed-answers) §4b. It sets 10 participants via
> investor communities, RMIT and acquaintances; admits experienced investors where available; and
> allows up to 2 acquaintances, with safeguards. The round-1 threshold at n = 10 was resolved via Q-9
> (amendment AM-1 to A-9: ≥6 of 10 meets, ≤3 of 10 clearly below).
- Vietnamese.
- Has a securities account, or plans to open one within 6 months.
- Under 3 years of investing experience.
- Has tried to look up a company's fundamentals at least once.
- A mix of students and working professionals; at least 3 women; at least 2 outside Hà Nội and
  TP.HCM.
- Excluded: finance professionals (segment D) and friends of the founder (bias).
- Recruit via investing-learning communities and university clubs. Record consent, and keep no
  names in the repo.

**Problem-interview questions (round 1):**
1. Tell me about the last time you looked into a company before investing. What did you do, step by step?
2. Which sites or apps did you use? What was hard or confusing?
3. How did you decide whether the numbers were correct? Have you ever found a number that was wrong?
4. When you read an annual report or financial statement, what do you not understand?
5. How do you hear about companies to research?
6. Do you pay for any investing tool or course today? What made it worth paying for?
7. If a site showed where every number came from, would that change what you do? (Ask last, so it doesn't lead the earlier answers.)

**Usability scenarios (round 2), mapped to the journeys:**
- **S1 (J1):** "A friend mentioned [pilot company]. Find out what it does and whether its profit grew last year."
- **S2 (J2):** "Find two listed banks and tell me one difference."
- **S3 (J3):** "Check that the revenue figure shown is correct."
- **S4 (J4, if built):** "Which of these two is more profitable?"

**Evidence thresholds.** These are proposed and pre-registered **[H]**; the owner sets the final values.

> **Superseded by approved decision A-9 (2026-11-23):** rounds of 8–10 people are qualitative (NN/g:
> quantitative studies usually need more than 30 participants). The A-9 proposal in
> [PRODUCT_DECISIONS.md](PRODUCT_DECISIONS.md#2a-decision-proposals-for-owner-review-a-5-a-8-a-9-a-10)
> replaces the table below. It uses **qualitative pilot decision thresholds** (not market
> estimates) for task completion, comprehension of figures and sources, verified-vs-sample
> distinction and perceived usefulness; SUS 68 as a reference only; Continue / Iterate / Pivot
> rules; and the 14-day return measure only after G1. Approved by the project owner on
> 2026-11-23.

| Hypothesis | Supported if | Rejected if |
| --- | --- | --- |
| H1: learners struggle to understand and trust company data today | ≥5 of 8 round-1 interviewees describe confusion or distrust unprompted | ≤2 do |
| H2: per-figure sources matter | ≥50% of round-2 testers open a source without prompting, or rate it in their top 2 most useful features | <20% open one, and it is rated low |
| H3: ATLAS profiles aid understanding | ≥80% complete S1 without help, median ≤3 minutes | <50% complete it |
| H4: users would return | ≥40% of testers voluntarily use ATLAS again within 14 days (opt-in follow-up) | <15% |
| H5: willingness to pay exists for depth | ≥30% say they'd pay for a specific premium feature *and* click the fake door | <10% |

**Metrics** (needs privacy-respecting, opt-in analytics; none exists yet):
- discovery task completion rate and time to answer (S1, S2)
- source-inspection rate (figure → source clicks ÷ profile views)
- 14-day return rate
- saved companies (if the watchlist is built)
- user-rated usefulness (1–5)
- stated willingness to pay plus fake-door click-through

**No claims of product-market fit** will be made from this pilot. At most it can show that the
direction is worth continuing.

## 11. Strategic recommendations

1. **Initial segment:** C, new Vietnamese investors learning fundamentals; E (English) designed in
   as second.
2. **Primary problem:** understanding a company and trusting its numbers.
3. **Positioning:** §5.
4. **MVP:** M1–M5 (§6); SHOULDs only after the M1–M2 data pilot succeeds.
5. **Journeys:** J1–J3 must work; J4 if the SHOULD is built.
6. **Differentiation:** depth of understanding plus per-figure provenance on a small, verified,
   growing set, not breadth, speed or AI.
7. **Monetization:** free core; premium-depth hypothesis tested only after validation.
8. **Validation:** two rounds, 10–15 people, with the pre-registered thresholds in §10.
9. **Top 10 risks:** §12.
10. **90-day roadmap:** below.

### 90-day roadmap

Weeks are approximate. **Gates are dependencies, not dates.** Engineering on real data cannot start
before G1.

| Weeks | Product decisions | Data access and licensing | Engineering | UX | User research | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| 1–2 | Owner approves segment, positioning, MVP and Vietnamese-first (PRODUCT_DECISIONS A-1 to A-5) | Owner decides the data path; get a legal view on storing and displaying figures from companies' published reports (**gate G1**) | Fixes with no data dependency: Vietnamese font subset, `lang`, i18n scaffold; `rejected` verification state (schema change, P2-2.5) | Wireframes: profile with per-figure sources | Recruit round 1 | Pre-register thresholds (§10) |
| 3–4 | Choose the pilot sectors and the 20–30 company selection criteria (P2-3.1) | **Private pilot (A-6, independent of G1):** verify the first **5 companies** end to end; measure hours per company (**gate G2**) | Per-figure source display; "not reported" state; Vietnamese number scales (using fixtures) | Vietnamese copy and glossary drafts | **Round 1 interviews (8)** | Score H1 |
| 5–8 | Go/no-go on scaling to 20–30 companies based on G2 cost, and on H1 | Verify the remaining companies with second-reviewer checks; coverage report (P2-3.9) | Verification workflow tooling (P2-2.1); import pilot data; ratios as SHOULD (P2-5.11–5.17) | Usability-test prototype on pilot data | Synthesis | — |
| 9–11 | Decide on the SHOULDs (comparison, watchlist) | Re-verification process for new quarterly reports | Opt-in analytics; bug fixes from tests | Iterate on test findings | **Round 2 usability (8–10)** | Score H2–H5 |
| 12–13 | Continue / pivot / stop decision, recorded in PRODUCT_DECISIONS | Decide on a licensed-provider path for scale | Release readiness (P2-8.x) | — | Write-up | Report against thresholds; **no product-market-fit claims** |

**If G1 fails** (no permitted data path), the pilot runs on internal, non-public data for user
testing only, and nothing real is published. The roadmap then centres on getting a licence.

## 12. Risks and assumptions

**Top 10 product risks**

| # | Risk | Likelihood / impact | Mitigation |
| --- | --- | --- | --- |
| 1 | **No legal right** to store or display company figures (B-1) | High / critical | Gate G1 legal view before publishing; only internal testing until cleared |
| 2 | **Verification effort is too high** to scale beyond 20–30 companies | High / high | Measure at G2; design the workflow for speed; licensed data for scale later |
| 3 | **Learners don't value provenance** (H2 fails) | Medium / critical | Test early (round 1, Q7 asked last); pivot to understanding-first if needed |
| 4 | Segment C won't pay **[H]** | High / medium | Treat C as the entry funnel; depth for B monetizes later; don't over-invest before evidence |
| 5 | 20–30 companies feels too small, so users hit "not covered" often | Medium / high | Pick the most-searched large caps; clear "not covered yet" plus a request button |
| 6 | Incumbents add source links or learning modes | Medium / medium | Differentiation is the whole verification model, not one feature; move fast on the pilot |
| 7 | Data goes stale between quarterly reports | Medium / high | Visible "last verified" date; re-verification schedule |
| 8 | Errors in verified data damage trust disproportionately | Medium / critical | Two-person verification for financials; public corrections log (P2-2.8) |
| 9 | Founder bandwidth: one person doing product, data, engineering and research at once | High / high | Gates and a narrow MVP; data verification is the bottleneck, so cut engineering scope first |
| 10 | Dev environment fragility: repo in iCloud-synced folder (Phase 2 R-1) | Medium / medium | Move the repo out of iCloud |

**Key assumptions to test:** segment C's pain is real (H1); provenance matters to them (H2);
plain-language profiles help (H3); learners start with large caps **[A]**; public company reports
are a lawful source for display, which legal review must decide **[A]**.

## 13. References

All pages read on 2026-11-23 unless noted.

| Ref | Source |
| --- | --- |
| R1 | Simplize pricing: https://simplize.vn/pricing |
| R2 | Simplize about: https://simplize.vn/about-us |
| R3 | FireAnt membership tiers: https://fireant.vn/goi-hoi-vien |
| R4 | FireAnt homepage: https://fireant.vn/ |
| R5 | 24HMoney: https://24hmoney.vn/ |
| R6 | Vietstock: https://vietstock.vn/ and https://finance.vietstock.vn/ (partly read; some content came from a page summary) |
| R7 | Vietstock upgrade page (tier prices not present in fetched markup): https://finance.vietstock.vn/nang-cap-tai-khoan |
| R8 | CafeF data: https://cafef.vn/du-lieu.chn |
| R9 | FiinGroup FiinPro-X: https://fiingroup.vn/vi/fiinpro-x-nen-tang-du-lieu-tai-chinh-va-cong-thong-tin-trai-phieu.html |
| R10 | FiinGroup API/DataFeed: https://fiingroup.vn/vi/giai-phap-du-lieu-chung-khoan-api-datafeed-microsite.html |
| R11 | WiData (wichart.vn redirects here): https://widata.vn/ |
| R12 | TradingView pricing: https://www.tradingview.com/pricing/ |
| R13 | TradingView Vietnam stocks: https://www.tradingview.com/markets/stocks-vietnam/ |
| R14 | TradingView HOSE:FPT financials: https://www.tradingview.com/symbols/HOSE-FPT/financials-overview/ |
| R15 | Securities accounts at 31 Oct 2026, citing VSDC: https://thoibaotaichinhvietnam.vn/so-luong-tai-khoan-nha-dau-tu-dat-14-4-trieu-tai-khoan-tinh-den-cuoi-thang-10-2026-206477.html |
| R16 | FTSE Russell country classification, Sep 2025: https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2025/ftse-russell-country-classification-september-2025 |
| R17 | Repository facts: `data/SOURCES.md`, `docs/PHASE_1_CHECKLIST.md`, `docs/PHASE_2_CHECKLIST.md`, `frontend/src/app/layout.tsx` |
