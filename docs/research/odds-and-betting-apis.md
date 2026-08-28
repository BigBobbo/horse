# Odds Data & Bet-Placement Integration for an Irish Horse-Racing Betting App

*Research audit, 2026-08-28. Focus: what a developer physically located in Ireland can integrate today for (a) live/historical odds and (b) programmatic bet placement, for Irish + UK racing.*

## Key takeaways

- **Betfair Exchange is the only serious, fully-supported programmatic route** for both odds data and automated bet placement from Ireland. Free delayed app key for development; **live app key now costs a one-off £499** (widely-cited £299 figure is stale — official docs say £499 as of 2025-26) ([Betfair support](https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access), [app-keys doc](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687105/Application+Keys)).
- Betfair commission for UK/Ireland accounts is now chosen via **My Betfair Rewards: 2% (Basic, no promos) / 5% / 8%** plans ([Bet4bettor](https://bet4bettor.com/my-betfair-rewards/)); the **Premium Charge was abolished and replaced by the "Expert Fee" from 6 Jan 2025** (0% below £25k rolling-52-week gross profit; 20% for £25k–£100k; 40% above £100k) ([Racing Post](https://www.racingpost.com/news/britain/betfair-exchange-to-introduce-new-commission-system-for-2025-as-premium-charge-is-dropped-a7wbg0v4GCAJ/)).
- **Betfair bots are explicitly permitted** by Betfair's terms; **bookmaker bots are explicitly prohibited** (bet365 et al. close accounts for automation) ([Betfair T&Cs](https://support.betfair.com/app/answers/detail/betfair-general-terms-and-conditions), [ontheballbets/bet365](https://www.ontheballbets.com/betting-guides/bet365/account-restricted/)).
- **No Irish/UK retail bookmaker (Paddy Power, BoyleSports, Ladbrokes, bet365) offers a public API** for odds or bet placement. Programmatic bookmaker access exists only via brokers (BetInAsia BLACK/Mollybet — **€600 API connection fee**, horse racing carried) or grey-area third-party services.
- Mainstream odds-aggregation APIs are weak for racing: **The Odds API does not cover horse racing at all** ([sports list](https://the-odds-api.com/sports-odds-data/sports-apis.html)); OpticOdds/OddsJam are enterprise (~$5k/mo) and racing coverage is unverified; **Oddschecker has no public API**. The practical racing-odds feed is **The Racing API (from ~£24.99/mo, 20+ bookmakers' odds, 5 req/s)**.
- **Account restriction of winning punters is fast and near-universal**: UKGC-era data shows **643,779 accounts (4.31% of 15M) restricted in 2024**; surveys show ~20% of winning punters closed after fewer than 10 bets ([UK Bookmakers](https://www.ukbookmakers.org.uk/2025/07/more-than-600000-uk-punters-have-accounts-restricted/), [Justice for Punters](https://justiceforpunters.org/campaigning/how-many-people-have-restricted-betting-accounts/)). A bookmaker-odds "value" strategy therefore has a short shelf-life per account; the exchange is the durable venue.
- **Liquidity reality**: UK Saturday Class 1–3 races match £3–8M each; festivals £15–40M/race (~£40M matched on a single Cheltenham Tuesday). Irish midweek cards are markedly thinner than UK equivalents and overall exchange racing turnover is declining (-4.3% 2025 vs 2024) — but this is still one to three orders of magnitude more liquidity than greyhounds (top BAGS greyhound race rarely clears £150k) ([Betfair Square](https://betfairsquare.com/sports/horse-racing), [BetAngel forum](https://forum.betangel.com/viewtopic.php?t=28100)).
- **Verdict for the project**: horse racing is materially better than greyhounds on every axis that killed the greyhound app — odds data availability, exchange liquidity, historical depth, and a legal automation path.

---

## 1. Betfair Exchange API (the centrepiece)

### 1.1 How it works

Betfair exposes the **Exchange API ("API-NG")**: JSON-RPC/REST endpoints for market navigation (`listEventTypes`, `listMarketCatalogue`), prices (`listMarketBook`, `listRunnerBook`), and betting (`placeOrders`, `cancelOrders`, `replaceOrders`), plus an **Exchange Stream API** that pushes market-change and order-change deltas over a TCP/SSL socket for low-latency price/volume updates ([developer.betfair.com](https://developer.betfair.com/)). Every Betfair account can self-serve two app keys via the API-NG Accounts visualiser (`createDeveloperAppKeys`) ([BotBlog guide](https://botblog.co.uk/betfair-api-key/)).

### 1.2 Delayed vs live keys — and the fee

Per the official Application Keys documentation ([Betfair docs](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687105/Application+Keys)):

| | Delayed key (free) | Live key |
|---|---|---|
| Price data | Delayed **1–180 s** (variable) | Real time |
| Price depth | Top **3 levels** only | Full ladder (`EX_ALL_OFFERS`) |
| Traded volume (`totalMatched`) | **Not provided** | Provided |
| BSP near/far prices | Not available | Available |
| Bet placement | Blocked | Enabled |
| Read-only use | Permitted | **Not permitted** (must be used for betting) |
| Fee | None | **£499 one-off activation**, debited from the Betfair account, non-refundable |

**Fee verification**: current official Betfair developer-support pages state **£499** for the Live App Key ([costs article](https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access), [activation article](https://support.developer.betfair.com/hc/en-us/articles/115003860331-How-do-I-activate-my-Live-App-Key)). The **£299** figure the user may have seen (still repeated by third-party blogs like [BotBlog](https://botblog.co.uk/betfair-api-key/) and older forum posts) is **stale** — treat £499 as current. Application is under "Exchange API → For My Personal Betting"; a separate **commercial/vendor licence** (extra fees, revenue share) applies if you ever sell the app or run it for other people's accounts ([Betfair developers](https://developer.betfair.com/)).

Practical build path: develop and backtest the whole pipeline free on the delayed key (bet placement stubbed), pay £499 only when going live.

### 1.3 Rate limits and transaction charges

- **Market data weighting**: a `listMarketBook`-style request must not exceed **200 weight points** (weight × number of market IDs); exceeding returns `TOO_MUCH_DATA` ([Market Data Request Limits](https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687478/Market+Data+Request+Limits)).
- **Transaction charge**: **5,000 free transactions per hour**; excess charged at **£0.002 (0.2p) each**, offset against commission generated — ordinary single-user bots essentially never pay this ([Betfair support](https://support.developer.betfair.com/hc/en-us/articles/115003864671-What-data-request-limits-exist-on-the-Exchange-API), [Betfair charges](https://www.betfair.com/aboutUs/Betfair.Charges/)).

### 1.4 Data available

Live key: full order-book depth, last traded price, total matched per runner/market, BSP projections (near/far), actual BSP after reconciliation, in-play flags, and streaming deltas at sub-second cadence. This is exactly the market-microstructure data the greyhound project could not get from any source.

### 1.5 Historical data

- **Betfair Historic Data site** ([historicdata.betfair.com](https://historicdata.betfair.com/)) sells time-stamped Stream-API recordings of **nearly all Exchange markets since 2016**, per sport per month, in TAR/BZ2 of JSON market-change files. Tiers ([Betfair Automation Hub](https://betfair-datascientists.github.io/data/usingHistoricDataSite/), [Betfair Hub AU](https://www.betfair.com.au/hub/education/how-to-model/historical-data-sources/)):
  - **Basic — free**: 1-minute intervals, last traded price only, no volume.
  - **Advanced — paid**: 1-second intervals, top-3 ladder, volume.
  - **Pro — paid**: full API tick (50 ms) intervals, full ladder, volume.
  - **Could not verify exact GBP prices** for Advanced/Pro from outside a logged-in session (the pricing page is JS/login-gated); third-party guides put paid tiers in the **~£30–£200/month-of-data** range depending on sport and tier ([tryfix guide](https://tryfix.it.com/how-much-does-betfair-api-cost-the-complete-2026-pricing-guide/) — treat as indicative only). Each month of data is purchased once and re-downloadable.
- **Free BSP files**: Betfair publishes free daily CSVs of Betfair Starting Prices (win & place, GB and IRE) going back years at [promo.betfair.com/betfairsp](https://promo.betfair.com/betfairsp/SP_history.html) ([file directory](https://promo.betfair.com/betfairsp/prices)) — enough on their own to backtest "model price vs BSP" value strategies at zero cost.
- Format/spec: [Historical Data Feed Specification PDF](https://historicdata.betfair.com/Betfair-Historical-Data-Feed-Specification.pdf).

### 1.6 ToS for apps/bots

Betfair's general terms **explicitly permit bots**: customers may "use programs designed to automatically place bets within certain parameters" ([Betfair General T&Cs](https://support.betfair.com/app/answers/detail/betfair-general-terms-and-conditions)). Non-interactive (bot) login is a documented, supported flow. Constraints: personal-use licence only unless you take a vendor licence; excessive/manipulative API usage can trigger suspension ([SportsFirst overview](https://www.sportsfirst.net/sportsapi/betfairapi)). This is the single biggest structural advantage over any bookmaker route.

### 1.7 Commission & Expert Fee (Ireland)

- **My Betfair Rewards** (UK & Republic of Ireland accounts): choose monthly between **Basic 2% commission** (no promotions, no BOG), **5%** (small monthly perks), or **8%** (10% loss rebate + promos) ([Bet4bettor](https://bet4bettor.com/my-betfair-rewards/), [Team Profit](https://www.teamprofit.com/betfair-rewards)). A value bettor should sit on the 2% plan. (Some guides still describe the older 5% market-base-rate + discount-rate scheme, e.g. [Betfair Square](https://betfairsquare.com/sports/horse-racing) quotes 2% on UK/IRE racing; the operative fact is that **2% commission on Exchange winnings is attainable for an Irish account**.)
- **Expert Fee** (from **6 January 2025**, replacing the Premium Charge): assessed on **rolling 52-week gross profit** — £0–£25k: nothing extra; **£25k–£100k: 20%**; **>£100k: 40%** ([Racing Post](https://www.racingpost.com/news/britain/betfair-exchange-to-introduce-new-commission-system-for-2025-as-premium-charge-is-dropped-a7wbg0v4GCAJ/)). For a hobby-scale model this is irrelevant until you're winning >£25k/yr; the old up-to-60% lifetime Premium Charge is gone.

### 1.8 Irish liquidity reality

- Headline UK figures: **£3–8M matched on the win market of each Class 1–3 Saturday ITV race; £15–40M per race at Cheltenham/Aintree/Royal Ascot; ~£40M matched across a single Cheltenham Tuesday** ([Betfair Square](https://betfairsquare.com/sports/horse-racing)).
- Racing exchange turnover is **declining: -4.3% in 2025 vs 2024, -10.7% vs 2023**, with liquidity concentrating into fewer, bigger markets; extreme cases of tiny midweek markets (a forum report of as little as **£12 matched pre-off** on a minor race) exist ([BetAngel forum — Declining Horse Racing Volumes](https://forum.betangel.com/viewtopic.php?t=28100), [Betfair community thread](http://community.betfair.com/horse_racing/go/thread/view/94102/30574373/horse-racing-liquidity-at-an-all-time-low)).
- **Irish racing specifically** trades thinner than equivalent UK races: traders note Ireland's small population and the split of money across retail bookies leaves "not enough punters… to create decent volumes on all Irish races", and most exchange traders concentrate on UK cards; the flip side is Irish non-handicap markets are sometimes mispriced relative to UK-equivalent races ([BetAngel forum — Irish liquidity](https://forum.betangel.com/viewtopic.php?t=24420), [Geekstoy thread](https://www.geekstoy.com/forum/forum/betting-trading/traders-exchange/11754-the-liquidity-in-uk-and-ire-horse-racing)).
- **Could not verify a published per-race average matched figure for Irish midweek racing** — no official per-country breakdown is published. Practical expectation from trader commentary: big Irish festivals (Punchestown, Leopardstown Christmas, Irish Champions Weekend) trade deep (seven figures per race); ordinary Irish midweek win markets often match low-to-mid six figures or less by the off, and **place markets run at only ~25–40% of win-market volume** ([Betfair Square](https://betfairsquare.com/sports/horse-racing)). For a €10–€50-stakes app this is ample; for scaling into five-figure stakes on midweek Irish racing it is a real constraint — measure it empirically with the delayed key before going live.

## 2. Other exchanges usable from Ireland

### 2.1 Matchbook (Irish-run exchange)

- **API: open and free to customers.** Any registered Matchbook customer can use the REST API immediately with their login credentials; docs at [developers.matchbook.com](https://developers.matchbook.com/). Default rate limits: **events 700 req/min, betting writes 3,000 req/min, account 300 req/min, reports 40 req/min**, upgradeable via the Trader Plan / api@matchbook.com ([Matchbook FAQ](https://developers.matchbook.com/docs/faq)). Automated bots are permitted within a fair-usage policy.
- **Commission**: **2% on net market winnings for UK/Ireland residents** (4% elsewhere), losing markets free; periodic **"Matchbook Zero"** 0%-commission promos on selected horse-racing markets ([matchbookbetting.co.uk](https://matchbookbetting.co.uk/commission/), [Compare.bet](https://www.compare.bet/betting/matchbook), [BetAngel forum](https://forum.betangel.com/viewtopic.php?t=15763)).
- **Company/risk note**: operated by Triplebet Ltd with its operational base in Ireland; UKGC **suspended its GB licence Feb–Aug 2020** over AML failings (£740k penalty) before reinstatement ([SBC News](https://sbcnews.co.uk/sportsbook/2020/04/08/ukgc-suspended-matchbook-licence-over-aml-risk-assessment-failures/), [EGR](https://www.egr.global/intel/news/matchbook-relaunches-to-uk-players-as-uk-licence-suspension-is-lifted/)). Racing liquidity is a fraction of Betfair's — usable for taking stray value prices, not as the primary venue. B2B feed products exist at [b2b.matchbook.com](https://b2b.matchbook.com/).

### 2.2 Smarkets

- **API exists but is application-gated** (not fully open): you must submit an API request form and be approved against "exchange health guidelines"; keys are then activated ([Smarkets Help — API Access, Integration & T&Cs](https://help.smarkets.com/hc/en-gb/articles/34697834941085-Smarkets-API-Access-Integration-T-Cs), docs at [docs.smarkets.com](https://docs.smarkets.com/)). Historically free for approved users; heavy commercial use negotiable.
- **Commission**: standard **2% on net market winnings**; a **1% "Pro" tier** and a punitive **3% "Select" tier** applied to the most profitable users; recurring **0%-for-60-days** promos for new UK/IE/Malta customers ([Smarkets commission FAQ](https://help.smarkets.com/hc/en-gb/articles/212654665-Smarkets-commission-FAQ), [mybettingsites.com/ie](https://mybettingsites.com/ie/smarkets)). Note: Smarkets *can* move winners onto the worse tier — a form of exchange-side "soft limiting" Betfair doesn't do.
- UK/Irish racing markets carried; liquidity again far below Betfair.

### 2.3 Betdaq

- **API: open, SOAP/XML-era but functional**, purpose-built for automated trading; docs at [api.betdaq.com](https://api.betdaq.com/v2.0/Docs/Intro.aspx). Access requires a verified account, an application (approved ~next business day), and a **one-off £250 access fee** ([Betdaq support](https://betdaq.zendesk.com/hc/en-gb/articles/360020067139-API-access), [BETDAQPRO](https://betdaqpro.com/api-technical-information/)).
- **Commission: flat 2%**; owned by Dermot Desmond's group again since Entain sold it back in **November 2021** ([Punter2Pro](https://punter2pro.com/betdaq-review-free-bet/), [EGR](https://www.egr.global/intel/news/entain-sells-betdaq-back-to-billionaire-businessman-dermot-desmond/)). Racing liquidity is thin (much of it historically mirrored from other sources); useful mainly as a secondary venue.

## 3. Bookmaker integration & brokers

### 3.1 Retail bookmakers — no public APIs

- **bet365**: no public API, no developer portal; private APIs only for affiliates/partners. Its terms **prohibit automated tools/bots/scripts** and closure/withholding follows detection ([SharpAPI note](https://sharpapi.io/sportsbooks/bet365-odds-api), [ontheballbets](https://www.ontheballbets.com/betting-guides/bet365/account-restricted/)). Third-party bet-placement services (e.g. [BetLink](https://github.com/xjxckk/BetLink-bet365-place-bet-api-service)) exist but are ToS-violating and account-fatal — not a foundation for a product.
- **Paddy Power (Flutter)**: no public sportsbook API today; odds are only obtainable via third-party aggregators or its affiliate programme ([365oddsapi](https://365oddsapi.com/bookmakers-api/paddypower-api/), [odds-api.io Paddy Power page](https://odds-api.io/sportsbooks/paddy-power)). (Its long-dead public developer API from the early 2010s should be considered gone — could not find any live official developer programme.)
- **BoyleSports, Ladbrokes (Entain)**: no public APIs found — could not verify any official developer access for either; integration is affiliate-link-out only.
- **Practical model for a consumer app**: show odds via a licensed feed, deep-link the user to the bookmaker to place the bet manually (affiliate revenue), and reserve true automation for the exchange.

### 3.2 Brokers

- **BetInAsia BLACK / Mollybet**: BetInAsia's BLACK platform is powered by **Mollybet**, aggregating bookmakers and exchanges (incl. Betfair, Betdaq) behind one wallet. **Pull and Push APIs** are offered to professional clients; **API connection fee €600 (non-refundable) plus minimum-turnover requirements** ([BetInAsia API](https://betinasia.com/sports-betting-api/), [BetInAsia zendesk](https://betinasia.zendesk.com/hc/en-us/articles/360013835620-Can-I-have-an-API-connection-on-BetInAsia-BLACK), [Arbusers](https://arbusers.com/betinasia-api-commission-t9416/)). **Horse racing is carried** among Mollybet's sports ([bookie.broker](https://bookie.broker/mollybet/)); Mollybet API docs are public at [api.mollybet.com/docs](https://api.mollybet.com/docs/).
- Caveats for Ireland: brokers primarily serve high-stakes/pro clients; racing coverage is thinner than their Asian-football core; KYC/residency acceptance for Irish customers should be confirmed directly, and broker use sits in a regulatory grey zone versus betting with an Irish-licensed operator (relevant as GRAI licensing under the Gambling Regulation Act 2024 comes into force).

## 4. Odds-aggregation APIs

| Provider | Horse racing UK/IRE? | Price | Notes |
|---|---|---|---|
| **The Odds API** | **No** — racing absent from its ~70-sport list ([sports page](https://the-odds-api.com/sports-odds-data/sports-apis.html)) | Free 500 credits/mo; $30/mo (20K) → $249/mo (15M) ([the-odds-api.com](https://the-odds-api.com/)) | Fine for football, useless for this project |
| **The Racing API** | **Yes — the practical choice.** UK+IRE racecards, results (>500k historical), **odds from 20+ bookmakers** on Standard plan; updates every 3 min today / 15 min tomorrow; **rate limit 5 req/s** ([theracingapi.com](https://www.theracingapi.com/)) | From **£24.99/mo** (SourceForge lists starting price; free trial tier via [RapidAPI](https://rapidapi.com/theracingapi/api/the-racing-api1/details)) ([SourceForge](https://sourceforge.net/software/product/The-Racing-API/)) | 3-min refresh = fine for pre-race value scans, not for steamers/last-minute moves |
| **OpticOdds / OddsJam** (same company — Gambling.com Group since Jan 2025) | Unverified — marketing lists 200+ sportsbooks/25+ sports, racing not confirmed ([opticodds.com](https://opticodds.com/sports-betting-api), [oddspapi comparison](https://oddspapi.io/blog/oddsjam-api-alternative/)) | **~$5,000/mo**, sales-led, no self-serve ([sportsgameodds comparison](https://sportsgameodds.com/blog/comparing-odds-api-providers)) | Enterprise-only; overkill |
| **odds-api.io** | Covers Paddy Power, bet365, Ladbrokes among 265+ books, but **horse racing not listed** among its 34 sports — could not verify racing coverage ([odds-api.io](https://odds-api.io/)) | Free (2 books, 100 req/hr); £49–£229/mo, 5,000 req/hr ([odds-api.io](https://odds-api.io/)) | Confirm racing before relying on it |
| **Oddschecker** | Displays 25+ books for UK/IRE racing but **no public API**; data access only via commercial/affiliate arrangement ([oddschecker.com](https://www.oddschecker.com/), [T&Cs](https://www.oddschecker.com/myoddschecker/terms-and-conditions)) | n/a | Scraping it breaches its terms |
| **Others** | Goalserve ([horse-racing feed](https://www.goalserve.com/en/sport-data-feeds/horse-racing-api/prices)), OddsMatrix ([horseracing](https://oddsmatrix.com/sports/horseracing/)), LSports, Podium — B2B racing feeds with sales-led pricing | ~$100s–$1000s/mo | Alternatives if The Racing API's refresh rate proves too slow |

**Bottom line**: bookmaker odds for UK/IRE racing → The Racing API (£25/mo tier); exchange odds/depth/BSP → Betfair API directly (free delayed, £499 live). The generic US-centric odds APIs do not solve this problem.

## 5. Practicalities

### 5.1 Account restrictions (the decisive constraint on "bet the bookmaker value" strategies)

- **Scale**: **643,779 GB accounts (4.31% of 15M active) had restrictions applied in 2024** for commercial reasons ([UK Bookmakers, Jul 2025](https://www.ukbookmakers.org.uk/2025/07/more-than-600000-uk-punters-have-accounts-restricted/)). Justice for Punters' survey work: ~4% of casual bettors but **9–10% of regular punters** report restriction/closure, rising steeply for skilled bettors; **~20% of affected punters were closed after fewer than 10 bets, 37% after ≤20 bets** ([Justice for Punters](https://justiceforpunters.org/campaigning/how-many-people-have-restricted-betting-accounts/), [Racing Post debate coverage](https://www.racingpost.com/news/are-bookmakers-unfairly-closing-customer-accounts-views-from-tuesdays-debate-atwtK6X6m2pt/)).
- **Speed**: documented cases of accounts "effectively closed overnight after just two £50 bets"; stake factors cut to 50p–£10 max win; fixed-price betting removed (SP only) ([The Racing Forum](https://theracingforum.co.uk/forums/topic/restricted-stakes/), [OLBG](https://www.olbg.com/bookmakers/articles/bookmaker-restrictions)). Ireland mirrors the UK — same operators, and Irish forums list restrictions as a top punter complaint ([OLBG IE](https://www.olbg.com/ie/bookmakers/articles/bookies-that-dont-limit-winners)).
- **Design implication**: a value-betting app whose signal beats the market will get its bookmaker accounts limited within weeks; the exchange (Betfair does not restrict winners — it monetises them via commission/Expert Fee) is the only stable venue for sustained automated staking.

### 5.2 Exchange costs summary (Ireland)

- Betfair: **2%** achievable (My Betfair Rewards Basic), Expert Fee only above £25k/52-week profit ([Bet4bettor](https://bet4bettor.com/my-betfair-rewards/), [Racing Post](https://www.racingpost.com/news/britain/betfair-exchange-to-introduce-new-commission-system-for-2025-as-premium-charge-is-dropped-a7wbg0v4GCAJ/)).
- Matchbook **2%** (UK/IE), Smarkets **2%** (1% Pro / 3% Select), Betdaq **2%** ([sources above](#2-other-exchanges-usable-from-ireland)).

### 5.3 Best Odds Guaranteed as a value source

Most Irish-facing bookmakers pay the bigger of taken price vs SP on UK/IRE racing: bet365 (early prices from previous evening), Paddy Power, BoyleSports, William Hill (cap £2,500), BetVictor (from 9am, £25k cap), BetGoodwin (from 7am) ([OLBG IE BOG list](https://www.olbg.com/ie/bookmakers/articles/best-odds-guaranteed-ireland), [GG.co.uk IE](https://gg.co.uk/ie/bookmaker/best-odds-guaranteed-bookmakers/)). BOG is genuinely free EV for early-price value bets — but it is a promotion, routinely **removed from restricted accounts** (and unavailable on Betfair's 2%-commission Basic plan), so it accelerates the limiting described above. Note BOG availability is promo-dependent and should be re-verified at build time.

### 5.4 Each-way / place markets

Bookmaker each-way terms (esp. extra-place offers) are a classic value pocket but only accessible manually/via restricted accounts. On Betfair, "To Be Placed" markets carry ~**25–40% of win-market volume** ([Betfair Square](https://betfairsquare.com/sports/horse-racing)) — modelling place probabilities is viable on good cards, thin on Irish midweek ones. BSP exists for both win and place markets and is published free ([BSP files](https://promo.betfair.com/betfairsp/SP_history.html)).

### 5.5 Automation legality/ToS by platform

- **Betfair**: bots expressly allowed; personal live key £499; vendor licence needed to run for others ([T&Cs](https://support.betfair.com/app/answers/detail/betfair-general-terms-and-conditions)).
- **Matchbook**: API + bots allowed under fair use ([FAQ](https://developers.matchbook.com/docs/faq)). **Betdaq**: API explicitly built for automated trading ([Betdaq docs](https://api.betdaq.com/v2.0/Docs/WhatIsTheAPI.aspx)). **Smarkets**: allowed once your application is approved ([Smarkets help](https://help.smarkets.com/hc/en-gb/articles/34697834941085-Smarkets-API-Access-Integration-T-Cs)).
- **Bookmakers**: automation is a breach everywhere; bet365's terms authorise immediate closure and confiscation for bots/scrapers ([bet365 closure analysis](https://www.thecreditpeople.com/credit/bet365-account-closure-reasons-nature-business)).
- **Scraping odds** from bookmaker sites/Oddschecker: breaches their ToS, triggers IP blocking, and puts any linked betting accounts at risk; licensed feeds (The Racing API, Goalserve, OddsMatrix) exist at hobby-to-SME prices, so scraping is unnecessary as well as fragile.
- **Irish regulatory backdrop**: the Gambling Regulation Act 2024 / GRAI licensing regime is rolling out during 2025–2027; a personal-use bot betting your own money on licensed operators is unaffected, but any *product* that facilitates betting for others may need to consider GRAI B2B licensing — flag for later legal review (fast-moving; verify at build time).

## 6. Comparison with the greyhound project

| Axis | Greyhounds (what you hit) | Horse racing (IRE/UK) |
|---|---|---|
| Exchange liquidity | Top BAGS race rarely clears £150k; many races £30k or less; one or two bets can move the BSP ([Betfair Square greyhounds](https://betfairsquare.com/blog/betfair-greyhound-trading-strategies-guide), [Caan Berry BSP](https://caanberry.com/bsp-betfair-starting-price/)) | £3–8M per Saturday Class 1–3 race; £15–40M festival races; BSP highly efficient and hard to skew ([Betfair Square](https://betfairsquare.com/sports/horse-racing)) |
| Odds feeds | Almost no licensed multi-bookmaker greyhound odds feed at consumer prices | The Racing API: 20+ bookmakers' UK/IRE racing odds from ~£24.99/mo; Betfair full depth via API |
| Historical odds/market data | Sparse | Betfair Stream recordings of every market since 2016 (Basic tier free) + free BSP CSV archive |
| Bet-placement integration | Same bookmaker wall, but no liquid exchange fallback | Fully-supported, ToS-legal Betfair/Matchbook/Betdaq APIs |
| Media/data ecosystem | Thin | Deep (racecards, ratings, form APIs — see companion research docs) |

**Conclusion**: horse racing is materially better on every dimension that blocked the greyhound app. The two honest caveats are (1) Irish midweek liquidity is the weak end of the horse-racing spectrum and overall racing exchange turnover is trending down (-4.3% y/y), and (2) bookmaker-side "value vs odds" can be *displayed* but not durably *exploited* through retail accounts — the sustainable execution venue is the exchange, priced against BSP/exchange odds with 2% commission baked into the value calculation.

## Recommended integration architecture

1. **Odds in**: The Racing API (bookmaker odds, ~£24.99/mo) + Betfair delayed key (exchange odds, free) during development.
2. **Backtesting**: free Betfair BSP CSVs + Basic historic Stream data; buy Advanced/Pro months only for the markets the model trades.
3. **Execution**: Betfair live key (£499 one-off), 2% commission plan, Stream API for price triggers; optional Matchbook/Betdaq accounts for stray value.
4. **Bookmaker value surface**: display-only with deep links (affiliate), BOG-aware EV calc, explicit user warning about limiting.

## Sources

- https://support.developer.betfair.com/hc/en-us/articles/115003864531-Are-there-any-costs-associated-with-API-access
- https://support.developer.betfair.com/hc/en-us/articles/115003860331-How-do-I-activate-my-Live-App-Key
- https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687105/Application+Keys
- https://betfair-developer-docs.atlassian.net/wiki/spaces/1smk3cen4v3lu3yomq5qye0ni/pages/2687478/Market+Data+Request+Limits
- https://support.developer.betfair.com/hc/en-us/articles/115003864671-What-data-request-limits-exist-on-the-Exchange-API
- https://botblog.co.uk/betfair-api-key/
- https://developer.betfair.com/ and https://developer.betfair.com/en/historical-data-services-api/
- https://historicdata.betfair.com/ and https://historicdata.betfair.com/Betfair-Historical-Data-Feed-Specification.pdf
- https://betfair-datascientists.github.io/data/usingHistoricDataSite/
- https://www.betfair.com.au/hub/education/how-to-model/historical-data-sources/
- https://promo.betfair.com/betfairsp/SP_history.html and https://promo.betfair.com/betfairsp/prices
- https://www.racingpost.com/news/britain/betfair-exchange-to-introduce-new-commission-system-for-2025-as-premium-charge-is-dropped-a7wbg0v4GCAJ/
- https://bet4bettor.com/my-betfair-rewards/ ; https://www.teamprofit.com/betfair-rewards
- https://support.betfair.com/app/answers/detail/betfair-general-terms-and-conditions
- https://betfairsquare.com/sports/horse-racing ; https://betfairsquare.com/blog/betfair-greyhound-trading-strategies-guide
- https://forum.betangel.com/viewtopic.php?t=28100 ; https://forum.betangel.com/viewtopic.php?t=24420 ; https://forum.betangel.com/viewtopic.php?t=15763
- https://www.geekstoy.com/forum/forum/betting-trading/traders-exchange/11754-the-liquidity-in-uk-and-ire-horse-racing
- https://developers.matchbook.com/ ; https://developers.matchbook.com/docs/faq ; https://b2b.matchbook.com/
- https://matchbookbetting.co.uk/commission/ ; https://www.compare.bet/betting/matchbook
- https://sbcnews.co.uk/sportsbook/2020/04/08/ukgc-suspended-matchbook-licence-over-aml-risk-assessment-failures/
- https://www.egr.global/intel/news/matchbook-relaunches-to-uk-players-as-uk-licence-suspension-is-lifted/
- https://help.smarkets.com/hc/en-gb/articles/34697834941085-Smarkets-API-Access-Integration-T-Cs ; https://docs.smarkets.com/ ; https://help.smarkets.com/hc/en-gb/articles/212654665-Smarkets-commission-FAQ
- https://mybettingsites.com/ie/smarkets
- https://api.betdaq.com/v2.0/Docs/Intro.aspx ; https://betdaq.zendesk.com/hc/en-gb/articles/360020067139-API-access ; https://betdaqpro.com/api-technical-information/
- https://punter2pro.com/betdaq-review-free-bet/ ; https://www.egr.global/intel/news/entain-sells-betdaq-back-to-billionaire-businessman-dermot-desmond/
- https://betinasia.com/sports-betting-api/ ; https://betinasia.zendesk.com/hc/en-us/articles/360013835620-Can-I-have-an-API-connection-on-BetInAsia-BLACK ; https://arbusers.com/betinasia-api-commission-t9416/
- https://www.mollybet.com/home ; https://api.mollybet.com/docs/ ; https://bookie.broker/mollybet/
- https://the-odds-api.com/ ; https://the-odds-api.com/sports-odds-data/sports-apis.html
- https://www.theracingapi.com/ ; https://sourceforge.net/software/product/The-Racing-API/ ; https://rapidapi.com/theracingapi/api/the-racing-api1/details
- https://opticodds.com/sports-betting-api ; https://developer.opticodds.com/reference/getting-started ; https://oddspapi.io/blog/oddsjam-api-alternative/ ; https://sportsgameodds.com/blog/comparing-odds-api-providers
- https://odds-api.io/ ; https://odds-api.io/sportsbooks/paddy-power ; https://365oddsapi.com/bookmakers-api/paddypower-api/
- https://www.oddschecker.com/ ; https://www.oddschecker.com/myoddschecker/terms-and-conditions
- https://www.ukbookmakers.org.uk/2025/07/more-than-600000-uk-punters-have-accounts-restricted/
- https://justiceforpunters.org/campaigning/how-many-people-have-restricted-betting-accounts/ ; https://justiceforpunters.org/restrictions-closures/
- https://www.racingpost.com/news/are-bookmakers-unfairly-closing-customer-accounts-views-from-tuesdays-debate-atwtK6X6m2pt/
- https://theracingforum.co.uk/forums/topic/restricted-stakes/ ; https://www.olbg.com/bookmakers/articles/bookmaker-restrictions ; https://www.olbg.com/ie/bookmakers/articles/bookies-that-dont-limit-winners
- https://www.olbg.com/ie/bookmakers/articles/best-odds-guaranteed-ireland ; https://gg.co.uk/ie/bookmaker/best-odds-guaranteed-bookmakers/
- https://www.ontheballbets.com/betting-guides/bet365/account-restricted/ ; https://www.thecreditpeople.com/credit/bet365-account-closure-reasons-nature-business
- https://github.com/xjxckk/BetLink-bet365-place-bet-api-service
- https://caanberry.com/bsp-betfair-starting-price/
- https://www.goalserve.com/en/sport-data-feeds/horse-racing-api/prices ; https://oddsmatrix.com/sports/horseracing/

*Verification gaps flagged: exact Betfair Advanced/Pro historic-data GBP prices (login-gated); OpticOdds/OddsJam and odds-api.io horse-racing coverage (unconfirmed); no published per-race matched-volume statistics specific to Irish midweek cards; The Racing API tier names/prices above £24.99 (site pricing section JS-gated). Figures dated 2025–2026 unless noted; £299 Betfair fee and pre-2025 Premium Charge are confirmed stale.*
