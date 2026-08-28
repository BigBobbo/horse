# The Economics of Beating the Horse-Racing Betting Market (UK & Ireland)

*Research audit for a value-betting suggestions app — Ireland-first, UK-relevant. Compiled 2026-08-28.*

> **Method note:** this session's web-search quota was exhausted by earlier work, so research was done by direct fetching of primary sources (HBF, Gambling Commission, BHA, SBC, academic PDFs, Wikipedia, Google News RSS). Claims that could not be verified against a primary source in this session are explicitly flagged **[unverified]**. Where data is old, it is flagged **[stale]**.

---

## Key takeaways

- **The win market at SP/BSP is close to efficient.** UK industry-SP overround averages ~**1.5–1.9% per runner** (≈112–125% books in a typical 8–13 runner race) per the Horseracing Bettors Forum's overround surveys; Betfair SP is formed with **no built-in margin** and Betfair's own 381,776-race study (2015–2020) found BSP-implied win chances "very accurate". A model must beat *that* after 2–5%+ commission.
- **The favourite-longshot bias is real, persistent, and mostly already known.** Snowberg & Wolfers (5.6M US starts, 1992–2001): 100/1+ shots return **−61%**, random betting **−23%**, favourites only **−5.5%**. The same pattern shows in UK bookmaker data. It is much weaker on exchanges (Smith, Paton & Vaughan Williams 2006) — so it is a *filter* (avoid longshots), not an edge in itself.
- **Realistic verified edges are small.** A well-regarded value-bet service verified by Smart Betting Club made **4.06% ROI over 16,488 bets**; SBC-verified tipsters cluster roughly at 4–13% ROI, with outliers higher on tiny niches. Benter's own paper caps achievable pari-mutuel profit at **0.25–0.5% of per-race pool turnover** (hard ceiling ~1.5%) even with an effectively infinite bankroll.
- **The binding constraint in UK/Ireland is not finding the edge, it's getting the bet on.** HBF's 2024 survey: **>55%** of respondents had experienced restrictions specifically targeting horse-racing bets. There is no minimum-bet-liability rule in UK/Ireland (unlike NSW/Victoria in Australia). Exchanges don't restrict winners but charge 5%+ commission, a Premium Charge up to **60%** for consistent big winners, and Irish midweek liquidity is thin **[quantify via Betfair API — no public stat]**.
- **Closing-line value (odds taken ÷ BSP or Pinnacle close, margin-adjusted) is the correct KPI for the app** — it predicts long-run profit with far smaller samples than P/L does (Buchdahl). Bet-level P/L needs ~**7,000–23,000 bets** for 2σ significance at plausible edges (see §6).
- **Variance is brutal at racing odds.** At a genuine 4% ROI and odds of 5.0, flat stakes: after 1,000 bets you're still **down ~25% of the time**; the median worst drawdown over 5,000 bets is **~107 units** (90th pct ~173u); expect a **24–31-loss losing run** somewhere along the way. Bankroll needs to be 150–300 units to survive comfortably.
- **Honest positioning:** the app can truthfully promise disciplined value identification, BSP/CLV-verified performance and realistic expectations (low-single-digit ROI, multi-year horizon, bookmaker restrictions as a certainty for winners) — not "beat the bookies" income claims. Most subscribers of even genuinely +EV services lose money through late execution (odds gone), partial availability, and abandoning the method during normal drawdowns.

---

## 1. Market-efficiency evidence for UK/Irish racing

### 1.1 Overround: bookmakers vs exchanges

The best public dataset is from the **Horseracing Bettors Forum (HBF)** — "the only recognised body representing punters in the UK today" ([ukhbf.org](https://ukhbf.org)). Its **Annual Overround Survey (Jan 2020)** measured overround-per-horse (OPH) at industry SP across 59 UK courses (excluding odds-on favourites and <5-runner races):

- Average OPH rose from **1.82% (2019) to 1.89% (2020)**.
- Course range: best **1.58%** (Cheltenham, Nottingham) to worst **2.76%** (Ffos Las), **2.49%** (Cartmel). ([HBF Annual Overround Survey, Jan 2020](https://ukhbf.org/hbf-annual-overround-survey-january-2020/)) **[stale — pre-2020 SP reform; direction of travel below]**

Concretely: 1.6–1.9% per runner means a 10-runner race bets to ~116–119%, a 16-runner handicap to ~126–130% at SP. Early-morning prices are typically wider than SP **[unverified — no current per-runner figure found this session; measure directly from an odds feed]**.

After the 2020 move to an "industrial SP" (off-course, largely derived from online prices rather than the on-course ring), HBF measured OPH of **1.52% (industrial, 1,048 races) vs 1.79% (on-course, 14,563 races, 2017–2020)** — about a 15% cut in margin ([HBF comparison on industrial SP](https://ukhbf.org/hbf-comparison-on-industrial-sp/)).

**Exchange:** Betfair SP is an auction cross of back/lay demand at the off; per Betfair, "there's no margin for profit built in" ([Betfair Hub — BSP](https://www.betfair.com.au/hub/betfair-starting-price-bsp/)). Exchange win-market books trade at ~100–101.5% pre-off **[order-of-magnitude, unverified precisely — easy to verify from the Betfair API]**. The bettor's cost is commission on net winnings: base **5% (2–7% by country/scheme, discountable by volume)**, plus the **Premium Charge** for consistently profitable high-volume accounts (min 20% of gross profits; up to **60%** for the largest winners since June 2011) ([Wikipedia: Betfair](https://en.wikipedia.org/wiki/Betfair)).

**Place/each-way:** standard each-way terms (1/5 odds 3 places in 8+ runner non-handicaps; 1/4 odds 3–4 places in 12+/16+ runner handicaps; 1/4 odds 2 places at 5–7 runners) are conventions, not prices ([Wikipedia: Each-way bet](https://en.wikipedia.org/wiki/Each-way_bet)). Because the place fraction is mechanically tied to win odds, the *place* component's implied margin varies hugely with field size and shape — this is the best-documented structural soft spot (see §2.3). HBF's Starting Price Analysis (Mar 2021; Jan 2017–Jan 2021 data) found industry SP was "**markedly worse for the bettor**" than Betfair SP precisely in the **4/1–15/2** band "notably [where] many bettors bet each way", roughly fair at 40/1+, and slightly bettor-unfriendly below 5/4 ([HBF SP Analysis, Mar 2021](https://ukhbf.org/hbf-news/hbf-starting-price-analysis-march-2021/)).

### 1.2 Favourite-longshot bias (FLB)

- **Snowberg & Wolfers (2010, JPE / NBER w15923)**, 5,610,580 US starts 1992–2001: returns of **−61% at odds ≥100/1**, **−23% betting randomly**, **−5.5% backing every favourite**; −18% roughly flat across 4/1–9/1. UK data (flatstats.co.uk) shows the bias "equally evident" in a bookmaker-dominated market; the bias has persisted 50+ years. They conclude probability **misperception**, not risk-love, drives it ([NBER w15923](https://www.nber.org/papers/w15923)).
- **Smith, Paton & Vaughan Williams (Economica, 2006)**: person-to-person **betting exchanges show significantly lower FLB** than bookmaker odds — lower transaction costs → more efficient prices ([IDEAS/RePEc](https://ideas.repec.org/a/bla/econom/v73y2006i292p673-689.html)).
- Interesting exception: FLB was largely **absent in Hong Kong pools** (Busche & Hall 1988; Busche 1994, cited in w15923) — big pools + sophisticated money flatten it, which foreshadows §4.

**Implication for the model:** calibrating probabilities against BSP and *never* taking the bookmaker's longshot prices is table stakes; a "back longshots the model likes" strategy fights a −20%..−60% headwind at bookmaker prices.

### 1.3 How efficient is Betfair SP?

- Betfair's own study: **381,776 races, 3.2M+ runners, 2015–2020** — BSP-implied win chance "very accurate when compared against the actual chance" at every percentage point ([Betfair Hub — BSP](https://www.betfair.com.au/hub/betfair-starting-price-bsp/)). Vendor source, but consistent with the academic exchange-efficiency literature above.
- Practical consensus in the professional community: blind backing at BSP loses roughly the commission; models are judged on **profit at BSP after commission** — if a model can't beat BSP flat-stakes on paper, it has no edge worth routing to bookmakers **[community convention; no single canonical citation]**.

### 1.4 Closing-line value as the benchmark

Joseph Buchdahl's closing-odds work (football, but odds-market-generic): **the ratio of odds taken to margin-adjusted closing odds is a good predictor of expected profit** — e.g. taking 1.80 that closes 1.65 with a 3% margin ⇒ 1.80/1.65/1.03 ≈ **+5.9% EV**; skilled vs fake tipsters were separable on samples of only ~20–26 tips, with one 26-tip record significant at ~1-in-60,000 ([football-data.co.uk: closing odds analysis](https://www.football-data.co.uk/blog/closing_odds.php)). For racing, the natural closing line is **BSP** (win and place). The app should log CLV vs BSP for every suggestion from day one: it converges orders of magnitude faster than P/L (§6) and is fraud-proof marketing.

---

## 2. Where edges are believed to exist (2025–26)

1. **Early price vs close ("beating the move").** The morning market on UK/Irish racing is informationally weaker than the last 10 minutes; a bet at 10am that is shorter at the off held positive CLV. This is the core of odds-drop/steamer services (an SBC-reviewed "odds-dropping software" service shows **6.89% ROI over 5,391 bets** [smartbettingclub.com](https://smartbettingclub.com/)). It is also the fastest way to get restricted (§3).
2. **Best Odds Guaranteed (BOG).** Take an early price, get SP if bigger — a free option worth several % on ROI on drifters. Still widely offered in 2025–26, increasingly by **independent bookmakers** as a differentiator, alongside extra places/cashback ([SBC Independent Bookmakers Guide](https://smartbettingclub.com/blog/independent-bookmakers/)). BOG is routinely withdrawn from winning accounts **[unverified as a documented policy; widely reported anecdotally]**.
3. **Each-way and extra-place structures.** Because place terms are fixed fractions, big-field races with a strong favourite make the place part systematically generous; **extra-place offers** (paying 4–6+ places vs the exchange's 3) create outright positive EV/arb situations — the matched-betting industry farms them daily: back E/W at the bookie, lay win and place separately on the exchange; a worked example risks **£3.37 to win £106.63 on a £10 E/W stake** when the horse lands exactly the extra place ([Matched Betting Blog: extra places](https://matchedbettingblog.com/extra-place-offers/)). HBF's finding that industry SP is worst for bettors exactly in the 4/1–15/2 each-way band is the mirror image of this ([HBF SP Analysis](https://ukhbf.org/hbf-news/hbf-starting-price-analysis-march-2021/)). This is the most defensible "retail" edge for an app, but it is stake-limited and offer-gated.
4. **Small/illiquid Irish midweek markets.** Double-edged: fewer sharp eyes and lazier bookmaker copies of each other's prices, but (a) Betfair win-market liquidity on e.g. a Tuesday at Sligo/Ballinrobe is thin pre-off **[no public per-market stat; measure traded-volume via the Betfair Exchange API — recommended first task]**, and (b) bookmakers limit fastest exactly where their prices are softest. SBC podcast guest "Harry" (£1m+ lifetime, ~20 years) now places **95–98% of bets on exchanges (Matchbook, BetDAQ, Smarkets, Betfair)** hunting "incorrectly priced and inflated markets" — i.e. even exchange-first pros treat bookmaker access as marginal ([SBC podcast #105](https://smartbettingclub.com/blog/how-harry-made-over-1-million-betting-exchanges-syndicates-and-professional-betting-insights-sbc-podcast-105/)).
5. **In-running.** Betfair in-play racing markets are dominated by low-latency operators (course-side or fast pictures); a daily-suggestions app has no realistic edge here **[assessment; latency landscape unverified this session]**.
6. **Tote pools / World Pool.** UK/Irish domestic Tote pools are small and takeout-heavy, but **World Pool days** (co-mingled into Hong Kong Jockey Club pools; Tote is HKJC's exclusive UK & Ireland partner under a five-year deal signed June 2023) put serious liquidity behind ~big UK/Irish meetings: **£521M turnover across World Pool days on British/Irish racing in 2022, +44% YoY** ([Wikipedia: The Tote](https://en.wikipedia.org/wiki/The_Tote)). Pool betting doesn't limit winners, and a probability model ports naturally to pool EV (bet where pool% < model%). Precise UK Tote/World Pool takeout rates could not be verified this session (tote.co.uk is geo-blocked from the fetcher) **[unverified: commonly reported ~17.5% win / ~25% exotics on HKJC-hosted pools; ~19–27% on domestic UK pools — confirm from tote.co.uk/HKJC]**. The **Tote Guarantee** (Tote win dividend matches or beats SP, all UK courses since Nov 2021) makes pools a viable bookmaker substitute for win bets ([Wikipedia: The Tote](https://en.wikipedia.org/wiki/The_Tote)).
7. **Arbitrage/matched offers.** Bookmaker-vs-exchange arbs and sign-up/reload offers remain the most reliable +EV in the ecosystem (the entire OddsMonkey/Outplayed industry), but they're an account-burning treadmill, not a modelling business. Useful as a subscriber on-ramp, not the product core.

---

## 3. The limiting problem

- **Prevalence.** HBF Survey 2024 (205 respondents, self-selected sharp-ish audience): **over 55% had experienced restrictions specifically targeting horse-racing bets**; 46.8% of those asked for ID/income documentation refused; 16.4% admitted using unlicensed bookmakers; 39.3% said affordability checks make black-market betting more likely ([HBF Survey 2024](https://ukhbf.org/horseracing-bettors-forum-survey-2024/)). HBF has published bettors' restriction correspondence since 2018 — accounts restricted "often with little to no evidence" ([ukhbf.org](https://ukhbf.org/account-restrictionclosure-survey/examples-of-correspondence-from-bettors-whose-activity-has-been-restricted/)) — and was still lobbying the Gambling Commission for punter protection from restrictions in **July 2025** (Racing Post, via [Google News](https://news.google.com/rss/search?q=%22Horseracing+Bettors+Forum%22+restrictions)). The Racing Post's 2024 "Right to Bet" campaign/survey exists but its numbers **could not be verified this session** (paywall/fetch blocks) **[unverified]**.
- **Speed and stakes.** How fast accounts get cut is anecdotal: consistent CLV-positive customers commonly report restriction inside weeks, sometimes days, with limits cut to pennies **[forum-level evidence; no systematic public dataset]**. No UK/Irish rule forces a layer to take a bet — unlike Australia, where **NSW banned online bookies from restricting winning punters (2015)** and state minimum-bet-limit rules oblige bookmakers to lay to lose fixed amounts ([Guardian, Jan 2015 via Google News](https://news.google.com/rss/search?q=minimum+bet+limit+racing+NSW+bookmakers); Champion Bets state-by-state MBL guide, 2022).
- **Regulatory overlay (current, and fresh):** the Gambling Commission is rolling out **Financial Risk Assessments** in stages (announced **7 July 2026**): stage 1 triggers at **£5,000 net deposits in 24h (25+)** / £2,500 (under-25), final stage at **£1,000/24h or £3,000/90 days** (25+); frictionless for ~97% in the pilot ([Gambling Commission, 7 Jul 2026](https://www.gamblingcommission.gov.uk/news/article/commission-to-introduce-financial-risk-assessments-in-staged-approach)). This replaces the 2024–25 £500→£150/month vulnerability-check pilot thresholds **[the £150/£500 figures are from the earlier announcements; treat as superseded]**. Context: the BHA's Oct 2023 survey (14,000+ respondents, with Racing Post/Racing TV/ATR) found **26% already experienced intrusive checks** and 52% would cut back racing betting under intrusive checks; 40% would consider the black market ([BHA press release, 16 Oct 2023](https://www.britishhorseracing.com/press-releases/british-horseracing-faces-exodus-of-bettors-if-intrusive-affordability-checks-are-introduced-by-gambling-commission-survey-finds/)). **App implication:** even *losing-so-far* users winning after following tips can hit deposit-based friction; Ireland's new GRAI regime is evolving separately **[not covered this session]**.
- **The exchange alternative and its ceiling.** Exchanges don't ban winners; instead: 5%+ commission, **Premium Charge 20–60%** once lifetime commission < 20% of gross profits across 250+ markets ([Wikipedia: Betfair](https://en.wikipedia.org/wiki/Betfair)), and finite liquidity — on Irish midweek cards, meaningful size only arrives in the final minutes **[anecdotal]**. Harry (above) says he keeps so much capital parked across exchanges that each betting year starts feeling negative ([SBC #105](https://smartbettingclub.com/blog/how-harry-made-over-1-million-betting-exchanges-syndicates-and-professional-betting-insights-sbc-podcast-105/)).
- **Realistic solo ceilings.** Triangulating: SBC's flagship verified value service = 4.06% ROI (16,488 bets) with SBC projecting ~80% annual bankroll growth for ~185 bets/month at 100-pt banks ([SBC Bet Hero review](https://smartbettingclub.com/blog/bet-hero_review/)); Benter's cap of 0.1–0.5% of pool turnover for pool betting; Premium Charge kicking in for consistent exchange winners. A sharp UK/Irish solo bettor mixing BOG/extra-places/exchange value at £10–£50 average stakes plausibly clears **£5k–£30k/yr before it stops scaling**; sustained six figures essentially requires exchange-scale liquidity (mostly UK Saturday/festival cards), pool play, or agents/multiple accounts (rule-breaking) **[synthesis; the components are sourced, the total is an estimate]**.

---

## 4. Syndicate and professional benchmarks

- **Bill Benter (Hong Kong).** Started with US$150k capital (1984-); $600k won in 1988, $3M by 1989; estimated lifetime winnings **"nearly $1 billion"** ([Wikipedia: Bill Benter](https://en.wikipedia.org/wiki/Bill_Benter)). His own paper ([1994, *Efficiency of Racetrack Betting Markets*; PDF via gwern.net](https://gwern.net/doc/statistics/decision/1994-benter.pdf)) is the honest blueprint: ~2,000-race development sample; **five man-years to a significant edge, five more to high profitability**; ~470 races bet/year; average track take ~19%; **4 of 5 seasons profitable, the losing season −20% of starting capital**; per-race HK pools **>US$10M**; fractional Kelly throughout; exotics out-earn win pools; and the ceiling: **max expected profit ≈ 0.25–0.5% of per-race turnover (≤1.5% absolute), 0.1–0.2% realistic for a start-up** — "at small volume tracks one could probably not make enough money for the operation to be viable." That last sentence is the single most important line in this report for an Irish-pool strategy.
- **Zeljko Ranogajec (Australia).** Syndicate turnover reportedly **6–8% of Tabcorp's ~A$10B annual revenue**, ~⅓ of Betfair Australia's volume; profitability rests on **negotiated rebates** (his Tote Tasmania rebate deal "virtually wiped out" that tote's profits, contributing to its 2012 sale); ~300 people indirectly employed ([Wikipedia: Zeljko Ranogajec](https://en.wikipedia.org/wiki/Zeljko_Ranogajec)). The model: tiny edge × colossal churn × **rebates that turn −2% into +2%**.
- **Why HK/Australia ≠ Ireland.** (1) **Pool size:** HK >US$10M/race vs Irish Tote pools that are often four figures midweek **[order-of-magnitude, unverified]**; UK/IE only reach real pool depth on World Pool days (£521M across 2022's World Pool days — [Wikipedia: The Tote](https://en.wikipedia.org/wiki/The_Tote)). (2) **Rebates:** HKJC and Australian totes rebate high-volume losers; no UK/Irish operator offers meaningful rebates **[unverified for 2025-26 — HKJC rebate page unreachable this session]**. (3) **Takeout vs margin structure:** pool takeout is fixed and payable by the crowd, while UK/IE fixed-odds margin is applied *personally* — the sharp customer is simply ejected. (4) **Closed populations** (HK's one jockey club, deep data, no competing books) make modelling cleaner. Ireland offers none of these structural advantages; what it offers is data richness relative to field quality and softer early prices.

---

## 5. Honest product implications for a daily-suggestions app

**What the evidence supports promising:**
- "We identify bets whose odds exceed our modelled fair price, benchmarked against Betfair SP; here is our live, bet-by-bet CLV and P/L record." (CLV vs BSP is auditable and converges fast — [Buchdahl](https://www.football-data.co.uk/blog/closing_odds.php).)
- Target ROI honesty: verified long-run value services sit at **~4–7% ROI at bookmaker prices** (Bet Hero 4.06%/16,488 bets; odds-drop service 6.89%/5,391 bets; SBC-tracked tipsters ~4–13% — [SBC](https://smartbettingclub.com/); Tipstrr's featured tipsters range −24.4% to +28.6% ROI with verification, [tipstrr.com](https://tipstrr.com/)). Claiming 20%+ sustained ROI on daily racing volume is outside anything independently verified.
- Time horizon honesty: "profitable over 1,000+ bets/12+ months, with losing months guaranteed" (§6 numbers).

**Why most subscribers lose even following +EV tips (design against each):**
1. **Odds decay:** the value is at the advised price; five minutes later the 5.0 is 4.2 and EV is gone. Buchdahl's framework makes this precise — profit ≈ (taken/closing − 1) − margin. *Design: push notifications with price targets, "don't bet below X" floors, BOG routing.*
2. **Availability/limiting:** restricted users can't get the advised price or stake (§3). *Design: exchange/Tote fallback lines with adjusted EV, per-user "still +EV at your best available price?" checks.*
3. **Discipline/variance:** a 24–31-bet losing run and 60–100-unit drawdowns are *normal* at 4% edge (§6); subscribers quit at the trough. SBC's Harry: "Trust the expected value. We've had losing years… if the maths is right… the profits follow" ([SBC #105](https://smartbettingclub.com/blog/how-harry-made-over-1-million-betting-exchanges-syndicates-and-professional-betting-insights-sbc-podcast-105/)). *Design: bankroll-first onboarding (≥200-unit banks), drawdown simulators shown up front, Kelly-fraction stake sizing, monthly CLV (not P/L) scorecards.*
4. **Churn economics:** subscription businesses monetise hope; the defensible ethical version monetises *process* (tracking, CLV audit, staking discipline, restriction-aware routing). Comparable pricing: Bet Hero Pro **€215.80/yr** ([SBC review](https://smartbettingclub.com/blog/bet-hero_review/)); SBC itself sells tipster-vetting as the product.
5. **Regulatory duty of care:** with FRA thresholds (£1k/24h final stage — [Gambling Commission](https://www.gamblingcommission.gov.uk/news/article/commission-to-introduce-financial-risk-assessments-in-staged-approach)) and GRAI in Ireland, an app *suggesting daily bets* should build in loss limits and affordability messaging as product features, not compliance afterthoughts.

---

## 6. Variance math (computed for this report)

Model: independent flat 1-unit win bets, true ROI as stated, all bets at the stated decimal odds. 20,000 Monte Carlo trials per cell (simulation code in project scratchpad; analytic N via (2σ/EV)²).

**Bets needed for 2σ (95%) significance of the edge from P/L alone:**

| True ROI | Odds 4.0 | Odds 5.0 | Odds 6.0 |
|---|---|---|---|
| 3% | 13,600 | 18,200 | 22,800 |
| 4% | 7,700 | 10,300 | 12,900 |
| 5% | 5,000 | 6,600 | 8,300 |

At ~1,500–2,500 suggested bets/year (5–8/day), **a genuine 4% edge at odds ~5.0 takes 4–7 years to prove from P/L** — which is exactly why CLV must be the reported KPI (skill separable in tens-to-hundreds of bets, [Buchdahl](https://www.football-data.co.uk/blog/closing_odds.php)).

**Drawdowns and losing runs (flat 1u stakes):**

| Scenario | P(down) after N | Median P/L | Median max DD | 90th pct DD | 99th pct DD | Longest losing run (med / p90) |
|---|---|---|---|---|---|---|
| 3% @ 5.0, N=1,000 | **31%** | +30u | 61u | 102u | 150u | 24 / 32 |
| 3% @ 5.0, N=5,000 | 14% | +150u | 116u | 193u | 289u | 31 / 39 |
| 4% @ 5.0, N=1,000 | 25% | +40u | 57u | 97u | 145u | 24 / 32 |
| 4% @ 5.0, N=5,000 | 8% | +200u | 107u | 173u | 254u | 31 / 39 |
| 4% @ 6.0, N=1,000 | 29% | +38u | 66u | 111u | 164u | 29 / 38 |
| 4% @ 6.0, N=5,000 | 11% | +202u | 123u | 202u | 305u | 37 / 47 |
| 5% @ 5.0, N=5,000 | 4% | +250u | 99u | 156u | 235u | 31 / 39 |

Readings:
- **A 1,000-bet year at a real 4% edge still loses money ~1 year in 4.** Any app marketing must survive that fact.
- **Bankroll:** to keep risk of ruin negligible with flat stakes, users need ~**200–300 units** (the 99th-pct 5,000-bet drawdown is ~250–300u at odds 5.0–6.0). At £10 stakes that's a £2,000–£3,000 dedicated bank for £200/yr expected profit at 4% ROI on 5,000 bets — worth stating this baldly in-app.
- **Kelly:** optimal fraction = edge/(odds−1) ≈ 0.04/4 = **1% of bankroll per bet** at 4% edge, odds 5.0; half-Kelly (0.5%) is the sane default (full Kelly has a 50% chance of ever halving the bank; Benter used fractional Kelly and still logged a −20% season — [Benter 1994](https://gwern.net/doc/statistics/decision/1994-benter.pdf)).
- Higher average odds monotonically worsen every risk metric at fixed ROI — a product tilt toward the 2.5–6.0 band (also where HBF shows bookmaker E/W pricing is weakest) improves subscriber survival.

---

## Verification gaps (explicit)

- **Current (2025–26) average overrounds** for early prices and each-way place markets: not found from a primary source this session; HBF's last overround survey is Jan 2020 **[stale]**. Recommend computing daily from an odds feed once the data pipeline exists.
- **UK Tote / World Pool takeout percentages**: tote.co.uk geo-blocked; HKJC rebate/takeout pages unreachable. The ~17.5% win-pool figure is **[unverified]**.
- **Betfair liquidity on Irish midweek races**: no public statistics; must be measured via the Exchange API (traded volume per market is in the API and in Betfair's historical data files).
- **Racing Post "Right to Bet" survey (2024)** numbers: paywalled/unfetchable **[unverified]** — the campaign's existence and HBF's 2025 GC lobbying are confirmed via Google News/BHA.
- **Speed-of-limiting quantification**: only anecdotal/forum evidence exists anywhere; no dataset.
- Smart Betting Club current subscription pricing: page shows "low membership prices" without figures.

## Sources

- HBF Annual Overround Survey, Jan 2020 — https://ukhbf.org/hbf-annual-overround-survey-january-2020/
- HBF Industrial SP comparison, 2020 — https://ukhbf.org/hbf-comparison-on-industrial-sp/
- HBF Starting Price Analysis, Mar 2021 — https://ukhbf.org/hbf-news/hbf-starting-price-analysis-march-2021/
- HBF Survey 2024 — https://ukhbf.org/horseracing-bettors-forum-survey-2024/
- HBF restriction correspondence — https://ukhbf.org/account-restrictionclosure-survey/examples-of-correspondence-from-bettors-whose-activity-has-been-restricted/
- Snowberg & Wolfers, "Explaining the Favorite-Longshot Bias" (NBER w15923 / JPE 2010) — https://www.nber.org/papers/w15923
- Smith, Paton & Vaughan Williams, "Market Efficiency in Person-to-Person Betting", Economica 2006 — https://ideas.repec.org/a/bla/econom/v73y2006i292p673-689.html
- Benter, "Computer Based Horse Race Handicapping and Wagering Systems: A Report" (1994) — https://gwern.net/doc/statistics/decision/1994-benter.pdf
- Wikipedia: Bill Benter — https://en.wikipedia.org/wiki/Bill_Benter
- Wikipedia: Zeljko Ranogajec — https://en.wikipedia.org/wiki/Zeljko_Ranogajec
- Wikipedia: Betfair (commission, Premium Charge) — https://en.wikipedia.org/wiki/Betfair
- Wikipedia: The Tote (World Pool, Tote Guarantee) — https://en.wikipedia.org/wiki/The_Tote
- Wikipedia: Each-way bet — https://en.wikipedia.org/wiki/Each-way_bet
- Betfair Hub: Betfair Starting Price — https://www.betfair.com.au/hub/betfair-starting-price-bsp/
- Buchdahl, closing odds analysis — https://www.football-data.co.uk/blog/closing_odds.php
- Smart Betting Club (verified tipster ROIs) — https://smartbettingclub.com/
- SBC Bet Hero review (4.06% ROI / 16,488 bets; €215.80/yr) — https://smartbettingclub.com/blog/bet-hero_review/
- SBC podcast #105 ("Harry", £1m+, exchanges) — https://smartbettingclub.com/blog/how-harry-made-over-1-million-betting-exchanges-syndicates-and-professional-betting-insights-sbc-podcast-105/
- SBC Independent Bookmakers Guide (BOG/extra places) — https://smartbettingclub.com/blog/independent-bookmakers/
- Tipstrr — https://tipstrr.com/
- Matched Betting Blog: extra place offers — https://matchedbettingblog.com/extra-place-offers/
- Gambling Commission: Financial Risk Assessments, 7 Jul 2026 — https://www.gamblingcommission.gov.uk/news/article/commission-to-introduce-financial-risk-assessments-in-staged-approach
- BHA affordability-checks survey, 16 Oct 2023 — https://www.britishhorseracing.com/press-releases/british-horseracing-faces-exodus-of-bettors-if-intrusive-affordability-checks-are-introduced-by-gambling-commission-survey-finds/
- Guardian via Google News: NSW ban on restricting winners (2015); Racing Post: HBF pushes GC on restrictions (Jul 2025) — https://news.google.com/rss/search?q=%22Horseracing+Bettors+Forum%22+restrictions
