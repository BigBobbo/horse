# Commercial Horse-Racing Betting-Edge Apps, Tools & Services — UK & Ireland (Audit, August 2026)

Research audit for the feasibility of an Ireland-first horse-racing bet-suggestion app (historical results + predictive model + value-vs-odds). Information gathered 2026-08-28; anything older than 2024 is flagged where known.

## Key takeaways

- **The market splits into six archetypes**: (1) big-media subscriptions (Racing Post, Timeform), (2) ratings/racecard toolkits (Geegeez Gold, Inform Racing, Paceform), (3) database/system builders (HorseRaceBase, Proform, Smartform, FlatStats), (4) tipster marketplaces & free-tips affiliate sites (OLBG, MyRacing, Betting Gods, Tipstrr), (5) odds/value screens (Oddschecker+, ITV OddsFinder, Tilt The Odds), and (6) a new wave of small AI-predictor apps (Hedge/Equotion, Horserace-iQ+, EquiAnalytix, Tegabet).
- **Price anchors**: serious punter tools cluster at **£30–£50/month** (Geegeez £36, Inform £36, Timeform Race Passes ~£30, Paceform £30, Racing Post+ Ultimate £49.99, LightSpeed £49.99+VAT); tipster subscriptions cluster at **£19–£29/month**; free products monetise via **bookmaker affiliate commission**.
- **Almost nobody sells a genuine predictive model.** Nearly every commercial product sells *data + filters + human opinion* (ratings, flags, system builders, tipsters). Machine-learning probability outputs are only offered by tiny newcomers (Hedge, Horserace-iQ+ — the latter had ~9 paying users). This is a real gap, but also a signal about what the paying market currently buys.
- **Ireland is served as an appendage of the British market**, not as a standalone market. Racing Post, Timeform, At The Races, Geegeez, HorseRaceBase and Betwise Smartform all cover Irish racing alongside GB; Inform Racing only added Irish cards on 21 Oct 2024; FlatStats and several legacy tools are GB-only. There is **no significant Ireland-only paid analytics product** — Irish-focused services are free tips sites (irishracing.com) and small tipster subscriptions.
- **Timeform is in managed decline as a consumer brand**: print annuals ended 2020, B2B data supply handed to PA Betting Services in 2024, and in July 2026 it announced the end of its printed racecard, with *Horses to Follow* moving behind the Race Passes paywall. It remains owned by Flutter (via Betfair's 2006 £15m acquisition).
- **Legacy desktop software is dying** (Raceform Interactive is still sold as PC software; RaceAdvisor's Racing Dossier appears moribund; Adrian Massey's free ratings site closed in 2011), while browser-based toolkits (Geegeez, HorseRaceBase) and apps are where active development is.

---

## 1. Big-media incumbents

### 1.1 Racing Post (Racing Post+ / Members' Club)

- **Business model**: freemium media subscription, rebranded from "Members' Club" to **Racing Post+** ([announcement](https://www.racingpost.com/news/introducing-racing-post-the-new-name-for-our-digital-subscriptions-aIrF57G4GouN/)). Three tiers: **Tipping** (access to tipsters Tom Segal/Pricewise, Paul Kealy, Johnny Dineen, Steve Palmer — advertised "from 57p a day", ≈£17/mo), **Insights** (cards, statistics, closing-stages replays, race analysis — "from 38p a day", ≈£11/mo), and **Ultimate** (£49.99/month full price; everything incl. digital newspaper and full video replays) ([Racing Post subscriptions](https://www.racingpost.com/subscriptions/); tier prices per search results citing [Racing Post help](https://help.racingpost.com/hc/en-us/articles/211366149-More-Information-about-Racing-Post-Services) — *prices from aggregated snippets; racingpost.com blocks robot fetches, so verify on-site*). Heavy intro discounting is constant (e.g. Ultimate first two months at £9.99 with code SUMMER, [offer page](https://www.racingpost.com/landing/offers/welcome-offer-summer/); "50% off three months" [offer](https://www.racingpost.com/landing/offers/members-club-welcome-offer/)).
- **How it works**: human tipsters + the industry-standard form database. Racing Post Ratings (RPR) and Topspeed are expert-maintained, not an exposed model. Also monetises data via B2B (Racing Post is the GB/IRE data brand of Spotlight Sports Group).
- **Features**: full racecards, results and form archive, tracker (horse alerts), Predictor tool, statistics database (trainer/jockey/sire), digital paper, replays now inside the app ([app announcement](https://www.racingpost.com/news/introducing-members-club-content-on-the-racing-post-app-aSXHU2n4EzPL/)), free-bets/affiliate links throughout.
- **Ireland**: first-class. Racing Post is effectively the paper of record for Irish racing too (full Irish cards, Irish edition, Irish tipsters like Johnny Dineen).

### 1.2 Timeform (site + Race Passes; Betfair/Flutter-owned)

- **Ownership/trajectory**: acquired by Betfair (Portway Press Ltd) in 2006 for **£15m**; now inside **Flutter Entertainment**. 2020: closed mail-order publishing (end of *Racehorses of…* annuals after 73 volumes, *Chasers & Hurdlers*, weekly Black Book). **2024**: B2B commercial data supply handed to **PA Betting Services** (PA Media Group). **13 July 2026**: announced discontinuation of the printed racecard and migration of *Horses to Follow* to a Race Passes-only digital product ([Cutting Comment, "Timeform: The Slow Death of the Punters' Bible"](https://cuttingcomment.com/timeform-the-slow-death-of-the-punters-bible)).
- **Business model**: freemium. Free racecards/results with basic info + odds-comparison affiliate links; **Race Passes** paywall for ratings/analysis: **£1.50 single race**, timed passes from **~£5–£10 per 24h**, subscription **~£30/month** ([Sporting Life launch article, June 2021](https://www.sportinglife.com/racing/news/ultimate-form-guide-for-only-pound30/192190); [Race Passes subscribe page](https://www.timeform.com/horse-racing/race-passes/subscribe) — *timeform.com blocked direct fetch (403); £30/mo cross-checked via search snippets, treat exact current price as needs-verify*).
- **How it works**: the original ratings house — master ratings in lbs maintained by handicappers, plus **Timeform Flags** (Horse In Focus, Warning Horses, Horses For Courses, Trainer/Jockey Uplift, sectional-timing flags, trainer form) ([Timeform glossary](https://www.timeform.com/horse-racing/features/guides/glossary)). Pace maps, analyst verdicts, full performance histories. It sells *opinion encoded as ratings*, not a model.
- **Ireland**: covers "every runner in every race in Britain and Ireland" ([Sporting Life](https://www.sportinglife.com/racing/news/ultimate-form-guide-for-only-pound30/192190)).
- **B2B note**: Timeform data (incl. for one-off projects) is now licensed via PA Betting Services — relevant if the user ever wants to license ratings.

### 1.3 Sporting Life (free, Flutter-adjacent media)

Free racecards, results, news and tips; racecards carry **Topspeed-style speed figures** and a free "Racecards Plus" enhanced card with **runner-by-runner Timeform comments** for (free) Sporting Life Plus members ([sportinglife.com racecards](https://www.sportinglife.com/racing/racecards); [App Store listing](https://apps.apple.com/gb/app/sporting-life-horse-racing/id1345907668)). Affiliate/ad monetisation. Covers UK & Ireland.

### 1.4 At The Races / Sky Sports Racing (free)

- **Ratings Hub** — free and exclusive to attheraces.com: four ratings per runner (**Official (BHA/HRI), Speed** (best of last 6 runs/12 months, weight-adjusted), **Form**, **FormPlus** (form adjusted "for today's variables")), plus attribute ticks for scope, conditions suitability, trainer form, jockey form, attitude. Covers **British and Irish** fixtures (e.g. Curragh listed) ([ATR Ratings Hub](https://www.attheraces.com/tips/atr-tipsters/ratings-hub)).
- Free tips section aggregating ATR tipsters incl. Irish racing ([ATR tips](https://www.attheraces.com/tips)). Monetised by bookmaker advertising/affiliates (Sky Sports Racing media property).

### 1.5 Racing TV (subscription broadcaster with tools)

**£29.98/month** standard (Sky channel option £24.98; a well-publicised Oddschecker+ Premium perk cuts it to £11.99/mo for 12 months). Shows racing from **61 GB & Irish racecourses** (Racing TV holds the Irish media rights), app includes **racecards with Timeform premium ratings**, Oddschecker price comparison and results ([Oddschecker promo article, Mar 2025](https://www.oddschecker.com/insight/horse-racing/20250308-racing-tv-promo-code-save-60pp-on-racing-tv-with-oddscheckerplus-premium); [Racing TV app listing](https://apps.apple.com/gb/app/racing-tv-live-horse-racing/id352776768)). For an Ireland-first product, note: **Irish racing pictures live behind Racing TV's paywall**, which constrains any "watch + bet" feature.

### 1.6 irishracing.com (free, Ireland-focused)

Free daily tips, racecards, entries and results for **every Irish (and UK) race** ([irishracing.com tips](https://www.irishracing.com/tips/today); [racecards](https://www.irishracing.com/racecards)). Affiliate/ads model. Notable as one of the very few Ireland-first products — and it is content/tips, not analytics.

---

## 2. Ratings & racecard toolkits (the direct comparables)

### 2.1 Geegeez Gold — the benchmark racecard toolkit

- **Price**: **£36/month**, **£360/year** (2 months free), **£1 for 30-day trial**; price grandfathered at sign-up rate ([Geegeez Gold FAQ](https://www.geegeez.co.uk/geegeez-gold-faq/); [Trustpilot 4.8/5](https://uk.trustpilot.com/review/geegeez.co.uk)).
- **How it works**: data + interactive filters, not a model. Tools: **Query Tool** (custom historical queries), **Instant Expert** (auto form-suitability matrix), **Draw & Pace analysers**, **Full Form Filter**, reports (The Shortlist, Trainer/Jockey Combo, Handicap First Time, Trainer Change), **Tracker**, Stat of the Day tips, subscriber forum ([FAQ](https://www.geegeez.co.uk/geegeez-gold-faq/)). 2025 additions: **TRENDS tab** (Jan 2025), AvOR average-official-rating race-quality metric, **Betfair SP/Place SP/in-running price data** in results, video replays of all UK/Irish races ([Gold category updates](https://www.geegeez.co.uk/category/gold/)).
- **Ireland**: full British **and Irish** coverage — one of the best Irish-inclusive toolkits.
- **Business model note**: subscription plus affiliate links; owner Matt Bisogno also monetises via content marketing. This is the closest existing product to "racecards that surface angles" and the main UX benchmark.

### 2.2 Inform Racing — speed ratings + system builder

- **Price**: **£36/month (£30+VAT)**, **£84/3 months (£70+VAT)**; free tier = one full ratings meeting per day "for life", no card required ([subscriptions page](https://www.informracing.com/subscriptions/)).
- **How it works**: proprietary **speed ratings** per run (Master, M+A = master + avg of last 3, class/dist/going splits); colour-coded ratings racecards; **System Builder** with ~50 form categories and 20+ speed-rating options, CSV export, saved queries ([system builder tool](https://www.informracing.com/system-builder-tool/)); also a Betting Tissue tool (turns ratings into odds — i.e., a value screen) and In-Running trading tool.
- **Ireland**: **Irish race cards and Irish speed ratings added 21 October 2024** (ratings compiled since 1 June 2024 by a long-term subscriber) ([announcement](https://www.informracing.com/irish-race-cards-and-irish-speed-ratings/)) — i.e., Irish depth is still shallow (≈2 years of ratings history as of mid-2026).

### 2.3 Paceform Figures — flat-only speed figures

**£10/week or £30/month ("Paceform Platinum") recurring; £12/7-day or £35/30-day one-off passes** ([plans & pricing](https://www.paceformfigures.com/plans-pricing)). Objective, measured-performance speed figures for **UK & Irish Flat racing only** (no jumps — a big gap for Ireland, where NH dominates winters), plus "Paceform Qualifiers" (pre-filtered runners) ([paceformfigures.com](https://www.paceformfigures.com/); [methodology](https://www.paceformfigures.com/behindthefigures)).

### 2.4 RaceAdvisor / Racing Dossier — stale/legacy

RaceAdvisor (Michael Wilding) historically sold **Racing Dossier**, a Windows desktop tool exposing **400–490 pre-built ratings** with custom race-card filters and CSV/bot export ([review on classic.raceadvisor.co.uk](https://classic.raceadvisor.co.uk/racing-dossier-review/); [software listing](https://raceadvisor-racing-dossier.software.informer.com/)). Current product line has shrunk to daily **RA ratings sheets at £0.87/day** with no subscription ([raceadvisorproducts.co.uk/ratings](https://raceadvisorproducts.co.uk/ratings) — page intermittently 404s). The main raceadvisor.co.uk site blocks fetches and its review content lives on a "classic." archive subdomain. **Assess as stale/declining as of 2026; could not verify Racing Dossier is still purchasable.**

### 2.5 New-wave AI predictor apps (small, mostly 2024–2026 launches)

- **Hedge (hedge.tips) / Equotion**: Equotion claims to analyse "fifty million data points per day and fifteen years of racing history" to predict every UK & Irish race, with a portal integrating the **Betfair Exchange** for back/lay/hedge execution ([equotion.com](https://equotion.com/)); Hedge is its consumer app, free to download ([hedge.tips](https://www.hedge.tips/)). Monetisation unclear (likely freemium/affiliate) — **could not verify pricing**.
- **Horserace-iQ+**: solo-operator AI predictions for UK & Ireland; calibrated win/place probabilities, three named strategies (claimed +16.5% ROI "80/20 Method"), published backtest of 78,618 predictions/9,798 tracked bets; **free tier (5 races/day), £19.99/mo or £199/yr "founding member"**, capped at 50 subscribers with **9 registered users** at time of fetch ([horserace-iq.co.uk](https://horserace-iq.co.uk/)). Illustrates both the gap (nobody big does this) and the tiny current market for raw model output.
- **EquiAnalytix** (analytics/speed-ratings app, [equianalytix.com](https://www.equianalytix.com/)) and **Tegabet** ("Ask AI" predictions/alerts for UK & Ireland, [tegabet.com](https://www.tegabet.com/)) — small app-store products, pricing not verified.
- **Tilt The Odds**: data-driven value finder scanning **50+ bookmakers in real time** for out-of-line horse-racing odds ([tilttheodds.co.uk](https://www.tilttheodds.co.uk/)) — the closest thing found to a commercial "perceived value vs available odds" screen.

---

## 3. Database & system-builder products (for DIY edge-hunters)

### 3.1 HorseRaceBase

Browser-based UK & Ireland database with **200+ filter categories** in its System Builder, a **Ratings Machine** (build your own ratings), reports, "shared systems", and a newer **HRB Focus** toolset (RapidView, Stars & Slumps, Comment Shaper) ([horseracebase.com](https://www.horseracebase.com/index.php); [system builder help](https://www.horseracebase.com/v4help.php)). **7-day free trial, no card** ([signup](https://www.horseracebase.com/horseracebase_signup.php)). Pricing is deliberately low and semi-opaque — historically a **donation-style ~€7.50/month minimum** ([Geegeez review, Jan 2011 — old, flag](https://www.geegeez.co.uk/horseracebase-review-2/)); current exact price **could not be verified** (not published pre-signup). Widely named alongside Geegeez/Proform as one of the three standard system-builder tools ([Gwdihw Racing](https://gwdihwracing.substack.com/p/finding-the-criteria-for-systems)).

### 3.2 Proform Racing

Professional-grade Windows database + analysis suite: 17+ year database, daily stats/"signposts", sectional timing data, race simulations, in-running module, **Betfair integration**, custom reports. Pricing has moved around: legacy tiers were £10/24h, £20/week, £50/4 weeks, **£195/8 weeks Platinum** (from ~2020 reviews, [Jamie Anderson review](https://www.jamie-anderson.com/proform-racing-review-discount-code/)); a 2025 comparison lists it at **£50/month** ([LightSpeed comparison](https://lightspeedstats.com/horse-racing/horse-racing-system-builders/)). Official pricing pages returned server errors during this audit ([proformracing.com](https://www.proformracing.com/home.html)) — **current price needs on-site verification**. Known for steep learning curve, dated interface. **Irish coverage could not be verified** (historically GB-focused).

### 3.3 Betwise Smartform — the modeller's database

Most relevant to the user's build: a **fully programmable MySQL horseracing database** covering **all UK and Irish racing**, Flat and NH — results from **1 Jan 2003**, advance racecards from 2000; daily automated updates (next-day final racecards at 19:30, results after racing). **£195 initial purchase + £65/month** (multi-month discounts; first month free) ([betwise.co.uk/smartform](https://www.betwise.co.uk/smartform); [field docs PDF](https://www.betwise.co.uk/smartform_database_fields.pdf)). This is a data product rather than an app, but it is the commercial baseline for "20 years of GB+IRE form in a queryable DB".

### 3.4 Raceform Interactive (Racing Post shop) — legacy but alive

PC (Windows) form-book software using **official BHA results** plus Raceform expert analysis; stats on trainers/jockeys/owners/pedigrees/sales; query/systems analyser. Sold via the Racing Post shop: monthly subscription product listed at **£72.00**, single-code (Flat-only/Jumps-only) year products around **£47**, and season packages "now until end of 2025" ([shop listing](https://shop1.racingpost.com/products/raceform-interactive-flat-jumps-monthly-subscription); [2025 package](https://shop1.racingpost.com/products/raceform-interactive-flat-jumps-2025)). Still sold as of the 2025 products, but it is legacy desktop software; **Irish coverage not stated on product pages — could not verify**.

### 3.5 FlatStats — flat/AW only, GB

Database of **every GB flat turf & all-weather race since 1990**; System Builder + Laying System Builder, ratings, daily qualifier alerts. **From ~94p/day on a 3-month subscription; £10 7-day trial**; one-off payments, no auto-rebill ([flatstats.co.uk](https://www.flatstats.co.uk/); [subscription page](https://www.flatstats.co.uk/join/flatstats-subscription.php)). No jumps, effectively no Irish focus — limited use for an Ireland-first product.

### 3.6 Others

- **LightSpeed Stats**: newer backtesting/strategy builder aimed at Betfair users; **£24.99+VAT first month, £49.99+VAT thereafter**; rapid backtesting, automated daily picks, data export ([lightspeedstats.com](https://lightspeedstats.com/horse-racing/horse-racing-system-builders/) — note this comparison is LightSpeed's own marketing).
- **BetTurtle**: automated pre-built systems/selections, tiers **£10/£25/£79 per month** (Basic/Enhanced/Professional) ([betturtle.com](https://www.betturtle.com/filters/freesystem/); tier prices via LightSpeed comparison).
- **Adrian Massey** (free ratings site beloved by system players) **closed March 2011** ([Honest Betting Reviews](https://www.honestbettingreviews.com/adrian-massey/)) — still cited in stale "best sites" roundups (e.g. [Punter2Pro's 2026 list](https://punter2pro.com/best-horse-racing-form-stats-database/) lists it as free/active — treat that entry as stale).

---

## 4. Tipster ecosystems (marketplace & affiliate models)

- **OLBG**: entirely **free to users**; revenue is **bookmaker affiliate commission** on sign-ups/bets. Community tipsters compete for **£6,000+ monthly cash prizes (800 monthly prizes; >£1m paid out historically)**; leaderboards create the content ([tipster competition](https://www.olbg.com/tipster-competition); [how to use OLBG](https://www.olbg.com/bookmakers/articles/how-use-olbg); [Mike Cruickshank review of the affiliate mechanics](https://mikecruickshank.com/olbg-review-will-the-tipsters-make-you-any-money/)). Dedicated **Irish racing tips pages** ([OLBG Irish tips](https://www.olbg.com/betting-tips/Horse_Racing/IE/2)). Apps on iOS/Android; betting integration limited to UK & Ireland punters.
- **MyRacing** (Spotlight Sports Group): free tips site (launched 2013 as Horse Racing Super Tips) — NAP of the day, accas, Lucky 15s, plus UK & Ireland racecards; monetised via a formal **affiliate programme with on-site bet slips and odds-comparison grids** ([about page](https://myracing.com/about-myracing-com/); [myracing.com](https://myracing.com/)).
- **Betting Gods**: proofed-tipster marketplace; tipsters must pass a **minimum 16-week proofing**; typical price **£29/month per tipster, £19 first month**, and a **15-tipster bundle at £79/month or £790 lifetime** ([bettinggods.com](https://bettinggods.com/); [bundle offer](https://bettinggods.com/limited-offer/)).
- **Tipstrr**: verified-tipster platform, **£0–£30/month per tipster** (top tipsters ~£29/mo; trials £8.70–£14.50/30 days); free account, automated ROI tracking ([tipstrr.com horse racing](https://tipstrr.com/horse-racing); [platform comparison](https://www.bettoredge.com/post/tipster-platforms-comparison)). Tipstrr's commission split with tipsters was **not verifiable** from public pages.
- **From The Stables**: trainer-quotes service (Tony Stafford) since 2010 — daily quotes direct from yards, **£30/month**; topped the William Hill Naps table 2018/2019/2021 ([fromthestables.com](https://www.fromthestables.com/); [Info From The Stables](https://infofromthestables.co.uk/)). Mostly GB yards — connection-driven "info" rather than data.
- **Racing To Profit** (Josh Wright): trainer-pattern/stats membership, ~**$199 per 6 months** via Clickbank with 60-day guarantee ([review](https://bettingsystemempire.com/racing-to-profit-reviews/); [racingtoprofit.co.uk](https://racingtoprofit.co.uk/meet-josh/)).
- **Betting School Insiders Club** (Darren Power, est. 2005): weekly members' reports/systems; **merged with On Course Profits in 2015**; still referenced by On Course Profits pages (last confirmed activity Nov 2024) but no independent 2025-26 signal — **treat as stale/possibly dormant** ([racing-index profile](https://mail.racing-index.com/horseracing/bettingschool/); [On Course Profits about](https://www.oncourseprofits.com/about-us/)).
- **Ireland-specific tipping**: thin. Free: irishracing.com, OLBG IE pages, CopyBet's Irish tips hub ([copybet.com](https://www.copybet.com/betting-tips/irish-racing-tips/)). Paid: "The Irish Line" tipster subscription ([allsportstips.com](https://www.allsportstips.com/product/the-irish-line/)) and assorted social-media tipsters. **No Irish equivalent of Geegeez/Timeform exists.**

---

## 5. Odds-comparison & value screens

- **Oddschecker / Oddschecker+**: the default odds-comparison screen (affiliate model). Paid tiers: **Oddschecker+ Essential and Premium — Premium £29.99/month**, adding full tipster columns, **AI-powered Value Bets, Trends and Public Betting Splits** tools, and 60% off Racing TV ([oddschecker.com/plus](https://www.oddschecker.com/plus); [FAQs, Mar 2025](https://www.oddschecker.com/insight/specials/20250308-oddscheckerplus-faqs)). Directly overlaps the user's "value vs odds" pillar — incumbents are now selling "AI value bets" as a feature.
- **ITV OddsFinder**: launched **July 2026** with partner Funteron — free odds-comparison app aggregating live prices from licensed UK bookmakers ([SBC News, 31 Jul 2026](https://sbcnews.co.uk/sportsbook/2026/07/31/itv-launches-oddsfinder-for-racing)). Signals mainstream media pushing into comparison.
- **Timeform odds comparison** (bookies + Betfair Exchange, free, affiliate) ([timeform.com/horse-racing/odds](https://www.timeform.com/horse-racing/odds)).
- **Tilt The Odds** (see §2.5) and **FormGenie** (odds-comparison grid) round out the niche.

---

## 6. Ireland coverage scorecard

| Product | Irish racing? | Notes |
|---|---|---|
| Racing Post / Racing Post+ | Full | Paper of record for IRE; Irish tipsters, full cards/results |
| Timeform Race Passes | Full | "Every runner in every race in Britain and Ireland" |
| At The Races Ratings Hub | Full, free | Official (HRI)/Speed/Form/FormPlus for Irish fixtures |
| Sporting Life | Full, free | UK & IRE cards + speed figures |
| Racing TV | Full (paywall) | Holds Irish media rights; Timeform ratings in app |
| Geegeez Gold | Full | UK & Irish cards, replays, Irish data in all tools |
| Inform Racing | Partial | Irish cards/ratings only since 21 Oct 2024; shallow ratings history |
| Paceform | Flat only | UK & Irish Flat; no NH (major gap for IRE) |
| HorseRaceBase | Full | UK & IRE database |
| Betwise Smartform | Full | All UK & Irish racing since 2003 (results) |
| Proform Racing | Unverified | Historically GB-centric — could not verify current IRE coverage |
| Raceform Interactive | Unverified | BHA-results based; IRE coverage not stated |
| FlatStats | No | GB flat/AW only |
| OLBG / MyRacing / irishracing.com | Full, free | Tips + cards for IRE |

**Implication**: an Ireland-first analytics product would compete mainly with the UK-centric incumbents' Irish coverage, not with any Irish native product. The Irish-only niche is unoccupied at the paid-analytics level, but that also reflects market size — Irish racing has ~390 fixtures/year vs ~1,450 in GB, so every commercial player bundles IRE with GB.

## 7. Dead, stale or shrinking (as of 2025–2026)

- **Adrian Massey** — free ratings/stats site, closed March 2011 ([Honest Betting Reviews](https://www.honestbettingreviews.com/adrian-massey/)); still erroneously listed in some 2026 roundups.
- **Timeform print estate** — annuals/Black Book ended 2020; printed racecard + print *Horses to Follow* discontinued per 13 Jul 2026 announcement; B2B handed to PA Betting Services 2024 ([Cutting Comment](https://cuttingcomment.com/timeform-the-slow-death-of-the-punters-bible)).
- **RaceAdvisor / Racing Dossier** — desktop software appears unsupported; site fragmented across classic./products subdomains; only £0.87/day ratings sheets clearly on sale. Could not verify Racing Dossier availability.
- **Betting School Insiders Club** — merged into On Course Profits (2015); no clear 2025-26 activity signal.
- **Raceform Interactive** — still sold (2025 season products) but Windows-only legacy software with an ageing user base.
- **HorseRaceBase pricing** — donation-model info dates to 2011; current pricing undisclosed pre-trial (flagged, not dead).

## 8. What this means for the planned app

1. **Business-model precedent**: sustainable price point for a serious-punter tool is £30–£36/mo (Geegeez/Inform/Timeform); tipster-style output prices at £19–£29/mo; free tiers monetise via bookmaker affiliates (OLBG/MyRacing prove the affiliate model works at scale in UK+IRE).
2. **Feature table stakes** (set by Geegeez/Timeform): full UK+IRE racecards, ratings, trainer/jockey stats, draw/pace analysis, form filters, a tracker/alerts, results archive, and odds links. A model alone won't be perceived as a product without a credible card UI.
3. **Genuine differentiation available**: (a) calibrated probabilities + explicit value overlay vs live odds — only tiny players (Horserace-iQ+, Tilt The Odds) and Oddschecker's new "AI Value Bets" occupy this; (b) Ireland-first depth (Irish sectionals, Irish trainer patterns) which even the incumbents treat as an afterthought; (c) transparent bet tracking/verification, which tipster marketplaces (Tipstrr, Betting Gods) have trained users to expect.
4. **Build-vs-buy input**: Betwise Smartform (£195 + £65/mo) is the off-the-shelf GB+IRE modelling database; Timeform ratings are licensable via PA Betting Services; Betfair historical exchange data is purchasable per-dataset.
5. **Warning from the market**: Horserace-iQ+'s 9 subscribers and the dominance of opinion/ratings brands suggest punters buy *narrative + tools* more readily than raw model output — package model probabilities inside a racecard/value UX rather than as bare predictions.

---

## Sources

- https://www.timeform.com/horse-racing/race-passes/subscribe (403 on fetch; pricing via snippets)
- https://www.sportinglife.com/racing/news/ultimate-form-guide-for-only-pound30/192190 (June 2021)
- https://cuttingcomment.com/timeform-the-slow-death-of-the-punters-bible
- https://www.timeform.com/horse-racing/features/guides/glossary
- https://www.racingpost.com/subscriptions/ ; https://www.racingpost.com/landing/offers/welcome-offer-summer/ ; https://www.racingpost.com/news/introducing-racing-post-the-new-name-for-our-digital-subscriptions-aIrF57G4GouN/ ; https://help.racingpost.com/hc/en-us/articles/211366149
- https://www.geegeez.co.uk/geegeez-gold-faq/ ; https://www.geegeez.co.uk/category/gold/ ; https://uk.trustpilot.com/review/geegeez.co.uk
- https://www.informracing.com/subscriptions/ ; https://www.informracing.com/system-builder-tool/ ; https://www.informracing.com/irish-race-cards-and-irish-speed-ratings/
- https://www.paceformfigures.com/ ; https://www.paceformfigures.com/plans-pricing ; https://www.paceformfigures.com/behindthefigures
- https://www.horseracebase.com/index.php ; https://www.horseracebase.com/horseracebase_signup.php ; https://www.geegeez.co.uk/horseracebase-review-2/ (2011)
- https://www.proformracing.com/home.html ; https://www.jamie-anderson.com/proform-racing-review-discount-code/ ; https://lightspeedstats.com/horse-racing/horse-racing-system-builders/
- https://www.betwise.co.uk/smartform ; https://www.betwise.co.uk/smartform_database_fields.pdf
- https://shop1.racingpost.com/products/raceform-interactive-flat-jumps-monthly-subscription ; https://shop1.racingpost.com/products/raceform-interactive-flat-jumps-2025
- https://www.flatstats.co.uk/ ; https://www.flatstats.co.uk/join/flatstats-subscription.php
- https://classic.raceadvisor.co.uk/racing-dossier-review/ ; https://raceadvisor-racing-dossier.software.informer.com/ ; https://raceadvisorproducts.co.uk/ratings
- https://www.olbg.com/tipster-competition ; https://www.olbg.com/bookmakers/articles/how-use-olbg ; https://www.olbg.com/betting-tips/Horse_Racing/IE/2 ; https://mikecruickshank.com/olbg-review-will-the-tipsters-make-you-any-money/
- https://myracing.com/about-myracing-com/ ; https://myracing.com/
- https://bettinggods.com/ ; https://bettinggods.com/limited-offer/
- https://tipstrr.com/horse-racing ; https://www.bettoredge.com/post/tipster-platforms-comparison
- https://www.fromthestables.com/ ; https://infofromthestables.co.uk/
- https://racingtoprofit.co.uk/meet-josh/ ; https://bettingsystemempire.com/racing-to-profit-reviews/
- https://mail.racing-index.com/horseracing/bettingschool/ ; https://www.oncourseprofits.com/about-us/
- https://www.attheraces.com/tips/atr-tipsters/ratings-hub ; https://www.attheraces.com/tips
- https://www.sportinglife.com/racing/racecards ; https://apps.apple.com/gb/app/sporting-life-horse-racing/id1345907668
- https://www.oddschecker.com/plus ; https://www.oddschecker.com/insight/specials/20250308-oddscheckerplus-faqs ; https://www.oddschecker.com/insight/horse-racing/20250308-racing-tv-promo-code-save-60pp-on-racing-tv-with-oddscheckerplus-premium
- https://sbcnews.co.uk/sportsbook/2026/07/31/itv-launches-oddsfinder-for-racing
- https://www.tilttheodds.co.uk/
- https://equotion.com/ ; https://www.hedge.tips/ ; https://horserace-iq.co.uk/ ; https://www.equianalytix.com/ ; https://www.tegabet.com/
- https://www.betturtle.com/filters/freesystem/
- https://www.irishracing.com/tips/today ; https://www.irishracing.com/racecards ; https://www.copybet.com/betting-tips/irish-racing-tips/ ; https://www.allsportstips.com/product/the-irish-line/
- https://www.honestbettingreviews.com/adrian-massey/
- https://punter2pro.com/best-horse-racing-form-stats-database/ (updated Aug 2026; contains at least one stale entry)
- https://gwdihwracing.substack.com/p/finding-the-criteria-for-systems
