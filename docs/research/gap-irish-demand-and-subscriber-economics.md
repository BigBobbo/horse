# Irish Demand & Subscriber Economics for a Racing Betting-Suggestions App

**Research date:** 28 August 2026. Gap-fill report on the demand side: how many Irish people bet on horse racing, how big the "studies form, would pay ~€30/mo" segment is, what churn/LTV looks like for tipster/analytics subscriptions, and whether the product should be Ireland-only or UK+IRE from day one.

**Method note:** the session's web-search quota was exhausted at the start of this task, so this report was compiled by fetching primary sources directly (HRI Factbook 2025 PDF, ESRI/GRAI study PDF, Revenue.ie excise CSV, BHA data pack PDF, Gambling Commission GSGB pages, Press Gazette, product pricing pages). Every figure below carries its source URL. Items that could not be reached are listed in "Could not verify" — none of them changes the direction of the conclusions.

---

## Key takeaways

- **The Irish betting market is large and racing is central to it.** Irish betting duty (2% of stakes) raised **€141m in 2024** (€46.7m retail + €95.4m remote — [Revenue.ie CSV](https://www.revenue.ie/en/corporate/documents/statistics/excise/net-receipts-by-commodity.csv)), implying roughly **€7bn staked** in 2024 (with a caveat on the remote jump, below). The ESRI/GRAI population study independently estimates Irish adults stake **€6–8bn/yr** ([ESRI RS169](https://www.esri.ie/system/files/publications/RS169.pdf)).
- **~16% of Irish adults (~600k people) bet on horse/dog racing in a given month** — 11.1% online, 8.8% in person (ESRI, Aug–Sep 2023, N=2,850). Of online racing bettors, **~39% bet 2+ times per week** — an engaged core of very roughly **~150–170k** (derived estimate).
- **The paying "serious punter" segment across ALL of UK+Ireland is only tens of thousands.** The Racing Post — the category-defining premium product for both islands — had just **15,000 digital subscribers in mid-2023** at ~£40/mo ([Press Gazette](https://pressgazette.co.uk/publishers/nationals/how-racing-post-survived-pandemic-shutdown-and-bounced-back-to-growth/)), against 500k+ registered (free) OLBG members and 1.1m OLBG app installs ([OLBG](https://www.olbg.com/about-us)). Free-to-paid in this vertical is a ~1–3% game.
- **Ireland is ~7–8% of the UK+IRE adult population and ~21% of the fixture supply** (Ireland ~390 fixtures/yr vs GB 1,427 ran in 2025 — [HRI Factbook 2025](https://www.hri.ie/HRI/media/HRI/Comms/Documents/HRI-Factbook-2025-FINAL-VERSION.pdf), [BHA 2025 data pack](https://www.britishhorseracing.com/wp-content/uploads/2026/05/2025_Annual-Data-Pack-1.pdf)). An Ireland-only paid product fights for perhaps **1,000–3,000 realistically winnable subscribers in total** (estimate) and has no racing to cover on many days.
- **HRI's own commissioned economics report says the quiet part out loud:** "Irish and British racing have such strong links, **they are treated in many ways as a single product**" ([Deloitte/HRI 2023](https://www.hri.ie/HRI/media/HRI/HRI-2023-Deloitte-Social-and-Economic-Impact-Report-FINAL.pdf)). The absence of an Ireland-only paid analytics product looks like rational market structure, not an unserved niche.
- **Churn benchmarks are brutal for consumer subscriptions:** median 12-month retention on monthly plans is **17%** (high-priced monthly: **6.7%**), freemium download→paid conversion medians **2.18%** ([RevenueCat State of Subscription Apps 2025](https://www.revenuecat.com/state-of-subscription-apps-2025/)); Recurly's network benchmark is ~**3.6%/mo churn overall, 4.1%/mo for digital media** ([Recurly, July 2026](https://recurly.com/research/churn-rate-benchmarks/)).
- **Seasonality is extreme:** Racing Post traffic goes from ~300k daily visitors to **1.5m on Cheltenham/Grand National days** (5x) ([Press Gazette](https://pressgazette.co.uk/publishers/nationals/how-racing-post-survived-pandemic-shutdown-and-bounced-back-to-growth/)); ESRI explicitly warns its own spend estimates may be inflated by the Galway Races falling near its survey window (RS169, p.36).
- **Verdict (analyst view): the paying audience exists but is small and UK+IRE-shaped.** Build UK+IRE coverage from day one with Irish-first positioning as the wedge; price at the verified €30–40/mo cluster (Geegeez £36, Betting Gods £29/tipster, SBC £24.99, Racing Post up to £50); plan around a few hundred subscribers in year one, not thousands.

---

## 1. Market size: Irish betting and racing's place in it

### 1.1 Betting duty → total stakes

Ireland levies **2% duty on all bets** placed with bookmakers by customers in Ireland (retail and remote), plus a 25% duty on betting-exchange commission ([Deloitte/HRI 2023](https://www.hri.ie/HRI/media/HRI/HRI-2023-Deloitte-Social-and-Economic-Impact-Report-FINAL.pdf), "Taxation of betting" section). Revenue's official excise receipts ([CSV, last modified 30 May 2025](https://www.revenue.ie/en/corporate/documents/statistics/excise/net-receipts-by-commodity.csv)):

| Year | Traditional (retail) duty | Remote (online) duty | Exchange commissions duty | Total | Implied stakes @2% |
|---|---|---|---|---|---|
| 2020 | €39.0m | €44.9m | €2.8m | €86.8m | ~€4.2bn |
| 2021 | €24.4m | €60.6m | €4.2m | €89.2m | ~€4.2bn |
| 2022 | €45.9m | €49.2m | €3.9m | €99.0m | ~€4.8bn |
| 2023 | €47.5m | €51.3m | €3.8m | €102.7m | ~€4.9bn |
| 2024 | €46.7m | €95.4m | −€0.8m | €141.3m | ~€7.1bn |

**Caveats (important):** the 2024 remote-duty figure nearly doubled year-on-year; HRI notes betting-duty figures are **provisional and collected quarterly in arrears** ([HRI Factbook 2025](https://www.hri.ie/HRI/media/HRI/Comms/Documents/HRI-Factbook-2025-FINAL-VERSION.pdf), betting section), and HRI's 2025 provisional duty figure of **€113.6m (−19.4%)** suggests 2024 contained timing/arrears effects. Treat Irish annual stakes as **~€5–7bn**, of which **remote/online is ~55–67% and rising** (2024 duty split: 67% remote). I could not find a published explanation for the 2024 remote spike — flag as unexplained.

Cross-check: the ESRI/GRAI study independently triangulates **€6–8bn/yr staked** ("industry revenue before winnings are subtracted"), and its own survey-based estimate of adult gambling spend is **€5.5bn/yr** (mean €27/adult/week; its most-accurate panel implied €6.6bn) ([ESRI RS169, Oct 2023](https://www.esri.ie/system/files/publications/RS169.pdf), sections 1.3 and 3). Deloitte/HRI reports betting duty of "a record €102m in 2022... as low as €26m in 2014 before online betting from Irish punters was made subject to the duty" — i.e. the *measured* market tripled once remote was taxed.

### 1.2 Racing-specific betting in Ireland (verified 2025 figures)

From the [HRI Factbook 2025](https://www.hri.ie/HRI/media/HRI/Comms/Documents/HRI-Factbook-2025-FINAL-VERSION.pdf) (published 2026) and [HRI H1-2026 release](https://www.hri.ie/corporate/press-office/press-release/hri-publishes-figures-for-first-six-months-of-2026):

- **On-course bookmaker betting 2025: €82.8m (+9.9%)** (home €70.7m + away €2.5m + SP shops €9.7m).
- **Tote handle 2025: €81.3m (+7.2%)** — €10.6m on-course (+1.9%), €62.8m off-course Irish pools (+9.0%); **World Pool turnover on Irish fixtures €7.9m (+1.3%)**.
- Total on-course + Tote "total betting" 2025: **€156.2m (+9.0%)**.
- H1 2026: on-course bookmaker turnover €34m (−4.8%), Irish Tote pools €31.1m (+11.1%), World Pool €55.4m (+5.7% — note this H1 figure includes co-mingled international pools on Irish classics).
- **Attendance 2025: 1.31m (+6%)** — racing is Ireland's **second-best-attended sport after the GAA**; Punchestown Festival alone 136k (+15%).

**What's missing:** neither HRI, Revenue nor GRAI publishes **off-course betting turnover on horse racing specifically** (duty is collected across all sports/products). Deloitte/HRI describes racing as "a core product" competing with fast-growing sports bet-builders but gives no percentage. **Could not verify racing's exact share of the €5–7bn.** For context only (estimate): if racing's share of Irish off-course betting resembles racing's historic share of UK betting shop/online real-event turnover (roughly a third to a half in retail, lower online), Irish off-course racing stakes would be on the order of **€1.5–3bn/yr** — treat as an unverified order-of-magnitude.

### 1.3 How many Irish adults bet on racing

The ESRI/GRAI population study ([RS169](https://www.esri.ie/system/files/publications/RS169.pdf), fieldwork 21 Aug–5 Sep 2023, N=2,850, weighted to ~3.9m adults 18+):

- **72.9%** of adults gambled in the past year; **74.1% spent money on gambling in the previous 4 weeks** (incl. lotteries); 35.1% gambled online, 60.9% in person.
- **Horse and dog betting in the previous 4 weeks: 16.0% of all adults (all modes) — ≈620,000 people** (derived: 16.0% × 3.9m). Online: **11.1% (~430k)**; in person: **8.8% (~340k)**. It is the most popular non-lottery betting activity alongside sports betting (12.7% online / 5.4% in person).
- **Frequency (online horse/dog bettors):** 22.4% bet ~once a week, 26.2% 2–3×/week, 5.4% 4–5×/week, 7.6% daily — i.e. **~61.6% bet at least weekly and ~39% bet 2+ times/week ⇒ roughly 150–170k engaged online racing bettors** (derived estimate; includes greyhound bettors, so the horse-only figure is somewhat lower).
- Problem gambling: **3.3% of adults (~130,000)** meet the PGSI problem-gambling threshold — ten times prior estimates; another 7.1% (~279,000) show moderate risk. Among problem gamblers, horse/dog betting averaged €29/week (€1,500/yr) of in-person spend. (Relevant for compliance/RG posture of a tips product, and for GRAI's likely attitude to "betting suggestions" marketing.)
- Interest base: a RED C poll (Feb 2022) found **44% of Irish adults are interested in horse racing**, 4th behind rugby (62%), soccer (52%), Gaelic football (49%) ([Deloitte/HRI 2023](https://www.hri.ie/HRI/media/HRI/HRI-2023-Deloitte-Social-and-Economic-Impact-Report-FINAL.pdf)).

### 1.4 UK comparison

- **GSGB annual report 2025** ([Gambling Commission, released 16 Jul 2026](https://www.gamblingcommission.gov.uk/statistics-and-research/publication/gambling-survey-for-great-britain-annual-report-2025-official-statistics); N=20,775, Jan 2025–Jan 2026): **47% of GB adults gambled in the past 4 weeks**; 38% online, 28% in person.
- **Betting participation: 12%** of GB adults in the past 4 weeks (up 3pp) — [GSGB Year-2 wave 2, Apr–Jul 2024](https://www.gamblingcommission.gov.uk/statistics-and-research/publication/statistics-on-gambling-participation-year-2-2024-wave-2-official-statistics) — ≈ **6.3m adults**. **Could not verify the horse-racing-specific GSGB split** from fetchable pages (it lives in the GSGB data tables); do not quote a GB horse-only participation % without pulling those tables.
- Scale of GB racing betting: the statutory Horserace Betting Levy (10% of bookmaker gross profits on British racing above a threshold) yielded **£105m in 2023/24, c.£108m in 2024/25, £103m estimated 2025/26** ([HBLB Business Plan 2025–28](https://www.hblb.org.uk/documents/Executive/HBLB%20Business%20Plan%202025-2028.pdf)) — implying **~£1.0–1.1bn/yr bookmaker gross win on British racing alone**.
- Supply: GB ran **1,427 fixtures in 2025** (1,460 programmed) ([BHA annual data pack 2025](https://www.britishhorseracing.com/wp-content/uploads/2026/05/2025_Annual-Data-Pack-1.pdf)); Ireland stages **~390/yr** (HRI Factbook 2025; H1 2026: 1,288 races).

**Bottom line on market size:** Ireland has a genuinely large per-capita betting market (~€1,300–1,800 staked per adult per year) and ~600k monthly racing bettors. The *demand pool* is real. The question is how much of it buys tools rather than just bets — see next section.

---

## 2. The serious-punter segment: what the paid products reveal

Disclosed audience/subscriber numbers in this vertical (UK+IRE-wide unless noted):

| Product | Model / price | Disclosed scale | Source & date |
|---|---|---|---|
| **Racing Post** (flagship for both islands) | Premium digital ~£39.95/mo (2023); top tier **£50/mo** (2024); print £5/day | **15,000 digital subscribers** (2023); ~50,000 print circulation; ~300k daily site visitors, **1.5m on festival days** | [Press Gazette Jul 2023](https://pressgazette.co.uk/publishers/nationals/how-racing-post-survived-pandemic-shutdown-and-bounced-back-to-growth/); [Press Gazette Oct 2024](https://pressgazette.co.uk/publishers/nationals/why-ft-politico-and-racing-post-charge-big-for-online-news/) ("we are an unashamedly premium product" — editor Tom Kerr) |
| Racing Post (history) | £9.50/mo tipping tier | ~10,000 web subscribers | [Press Gazette, Sep 2009](https://pressgazette.co.uk/news/racing-posts-paid-for-website-approaches-10000-subscribers/) — 14 years to go from 10k to 15k paying |
| **OLBG** | Free, affiliate-funded | **500k+ registered members; 1.1m+ app installs** (founded 2002; 100k members by 2012) | [olbg.com/about-us](https://www.olbg.com/about-us) (fetched Aug 2026) |
| **Geegeez Gold** | **£36/mo**, 30-day free trial | member count not disclosed | [geegeez.co.uk/geegeez-gold](https://www.geegeez.co.uk/geegeez-gold/) (fetched Aug 2026) |
| **Smart Betting Club** | **£24.99/mo / £59.99/qtr / £139.99/yr** (+VAT), running since 2006 | membership not disclosed; "analysed hundreds, proofed thousands of tipster services" | [smartbettingclub.com/subscribe](https://smartbettingclub.com/subscribe/) (fetched Aug 2026) |
| **Betting Gods** | **£19 first month, then £29/mo per tipster; £97/mo VIP all-access** | member counts not disclosed on current site | [bettinggods.com/tipsters](https://bettinggods.com/tipsters/) (fetched Aug 2026) |
| **Tipstrr** | per-tipster subs (prices behind login) | founded 2014; **8.6m tips verified**; user count not disclosed | [tipstrr.com](https://tipstrr.com/) (fetched Aug 2026) |
| **Racing TV** (RMG) | **£29.98/mo (annual) / £39.98 rolling / £10 day pass** | subscriber count not disclosed; covers 61 GB+IRE courses incl. all Irish tracks | [racingtv.com/join](https://www.racingtv.com/join) (fetched Aug 2026) |
| **IrishRacing.com** (the Ireland-branded portal) | **Free**, affiliate/bookmaker-offer funded; covers "Ireland and the UK" | no paid tier at all | [irishracing.com/news](https://www.irishracing.com/news) (fetched 28 Aug 2026, active) |

**Reading the tea leaves:**

1. **The ceiling is visible.** The Racing Post — with a 40-year brand, exclusive content, and the entire UK+IRE market — converts to ~**15k digital payers** at £20–50/mo. Its own free audience is ~300k daily. That is a ~5% engaged-user→payer rate for the strongest brand in the vertical, and it took a pandemic to push subs up 20%.
2. **The free tier is where the volume is.** OLBG (500k+ members) and IrishRacing.com monetize entirely via affiliates. Nobody with a mass racing audience in Ireland has judged a paid Irish tier worth building — OLBG's and IrishRacing's revealed preference is affiliate economics.
3. **Ireland's slice (estimate, clearly flagged):** ROI adults ≈ 3.9m vs GB adults ≈ 53m → Ireland ≈ **7%** of the combined adult pool. Racing over-indexes in Ireland (44% interest; 2nd-most-attended sport), so assume 10–15% of the paying UK+IRE tools market is Irish: **≈1,500–2,500 Irish people currently pay for premium racing analytics of any kind** (derived from Racing Post 15k plus the undisclosed tail of Timeform/Geegeez/SBC/tipsters — order-of-magnitude only).
4. Timeform, At The Races/Sporting Life audiences and Racing TV subscriber counts are **not publicly disclosed** (see "Could not verify").

---

## 3. Willingness to pay, churn, LTV, seasonality

### 3.1 Price anchors (verified, 2025–26)

The market has already set the price band the developer proposes (€30/mo ≈ £26):

- Geegeez Gold **£36/mo** (tools+form product — the closest analogue).
- Betting Gods **£29/mo** per tipster (after £19 first month); SBC **£24.99/mo**; Racing Post premium **~£40–50/mo**; Racing TV **£29.98–39.98/mo**.
- €30/mo sits comfortably in-band. **Note VAT:** Irish B2C digital services carry 23% VAT — €30 gross is **€24.39 net**, so €30/mo × 500 subs is ~€146k/yr net revenue, not €180k.

### 3.2 Churn/retention benchmarks (no racing-specific public data exists; nearest verified proxies)

- **RevenueCat, State of Subscription Apps 2025** (75,000 apps, $10bn+ tracked revenue — [source](https://www.revenuecat.com/state-of-subscription-apps-2025/)):
  - Freemium **download→paid median 2.18%** (hard paywall 12.11%).
  - Trial→paid ~40–46% for 2–4-week trials.
  - **Monthly plans: median 17% of subscribers still active at 12 months**; for high-priced monthly plans **just 6.7%**. Annual plans: 44.1% at 12 months; ~30% of annual subs cancel within the first month; 61.7% of annual survivors renew year 2.
  - Top cancellation reason: "not enough usage" (32–47%) — directly relevant to a picks product whose users lose money in a bad month.
- **Recurly churn benchmarks (July 2026)** ([source](https://recurly.com/research/churn-rate-benchmarks/)): overall churn **3.60%** (2.34% voluntary + 1.25% involuntary); **digital media & entertainment 4.14%** — Recurly reports these as monthly rates across its network (flag: the page's labelling is terse; treat as ~3.5–4%/mo).
- Implication at €30/mo: 5%/mo churn ⇒ mean lifetime 20 months ⇒ **gross LTV ≈ €600 (≈€488 net of VAT)**; at 10%/mo (more realistic for a tips product per RevenueCat's high-priced-monthly cohort) ⇒ **LTV ≈ €300 gross / €244 net**. A blended assumption of **€250–450 net LTV** is defensible; anything above that needs an annual plan and a genuinely sticky toolset.
- **Tipster-vertical specifics: no public churn stats.** Betting Gods'/Tipstrr's own numbers (revenue, subscriber counts, churn) were not retrievable from their current sites, and the old Indie Hackers interview with Betting Gods' founder is no longer accessible — **could not verify** the frequently-cited ~$50–60k/mo revenue figures. SBC's 20-year survival at £25/mo and Geegeez's multi-year testimonials show the *category* retains a hard core, but the universal use of heavy first-month discounts (£19 first month; 30-day free trials; 90-day money-back guarantees) is itself evidence of high early churn and trial-shopping behaviour.

### 3.3 Seasonality (verified signals)

- **Racing Post traffic: ~300k daily → 1.5m on Grand National/Cheltenham days** — a 5x festival multiplier at the top of the funnel ([Press Gazette](https://pressgazette.co.uk/publishers/nationals/how-racing-post-survived-pandemic-shutdown-and-bounced-back-to-growth/)).
- ESRI explicitly warns its Aug–Sep 2023 fieldwork may overstate racing betting because of the **Galway Races** and understate GAA/rugby betting ([RS169](https://www.esri.ie/system/files/publications/RS169.pdf), p.36) — i.e. even the national statisticians treat Irish racing demand as festival-spiked.
- HRI's H1-2026 figures show attendance and Tote handle swing on festival scheduling (Dublin Racing Festival postponement dented H1) ([HRI](https://www.hri.ie/corporate/press-office/press-release/hri-publishes-figures-for-first-six-months-of-2026)).
- Practical read (estimate/industry lore, not verified with hard data): expect **signup spikes at Cheltenham (March), Punchestown/Aintree (April–May), Galway (July–Aug)** and elevated churn in the post-festival months; an annual plan sold in February and a "festival pass" product are the standard mitigations.

---

## 4. The Ireland-only question

**Why does no Ireland-only paid analytics product exist? The evidence says: because Ireland-only is not how Irish punters consume racing.**

1. **One product, two jurisdictions (primary-source quote).** HRI's own Deloitte report: *"Irish and British racing have such strong links, they are treated in many ways as a single product. While there is naturally a level of competition between the two jurisdictions, there is also a lot of co-operation around the respective fixture list to maximise betting revenues."* And: betting on Irish racing "is very popular with British punters (serving as another major export)" ([Deloitte/HRI 2023](https://www.hri.ie/HRI/media/HRI/HRI-2023-Deloitte-Social-and-Economic-Impact-Report-FINAL.pdf)). The fixture lists are deliberately coordinated so that Irish and British racing fill each other's gaps — meaning an Ireland-only daily-picks app has **no content on a large share of days** (Ireland: ~390 fixtures across 365 days, frequently 0–1 meetings on winter weekdays; GB: 1,427).
2. **Irish media behaviour matches.** The Ireland-branded portal [IrishRacing.com](https://www.irishracing.com/news) covers "Ireland and the UK" and is entirely free/affiliate-funded; Racing TV sells Irish racing only inside a 61-course GB+IRE bundle at £30–40/mo ([racingtv.com/join](https://www.racingtv.com/join)); the Racing Post (UK+IRE product) is the de facto Irish paper of record for form. Irish punters already pay for UK+IRE bundles — nobody sells, and nobody appears to buy, an Ireland-only one.
3. **Failed Ireland-only startups: no documented graveyard found.** I searched for defunct Irish racing-tips/analytics subscription businesses and found no reported failures — but also no survivors. The honest reading is that the experiment has rarely been attempted at scale, because the addressable base (Section 2: ~1.5–2.5k Irish premium payers across all products, estimate) is too small to fund customer acquisition, while the marginal cost of adding GB coverage is near zero (same data vendors — Racing Post/RMG/Timeform ecosystems — same bookmakers, same media). **Marked explicitly: absence of evidence of failures, not evidence that Ireland-only works.**
4. **Does Irish-specialist content command a premium inside existing services?** No direct pricing evidence found (no service charges extra for Irish coverage; The Irish Field is a general Irish racing/breeding weekly whose current subscription price I could not retrieve). What does command money in Ireland-specific form study is data access itself — HRI sells the official Irish form via its RÁS "Rate Card for Pre-Race & Raceday Data" ([HRI publications page](https://www.hri.ie/corporate/press-office/publications)) — which is a cost line for the developer, not a demand signal.
5. **Counter-argument worth keeping:** Irish racing over-indexes culturally (44% adult interest, 1.31m attendances, second only to GAA), Irish trainers dominate Cheltenham, and no competitor markets *to Irish punters in Irish terms* (euros, Irish tracks first, Tote/World Pool angles, Irish handicapping quirks). "Irish-first UK+IRE product" is an open positioning; "Ireland-only product" is an unproven and structurally handicapped one.

---

## 5. Realistic funnel math

No racing-analytics company publishes its funnel. Combining the verified anchors (OLBG 500k free members vs Racing Post 15k payers ⇒ the vertical's free:paid ratio is ~30:1 at best; RevenueCat freemium median 2.18% download→paid; Recurly/RevenueCat churn above), a defensible scenario model — **all figures below are estimates, assumptions stated**:

**Model:** steady-state subscribers ≈ (new paid subs per month) ÷ (monthly churn). Net revenue = €30 × 0.813 (VAT 23%) = €24.39/sub/mo.

| Scenario | Free-tier audience (emails/MAU) | Free→paid | Monthly churn | Steady-state subs | Net MRR / ARR |
|---|---|---|---|---|---|
| **Ireland-only, conservative** | 5,000 (hard-won: Irish racing Twitter/SEO is small) | 2% ≈ 100 ever-paid; ~15 adds/mo | 8% | **~190** | ~€4.6k / **€56k** |
| **Ireland-first UK+IRE, base** | 20,000 (festival content + affiliate free tips) | 2.5%; ~60 adds/mo | 7% | **~860** | ~€21k / **€250k** |
| **UK+IRE, stretch (top-quartile execution)** | 50,000 | 4% (strong trial funnel, 40%+ trial→paid) | 5% | **~2,000** | ~€49k / **€585k** |

Sanity checks: the stretch case equals ~13% of Racing Post's entire 2023 digital sub base — very hard for a solo developer; the base case (~860 subs) is roughly Geegeez/SBC-scale after years of list-building (their longevity suggests it is attainable but slow); the Ireland-only case shows why nobody has built it: **~€56k/yr net before data costs, affiliate revenue aside** — HRI data licensing, odds feeds and betting-API costs (per the supply-side reports) eat a large share of that. The free tier's affiliate income (OLBG's whole model) is the plausible bridge revenue while the paid list compounds; Irish/UK racing CPAs are covered in the affiliate gap report.

**Go/no-go answer:** the paying audience is big enough for a modest but real business **only if the product covers UK+IRE racing from day one**. Ireland-only fails on content cadence (no racing most winter weekdays), addressable payers (~low thousands in total), and CAC. Ireland-first positioning over UK+IRE coverage — euros, Irish tracks promoted first, Cheltenham-as-national-event marketing — is the differentiated wedge no incumbent occupies.

---

## Could not verify (explicit dead ends)

- **Racing's exact share of Irish off-course betting turnover** — not published by Revenue, HRI, GRAI or Deloitte/HRI.
- **GSGB horse-racing-specific participation %** for GB (lives in GSGB data tables; the report chapters fetched give only overall 47% and betting 12%).
- **H2 Gambling Capital / Regulus Ireland GGR figures** — paywalled; EGBA country chart not extractable. (ESRI's €6–8bn stakes triangulation and Revenue duty data used instead.)
- **Timeform, At The Races, Sporting Life audience/subscriber numbers; Racing TV subscriber count** (RMG site bot-blocked; no disclosures found).
- **Geegeez Gold and Smart Betting Club member counts** — never disclosed.
- **Betting Gods / Tipstrr revenue, subscriber and churn figures** — current sites disclose none; the old Indie Hackers Betting Gods interview (widely cited ~$50k+/mo) is no longer accessible and is not archived — treat any such number as unverified.
- **App-download estimates for racing apps in Ireland** (data.ai/Sensor Tower are paywalled; Google Play page for Racing Post returned 404 under the guessed package name).
- **The Irish Field subscription price** (subscribe page renders client-side; archive fetch blocked).
- **Documented failed Ireland-only racing-analytics startups** — none found; absence of evidence, not evidence of absence.
- **Cheltenham-week Irish staking totals** (e.g. "€xxxm staked by Irish punters") — only anecdotal press claims exist; none fetchable/verifiable here.

---

## Sources

1. Revenue Commissioners — Excise net receipts by commodity (CSV, mod. 30 May 2025): https://www.revenue.ie/en/corporate/documents/statistics/excise/net-receipts-by-commodity.csv
2. HRI Factbook 2025 (PDF): https://www.hri.ie/HRI/media/HRI/Comms/Documents/HRI-Factbook-2025-FINAL-VERSION.pdf
3. HRI H1-2026 industry figures (23 Jul 2026): https://www.hri.ie/corporate/press-office/press-release/hri-publishes-figures-for-first-six-months-of-2026
4. HRI publications index: https://www.hri.ie/corporate/press-office/publications
5. Deloitte/HRI — Social and Economic Impact of Irish Thoroughbred Breeding & Racing 2023: https://www.hri.ie/HRI/media/HRI/HRI-2023-Deloitte-Social-and-Economic-Impact-Report-FINAL.pdf
6. ESRI/GRAI — Measures of Problem Gambling, Gambling Behaviours and Perceptions of Gambling in Ireland (RS169, Oct 2023): https://www.esri.ie/system/files/publications/RS169.pdf (landing page: https://www.esri.ie/publications/measures-of-problem-gambling-gambling-behaviours-and-perceptions-of-gambling-in)
7. GRAI research index: https://www.grai.ie/publications/research
8. Gambling Commission — GSGB annual report 2025 (16 Jul 2026): https://www.gamblingcommission.gov.uk/statistics-and-research/publication/gambling-survey-for-great-britain-annual-report-2025-official-statistics
9. Gambling Commission — participation statistics, Year 2 wave 2 (Apr–Jul 2024): https://www.gamblingcommission.gov.uk/statistics-and-research/publication/statistics-on-gambling-participation-year-2-2024-wave-2-official-statistics
10. HBLB Business Plan 2025–2028 (levy yields): https://www.hblb.org.uk/documents/Executive/HBLB%20Business%20Plan%202025-2028.pdf
11. BHA Racing & Industry Statistics 2021–2025 (annual data pack): https://www.britishhorseracing.com/wp-content/uploads/2026/05/2025_Annual-Data-Pack-1.pdf
12. Press Gazette — "How Racing Post survived pandemic shutdown..." (20 Jul 2023): https://pressgazette.co.uk/publishers/nationals/how-racing-post-survived-pandemic-shutdown-and-bounced-back-to-growth/
13. Press Gazette — "Why FT, Politico and Racing Post charge big for online news" (9 Oct 2024): https://pressgazette.co.uk/publishers/nationals/why-ft-politico-and-racing-post-charge-big-for-online-news/
14. Press Gazette — "Racing Post's paid-for website approaches 10,000 subscribers" (21 Sep 2009): https://pressgazette.co.uk/news/racing-posts-paid-for-website-approaches-10000-subscribers/
15. OLBG — About us: https://www.olbg.com/about-us
16. Geegeez Gold: https://www.geegeez.co.uk/geegeez-gold/
17. Smart Betting Club — Subscribe: https://smartbettingclub.com/subscribe/
18. Betting Gods — Tipsters: https://bettinggods.com/tipsters/
19. Tipstrr: https://tipstrr.com/
20. Racing TV — Join: https://www.racingtv.com/join
21. IrishRacing.com — News (activity check 28 Aug 2026): https://www.irishracing.com/news
22. RevenueCat — State of Subscription Apps 2025: https://www.revenuecat.com/state-of-subscription-apps-2025/
23. Recurly — Churn rate benchmarks (July 2026): https://recurly.com/research/churn-rate-benchmarks/
