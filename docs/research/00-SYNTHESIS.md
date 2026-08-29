# Irish Horse-Racing Betting-Edge App — Research Synthesis

*Compiled 2026-08-28 from twelve detailed research reports in this directory (each fully sourced; see the individual files for citations and verification flags).*

## The verdict in one paragraph

The pivot from greyhounds to horse racing is **validated on every axis that killed the greyhound project**: a purpose-built hobbyist API with explicit Irish coverage exists (The Racing API, from ~£24.99/mo), Betfair publishes a free 18-year Irish closing-odds archive and a fully ToS-legal betting/automation API, the open-source ecosystem is ~17–50x larger, and Irish sectional (GPS) data has existed for every race at all 26 tracks since 1 January 2024. The modeling problem has a public blueprint (Benter's two-stage "model + market odds" logit) with realistic expectations of low-single-digit ROI at exchange prices. The honest constraints are: bookmaker accounts that win get restricted within weeks (the durable venue is the Betfair exchange at 2% commission, plus the Tote), Irish midweek exchange liquidity is thin, a paying Irish-only audience is only ~1,000–3,000 people (build UK+IRE coverage with Irish-first positioning), and advised prices decay within minutes at scale (design around BSP/CLV, not single advised prices). A tips-only app needs **no gambling licence** in Ireland today.

---

## 1. The competitor landscape (reports: `edge-apps-uk-ireland`, `edge-apps-global`)

**Six archetypes in UK/IRE:** big-media subscriptions (Racing Post+ up to £49.99/mo; Timeform Race Passes ~£30/mo), ratings/racecard toolkits (Geegeez Gold £36/mo — the UX benchmark; Inform Racing £36/mo), database/system builders (HorseRaceBase, Proform ~£50/mo, Betwise Smartform £195+£65/mo), tipster ecosystems (OLBG free/affiliate; Betting Gods £29/mo/tipster; Tipstrr), odds/value screens (Oddschecker+ Premium £29.99/mo now selling "AI Value Bets"; ITV OddsFinder launched free July 2026), and a new wave of tiny AI-predictor apps (Horserace-iQ+ £19.99/mo with ~9 subscribers).

**Key structural facts:**
- **Almost nobody sells a genuine predictive model.** The market sells data + filters + human opinion. Calibrated probabilities + explicit value overlay is a real gap — but the tiny AI apps' subscriber counts warn that bare model output doesn't sell; it must live inside a credible racecard UX with narrative.
- **No Ireland-only paid analytics product exists.** Ireland is served as an appendage of GB by every incumbent. This is rational market structure (Ireland ≈ 390 fixtures/yr vs GB ~1,458; ~7% of the combined adult population), not an unserved goldmine.
- **Price anchors:** serious-punter tools £30–36/mo; tipster output £19–29/mo; free tiers monetise via bookmaker affiliate commission.
- **Global patterns worth copying:** Punting Form's four-tier ladder (free → cheap API → expensive sectionals → bespoke modeller DB, exited to BetMakers); EquinEdge's structure (win% + value price + ticket builder + community, ~$50–80/mo); Betfair Australia's "free model as funnel"; RebelBetting's profit guarantee; Trademate's CLV tracking as proof-of-edge; day-pass SKUs for festivals (Cheltenham/Punchestown/Galway); Tipstrr as free third-party verification.

## 2. Data feasibility (reports: `irish-racing-data`, `open-source-and-community`)

**The recommended stacks:**

| Tier | Contents | Cost |
|---|---|---|
| Budget | rpscrape-lineage / Kaggle UK+IRE corpus (1990–2026, personal-use grey) + free Betfair BSP CSVs (GB+IRE back to 28 May 2008) + free delayed Betfair API key | ~€0–10/mo |
| **Mid (sweet spot)** | The Racing API Standard (racecards, results, 20+ bookmakers' UK+IRE odds, 5 req/s) + free BSP CSVs + delayed Betfair key; one-off Smartform £195 for 2003→ MySQL history | ~€47–88/mo |
| Pro | Racing API Pro + Smartform sub (£65/mo) + Timeform Race Passes (reference) + Betfair Historic Advanced packs + live Betfair key (£499 one-off) | ~€210–350/mo |

**Critical facts:** HRI/Weatherbys publish nothing machine-readable for the public (data rights flow through RMG/SIS to commercial licensees). Irish sectionals (Coursetrack/RaceiQ) are free on racingtv.com but have no API and only ~2.5 years of history — an immature-market edge candidate. *BHB v William Hill* (ECJ 2004) gutted database rights over racecard facts, but site ToS still bind contractually (*Ryanair v PR Aviation*) — licensed feeds are the production path. The canonical scraper rpscrape was deleted from GitHub (forks survive) — a warning about building on scraping. The betcode-org stack (betfairlightweight 513★, flumine 242★, both MIT and active) is the mature execution/backtest layer.

## 3. The modeling blueprint (report: `prediction-modeling`)

1. **Architecture:** conditional-logit softmax per race (or GBDT with Plackett–Luce/listwise loss) trained on strictly point-in-time features, then **Benter's second stage**: blend model log-probs with market log-probs by MLE. The blend is where the edge lives — Benter called feeding public odds into the model his single most important innovation; his combined ΔR² over odds-only was just 0.0178 and that was enough for ~$1bn.
2. **The test of any feature is incremental information over the odds** (ΔR², log-loss gain), never standalone accuracy. A standalone model is worthless without the market blend (Benter's Table 4: its longshots are systematically overconfident).
3. **Features that matter for UK/IRE:** official ratings (OR) and handicap progression; speed figures (buildable: time vs course standard, daily going allowance); shrunk trainer/jockey form (cold yards are more predictive than hot); days-since-run × class; draw×going×course (odds-adjusted — headline biases like Chester are over-bet); pace/run-style; sire stats for lightly-raced horses; sectionals (the fresh Irish angle).
4. **Staking/evaluation:** fractional Kelly (¼–½), minimum-edge and minimum-probability filters (Bolton & Chapman's longshot exclusion), evaluate on **CLV vs Betfair SP minus commission**, walk-forward by season only. Any backtest showing +30% ROI is leakage.
5. **Evidence base:** Lessmann/Sung/Johnson two-stage SVR/RF beat plain CL (+17% ROI on small holdouts); modern GBDT-LTR papers agree; deep learning underwhelms on tabular racing data.

## 4. Odds & execution (reports: `odds-and-betting-apis`, `market-economics`, `gap-tote-world-pool-ireland`)

- **Betfair Exchange is the only durable venue**: bots expressly permitted, free delayed key for development, £499 one-off live key (must bet, can't be read-only), 2% commission attainable (My Betfair Rewards Basic), Expert Fee only above £25k/52-week profit (Premium Charge abolished Jan 2025). Matchbook (open free API, 2% — Irish company), Betdaq (£250 API fee), Smarkets (gated API) are secondary venues.
- **No retail bookmaker has a public API.** Bookmaker odds surface = The Racing API (20+ books). Display + deep-link + affiliate is the only bookmaker integration; automation there is account-fatal. The Odds API covers no horse racing.
- **Account limiting is decisive:** 643,779 GB accounts restricted in 2024; >55% of HBF-surveyed racing bettors restricted; winners cut within weeks. BOG (starts 8–9am race day) is real EV but accelerates limiting.
- **Market efficiency:** industry SP overround ~1.5–1.9% per runner; BSP is near-unbiased; favourite-longshot bias persists at bookmakers (backing 100/1+ loses ~61%) and is weak on exchanges → longshot filters are table stakes.
- **Where edges plausibly live:** early-price vs close (fastest route to limiting), BOG, each-way/extra-place structures, small Irish midweek markets (soft prices but thin liquidity — measure via API), Tote exotics on ordinary days, and **World Pool days** (~6 Irish days/yr, €26–28m/day, 17.5% win takeout, HK-weighted mispricing of Irish form, winners welcome; Tote Partner API is a real GraphQL bet-placement API; TDCO "Tote" got its Irish GRAI licence 26 Aug 2026).
- **Liquidity check:** UK Saturday Class 1–3 races match £3–8M; Irish midweek win markets often low-to-mid six figures or less; place markets ~25–40% of win volume. Ample for €10–50 stakes; a real constraint at scale. Racing exchange turnover is declining (−4.3% y/y 2025).
- **Verified performance ceilings:** SBC-verified value services sit at ~4–7% ROI (best: 4.06% over 16,488 bets); a real 4% edge at odds ~5.0 still loses money in 1 year out of 4 at 1,000 bets/yr; proving edge from P/L needs 7,000–23,000 bets — hence CLV as the KPI (separable in tens of bets). Bankroll guidance: 200–300 units.

## 5. Legal & regulatory (report: `legal-regulatory-ireland`)

- **A tips/analytics app that takes no bets needs no Irish gambling licence today.** The Gambling Regulation Act 2024 licenses operators, intermediaries, and B2B suppliers to operators. Selling tips to consumers is outside all three (re-check when B2B licensing commences 2027–28; selling odds/model feeds **to bookmakers** would need a B2B licence).
- **The hard rule: only link to GRAI-licensed operators** (register published; Betfair, Paddy Power, Smarkets, Tote already on it). Promoting unlicensed operators is GRAI's stated enforcement priority (€20m/10% fines, 8-year offences for operators).
- Advertising watershed/inducement rules (ss.143–151, 157) are enacted but **not yet commenced** (as of Aug 2026) — they'll bind via affiliate contracts; no affiliate registration regime exists.
- **Tax:** punters' winnings are tax-free (TCA 1997 s.613(2); *Graham v Green*); betting duty is the operator's problem; app revenue is ordinary trading income (+23% VAT on subscriptions).
- **App stores:** tips apps avoid real-money-gambling certification but get 17+/18+ ratings; Google flags "odds trackers stuffed with gambling ads". **Launch web-first (PWA)** — it sidesteps store gambling policy and store payment cuts.
- Build in from day one: 18+ gate, RG messaging + Irish helpline (1800 936 725), no profit guarantees, timestamped pre-off tip logging (ASA/CAP-compatible verification).

## 6. Demand & business model (reports: `gap-irish-demand-and-subscriber-economics`, `gap-affiliate-monetization-and-bet-tracking`, `gap-daily-pipeline-timing-and-price-decay`)

- ~600k Irish adults bet on racing monthly (~150–170k engaged online weekly+), but the **paying** analytics segment across all of UK+IRE is tens of thousands (Racing Post: 15k digital subs). Realistic year-one plan: a few hundred subscribers; Ireland-only caps at ~€56k/yr net — **cover UK+IRE from day one, position Irish-first** (euros, Irish tracks first, Tote/World Pool angles).
- Churn benchmarks are brutal (median 17% of monthly subs alive at 12 months; high-priced monthly 6.7%); annual plans + festival day-passes + free-tier affiliate revenue are the standard mitigations. €30/mo gross = €24.39 net of Irish VAT.
- **Affiliate reality check:** Betfair closed its UK&I affiliate programme (May 2025); Paddy Power/Sky Bet closed years ago. Open programmes: bet365 Partners, Entain, BoyleSports (30% lifetime), **UK Tote (no negative carryover — uniquely suited to referring winners)**, Matchbook (exchange — structurally aligned), William Hill, 888. Negative carryover + activity quotas make bookmaker affiliation a poor fit for a value product; Tote + Matchbook are the natural partners.
- **Bet tracking:** Betfair's Vendor Web API supports consented read of a user's bets; no bookmaker equivalent — manual entry/CSV import for the rest.

### The operational day (decisive for product design)

- Irish declarations close **10:00am two days out** (48h, both codes); GB Flat 48h, GB jumps 24h. Vendor overnight files land ~19:30. So everything is scoreable the evening before.
- Bookmakers price ~4–6pm the day before at tiny limits; BOG starts 8–9am race day; ~65% of turnover arrives in the final 15 minutes; pre-11am exchange depth on Irish midweek races is quote-only.
- **Advised prices decay in minutes** (Hugh Taylor: advised 10.41 → obtainable 7.35; SBC: −4.5% to −24.5% ROI hit within 15 minutes for the worst services).
- **Recommended publish window: 9:00–9:30am Irish time** (BOG live, morning ricks gone, pre-tipster-wave), plus an optional un-priced evening shortlist, an ~10:15 non-runner/reserve rescore (GB NR rate ~8–9%; Irish reserves declare in by 10/11am race day), and price-floor ("don't bet below X") semantics on every suggestion.
- Pipeline compute is trivial: ~35–60 races/day UK+IRE; a daily score-and-publish run costs <$10/mo of cloud.

## 7. Product strategy implications

1. **Positioning:** "Irish-first UK+IRE value engine" — calibrated win probabilities + fair price + value flags vs bookmaker/exchange/Tote odds, inside a proper racecard UI. The occupied niches are data-tools (Geegeez) and tips (OLBG); the open niche is honest model+value with verification.
2. **Trust as product:** timestamped advised-price log, CLV-vs-BSP reporting from day one, published monthly results, optionally run the model as a verified Tipstrr tipster.
3. **Route to execution:** exchange-first (Betfair API legal automation), Tote/World Pool as the ban-proof second venue, bookmaker prices display-only with BOG awareness and limiting warnings.
4. **Monetisation ladder:** free race-of-the-day + affiliate (Tote/Matchbook first) → ~€30/mo full daily suggestions + tracking → festival day-passes → later API/CSV tier.
5. **Honesty by design:** min-edge/min-prob filters, fractional Kelly with 200-unit bankroll onboarding, drawdown simulator up front, losing-run expectations, RG features. The economics report's variance tables should be in the marketing, not hidden.

## 8. Top risks

| Risk | Mitigation |
|---|---|
| Model has no real edge post-commission | CLV-vs-BSP gate before any public claims; paper-trade first season |
| Price decay makes advised prices fictional at scale | BSP-relative advice, price floors, publish-time snapshots, member caps |
| Data licence fragility (scraped history) | Licensed feeds for production (Racing API/Smartform); scraped data only for private prototyping |
| Bookmaker limiting of users | Exchange/Tote-first design; expectation-setting in UX |
| Irish liquidity ceiling | UK+IRE coverage; measure matched volume before recommending stakes |
| Regulatory drift (GRAI commencements, B2B licensing 2027-28) | Tips-only scope; GRAI-licensed links only; re-review at each commencement order |
| Tiny paid market | Free/affiliate tier + festival passes; costs held under ~€100/mo until traction |
