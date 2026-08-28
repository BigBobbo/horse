# Irish Horse Racing Data Landscape — Feasibility Audit (August 2026)

Research date: 2026-08-28. Scope: every data source relevant to building a betting-suggestion app for Irish (and by extension UK) horse racing — daily racecards, 10+ years of historical results, ratings, sectionals, and odds. Prices verified 2025–2026 where possible; anything not directly verifiable is flagged.

## Key takeaways

- **Irish racing data feasibility is dramatically better than greyhounds.** Ireland and Great Britain form one integrated data market: the same vendors (Racing Post/Raceform, Timeform, Weatherbys, Betfair, The Racing API, Smartform, Proform) cover both jurisdictions in one product, and every serious hobbyist product treats "UK & Ireland" as a single coverage unit.
- **The single best developer on-ramp is The Racing API** (theracingapi.com): a documented REST API with a free tier and paid plans from £24.99/month, "complete coverage of UK, Irish and Hong Kong racing", ~55,430 Irish results spanning 2017–2026 in its core dataset, 20+ bookmaker odds on the Standard plan, and explicit permission to build apps/do ML — with resale of raw data and use by betting operators prohibited ([theracingapi.com](https://www.theracingapi.com/), [data coverage](https://www.theracingapi.com/data-coverage), [ToS](https://www.theracingapi.com/terms-of-service)).
- **Free deep history exists but is legally grey**: the open-source `rpscrape` tool scrapes Racing Post results/racecards for Irish courses back decades ([github.com/joenano/rpscrape](https://github.com/joenano/rpscrape)), and Kaggle hosts UK/Ireland results datasets covering 1988–2026 ([Kaggle](https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025)). Provenance is scraping; fine for private model training, not for redistribution.
- **Odds data is essentially solved and cheap via Betfair**: free daily CSVs of Betfair SP (win & place) for **GB and Irish races back to 28 May 2008** ([promo.betfair.com/betfairsp](https://promo.betfair.com/betfairsp/SP_history.html)); a free "Basic" tier on the Historical Data site (1-minute-interval prices); free *delayed* Exchange API key for development; **£499 one-off** for a live App Key (which cannot be used read-only) ([Betfair Developer support](https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access)).
- **Sectional/GPS data for Ireland became universal in 2024**: Coursetrack (RMG's timing partner, built on TPD technology) tracks **all races at all 26 Irish racecourses since 1 January 2024**, and the full RaceiQ metric suite plus sectionals is **free** on racingtv.com — but there is no public API; Irish sectional history is only ~2.5 years deep ([RMG](https://www.racecoursemediagroup.com/news/blog/coursetrack-tracking-data-hailed-by-irish-racecourses-after-successful-roll-out/), [Racing TV](https://www.racingtv.com/news/raceiq-data-now-freely-available-to-users-on-racingtv-com)).
- **Official bodies (HRI, Weatherbys, Tote Ireland) publish plenty for humans, nothing for machines**: HRI's results archive goes back to 1998 on the website with no API/export ([hri-ras.ie](https://www.hri-ras.ie/results/results-archive)); Weatherbys sells bespoke B2B feeds (pricing on application); the Tote Partner API (GraphQL, covers UK & Irish pools) requires a partner account.
- **Legal context favours the modeller**: the landmark ECJ case *British Horseracing Board v William Hill* (C-203/02, 9 Nov 2004) held that the sui generis database right does **not** protect officially created lists of runners and riders — the data itself is hard to monopolise, though site ToS and copyright in editorial content (e.g., Racing Post Ratings, Timeform ratings) still bind ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62002CJ0203), [5RB summary](https://www.5rb.com/case/british-horseracing-board-v-william-hill/)).
- **Realistic monthly cost**: €0–10 (budget/scrape+free-tier), ~€40–70 (mid: The Racing API paid plan + free Betfair data), ~€150–300 (pro: API Pro plan + Smartform or Proform + Betfair Advanced historic packs + Timeform Race Passes), plus one-off £499 if you want live Betfair prices via API.

---

## 1. Official / industry sources

### Horse Racing Ireland (HRI) and HRI RÁS
HRI is the commercial governing body for racing on the island of Ireland (all-island: includes Down Royal and Downpatrick in NI). Its public results service lives at hri.ie and hri-ras.ie ("RÁS" = Racing Administration System).

- **What's published**: race-by-race results, racecards, entries and declarations, fixtures, going reports. The **results archive is searchable back to 1998** by racecourse/year or by date ([hri-ras.ie results archive](https://www.hri-ras.ie/results/results-archive)).
- **Format**: website only. **No public API, no bulk export** could be found anywhere on hri.ie/hri-ras.ie; the direct fetch of hri.ie returned a 403 to automated access, suggesting active bot-blocking on parts of the site. Could not verify any published HRI open-data or licensing policy for reuse.
- **Data rights**: HRI sells its data/media rights commercially. From the start of 2024 a five-year media-rights deal covers all 26 Irish racecourses, with Racecourse Media Group (RMG) and SIS as the rights partners; the package explicitly included "HRI's data rights for all fixtures" ([SBC News](https://sbcnews.co.uk/retail/2022/10/28/sis-rmg-hri-preferred-bidders/), [irishracing.com](https://www.irishracing.com/news/board-of-horse-racing-ireland-unanimously-approves-new-media-rights-arrangements/239820)). Practical implication: machine-readable Irish racing data flows to commercial licensees (bookmakers, media) via RMG/SIS/PA-type channels, not to the public.

### Weatherbys (racing administration, pedigree, entries/declarations)
Weatherbys is the administrative backbone of GB/IRE racing: it registers **every Thoroughbred in Ireland** (passports are a legal requirement) and its New Racing Administration System (NRAS) processes **over 100,000 race entries a year for GB and Ireland** ([Weatherbys](https://www.weatherbys.co.uk/breeding/breeding-ireland-registrations), [Grokipedia/Wikipedia summaries](https://en.wikipedia.org/wiki/Weatherbys)).

- **Data products**: Weatherbys "sells its data in a range of different formats, from statistical breakdowns to bespoke data feeds which provide real time updates" — it is the pedigree provider for Tattersalls, Tattersalls Ireland, Goffs and Goffs UK ([Weatherbys pedigree services](https://www.weatherbys.co.uk/breeding/pedigree-services)).
- **Access/pricing**: B2B, on application (named contact for Irish data on the pedigree page: mfogarty@weatherbys.ie). **No published price list.** For a solo developer this is the authoritative source of pedigree/entries data but almost certainly enterprise-priced. Could not verify any self-serve product.

### Tote Ireland
Owned by HRI since 1945; operates pool betting on Irish racing ([Wikipedia](https://en.wikipedia.org/wiki/Tote_Ireland)). The UK Tote Group runs a **Partner API** (GraphQL POST endpoint at `hub.production.racing.tote.co.uk/partner/gateway/graphql`) giving low-latency access to **all UK and Irish pools** with enhanced dividends for API users — but it requires an approved partner account/commercial relationship (operated with TDCO Ltd, which holds an Irish remote bookmaker's pool-betting licence) ([Tote partner docs](https://developers.services.tote.co.uk/getting-started/endpoint/), [sharpbetting.co.uk overview](https://sharpbetting.co.uk/articles/Tote-API-Betting-Unlocking-Value-in-Pool-Wagering)). Dividend history is published on tote sites but there's no public bulk archive. Deduction: Tote Ireland takes ~27% of pools ([irishracing.com guide](https://www.irishracing.com/betting/guides/what-is-a-tote-placepot)).

### Racecourses, RMG, Coursetrack and RaceiQ (sectionals/GPS)
- Since **1 January 2024**, GPS tracking (saddlecloth GNSS trackers) runs at **every race at all Irish racecourses**, operated by **Coursetrack**, RMG's timing partner, using Total Performance Data-designed technology; live in-race data feeds RTE, Virgin Media, ITV and Racing TV broadcasts ([TDN](https://www.thoroughbreddailynews.com/coursetrack-tracking-data-implemented-at-all-irish-racecourses/), [RMG](https://www.racecoursemediagroup.com/news/blog/coursetrack-tracking-data-hailed-by-irish-racecourses-after-successful-roll-out/)).
- **RaceiQ metrics went free on Racing TV platforms in March 2025**: finishing-speed %, Time Index, Par Time/Sectionals, 0–20 mph, Lengths Gained Jumping, Jump Index — minutes after every GB and Irish race. Racing TV's results pages are "the only place to view both British and Irish race sectionals": **British races back to March 2023, Irish races back to 1 January 2024** ([Racing TV](https://www.racingtv.com/news/raceiq-data-now-freely-available-to-users-on-racingtv-com), [EEGaming](https://eegaming.org/latest-news/2025/03/07/124002/raceiq-metrics-now-available-for-free-on-racing-tv-platforms-in-time-for-cheltenham-festival/)).
- **No public API** for RaceiQ/Coursetrack data was found; it's a website feature. For model features you'd have to scrape racingtv.com (ToS not verified) or license B2B. Flag: Irish sectional history is short (~2.5 seasons) — usable as a model feature only for recent form.

---

## 2. Commercial data vendors

### Racing Post / Spotlight Sports Group (B2B)
Racing Post syndicates data to bookmakers/media via a commercial **API (launched 2020, AWS-hosted, replacing XML feeds)**; packages of endpoints are sold per customer ([Spotlight Sports Group announcement](https://www.spotlightsportsgroup.com/sports-betting-news/announcing-the-racing-post-api-available-now/)). **No public developer registration, no published pricing** — access requires a licensing agreement. For a solo developer this is effectively out of reach; could not verify any indicative price.

### Raceform / Racing Post consumer database products
**Raceform Interactive (RFI)** — Racing Post's PC formbook (official BHA results + Raceform expert data; covers GB & IRE) is still sold in 2025: **£72/month**, or discounted prepaid terms (e.g. "now until end of 2025 for £432") ([Racing Post shop](https://shop1.racingpost.com/collections/raceform-interactive), [monthly sub page](https://shop1.racingpost.com/products/raceform-interactive-flat-jumps-monthly-subscription)). It's an end-user desktop tool with export abilities, licensed for personal use — a data source for research, not an app backend.

### Timeform
- **B2B**: since February 2024 **PA Betting Services is the official supplier/managing partner of Timeform's B2B services** — Timeform ratings/content are licensed via PABS alongside PA's core racing data ([PA Media Group](https://pamediagroup.com/timeform-and-pa-betting-services-announce-b2b-partnership/), [Timeform commercial](https://www.timeform.com/commercial)). The Timeform Horse Racing API delivers pre-race data to commercial customers with **coverage from the early 1990s** ([Timeform API page](https://www.timeform.com/horse-racing/features/api-b2b/timeform_api_and_b2b_content)). Enterprise pricing, on application.
- **Consumer**: **Race Passes at ~£30/month** unlocks full Timeform ratings, flags and form for every GB & Irish runner ([Sporting Life](https://www.sportinglife.com/amp/racing/news/ultimate-form-guide-for-only-pound30/192190), [timeform.com subscribe](https://www.timeform.com/horse-racing/race-passes/subscribe)). Personal use only — you can't legally pipe Timeform ratings into a redistributed app, but it's a benchmark/reference for a solo modeller.

### Proform Racing
Professional form database + system builder, **UK and Ireland flat & jumps**, ~**17-year database**, downloadable/queryable (Access/SQL-style) ([proformracing.com](https://www.proformracing.com/home.html), [Punter2Pro review](https://punter2pro.com/best-horse-racing-form-stats-database/)). Pricing (per reviews/sign-up page): **£10/24h trial-day, £20/week, £50/4 weeks, Platinum £195/8 weeks** ([sign-up](https://www.proformracing.com/sign-up), [Mike Cruickshank review](https://mikecruickshank.com/proform-racing-review/)) — i.e. roughly £98/month at Platinum. Includes speed/form ratings and data export for private analysis. Ireland: yes, covered.

### Betwise Smartform
The most developer-friendly commercial database: a **MySQL horseracing form database covering all UK and Irish flat & NH racing, results from 1 Jan 2003** (advance racecards back to 2000), with nightly results updates and next-day final racecards from ~19:30. Pricing per the product page: **£195 initial purchase, £65/month subscription** (multi-month discounts; first month free for new subscribers); older references cite £35–45/month, so treat exact current pricing as "£195 + ~£65/mo, verify at purchase" ([betwise.co.uk/smartform](https://www.betwise.co.uk/smartform)). License: "for the personal use of Betwise members" — no redistribution. This is arguably the best legal 20+-year historical Irish dataset a solo developer can buy.

### Horseracebase
Online UK & Ireland racing database/system-builder with ratings and statistics; operates on a low-cost subscription (historically ~£99/year; the site itself doesn't publish pricing publicly and one review claims a donation-style model — **exact current price unverified**) with a 3-day free trial ([horseracebase.com](https://www.horseracebase.com/index.php), [Punter2Pro](https://punter2pro.com/best-horse-racing-form-stats-database/)). End-user tool, personal use.

### Geegeez Gold
UK & Irish racecards, formbook, pace maps, draw analysis, reports and query tools: **£36/month (first 30 days £1)** ([geegeez.co.uk FAQ](https://www.geegeez.co.uk/geegeez-gold-faq/)). End-user tool, no API.

### Total Performance Data (TPD) / sectionals outside Ireland
TPD offers Live Data (UDP JSON at up to 10 Hz: GPS X/Y, velocity, position), Post-Race Sectional and Points APIs; inventory ~200,000 races: **UK 50,000+ races since 2016, North America 125,000+ since 2017, RoW ~25,000**; **pricing on request** for APIs ([totalperformancedata.com/live-pr-api](https://www.totalperformancedata.com/live-pr-api/)). Consumer-grade live GPS feeds are sold via **TPD.Zone** subscriptions (e.g. **Weekender £60/month**, plus a cheap "Taster" plan; feeds into Bet Angel, Gruss, Bf Bot Manager) ([tpd.zone FAQs](https://www.tpd.zone/faqs/)). **Ireland caveat**: Irish tracking is run by Coursetrack for RMG (TPD-designed tech, but distribution goes through RMG/RaceiQ, not TPD's UK feed). TPD's own coverage list centres on UK (ARC courses/At The Races) and US (Equibase). Sectional data for *Irish* races therefore comes from Racing TV/RaceiQ, not TPD retail products. ATR publishes free TPD sectionals ~48h after racing for its covered (UK/ARC) courses ([attheraces.com/sectionalsinfo](https://www.attheraces.com/sectionalsinfo)).

### France Galop / PMU (Irish runners abroad)
France-galop.com is the official reference for French racing (calendar, entries, results) but has **no public developer API**; developers report being unable to obtain feeds from PMU ([The Racing Forum thread](https://theracingforum.co.uk/forums/topic/french-racing-data/), [france-galop.com](https://www.france-galop.com/en)). McLloyd sells French GPS tracking data (36 tracks, history from January 2021) ([data.mclloyd.com](https://data.mclloyd.com/)). Relevance to an Irish app is marginal — big French targets for Irish stables (Arc weekend etc.) are covered as "global group races" by The Racing API anyway.

---

## 3. Developer-focused APIs

### The Racing API (theracingapi.com) — primary candidate
- **Coverage**: "complete coverage of UK, Irish and Hong Kong horse racing, as well as global coverage of group level races and selected handicaps"; live DB "500,000+ results and racecards" (older marketing says 200,000+ over 10–12 years). The data-coverage page shows the core dataset at **356,954 total results, of which Ireland = 55,430 results, displayed for 2017–2026**; add-ons: North America (116,230 records), Australia (329,974) ([data coverage](https://www.theracingapi.com/data-coverage)). One page claims "over 35 years of global horse racing data" in total ([Punter2Pro](https://punter2pro.com/best-horse-racing-form-stats-database/)) — the queryable per-course listing is ~10 years; flag the discrepancy and confirm historical depth per plan before committing.
- **Plans**: Free (basic daily racecards), Basic (advanced racecards, live results, per-horse historical results), Standard (adds **20+ bookmaker odds for UK & Irish racing**, advanced queries over last 12 months of results), Pro (past & future advanced racecards, add-ons) ([Racing-Index review](https://www.racing-index.com/horseracing/theracingapi/)). **Pricing starts at £24.99/month** with a free tier ([SourceForge listing](https://sourceforge.net/software/product/The-Racing-API/), [Slashdot listing](https://slashdot.org/software/p/The-Racing-API/)); the live pricing table is JS-rendered and could not be captured — exact Standard/Pro prices unverified (site: theracingapi.com/pricing).
- **Limits/updates**: default **5 requests/second**; today's cards/odds refresh every ~3 minutes ([theracingapi.com](https://www.theracingapi.com/)).
- **Licensing**: data is for building apps/websites/analysis; **resale of raw data prohibited without permission; betting operators/sportsbooks banned** from using it operationally; hobbyist and small-commercial app use is the explicit target market ([ToS](https://www.theracingapi.com/terms-of-service)). Also listed on RapidAPI ([rapidapi.com](https://rapidapi.com/theracingapi/api/the-racing-api1/pricing)) and ships an MCP server ([tools/mcp](https://www.theracingapi.com/tools/mcp)).

### Other API vendors
- **RapidAPI horse-racing APIs**: The Racing API's RapidAPI listing is the main credible UK/IRE one; others on the marketplace are thin or US-centric. **Goalserve** sells a horse-racing odds/cards XML/JSON feed (enterprise sports-feed pricing, typically hundreds USD/month) ([goalserve.com](https://www.goalserve.com/en/sport-data-feeds/horse-racing-api/prices)) — could not verify Irish-specific depth.
- **OurHub Racing API**: newer UK & Irish racecards/runners/stats + AI predictions ([github.com/TamB10/ourhub-racing-api](https://github.com/TamB10/ourhub-racing-api)) — small/unproven; pricing unverified.

### Betfair Exchange API (live/closing odds, the de-facto odds source)
- **Delayed App Key: free** (1–180 s delayed prices) for development/personal use — enough for *value screening* against morning/near-live markets.
- **Live App Key: one-off £499 activation** (older docs said £299 — the current support page says £499), debited from your Betfair account, and **"read-only access via the Live App Key isn't permitted"** — i.e. Betfair expects you to bet through it, which for this app (which suggests bets, and could place them) is fine ([Betfair Developer support](https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access), [developer.betfair.com](https://developer.betfair.com/exchange-api/)). Note: Betfair does not accept Irish residents? — **No: Betfair operates in Ireland normally**; no restriction found (not verified in depth — check account T&Cs).

### Betfair historical odds data
- **Free BSP CSVs**: daily win & place Betfair SP files for **GB and Irish racing back to 28 May 2008**, including BSP, pre-race weighted-average price (PPWAP), morning WAP, max/min traded prices ([promo.betfair.com/betfairsp](https://promo.betfair.com/betfairsp/SP_history.html), [file directory](https://promo.betfair.com/betfairsp/prices)). This is the canonical free closing-odds history for value/CLV backtesting.
- **Historic Data site** (historicdata.betfair.com, login required): tiers are **Basic — free (1-min interval last-traded price, no volume); Advanced — paid (1-sec intervals, top-3 price ladder, volume); Pro — paid (50 ms ticks, full ladder, volume)**, delivered as TAR archives of JSON market files, filterable by sport/country/date ([Betfair Automation Hub guide](https://betfair-datascientists.github.io/data/usingHistoricDataSite/), [spec PDF](https://historicdata.betfair.com/Betfair-Historical-Data-Feed-Specification.pdf)). **Exact Advanced/Pro prices sit behind the login and could not be verified**; third-party estimates put paid packs at roughly £30–£200 per month of data depending on tier/sport ([tryfix.it.com guide](https://tryfix.it.com/how-much-does-betfair-api-cost-the-complete-2026-pricing-guide/) — unofficial, treat as indicative).
- ToS: historic data is licensed for the purchaser's own use; redistribution is restricted (see terms on the historic-data portal — not fully verifiable without login).

### Odds-history archives beyond Betfair
Could not verify any legal bulk archive of Irish *bookmaker* (fixed-odds) price histories. Oddschecker/oddsportal have no licensed export; The Racing API's Standard plan (20+ bookmakers, UK & IRE) is the practical forward-collection route — start recording now and build your own odds history.

---

## 4. Free / scrapeable sources

- **Racing Post (racingpost.com)** — the richest free surface: racecards, results, Racing Post Ratings (RPR)/Topspeed shown on-page, per-horse form. `robots.txt` blocks only subsections (UGC comments, some profile tabs, `/api/auth/`, bloodstock sales) — the main results/racecards paths are not disallowed ([racingpost.com/robots.txt](https://www.racingpost.com/robots.txt)). The site's ToS page could not be fetched (404 on the checked URL), so the contractual scraping prohibition could not be quoted — assume standard anti-scraping terms exist. **No lawsuit by Racing Post against scrapers could be found**, and the widely used **rpscrape** scraper (Python, CSV results + JSON racecards, Irish region code `ire`, all Irish courses, arbitrary year ranges e.g. 2005–2015) has lived openly on GitHub for years ([github.com/joenano/rpscrape](https://github.com/joenano/rpscrape)). Legal posture: private research use is low-risk (especially post-*BHB v William Hill* on database right — [EUR-Lex C-203/02](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62002CJ0203)); republishing RP's ratings/comments in a commercial app is copyright infringement risk.
- **attheraces.com** — free results plus **free TPD sectional times ~48 h after racing** for its covered (UK/ARC) courses; also hosts +Timeform content ([ATR sectionals info](https://www.attheraces.com/sectionalsinfo)). Irish sectionals are NOT here — they're on Racing TV (RMG rights).
- **racingtv.com** — free registration gives the only combined GB+IRE sectionals + free RaceiQ metrics (Irish races since 1 Jan 2024) ([Racing TV](https://www.racingtv.com/news/raceiq-data-now-freely-available-to-users-on-racingtv-com)). No API; scraping ToS unverified.
- **sportinglife.com** — free racecards/results for GB & IRE (Flutter-owned). ToS/robots stance not verified in this audit.
- **irishracing.com** — free Irish+UK racecards with declarations, entries+weights pages, fast results, per-horse form pages and a HorseTracker alert service ([irishracing.com/racecards](https://www.irishracing.com/racecards), [raceentries](https://www.irishracing.com/raceentries), [fast-results](https://www.irishracing.com/fast-results)). Good scrape target for Irish declarations; ToS unverified.
- **HRI / hri-ras.ie** — free results back to 1998, entries/declarations pages ([archive](https://www.hri-ras.ie/results/results-archive)); observed 403s on automated fetch — expect bot defences.
- **p2p.ie** — Irish point-to-point results/fixtures since 2003, partially member-gated ([p2p.ie](https://p2p.ie/)); relevant if you want pre-track form for Irish NH horses (many top jumpers start in Irish points).
- **Open datasets**: Kaggle "**Horse Racing results — UK/Ireland 1988–2026**" (updated to 3 June 2026) ([Kaggle deltaromeo](https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025)); "Horse Racing Results — UK & Ireland 2005 to 2019" ([Kaggle sheikhbarabas](https://www.kaggle.com/datasets/sheikhbarabas/horse-racing-results-uk-ireland-2005-to-2019)); assorted GitHub scrapes. Licensing/provenance is typically "scraped from Racing Post" — fine to bootstrap a model, unsafe to redistribute or build a paid product on directly.
- **Wikipedia**: winners of big Irish races only — negligible for modelling.

**Legal history worth knowing**: *British Horseracing Board v William Hill* (ECJ C-203/02, 2004) — the sui generis EU database right does not cover data *created* by the racing authority (runners/riders lists), gutting the governing bodies' ability to claim database right over core racing facts ([5RB](https://www.5rb.com/case/british-horseracing-board-v-william-hill/), [EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62002CJ0203)). Separately, *At The Races v BHB* (2007) found BHB abused a dominant position in pricing pre-race data ([K&L Gates note](https://files.klgates.com/files/publication/a122121b-8f53-4c0c-bab0-046268e5a920/presentation/publicationattachment/25eedd3d-f466-47d3-8f0c-0a0e592e1f08/wslr.pdf)). Facts are free-ish; *expressions* (ratings, comments) and contractual ToS are the constraints.

---

## 5. Practical stacks for a solo developer (2026)

Requirement mapping: (a) daily racecards/declarations with runner details; (b) 10+ years historical results with ratings; (c) live/closing odds.

### Budget stack — ~€0–10/month
- (a) The Racing API **Free** plan (basic daily racecards) topped up by scraping irishracing.com/Racing Post cards via rpscrape.
- (b) Kaggle 1988–2026 UK/IRE dataset + rpscrape backfill (free; personal-use grey zone; no licensed ratings — engineer your own speed/form figures).
- (c) Free Betfair BSP CSVs (2008→now, GB+IRE) for closing prices/backtests + **free delayed Betfair App Key** for near-live prices.
- Cost: ~€0 (+ VPS ~€5–10). Risk: scraping fragility, no redistribution rights, no official ratings.

### Mid stack — ~€40–80/month
- (a)+(b)+(c) The Racing API **Standard** (from-£24.99 tier pricing; Standard likely ~£40–60/mo — confirm on site): advanced GB+IRE racecards, 20+ bookmaker odds, 12-month advanced results queries, per-horse history.
- (b) deepen history once with either the Kaggle/rpscrape corpus (free) or a one-off **Smartform** purchase (£195 for the 2003→ MySQL database) without keeping the update subscription.
- (c) Betfair BSP CSVs (free) + delayed key; pay the **£499 one-off** only when you're ready to place/track real bets programmatically.
- Cost: ~£40–75/month ≈ €47–88. This is the sweet spot: fully legal for a personal app, all three requirements met for Ireland.

### Pro stack — ~€200–350/month (+ one-offs)
- The Racing API **Pro** + add-ons (advanced past racecards for backtesting).
- **Smartform** subscription (£65/mo) as a second, SQL-native GB+IRE source 2003→ for cross-validation, or **Proform Platinum** (~£98/mo equivalent) for its ratings and system-builder.
- **Timeform Race Passes** (£30/mo) as a professional ratings benchmark (manual/reference use only).
- **Betfair Historic Data Advanced** packs for in-play/pre-off price ladders on Irish markets (est. £30–200 per data-month; verify behind login) + live App Key (£499 one-off).
- Optional: TPD.Zone live GPS (from ~£60/mo Weekender) — UK courses only; Irish sectionals remain free-but-manual on Racing TV.
- Cost: roughly £180–300/month ≈ €210–350. B2B feeds (Racing Post API, Timeform/PABS, Weatherbys, Tote Partner API) only become relevant if the app itself is commercialised — all are price-on-application.

### Feasibility verdict
Compared with greyhounds, Irish horse racing is well served: one purpose-built hobbyist API with explicit Irish coverage and ML-friendly ToS, a free 18-year closing-odds archive that includes Irish racing, at least three affordable 15–23-year GB+IRE historical databases (Smartform, Proform, Horseracebase), and free universal Irish sectionals since 2024. The main gaps: no official HRI API, Irish sectional history is shallow (2024→), licensed ratings (RPR/Timeform) cannot be redistributed cheaply, and The Racing API's deep-history-per-plan needs confirming before purchase.

---

## Could not verify (explicit)
- Exact The Racing API Standard/Pro monthly prices (JS-rendered pricing page; only "from £24.99" + free tier verified via listings).
- Exact Betfair Historic Data Advanced/Pro prices (behind account login).
- Racing Post's current ToS text on scraping (terms URL 404'd; robots.txt captured instead).
- Any HRI open-data/licensing policy, or any HRI bulk export.
- Horseracebase's current subscription price (site doesn't publish it publicly).
- Current Smartform pricing ambiguity (£195 initial + £65/mo per product page vs older £35–45/mo references).
- Tote Ireland historical dividend bulk data availability.
- Sporting Life / Racing TV / irishracing.com ToS on automated access.

## Sources
- The Racing API: https://www.theracingapi.com/ · https://www.theracingapi.com/data-coverage · https://www.theracingapi.com/terms-of-service · https://www.racing-index.com/horseracing/theracingapi/ · https://sourceforge.net/software/product/The-Racing-API/ · https://slashdot.org/software/p/The-Racing-API/ · https://rapidapi.com/theracingapi/api/the-racing-api1/pricing
- HRI: https://www.hri-ras.ie/results/results-archive · https://www.hri.ie/ · https://sbcnews.co.uk/retail/2022/10/28/sis-rmg-hri-preferred-bidders/ · https://www.irishracing.com/news/board-of-horse-racing-ireland-unanimously-approves-new-media-rights-arrangements/239820
- Weatherbys: https://www.weatherbys.co.uk/breeding/pedigree-services · https://www.weatherbys.co.uk/breeding/breeding-ireland-registrations · https://en.wikipedia.org/wiki/Weatherbys
- Tote: https://developers.services.tote.co.uk/getting-started/endpoint/ · https://en.wikipedia.org/wiki/Tote_Ireland · https://sharpbetting.co.uk/articles/Tote-API-Betting-Unlocking-Value-in-Pool-Wagering
- Sectionals/GPS: https://www.thoroughbreddailynews.com/coursetrack-tracking-data-implemented-at-all-irish-racecourses/ · https://www.racecoursemediagroup.com/news/blog/coursetrack-tracking-data-hailed-by-irish-racecourses-after-successful-roll-out/ · https://www.racingtv.com/news/raceiq-data-now-freely-available-to-users-on-racingtv-com · https://eegaming.org/latest-news/2025/03/07/124002/raceiq-metrics-now-available-for-free-on-racing-tv-platforms-in-time-for-cheltenham-festival/ · https://www.totalperformancedata.com/live-pr-api/ · https://www.tpd.zone/faqs/ · https://www.attheraces.com/sectionalsinfo
- Racing Post/Raceform: https://www.spotlightsportsgroup.com/sports-betting-news/announcing-the-racing-post-api-available-now/ · https://shop1.racingpost.com/collections/raceform-interactive · https://shop1.racingpost.com/products/raceform-interactive-flat-jumps-monthly-subscription · https://www.racingpost.com/robots.txt
- Timeform: https://www.timeform.com/commercial · https://pamediagroup.com/timeform-and-pa-betting-services-announce-b2b-partnership/ · https://www.timeform.com/horse-racing/features/api-b2b/timeform_api_and_b2b_content · https://www.sportinglife.com/amp/racing/news/ultimate-form-guide-for-only-pound30/192190
- Databases: https://www.betwise.co.uk/smartform · https://www.proformracing.com/home.html · https://mikecruickshank.com/proform-racing-review/ · https://www.horseracebase.com/index.php · https://www.geegeez.co.uk/geegeez-gold-faq/ · https://punter2pro.com/best-horse-racing-form-stats-database/ · https://www.racingformbook.com/ · https://www.flatstats.co.uk/horse-racing-data.php
- Betfair: https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access · https://developer.betfair.com/exchange-api/ · https://historicdata.betfair.com/ · https://betfair-datascientists.github.io/data/usingHistoricDataSite/ · https://promo.betfair.com/betfairsp/SP_history.html · https://promo.betfair.com/betfairsp/prices · https://historicdata.betfair.com/Betfair-Historical-Data-Feed-Specification.pdf · https://tryfix.it.com/how-much-does-betfair-api-cost-the-complete-2026-pricing-guide/
- Free/scrape: https://github.com/joenano/rpscrape · https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025 · https://www.kaggle.com/datasets/sheikhbarabas/horse-racing-results-uk-ireland-2005-to-2019 · https://www.irishracing.com/racecards · https://www.irishracing.com/raceentries · https://p2p.ie/
- Legal: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62002CJ0203 · https://www.5rb.com/case/british-horseracing-board-v-william-hill/ · https://files.klgates.com/files/publication/a122121b-8f53-4c0c-bab0-046268e5a920/presentation/publicationattachment/25eedd3d-f466-47d3-8f0c-0a0e592e1f08/wslr.pdf
- France: https://www.france-galop.com/en · https://data.mclloyd.com/ · https://theracingforum.co.uk/forums/topic/french-racing-data/
