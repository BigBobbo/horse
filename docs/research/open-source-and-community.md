# Open-Source Projects, Datasets, and Communities for Horse-Racing Prediction & Betting Automation (UK/Ireland focus)

*Research date: 2026-08-28. Focus: Ireland first, UK second. All GitHub star/fork/activity figures were pulled live from the GitHub API on this date; web sources were fetched directly where noted. Items that could not be verified are flagged explicitly.*

---

## Key takeaways

- **The open-source ecosystem for horse racing is an order of magnitude larger than for greyhounds.** GitHub holds ~2,713 repos matching "horse racing" vs 54 matching "greyhound racing"; the Bet Angel trading forum has 81,549 posts on horse racing vs 4,731 on greyhounds (17x). The pivot rationale is strongly supported by the community/tooling evidence.
- **The core betting-automation stack is mature, MIT-licensed, and actively maintained**: `betfairlightweight` (513★, updated Aug 2026) for the Betfair Exchange API and `flumine` (242★, updated Aug 2026) as a full trading/backtesting framework with paper-trading and historical simulation modes. Both are maintained under the betcode-org umbrella.
- **The canonical free Racing Post scraper, `joenano/rpscrape`, has been deleted from GitHub** (404 as of 2026-08-28; no DMCA notice on record in github/dmca). Its fork network survives — `robinhowlett/rpscrape` is now the network parent (84 forks) and still documents scraping of GB **and Irish** results (flat + jumps). Legal/ToS fragility of RP scraping is the single biggest data-supply risk on the free path.
- **Kaggle has one genuinely useful UK+Ireland dataset** (hwaitt "Horse Racing": 1990–2020, 759.73 MB, 63 files, includes RPR/TR/OR ratings and Oddschecker odds) — but it is licensed **CC BY-NC 4.0 (non-commercial)** and **ends in 2020**, so it is a prototyping/backtest resource, not a production feed.
- **Betfair's own ecosystem is the strongest free resource**: the Automation Hub (betfair-datascientists.github.io) with end-to-end automation/backtesting tutorials, the Historic Data site (nearly all Exchange markets since 2016; Basic tier free), the betfair-down-under GitHub org, a developer forum, and the invite-only "Betfair Quants" Discord for model builders.
- **Ireland-specific open-source is thin but Ireland is not orphaned**: almost every serious UK project (rpscrape lineage, Smartform, Kaggle hwaitt, The Racing API, Betfair markets) covers IRE as a first-class region alongside GB. There is no meaningful Irish-only OSS project.
- **Practitioner consensus (Betfair's "Golden Rules of Automation" and forum lore)**: the common failure modes are data leakage, overfitting, and unrealistic backtests that ignore fill bias ("losing bets are more likely to be filled and winning bets go unmatched"). Value-vs-odds logic and staking discipline matter as much as the model.

---

## 1. GitHub: the significant repositories

### 1.1 Core Betfair automation stack (betcode-org)

| Repo | What it does | Stars / forks | Last activity | Licence |
|---|---|---|---|---|
| [betcode-org/betfair](https://github.com/betcode-org/betfair) (**betfairlightweight**) | Python wrapper for Betfair Exchange API-NG incl. market/order **streaming** | 513★ / 154 forks | updated 2026-08-20 (active) | MIT ([LICENSE](https://raw.githubusercontent.com/betcode-org/betfair/master/LICENSE)) |
| [betcode-org/flumine](https://github.com/betcode-org/flumine) | Event-based betting **trading framework**: strategies, order management, paper trading, **historical simulation/backtesting**; clients for Betfair, BETDAQ, BetConnect (topics also list Matchbook, Smarkets, Polymarket, Kalshi) | 242★ / 66 forks | updated 2026-08-21 (active) | MIT ([LICENSE](https://raw.githubusercontent.com/betcode-org/flumine/master/LICENSE)) |
| [betcode-org/betconnect](https://github.com/betcode-org/betconnect) | BetConnect API client | 7★ | Oct 2025 | — |
| [betcode-org/betdaq-retail](https://github.com/betcode-org/betdaq-retail) | BETDAQ retail API wrapper | 2★ | Mar 2026 | — |

Flumine requires Python 3.10+, is installed via `pip install flumine`, and its docs explicitly cover simulation of multiple markets per event and paper-trading mode ([docs](https://betcode-org.github.io/flumine/)). This pair is the de-facto standard: it is what the Betfair Automation Hub's own "How to Automate" tutorial series builds on.

### 1.2 Official Betfair repos

- [betfair/API-NG-sample-code](https://github.com/betfair/API-NG-sample-code) — official snippets in many languages; 216★ / 554 forks, still being touched (Aug 2026).
- [betfair/stream-api-sample-code](https://github.com/betfair/stream-api-sample-code) — Exchange Stream API samples (C#/Java); 83★.
- [betfair/historic-data-workbook](https://github.com/betfair/historic-data-workbook) — Excel workbook for interpreting purchased historic data; 20★.

### 1.3 Horse-racing prediction repos (most-starred, from live GitHub search)

- [dominicplouffe/HorseRacingPrediction](https://github.com/dominicplouffe/HorseRacingPrediction) — SVR model for race results; **178★** / 55 forks (created 2017, still the most-starred "horse racing prediction" repo; 197 repos match that query in total).
- [dickreuter/betfair-horse-racing](https://github.com/dickreuter/betfair-horse-racing) — **121★** / 31 forks. The most complete open pipeline: collects Betfair prices (1/min pre-race, every 10s in-play) into MongoDB, engineers 28 features, trains a Keras NN with a custom returns-based loss to predict *payoff* (pricing inefficiency) rather than the winner, auto-places back/lay bets, Flask P&L dashboard. **Targets GB and IE markets.** No licence file; effectively dormant (README-era code, squashed history) — best treated as an architecture reference, not a dependency.
- [codeworks-data/mvp-horse-racing-prediction](https://github.com/codeworks-data/mvp-horse-racing-prediction) — HK racing ML, 64★.
- [Christy-Lo/Horse-Racing-Prediction](https://github.com/Christy-Lo/Horse-Racing-Prediction---Optimized-Gambling-Strategy) — HKJC random-forest project, 38★ (archived).
- [gotoConversion/goto_conversion](https://github.com/gotoConversion/goto_conversion) — **115★**; odds→probability conversion (de-vigging) library that has "powered $47,000 of Kaggle prize money"; directly relevant to the "perceived value vs available odds" leg of the app.
- [StefanBelo/BetfairAiTrading](https://github.com/StefanBelo/BetfairAiTrading) — 34★, MIT, active Feb 2026; a 2025-era community repo: 120+ AI analysis prompts, AI agents in Python/C#/TS/F#, **MCP integration with BFExplorer**, and horse racing as its most extensive sport (EV analysis, Timeform integration, dutching). Signal that the current (2025-26) hobbyist frontier is LLM-agent-assisted Betfair trading.
- Recent UK/IRE modelling pipelines (small but current, useful as reference implementations): [gmalbert/horse-racing-predictions](https://github.com/gmalbert/horse-racing-predictions) (9★, created Nov 2025, 508 commits, active into 2026 — see §5), [NuMetriq/horse-racing-ml](https://github.com/NuMetriq/horse-racing-ml) ("leakage-safe, time-aware ML pipeline… UK & Ireland", Jan 2026), [PhilippLetman/horse-racing-ml](https://github.com/PhilippLetman/horse-racing-ml) (UK/IRE flat, Oct 2025), [rjmac22/inside-rails-horse-racing](https://github.com/rjmac22/inside-rails-horse-racing) (UK/IE notebook-led DB project, Jul 2026).

### 1.4 rpscrape and Racing Post scrapers — status

- The canonical repo **`joenano/rpscrape` no longer exists**: direct fetch of https://github.com/joenano/rpscrape returns **HTTP 404** (verified 2026-08-28). The `joenano` user account still exists.
- A code search of GitHub's public DMCA-notice repository (`github/dmca`) for "rpscrape" returns **0 results**, so there is **no public evidence of a DMCA takedown** — deletion or privatisation by the author is the more likely explanation. Reason **could not be verified**.
- The fork network survives. [robinhowlett/rpscrape](https://github.com/robinhowlett/rpscrape) (created 2018-12-03, i.e. the era of the original; now 5★ but **84 forks** attached, updated Aug 2026) is the promoted network parent. Its README describes scraping horse-racing results to CSV for regions including **Ireland**, GB, France, Hong Kong, UAE, flat and jumps, per-course (Ascot, York, Aintree…), Python 3.6+, interactive `[region/course] [year/range] [flat/jumps]` CLI.
- Other RP-adjacent scrapers are tiny (≤1★ each): [dakiquang/Racing-Post-Scraper](https://github.com/dakiquang/Racing-Post-Scraper), [rbdog123/racing-post-scraper](https://github.com/rbdog123/racing-post-scraper), [aranej/bf_rpscrape](https://github.com/aranej/bf_rpscrape) (Dec 2025, joins RP data to Betfair), [sovdevs/rpscrape-raceday-actor](https://github.com/sovdevs/rpscrape-raceday-actor) (Apify actor wrapping rpscrape for **today's racecards**, Sep 2025).
- **Takeaway:** free RP-derived results data is still obtainable via maintained forks, but the upstream deletion demonstrates the fragility of building a product on scraping Racing Post (ToS risk). Budget for a licensed feed (Smartform, The Racing API — see §5) as the production path.

### 1.5 Ireland-specific repos

Nothing substantial exists that is *Irish-only*; Ireland rides along with UK projects:

- [adamcorren/horse_racing_data_analyzer](https://github.com/adamcorren/horse_racing_data_analyzer) — 6★; combines bookmaker, exchange and live hourly **UK and Ireland** odds into daily CSVs.
- [caffreit/Horse-SP-Scraper](https://github.com/caffreit/Horse-SP-Scraper) — scrapes **Irish** starting prices (stale, 2016).
- [smkirwan77/web_scraper](https://github.com/smkirwan77/web_scraper) — At The Races + Racing Post daily runner data for **UK or IRE** (archived 2024).
- GitHub search "horse racing ireland" returns only 12 repos total, most ≤6★.

---

## 2. Kaggle and open datasets

### 2.1 UK + Ireland: hwaitt "Horse Racing" (the key free dataset)

[kaggle.com/datasets/hwaitt/horse-racing](https://www.kaggle.com/datasets/hwaitt/horse-racing) — verified via full page fetch:

- Coverage: **UK and Ireland, 1990–2020** (Irish courses such as Limerick and Dundalk present).
- Size/shape: **759.73 MB**, **63 files** — `races_YYYY.csv` + `horses_YYYY.csv` per year, plus `forward.csv` (6.36 MB) of pre-race data with **Oddschecker odds** (~33,700 entries in preview).
- Fields: race id/course/date/class/distance/going/prize/winning time/country; runner age, draw, decimal odds, favourite flag, trainer, jockey, position, weight, **RPR, TR (Topspeed), OR ratings**, pedigree.
- Engagement: usability **8.82**, 38.5K views, **6,059 downloads**, 9 comments.
- **Licence: CC BY-NC 4.0 — commercial use prohibited.** Last updated ~6 years ago; **data ends late 2020 → stale**. Ideal for prototyping features/backtests; cannot be the production feed for a commercial app either legally or practically.

### 2.2 Hong Kong: gdaley "Horse Racing in HK"

[kaggle.com/datasets/gdaley/hkracing](https://www.kaggle.com/datasets/gdaley/hkracing) — two CSVs, `races.csv` and `runs.csv`, with venue, distance, going, **sectional times/positions**, dividends, horse ratings, weights, draw and odds; dates deliberately obscured (relative gaps preserved), horse/jockey names removed. Row counts are not stated on the page (community folklore says ~6.3k races / ~79k runs — **could not verify** this session). Old but the best free dataset for practising sectional-time features (HK data quality > UK/IRE public data).

### 2.3 US tracking data: Kaggle "Big Data Derby 2022"

[kaggle.com/competitions/big-data-derby-2022](https://www.kaggle.com/competitions/big-data-derby-2022) — organised by **NYRA + NYTHA**; **$50,000 prize pool** ($20k first, 3 × $10k); ran **2022-08-11 → 2022-11-10**; **9,349 entrants**; released never-before-public **X/Y coordinate tracking data** plus race metadata. Relevance: proof that granular tracking/sectional data exists and is analytically rich — but nothing equivalent is open for UK/IRE (UK sectionals are commercial via Total Performance Data; Irish sectional coverage is patchier still).

### 2.4 Betfair open data

- The **Automation Hub data listing** ([betfair-datascientists.github.io/data/dataListing/](https://betfair-datascientists.github.io/data/dataListing/)) offers free monthly **CSV/ZIP** files — but **only for markets taking place in Australia/NZ** (thoroughbred/harness/greyhound 2020–2026, plus ANZ sports). It does include Betfair's **UK/Ireland thoroughbred *model ratings* results 2024–2026**, not raw UK/IE market files.
- The **Betfair Historic Data site** (historicdata.betfair.com; site itself returned 403 to this environment — details verified via the Hub's guide [usingHistoricDataSite](https://betfair-datascientists.github.io/data/usingHistoricDataSite/)): nearly **all Exchange markets since 2016**, TAR archives of bz2 JSON stream files, three tiers — **Basic: 1-minute last-traded-price, free; Advanced: 1-second, top-3 ladder + volume, paid; Pro: 50ms full ladder, paid**. Free samples per tier exist; ANZ customers are told to email automation@betfair.com.au before purchasing (they routinely comp data for ANZ-market modellers). **Exact GBP prices could not be verified this session** (site blocked). The Hub homepage cites **~1.5TB** of raw/pre-processed JSON market data.
- Parsing that data is a solved problem in OSS: [tarb/betfair_data](https://github.com/tarb/betfair_data) (47★, Rust-speed Python parser), [mzaja/betfair-database](https://github.com/mzaja/betfair-database) (12★, turns file dumps into a queryable SQL DB), [mberk/betfairutil](https://github.com/mberk/betfairutil) (37★) and [mberk/betfairviz](https://github.com/mberk/betfairviz) (40★, order-book visualisation), [johntelforduk/betfair-data-analysis](https://github.com/johntelforduk/betfair-data-analysis) (20★, PySpark).

---

## 3. Betfair developer ecosystem

- **Automation Hub** — [betfair-datascientists.github.io](https://betfair-datascientists.github.io/) (source repo has 63★, updated 2026-08-28). Sections: Getting Started (staking methods, value & odds, commission), Betfair Data (JSON→CSV tutorials, TAR processing), API (cert login, Python & R tutorials), Modelling, Automation & Backtesting, Mental Game. Betfair states it "welcomes and supports winning clients."
- **Key tutorials for this project**: the five-part **"How to Automate" series**, **backtestingRatingsTutorial** (backtesting a ratings set against Exchange prices), **flumineSimulations**, **analysingAndPredictingBSP**, **automatedBettingAnglesTutorial**, plus greyhound modelling tutorials (FastTrack/Topaz) that translate directly to horses ([sitemap](https://betfair-datascientists.github.io/sitemap.xml)).
- **betfair-down-under GitHub org** — ANZ community org with sample code, the [AwesomeBetfair](https://github.com/betfair-down-under/AwesomeBetfair) curated list (37★, MIT: wrappers by language incl. Go `bfapi`, R `abettor` (56★), historic-data tools, backtesting frameworks) and a knowledgeShare repo.
- **Developer forum** — [forum.developer.betfair.com](https://forum.developer.betfair.com/) (fetch returned 403 to this environment, but it is referenced as live from the Hub's [apiResources page](https://betfair-datascientists.github.io/api/apiResources/)).
- **Betfair Quants Discord** — invite-only community "for people interested in modelling and automation", access via Microsoft Form: https://forms.office.com/r/ZG9ea1xQj1 (linked from the Hub). This is the highest-signal community for model builders.
- API visualiser web tools, Atlassian dev docs and a support knowledge base round it out.

---

## 4. Communities & practitioner sentiment

### 4.1 Quantified forums (fetched 2026-08-28)

- **Bet Angel forum** ([forum.betangel.com](https://forum.betangel.com/)) — **38,573 members, 28,290 topics, 380,124 posts**; 242 users online at fetch time; posts dated same-day. Board breakdown: **Horse racing 3,407 topics / 81,549 posts** (the most active market board); **Automation 5,526 topics / 29,938 posts**; shared automation files 316 topics / 10,265 posts; **Greyhound racing just 207 topics / 4,731 posts**. This is the single best like-for-like measure of horse-vs-greyhound practitioner attention: **~17x more posts on horses**.
- **Betfair Community forum** (community.betfair.com) — returned 403; activity level **could not be verified** this session.
- **Reddit r/horseracing** — Reddit is blocked from this environment; member counts and thread content **could not be verified** this session. (It exists and carries betting/model threads, but treat any size figure as unverified.)
- **Racing Post forum** — status **could not be verified** this session; do not plan around it.

### 4.2 Paid/curated communities

- **Smart Betting Club** ([smartbettingclub.com](https://smartbettingclub.com/)) — independent tipster-review service: monthly magazine, Tipster Profit Reports, 19+ years of archives, 90-day money-back on annual membership. Exact GBP pricing was not displayed on the fetched page — **could not verify current prices**. Useful as market intelligence (what edges tipsters actually sustain), not as a data source.
- **Geegeez Gold** ([geegeez.co.uk](https://www.geegeez.co.uk/)) — UK **and Irish** racecards, formbook, pace maps, draw analysis, Query Tool over 15+ years of form data, 20 winner-finding reports; **30-day trial for £1**; ongoing subscription price not shown on fetched pages (**could not verify**; claims "98% of Gold subscribers think it offers value").
- **BFExplorer / Bfexplorer BOT SDK** ([StefanBelo/Bfexplorer-BOT-SDK](https://github.com/StefanBelo/Bfexplorer-BOT-SDK), 5★) plus the active [BetfairAiTrading](https://github.com/StefanBelo/BetfairAiTrading) community (34★, weekly community reports) — the 2025-26 face of hobbyist Betfair botting, now heavily AI-agent flavoured.

### 4.3 What practitioners say about building your own model (2025-26)

From Betfair's own ["10 Golden Rules of Automation"](https://betfair-datascientists.github.io/tutorials/goldenRulesOfAutomation/) and the Hub's [How to Model](https://betfair-datascientists.github.io/modelling/howToModel/) guidance — the closest thing to codified community consensus:

1. **Data leakage is failure mode #1** — never use anything unknowable at bet time (final BSP, post-race stats).
2. **Overfitting is #2** — validate on truly unseen seasons; prefer simple explainable rules.
3. **Backtests lie unless you model fill bias**: "losing bets are more likely to be filled and winning bets go unmatched" — apply slippage/fill haircuts to simulated Exchange results.
4. Staking (flat vs Kelly vs proportional) and bankroll guards matter as much as model AUC.
5. Treat the bot as an engineering project: logging, error handling at market/bet/account level, no emotional tinkering in drawdowns.
6. Recommended path: Python or R → Betfair historical data → ranking/regression/ML tutorials → start simple.

A concrete cautionary reference point from the recent OSS crop: [gmalbert/horse-racing-predictions](https://github.com/gmalbert/horse-racing-predictions) reports **88.7% training accuracy but 0.671 ROC AUC** on 245,298 UK races (2015-2025) with 75 XGBoost features — i.e. even a diligent, automated, retrained-weekly pipeline sits in the "modest discrimination" zone where profitability depends entirely on odds-relative value filtering, which matches the community's standard warning that beating the SP/BSP market blend is the actual bar.

---

## 5. Adjacent tooling

- **Backtesting**: flumine's built-in market simulation + paper trading ([docs](https://betcode-org.github.io/flumine/)); Hub tutorials `backtestingRatingsTutorial` and `flumineSimulations`; [meister245/betfair-bookrunner](https://github.com/meister245/betfair-bookrunner) (odds recording + backtesting, archived). There is **no popular standalone "betting backtester" library** outside the flumine ecosystem — plan to build backtesting on flumine + Betfair historic files.
- **Odds scraping**: [Sowul/liveodds](https://github.com/Sowul/liveodds) (5★ — live **UK/IRE** horse odds API, same author lineage as the rpscrape world); 69 repos match "oddschecker", top ones 10-14★ and mostly 2017-2022 vintage Selenium scrapers ([mgirkins/Bet-arbitrage-finder](https://github.com/mgirkins/Bet-arbitrage-finder) 14★, [ChamRoshi/Oddschecker-Scraper](https://github.com/ChamRoshi/Oddschecker-Scraper) 13★, [GrovesD2/oddschecker_scraper](https://github.com/GrovesD2/oddschecker_scraper) 10★). Fragile; Oddschecker actively obfuscates. For the app's "value vs odds" leg, Betfair's own API is the robust free odds source; The Odds API has a 500-calls/month free tier (used by gmalbert).
- **Odds→probability / de-vig**: [goto_conversion](https://github.com/gotoConversion/goto_conversion) (115★) implements Shin/power methods — directly usable for converting bookmaker odds into fair probabilities.
- **Staking**: no dominant OSS staking library exists — Kelly implementations are all micro-repos (≤4★, e.g. [rjpeacock/kelly-cli](https://github.com/rjpeacock/kelly-cli)). Expect to implement fractional Kelly in-house (trivial) and follow the Hub's [staking methods](https://betfair-datascientists.github.io/gettingStarted/stakingMethods/) guidance.
- **Structured UK+IRE form database (commercial but programmer-oriented)**: **Betwise Smartform** ([betwise.co.uk/smartform](https://www.betwise.co.uk/smartform)) — MySQL database of UK **and Irish** flat + NH racing, full results **since January 2003**, advance racecards delivered nightly at 19:30, Betfair ID lookup tables; **£195 initial purchase (first month included) then £65/month**. Has an R modelling ecosystem around it (e.g. [gillenpj/awracing](https://github.com/gillenpj/awracing), 2026). This is the standard "serious hobbyist → small commercial" data substrate for UK/IRE.
- **Timeform / Racing Post parsers**: **no significant open-source Timeform parser was found** (could not verify any repo of note); Timeform data is closed. RP parsing = the rpscrape lineage above.
- **Commercial APIs with OSS presence**: **The Racing API** — "complete coverage of UK, Irish and Hong Kong horse racing with real-time data updates every 3 minutes" (per its [API listing](https://github.com/api-evangelist/the-racing-api)); free tier of **500 calls/month** (as used by gmalbert's pipeline). The natural production replacement for RP scraping.

---

## 6. Horses vs greyhounds: what exists for horses that didn't for greyhounds

| Dimension | Horses (UK/IRE) | Greyhounds (UK/IRE) | Evidence |
|---|---|---|---|
| GitHub footprint | ~2,713 repos match "horse racing"; 197 match "horse racing prediction"; top prediction repo 178★ | 54 repos match "greyhound racing"; top UK-relevant repos ≤3★ | Live GitHub search, 2026-08-28 |
| Community attention | Bet Angel horse board: 3,407 topics / **81,549 posts** | Bet Angel greyhound board: 207 topics / **4,731 posts** (~17x less) | [forum.betangel.com](https://forum.betangel.com/) |
| Free historical dataset | Kaggle UK+IRE 1990–2020, 759.73 MB, with official ratings (RPR/TR/OR) and odds | No comparable UK/IRE greyhound dataset found (could not verify any) | [Kaggle hwaitt](https://www.kaggle.com/datasets/hwaitt/horse-racing) |
| Scraper ecosystem | rpscrape lineage (84-fork network) + ATR/RP/odds scrapers, Irish SP scraper | Scattered ≤3★ scrapers | GitHub searches above |
| Ratings industry | Racing Post RPR/Topspeed, Timeform, official OR (BHA/IHRB) — machine-readable via scrapers/Smartform | No equivalent published ratings depth for UK/IE greyhounds | §2.1, §5 |
| Licensed programmable DB | Smartform MySQL (UK+IRE, since 2003, £65/mo) | Nothing equivalent for UK/IE greyhounds | [Betwise](https://www.betwise.co.uk/smartform) |
| Commercial API w/ free tier | The Racing API (UK+IRE+HK, 3-min updates, 500 calls/mo free) | The user's original pain point: no equivalent | §5 |
| Sectionals / tracking | HK Kaggle dataset with sectionals; NYRA tracking competition data; UK sectionals commercially (TPD) | UK greyhound sectionals: nothing open | §2.2, §2.3 |
| Exchange data & liquidity tooling | Identical Betfair stack works for both — but horse markets are the most liquid and the Hub's automation tutorials centre on horse ratings | Betfair's best greyhound resources (Topaz API, FastTrack) are **ANZ-only** | [Automation Hub](https://betfair-datascientists.github.io/) |

**Verdict:** the pivot rationale is validated. The one caveat: Betfair's *free bulk CSV* data programme is ANZ-markets-only for both species; for UK/IE horse markets you use the (partly paid) Historic Data site or record your own stream.

---

## 7. Gaps and unverified items (explicit)

- **Could not verify** why `joenano/rpscrape` disappeared (no github/dmca record; author account intact).
- **Could not verify** current GBP pricing of Betfair Historic Data Advanced/Pro tiers (site 403 from this environment) or Smart Betting Club and Geegeez Gold ongoing subscription prices.
- **Could not verify** r/horseracing subscriber counts or thread content (Reddit blocked), Betfair Community forum activity (403), or Racing Post forum status.
- **Could not verify** exact race/run counts of the Kaggle HK dataset (page does not state them).
- Kaggle hwaitt dataset is **stale (ends 2020)**; any model trained on it needs a fresh-data plan before production.

---

## Sources

- https://github.com/betcode-org/betfair · https://github.com/betcode-org/flumine · https://betcode-org.github.io/flumine/ · https://raw.githubusercontent.com/betcode-org/betfair/master/LICENSE · https://raw.githubusercontent.com/betcode-org/flumine/master/LICENSE
- https://github.com/betfair/API-NG-sample-code · https://github.com/betfair/stream-api-sample-code · https://github.com/betfair/historic-data-workbook
- https://github.com/dickreuter/betfair-horse-racing · https://github.com/dominicplouffe/HorseRacingPrediction · https://github.com/gotoConversion/goto_conversion · https://github.com/StefanBelo/BetfairAiTrading · https://github.com/gmalbert/horse-racing-predictions · https://github.com/NuMetriq/horse-racing-ml
- https://github.com/robinhowlett/rpscrape · https://github.com/joenano/rpscrape (404) · https://github.com/github/dmca (search: 0 hits) · https://github.com/sovdevs/rpscrape-raceday-actor
- https://github.com/adamcorren/horse_racing_data_analyzer · https://github.com/caffreit/Horse-SP-Scraper · https://github.com/smkirwan77/web_scraper
- https://www.kaggle.com/datasets/hwaitt/horse-racing · https://www.kaggle.com/datasets/gdaley/hkracing · https://www.kaggle.com/competitions/big-data-derby-2022
- https://betfair-datascientists.github.io/ · https://betfair-datascientists.github.io/data/dataListing/ · https://betfair-datascientists.github.io/data/usingHistoricDataSite/ · https://betfair-datascientists.github.io/api/apiResources/ · https://betfair-datascientists.github.io/tutorials/goldenRulesOfAutomation/ · https://betfair-datascientists.github.io/modelling/howToModel/ · https://betfair-datascientists.github.io/sitemap.xml
- https://github.com/betfair-down-under/AwesomeBetfair · https://forms.office.com/r/ZG9ea1xQj1 (Betfair Quants Discord invite)
- https://forum.betangel.com/ · https://smartbettingclub.com/ · https://www.geegeez.co.uk/
- https://www.betwise.co.uk/smartform · https://github.com/api-evangelist/the-racing-api · https://github.com/Sowul/liveodds · https://github.com/mberk/betfairutil · https://github.com/mberk/betfairviz · https://github.com/tarb/betfair_data · https://github.com/mzaja/betfair-database
