# The Operational Day: Declarations, Market Formation, Price Decay and Pipeline Timing for a Daily Irish/UK Value-Bets Service

**Research date: 28 August 2026.** Focus: Ireland first, Britain second. This report maps the daily operational timeline (when runners are known, when prices exist, when they can actually be taken), quantifies how fast advised prices decay after publication, covers non-runner/instability risk, surveys publish times of comparable services, and costs the daily pipeline. Every claim carries a source; unverifiable points are flagged.

> **Research-method caveat:** general web-search tooling was unavailable for most of this session (budget exhausted); findings were assembled from direct fetches of primary sources (IHRB Rules of Racing PDF, HRI RÁS live pages, BHA press releases, vendor pages, tipster-review sites) plus Google News RSS. A handful of secondary confirmations that a search engine would normally provide are explicitly flagged below.

---

## Key takeaways

- **Ireland runs a single, simple clock: all declarations (Flat and National Hunt) close at 10:00am two days before racing.** 48-hour declarations were made permanent in September 2021, and the live HRI RÁS system confirmed it during this research ("Next Declarations Close at 10:00 on 29-Aug-26" for Monday 31 Aug meetings). Final fields, jockeys and headgear for an Irish Sunday card are therefore public from ~10:30am Friday.
- **Britain: Flat = 48-hour declarations, Jumps = 24-hour declarations, both closing 10:00am**, with high-profile exceptions (Cheltenham Festival 48-hr since 2017; the Derby 72-hr since 2025; Grand National has a 5-day stage). BHA declarations become official "after 10:00 on the day of declarations"; provisional declarations stream on the BHA site before 10am (since March 2023).
- **Vendor overnight files land the evening before**: Betwise Smartform publishes "final racecards (available from 7.30 pm every evening) for the next day's racing"; The Racing API refreshes tomorrow's racecards/odds every 15 minutes and today's every 3 minutes.
- **Bookmakers price up the evening before (~4–6pm) at tiny limits, re-rate through the morning, and Best Odds Guaranteed typically only starts at 8–9am on race day.** Roughly 65% of bookmaker turnover still arrives "at the show" (final ~15 minutes). Betfair Exchange win markets exist early but carry meaningful liquidity only from late morning and are deepest in the final minutes.
- **Advised prices decay brutally fast once a followed tipster publishes**: Hugh Taylor's advised prices are "smashed in" "within a minute or two" (measured advised avg 10.41 vs 7.35 obtainable); Smart Betting Club odds-tracking found per-service ROI hits of −4.5% to −24.5% within 15 minutes for the worst offenders, and a general 6–8% price drop for anyone betting "later in the morning".
- **Non-runners are a first-order product problem**: GB non-runner rate ~8–9% of declarations (Flat turf 10.3–11.4%, Jumps 6.5–7.6%, 2012–16 BHA data — the longer 48-hr Flat window drives going-related withdrawals). Ireland adds a unique wrinkle: up to 3 published reserves per race, who must be declared in by 10am/11am on race day.
- **Comparable services publish either ~8:45–10:30am on race day or "tea time" the evening before.** myracing: 8:45am daily; HRI's own site: "Racing tips will be available before 10.30am on racedays"; Geegeez Stat of the Day (when it ran): tea-time the night before; Racing Post now releases Tom Segal's Saturday tips on Friday.
- **Recommended publish window: ~9:00–9:30am Irish time** (details and reasoning below), optionally preceded by an un-priced "shortlist" the evening before.
- **Pipeline cost is trivial**: a 4 vCPU/8 GiB cloud box is $0.179/hr on-demand (AWS c7i.xlarge); a daily 30–60-minute score-and-publish run is <$10/month. The workload is ~35–60 races/day (GB: 1,458 fixtures in 2026; Ireland: ~390 fixtures/yr, avg field 11.5).

---

## 1. The regulatory clock: when runners are actually known

### 1.1 Ireland (HRI / IHRB)

The governing text is the IHRB Rules of Racing (Master Rulebook, as amended 26 April 2024, downloaded from the IHRB regulation page: https://www.ihrb.ie/regulation-integrity/):

- **Entries** close "at 12 noon" on the advertised closing day (Rule 190 area of the rulebook) — in practice roughly 5–6 days before the meeting. A live RÁS notice observed on 28 Aug 2026 illustrates the cadence: a replacement Clonmel meeting "Entries for this meeting will close by noon Thursday 10 September with declarations to run to be made by Monday 14 September" (https://www.hri-ras.ie/).
- **Declarations to run**: "Every declaration of a runner must be made to Horse Racing Ireland by 10 a.m. on the day fixed for declarations" (Rule 194(i)). Since September 2021 the day fixed is **two days before racing for both codes** — the Racing Post reported "HRI reveals 48-hour declarations will remain permanent in Irish racing" on 9 Sep 2021 (headline via Google News RSS; article: racingpost.com). Live confirmation during this research: the RÁS declaration-status page showed "Next Declarations Close at 10:00 on 29-Aug-26" (https://status.hri-ras.ie/declaration-status.aspx, fetched Fri 28 Aug 2026 — i.e. Saturday's 10am deadline covers Monday's fixtures), and a RÁS stabling notice states "field size limits in races are being altered right up to declaration time (10am)" (https://www.hri-ras.ie/).
- **Supplementary window**: weight-for-age races with fewer than 5 declared runners get an automatic 15-minute telephone-only supplementary declaration period after 10am (Rule 194(i)).
- **Balloting and reserves**: oversubscribed races are reduced by ballot/elimination at the declaration stage, and "not more than three extra Horses will be included as Reserves", published on the racecard in priority order (Rule 194(ii)(c)). A reserve that wants to run must be declared in **"not later than 10am"** on race day in November–January (non-floodlit) and **"not later than 11am"** the rest of the year (Rule 194(iii)(b)) — i.e. Irish fields are not final until 10/11am on the day.
- **Riders**: nominated at a separate "overnight nomination of Riders" deadline set by HRI (Rules 195/Regulation R3 reference "the deadline fixed for nomination of Riders to the Registry Office"); a trainer who misses it must nominate in writing "not less than one and a half hours before … the first Race" and explain to the stewards (Regulation R3.1). *Flag: the rulebook does not print the clock time of the rider-nomination deadline (it is set administratively by HRI); in practice riders appear on RÁS/racecards with the declarations. Could not verify the exact rider-deadline hour from a public page.*
- **Non-runners**: withdrawal must be notified on RÁS or the Non-Runner Line "not less than one and a half hours before the time fixed for the running of the first Race" (Rule 194(iii)(a)); later withdrawal fines are **€200 first offence, not less than €320 for each subsequent** in a calendar year (Rule 194(iv)); a vet cert must be lodged within 3 days (IHRB non-runners page: https://www.ihrb.ie/non-runners-landing-page/).

**Operational meaning for the app (Ireland):** the full Monday field with riders is machine-readable from ~10:15–10:30am Saturday; the only day-of-race instability is (a) reserves declaring in up to 10/11am, (b) withdrawals up to 90 minutes before the first race, and (c) going changes.

### 1.2 Britain (BHA / Weatherbys)

- **Flat: 48-hour declarations, closing 10:00am** two days before. The BHA's 17 June 2020 resumption release states the mechanics precisely: "declarations to run on 24 June must be made by 10am on Monday 22 June" (https://www.britishhorseracing.com/press_releases/resumption-update-48-hour-declarations/). 48-hr Flat declarations date to 2006 (BHA: "STATEMENT ON 48-HOUR DECLARATIONS", 9 Jun 2006, target 1 Aug 2006: https://www.britishhorseracing.com/press_releases/statement-on-48-hour-declarations/), after a 2003 all-weather trial (15 Oct 2003 release).
- **Jumps: 24-hour declarations (10:00am the day before) as standard.** Evidence: the BHA's 12 Sep 2017 release "Cheltenham Festival moves to 48 hour declarations" (https://www.britishhorseracing.com/press_releases/cheltenham-festival-moves-48-hour-declarations/) only makes sense against a 24-hr default; jumps ran 48-hr temporarily during the 2020 Covid protocols (17 Jun 2020 release above). *Flag: I could not locate a single current official page that states "jump racing declares at the 24-hour stage" in one sentence — this is the standard industry position (and consistent with everything above) but deserves a one-line confirmation from the BHA rules microsite (rules.britishhorseracing.com, a JS app that resisted fetching) before it goes in marketing copy.*
- **Exceptions**: the Derby became Britain's first **72-hour declaration** race in 2025 (Sporting Life / Racing TV, 5 May 2025: "Epsom ushers in 72-hour declarations for the Derby"); the Grand National has a five-day declaration stage before final 48-hr decs (e.g. "7 More Withdrawn From The 2025 Grand National Following The Five Day Declaration Stage", grandnationalfans.co.uk, 31 Mar 2025).
- **When declarations are published**: since March 2023 the BHA shows provisional declarations live on its fixtures pages *before* 10am, but "declarations are not official until they have been formally checked and published after 10:00 on the day of declarations; subsequent changes, including to race times and the final fields, may still occur prior to this point" ("Transparent declaration tracking available on BHA Website", 10 Mar 2023: https://www.britishhorseracing.com/press_releases/transparent-declaration-tracking-available-on-bha-website/). Draws for Flat races are allocated and published with the final declarations shortly after 10am.

### 1.3 When the data actually lands in vendor feeds

- **Betwise Smartform** (the SQL research database many UK/IRE modellers use): "final racecards (available from 7.30 pm every evening) for the next day's racing"; database £195 one-off + £65/month subscription (https://www.betwise.co.uk/smartform). This 7:30pm file is the natural trigger for an evening scoring run.
- **The Racing API** (the 20+ bookmaker odds feed already in the build plan): "Today's racecards, odds and results are updated every 3 minutes. Tomorrow's racecards and odds are updated every 15 minutes. Future racecards are updated daily." (https://www.theracingapi.com/ FAQ.)
- Because Irish decs are 48-hr and GB Flat is 48-hr, **most of a given day's racing is fully known by 10:30am the previous day**; the only late adds are GB jumps cards (known 10:30am day-before) — i.e. *everything* needed for a morning-of-race pipeline is stable by the prior evening.

---

## 2. Market formation: when prices exist, and when they can be hit

The best single source found is Irish racing journalist Tony Keenan's "Watching the Markets" (Geegeez, 10 Sep 2018, https://www.geegeez.co.uk/tony-keenan-watching-the-markets/), an explicit timeline of how Irish/UK race markets unfold. Dated 2018 — the structure is stable but the firm-by-firm details may have drifted; flagged accordingly.

- **Overnight prices (~4–6pm the day before):** bookmakers open markets roughly six hours after declarations, led by Paddy Power/Betfair Sportsbook, followed by Bet365, Sky Bet, Betfred and Ladbrokes/Coral. Compilers may "price up on a hundred horses for the following day … little more than three minutes per horse", so overnight books are defensive and error-prone — but "no one, unless you have access to a whale account, can get at these prices to any scale": limits are tiny.
- **Morning of the race (9am–noon):** overrounds come in, "the obvious ricks generally being quickly ironed out"; prominent tipsters (the article names Andy Holding and Gary O'Brien) post "around 9:30am" and move markets; exchange liquidity builds, with Matchbook "a notably bigger player" on Irish racing.
- **The show (final ~15 minutes):** "the show is still when the bulk of betting turnover comes" — approximately **65% of turnover** — and "there are still big swings in prices near the off".
- **Best Odds Guaranteed:** BOG "only kicks in from around 8am or 9am on the day of the race. In fact, a growing number of bookies have changed their terms so that only bets placed after a set time on race day qualify … some may offer different BOG starting times with anywhere from 8am to 1pm being common" (ThePuntersPage BOG guide, https://www.thepunterspage.com/best-odds-guaranteed/; one listed UKGC bookmaker's terms: "Applies to bets placed from 08:00 on the race day"). **This is decisive for publish timing: a price advised at 8pm the night before carries no BOG protection; the same price advised at 9am does.**
- **Betfair Exchange liquidity:** no formal UK/IRE study of matched volume by hours-to-off was found in fetchable form (*flagged below*). Converging practitioner evidence: Keenan's 65%-at-the-show figure; Betfair's own automation tutorials place model bets only when "market.seconds_to_start < 60" i.e. betting at/near the off where depth exists (How to Automate series, https://betfair-datascientists.github.io/tutorials/How_to_Automate_3/); and the Hugh Taylor evidence below shows morning exchange/bookmaker depth is thin enough that one free tipster empties it in minutes. Treat pre-11am exchange depth on ordinary Irish midweek races as "quote-only": fine for a fair-value reference price, unreliable for filling size.
- *Flag: could not verify a published percentage curve of Betfair matched volume vs minutes-to-off for UK/IRE racing (Betfair forum and betting.betfair archive pages resisted fetching). The AU Betfair Hub and UK trading-community folklore both put the large majority of pre-race volume in the final 10–15 minutes, consistent with the 65% show figure, but pin this with Betfair historical data (which the project already plans to buy) rather than a citation.*

---

## 3. Price decay after tips: the core constraint on the product promise

This is the best-documented and most alarming part of the research. Three independent sources quantify it.

### 3.1 Hugh Taylor (At The Races) — the canonical case

Honest Betting Reviews' long trial of Hugh Taylor's free daily tips ("Hugh Taylor Tips – Final Review", 26 Dec 2015, https://www.honestbettingreviews.com/hugh-taylor-tips/):

- "**Within a minute or two of the tips being given out the prices have been smashed in.**"
- Average advised price over the trial: **10.41**; average price actually obtainable: **7.35** — a ~29% haircut on decimal odds.
- Results at advised prices: +9 pts, 15% strike rate, 6% ROI — i.e. the entire paper edge lived inside the price the followers destroyed.
- Tips "aren't given out at the same time every day so you have to be quite watchful" (they appear on the ATR site mid-morning).

Geegeez' commentary on the same phenomenon ("The Ups and Downs of Tipping Services", https://www.geegeez.co.uk/the-ups-and-downs-of-tipping-services/): Taylor "makes his picks on the morning of the racing"; "the prices, often only available in one place, **evaporate in seconds**"; a reader reports a bet "accepted … @ 25 … but when checked on open bets odds got only 18"; and sustained backing of his picks means "your betting accounts very quickly get marked and then restricted". The author's conclusion — headline results are "published for academic purposes only" — is exactly the trap the app's "value vs available odds" claim must avoid.

### 3.2 Smart Betting Club odds-tracking (quantified decay curves)

- "Have You Fallen Into This Tipster 'Advised Odds' Trap?" (SBC blog, 19 Sep 2014, https://smartbettingclub.com/blog/fallen-tipster-advised-odds-trap/): betting **immediately** on release costs only "a small reduction in profitability … (1-2%)", but "if betting later in the morning … prices are seen to drop by an average of **6-8%**". Concrete examples: a selection "advertised … at 20/1" where "the best price overall is now 12/1"; another "tipped at 8s but you could only get on at 5s".
- "Odds Availability & How It Impacts Your Real-World Betting Profits, Part 2" (SBC blog, 30 Jan 2020, https://smartbettingclub.com/blog/judging-a-tipster-by-odds-part2/): SBC tracked prices for "a minimum of 15 minutes" after each service's release. Per-service ROI impact of taking the 15-minute-later price instead of the advised price ranged from **+2% / +2.5%** (two services whose prices drift — typically longer-odds, exchange-friendly picks) through **−0.5%**, **−4.5%** (−£1,020 on the year), **−10.82%** (turning +£982 into −£1,490), to **−24.5%** for a service with "completely unrealistic odds" (+£2,688 on paper → −£307 real).

### 3.3 Pricewise and the academic record

- Racing Post's Pricewise (Tom Segal) remains the reference case of a tipster who moves national markets; the Post now releases his Saturday selections **the day before**: Friday-dated articles such as "Tom Segal has opened up with a 7-2 winner and has more tips for Saturday's racing" (Racing Post, Fri 17 Jul 2026) and "Tom Segal has an 8-1 winner at Glorious Goodwood on Saturday – find out his two tips…" (Racing Post, Fri 31 Jul 2026) (headlines via Google News RSS). *Flag: the exact hour of Pricewise release (historically 8.30am Saturday, moved earlier for digital members) could not be verified from a fetchable page.*
- Academic treatment: B. Deschamps & O. Gergaud, "Efficiency in Horse Race Betting Markets: The Role of Professional Tipsters", in the *Handbook of Sports and Lottery Markets* (2008), DOI 10.1016/B978-044450744-0.50019-6 — evidence that professional tipsters' information is rapidly incorporated into bookmaker odds.

### 3.4 What this means for follower counts and member caps

- *Flag: no published threshold of "N followers moves an Irish midweek market" was found — nobody publishes this.* The qualitative evidence is consistent: ordinary Irish midweek races are priced defensively at small limits until mid-morning (Keenan), so even low-hundreds of followers taking £10–£50 each at one or two firms will trigger cuts within minutes (the SBC/HBR observations above were generated by subscriber bases in the hundreds-to-low-thousands). UK Saturday handicaps (ITV races) absorb far more before moving — that is precisely why Pricewise can still exist there.
- Member caps/staggered release: SBC's odds-tracking articles recommend betting "promptly after tips release", and the trade norm is that serious paid services either cap membership or push members to Betfair SP; however, *specific named member-cap examples could not be verified this session* (SBC's membership-cap case studies sit behind its paywall). Treat "cap subscribers, randomize/stagger release, or advise to BSP/exchange" as an industry-standard mitigation with anecdotal rather than cited support.

---

## 4. Non-runners, Rule 4 and going instability

### 4.1 Britain — hard numbers

BHA, "Major measures to tackle non-runners announced" (16 Aug 2017, https://www.britishhorseracing.com/press_releases/major-measures-tackle-non-runners-announced/) — the most recent public aggregate found:

| Year | Jump | Flat turf | Flat AW | Total |
|------|------|-----------|---------|-------|
| 2012 | 7.50% | 11.43% | 7.48% | 9.13% |
| 2013 | 7.36% | 10.31% | 8.06% | 8.73% |
| 2014 | 6.71% | 10.86% | 7.21% | 8.58% |
| 2015 | 6.50% | 10.44% | 6.37% | 8.13% |
| 2016 | 7.56% | 10.59% | 6.55% | 8.56% |

Reasons per year (2012–16): going-related ~2,800–3,400; self-certificates ~2,900–3,850; vet certificates ~1,000; other ~850–1,000. Note the inversion of intuition: **Flat turf has the *highest* NR rate — because its 48-hour declaration window leaves two days for the ground to change** — which is exactly the exposure a 48-hr-based Irish service inherits across the board. The 2017 measures included publishing trainer NR-rate tables and raising fines for withdrawals "after 9am" on race day — making ~9am the natural GB cut-off before which most non-going NRs surface.

Separately, a rule letting stewards declare a horse denied a fair start a non-runner took effect 1 May 2024, was extended to Jumps in 2025 (BHA, 24 Sep 2025), and had been applied six times in 2026 by June (BHA blog "Non-runners at the start", 8 Jun 2026, https://www.britishhorseracing.com/non-runners-at-the-start/) — a settlement edge-case for bet tracking, not a pricing issue.

### 4.2 Ireland

- Withdrawals must be notified ≥90 minutes before the FIRST race (Rule 194(iii)(a)); late withdrawal fines €200/€320+ (IHRB non-runners page). Irish going reports are published on the IHRB ground-reports page (https://www.ihrb.ie/ground-reports/).
- **Reserves**: up to 3 per oversubscribed race, on the card in priority order, declared in by 10am (Nov–Jan) / 11am (rest of year) on race day — a uniquely Irish source of morning field churn the model must re-score for.
- *Flag: no published aggregate Irish non-runner percentage was found (IHRB monthly integrity statistics cover fixtures, runners, enquiries, samples — not NR rates: https://www.ihrb.ie/monthly-integrity-statistics/). Assume GB-like or slightly higher rates given the universal 48-hr window; measurable from the app's own data within weeks.*

### 4.3 Rule 4 and practical handling

Any priced bet whose race subsequently loses a runner suffers a Tattersalls Rule 4 deduction scaled to the withdrawn horse's price. *Flag: no published statistics on Rule 4 frequency were found — no regulator or bookmaker publishes them.* A defensible internal estimate: with ~8–9% of declared runners scratching and ~10-runner fields, a majority of race-morning-priced races experience at least one withdrawal between morning price and off on soft-going days, and a substantial minority on normal days; deductions only bite when the NR is short-priced. Daily-picks services handle this by (a) publishing after the bulk of morning withdrawals are known (post-9am GB, post-10/11am Irish reserves), (b) quoting BOG bookmakers so going-driven price surges are captured, and (c) settling advice records "with a run" / applying Rule 4 to claimed results.

---

## 5. What time comparable services actually publish

| Service | Stated publish time | Source |
|---|---|---|
| myracing (free, large audience) | "Our tips are updated at **8.45am** every day"; evening-racing bets added ~5pm | https://myracing.com/free-horse-racing-tips/ |
| HRI's own racing tips (RÁS site) | "Racing tips will be available **before 10.30am** on racedays" | https://www.hri-ras.ie/ |
| Hugh Taylor (At The Races) | Morning of racing, deliberately variable time (~10am era) | HBR review (26 Dec 2015); Geegeez "Ups and Downs" |
| Geegeez Stat of the Day (ran 2011–Sep 2020) | "published **tea time the night before** racing" | https://www.geegeez.co.uk/the-ups-and-downs-of-tipping-services/ |
| Racing Post / Tom Segal (Pricewise) Saturday | Released **the day before** (Friday) online | Racing Post Friday-dated articles, 17 & 31 Jul 2026 (via Google News) |
| Timeform daily tips / OLBG hot tips | No fixed published release time found — *flagged unverified*; OLBG tips accrete from member submissions rather than dropping at one time | timeform.com/horse-racing/tips; olbg.com |

The revealed pattern: **mass-market free services publish 8:45–10:30am on race day** (after BOG starts, after morning re-pricing, before lunchtime); evening-before publication is used either by form-stats products that don't quote prices (Stat of the Day) or by tipsters whose market impact is so large that bookmakers reprice around them anyway (Pricewise).

---

## 6. Recommended publish window (with reasoning)

**Primary recommendation: publish at 9:00–9:30am Irish time on race day**, with prices snapshotted at publish time and each pick tagged "BOG-protected at [bookmakers]".

1. **Everything is known.** Irish fields + riders final since 10am two days prior; GB Flat likewise; GB jumps since 10am the day before. Overnight vendor files (7:30pm) allow full model scoring the previous evening — publishing at 9am is a *choice about price availability, not data availability*.
2. **BOG is live.** Most BOG concessions start 8:00–9:00am race day (ThePuntersPage). Publishing before 8am strips subscribers of BOG on early bets; 9:00am+ means every advised price is a floor at BOG firms.
3. **Morning books are formed but not yet efficient.** By ~9am the "obvious ricks" are gone but overrounds are still coming in and the pro-tipster wave (9:30am, per Keenan) hasn't fully landed — this is the widest window where a real price exists at meaningful (if modest) limits.
4. **Non-runner exposure is reduced.** GB self-cert withdrawals cluster before the 9am fine threshold; Irish reserves resolve by 10/11am. A 9:00–9:30 release with an automated 10:15am "NR update" message (re-scored without withdrawals, Irish reserves resolved) covers the residue.
5. **Anti-decay design is mandatory, not optional.** The evidence in §3 says advised-price claims die within minutes at scale. Mitigations to build in from day one: quote a *price range* and Betfair SP expectation rather than a single price; track and publish "price 15 minutes after release" (the SBC metric) as the honest performance line; consider staggering or capping paid-tier membership as the base grows; prefer selections whose value survives at BSP (SBC found BSP-robust services keep +17–37% ROI at exchange SP, e.g. https://smartbettingclub.com/blog/hanbury-racing-bookmakers-betfair-sp/).
6. **Optional evening tier.** A 8–9pm "tomorrow shortlist" (post-7:30pm final racecards) with model ratings but *no advertised prices* serves engaged users without making price promises the overnight market can't honour, and mirrors Stat of the Day/Pricewise precedent.

**Betfair quoting rule:** before ~11am treat exchange prices on ordinary IRE/UK races as reference marks only; advise exchange execution either near the off or at BSP.

---

## 7. Pipeline cost and latency

**Workload sizing.** GB 2026: **1,458 scheduled fixtures + 52 Premier Racedays** (BHA, 6 Aug 2025, https://www.britishhorseracing.com/press_releases/bha-publishes-2026-fixture-list/) → ~28 races/day GB average at ~7 races/fixture. Ireland: **~390 fixtures/yr** and average field **11.51 runners** (HRI Factbook 2025, https://www.hri.ie/ — Ireland runs ~2,700 races/yr) → 1–3 Irish meetings most days. Combined: **typically 35–60 races and 350–650 runners per day**, peaking on summer Saturdays/bank holidays.

**Compute.** Scoring 650 runners with a trained GBDT (LightGBM/XGBoost) is sub-second; feature building from a local DB is seconds-to-minutes; a full retrain on ~10 years of UK+IRE form (order 1M runner-rows × a few hundred features) runs in minutes on a 4-vCPU box. Benchmark instance: AWS c7i.xlarge (4 vCPU, 8 GiB) at **$0.179/hr on-demand US-East** (https://instances.vantage.sh/aws/ec2/c7i.xlarge). A daily 1-hour pipeline ≈ **$5.50/month**; a small always-on VPS (needed anyway for the 3-minute odds poller) runs €5–15/month (Hetzner/OVH class — *exact EUR price not verified this session*; the pricing page needed its JS calculator). Odds polling at 3-minute resolution for one day's cards is a few thousand small API calls/day — negligible bandwidth. Practical schedule: 19:45 ingest final racecards → 20:00 score + build shortlist → 06:00 refresh odds + rescore → 08:55 final value screen vs live odds → 09:00–09:30 publish → 10:15 NR/reserve update → results ingest post-racing.

**Practitioner architectures (citable patterns):**
- Betfair's official "How to Automate" tutorial series (parts 1–5) automates a daily thoroughbred ratings strategy with the **Flumine** framework: ratings CSV fetched by date each morning from a hub endpoint, a BackgroundWorker polling every 60s, bets placed when "seconds_to_start < 60", auto-shutdown after the day's markets close (https://betfair-datascientists.github.io/tutorials/How_to_Automate_3/). The same site hosts "Back testing ratings in Python" and "Golden rules of automation".
- Public GitHub example of exactly this product shape: **AChow906/racing_model** (created Apr 2026) — "Python ML Horse Racing value finder: Predicts win probabilities and compares to Betfair SP to surface value bets, posted to Discord" (https://github.com/AChow906/racing_model).

---

## 8. Flagged gaps / could not verify

1. Current one-line official confirmation that GB jumps declare at the 24-hour stage (inferred from BHA Cheltenham-exception release + practice). Confirm via rules.britishhorseracing.com.
2. Exact clock time of the Irish rider-nomination deadline (administrative, not printed in the rulebook).
3. A quantitative Betfair matched-volume-by-minutes-to-off curve for UK/IRE racing (buyable from Betfair Historical Data; folklore + Keenan's 65%-at-the-show is the best public proxy).
4. Exact current Pricewise release hour; Timeform/OLBG fixed release times.
5. Aggregate Irish non-runner rate; any Rule 4 frequency statistics (nobody publishes either).
6. Named examples of tipster member caps with numbers (industry practice, but the concrete cases sit behind SBC's paywall).
7. GB non-runner aggregates newer than 2016 (BHA now publishes per-trainer tables rather than headline rates).
8. Several sources are dated (Keenan 2018; HBR 2015; SBC 2014/2020) — structures described are stable but firm-level details (which bookmaker prices first, BOG hours per firm) should be re-verified against current bookmaker T&Cs at build time.

---

## Sources

- IHRB Rules of Racing (Master Rulebook PDF, as amended 26 Apr 2024) — via https://www.ihrb.ie/regulation-integrity/ (Rules 190, 194, 195, Regulation R3)
- IHRB non-runners page — https://www.ihrb.ie/non-runners-landing-page/
- IHRB monthly integrity statistics — https://www.ihrb.ie/monthly-integrity-statistics/ ; ground reports — https://www.ihrb.ie/ground-reports/
- HRI RÁS (notices; declarations close 10:00) — https://www.hri-ras.ie/ and https://status.hri-ras.ie/declaration-status.aspx (fetched 28 Aug 2026)
- Racing Post, "HRI reveals 48-hour declarations will remain permanent in Irish racing", 9 Sep 2021 (headline via Google News RSS)
- BHA press releases: 48-hour declarations statement (9 Jun 2006); AW trial (15 Oct 2003); Cheltenham 48-hr (12 Sep 2017); Resumption update – 48-hour declarations (17 Jun 2020); Transparent declaration tracking (10 Mar 2023); Major measures to tackle non-runners (16 Aug 2017); NR-at-start rule change (25 Apr 2024, 24 Sep 2025); blog "Non-runners at the start" (8 Jun 2026); 2026 fixture list (6 Aug 2025) — all at https://www.britishhorseracing.com/
- Sporting Life / Racing TV, "Epsom ushers in 72-hour declarations for the Derby", 5 May 2025 (headlines via Google News RSS)
- Betwise Smartform — https://www.betwise.co.uk/smartform
- The Racing API FAQ — https://www.theracingapi.com/
- Tony Keenan, "Watching the Markets", Geegeez, 10 Sep 2018 — https://www.geegeez.co.uk/tony-keenan-watching-the-markets/
- ThePuntersPage, Best Odds Guaranteed guide — https://www.thepunterspage.com/best-odds-guaranteed/
- Honest Betting Reviews, "Hugh Taylor Tips – Final Review", 26 Dec 2015 — https://www.honestbettingreviews.com/hugh-taylor-tips/
- Geegeez, "The Ups and Downs of Tipping Services" — https://www.geegeez.co.uk/the-ups-and-downs-of-tipping-services/
- Smart Betting Club blog: "Advised Odds Trap" (19 Sep 2014) — https://smartbettingclub.com/blog/fallen-tipster-advised-odds-trap/ ; "Odds Availability Part 2" (30 Jan 2020) — https://smartbettingclub.com/blog/judging-a-tipster-by-odds-part2/ ; Hanbury Racing BSP comparison (24 Apr 2022) — https://smartbettingclub.com/blog/hanbury-racing-bookmakers-betfair-sp/
- Deschamps & Gergaud (2008), "Efficiency in Horse Race Betting Markets: The Role of Professional Tipsters", Handbook of Sports and Lottery Markets, DOI 10.1016/B978-044450744-0.50019-6 (via Crossref/Semantic Scholar)
- Racing Post Segal/Pricewise Friday-release headlines, Jul 2026 (via Google News RSS)
- myracing free tips page — https://myracing.com/free-horse-racing-tips/
- HRI Factbook 2025 (fixtures ~390/yr; avg field 11.51) — via https://www.hri.ie/
- Betfair (AU) automation tutorials — https://betfair-datascientists.github.io/tutorials/How_to_Automate_3/
- AWS c7i.xlarge pricing — https://instances.vantage.sh/aws/ec2/c7i.xlarge
- AChow906/racing_model (GitHub, Apr 2026) — https://github.com/AChow906/racing_model
- Grand National five-day stage — grandnationalfans.co.uk headline, 31 Mar 2025 (via Google News RSS)
