# Legal & Regulatory Position: A Betting-Suggestions App in Ireland (as of August 2026)

**Scope:** Legal/regulatory feasibility of an app that, on a given day, suggests horse-racing bets (using historical results, a predictive model, and value-vs-odds analysis) but does **not** take bets. Focus on Ireland; UK noted where it shares the picture. Researched 2026-08-28; the Irish regime is being commenced in phases, so several points below can change with a single statutory instrument — staleness flags are included.

---

## Key takeaways

- **A pure tips/analytics/predictions app that does not accept bets, does not match bettors with each other, and does not supply services to bookmakers needs NO Irish gambling licence today.** The Gambling Regulation Act 2024 licenses "betting activities" (B2C), betting intermediaries, and B2B suppliers of "gambling products/related services" — none of which a consumer-facing tips app is. Tipster subscription businesses (e.g. Pro Sports Advice, €19–€149/month) operate openly without licences ([Irish Times, Apr 2026](https://www.irishtimes.com/ireland/2026/04/06/racing-tipster-deletes-series-of-posts-promoting-gambling-site-that-claims-to-be-regulated-from-small-african-island/)).
- **The bright lines that WOULD trigger licensing:** taking bets or running a white-label book (remote betting licence, application fee €20,000–€400,000 tiered by gross win); providing a facility for people to bet with each other (remote betting intermediary licence, €20,000–€230,000); or selling odds/predictions **to licensed operators** — that is "providing odds to licensees", a "gambling related service" needing a B2B licence (s.70/s.89 of the Act; not yet commenced, B2B applications expected 2027–2028).
- **Since 1 July 2026 it is illegal for remote betting operators to serve Ireland without a GRAI licence** (up to 8 years' imprisonment; administrative fines up to €20m or 10% of turnover). GRAI is actively enforcing, including against a major prediction-market operator ([RTÉ, Jul 2026](https://www.rte.ie/news/2026/0719/1584077-gambling-regulator/)). **Affiliate-linking only to GRAI-licensed bookmakers is therefore a hard requirement** — promoting unlicensed sites is exactly what GRAI says it will seek High Court orders to stop.
- **The Act's advertising watershed (5:30am–9pm), social-media "followers-only" rule, and inducement ban (ss.143–151, 157, 159) are on the statute book but NOT yet commenced as of August 2026** — they bind *licensees* (directly and via s.143 for ads "caused... on the licensee's behalf", which reaches affiliates contractually). There is **no affiliate registration or affiliate licence in Ireland**.
- **Tax is favourable:** gambling winnings are not taxable for individuals (TCA 1997 s.613(2); *Graham v Green* (1925) — betting is not a trade); the 2% betting duty and 25% intermediary duty are paid by operators, not punters; app subscription revenue is ordinary trading income (income tax/corporation tax + VAT).
- **App stores:** a tips app is *gambling-adjacent*, not real-money gambling — it avoids Apple 5.3.4 / Google Play RMG certification, but gets an adult age rating (17+/18+) and faces restrictions on gambling ads/links; Google Play flags "dedicated sports odds tracker apps with integrated gambling ads" as a common violation. **A PWA/web app sidesteps store gambling policies entirely.**
- **Data/IP:** the ECJ's *BHB v William Hill* (C-203/02) gutted sui generis database protection for *created* racing data (runners/riders lists), but *Ryanair v PR Aviation* (C-30/14) means website terms of use can still prohibit scraping by contract — Racing Post's T&Cs ban commercial use. Licensed data is the safe path. Jockey/trainer names ARE personal data under GDPR; legitimate interest is a workable basis for public sports statistics but do a documented assessment ("Project Red Card" is the cautionary tale).

---

## 1. The Gambling Regulation Act 2024, GRAI, and where the licensing line sits

### 1.1 Implementation status (verified to primary sources, current at 2026-08-28)

- The **Gambling Regulation Act 2024** (No. 35 of 2024) was enacted 23 October 2024 ([Irish Statute Book](https://www.irishstatutebook.ie/eli/2024/act/35/enacted/en/html)). The **Gambling Regulatory Authority of Ireland (GRAI)** was formally established in March 2025.
- A major commencement order — **S.I. No. 31/2026**, signed 3 February 2026, effective **5 February 2026** — switched on most of the licensing, obligations, complaints and enforcement architecture ([S.I. 31/2026 text](https://www.irishstatutebook.ie/eli/2026/si/31/made/en/print); [DLA Piper](https://www.dlapiper.com/en-us/insights/blogs/mse-today/2026/raising-the-stakes)). Applications for remote betting, remote betting intermediary and in-person betting licences opened **9 February 2026** ([Yogonet](https://www.yogonet.com/international/news/2026/02/05/117460-irelands-new-gambling-licensing-regime-now-open-for-applications)).
- **From 1 July 2026, remote betting and remote betting intermediary operators targeting Ireland require a GRAI licence**; the legacy Revenue Commissioners remote licences expired that day. In-person betting transitions on **1 December 2026**. Remote *gaming* (casino) licensing follows later in 2026; **B2B, lottery and charitable licences open through 2027–2028** ([Licentium](https://www.licentium.io/post/ireland-grai-remote-betting-licences-1-july-2026); [EEGaming](https://eegaming.org/latest-news/2026/07/06/142060/grai-starts-issuing-remote-betting-licences/); [Gamblee](https://www.gamblee.com/articles/irelands-remote-betting-licence-requirement-starts-under-new-grai-regime/)).
- Enforcement teeth: unlicensed provision of a gambling activity is an offence carrying "up to eight years imprisonment" per GRAI ([Irish Times](https://www.irishtimes.com/ireland/2026/04/06/racing-tipster-deletes-series-of-posts-promoting-gambling-site-that-claims-to-be-regulated-from-small-african-island/)); administrative sanctions run to **€20m or 10% of annual turnover, whichever is greater**, plus High Court blocking orders ([RTÉ](https://www.rte.ie/news/2026/0719/1584077-gambling-regulator/); [Licentium](https://www.licentium.io/post/ireland-grai-remote-betting-licences-1-july-2026)). In July 2026 GRAI said it was preparing proceedings against "one of the largest prediction market operators in the world" operating in Ireland unlicensed, and that another major platform geo-blocked Ireland after GRAI contact ([RTÉ](https://www.rte.ie/news/2026/0719/1584077-gambling-regulator/)).

### 1.2 Licence categories and fees

Three families of licence ([GRAI B2C page](https://www.grai.ie/licensing-regulation/business-to-consumer-licenses); [GRAI glossary](https://www.grai.ie/licensing-regulation/glossary)):

| Licence | Covers | Application fee (S.I. 37/2026, tiered by "turnover" = **Gross Win** on Irish business) |
|---|---|---|
| B2C betting — in-person | Betting from premises | €1,500–€175,000 + €1,200 per premises ([GRAI fee guidance PDF](https://grai-cms-production-bucket.s3.eu-west-2.amazonaws.com/cms-media/application-fees-guidance.pdf)) |
| B2C betting — on-course | Racecourse/greyhound track pitches | €750–€20,000 |
| B2C betting — remote | Online bookmaker | **€20,000–€400,000** |
| B2C remote betting intermediary | Exchange-style "facility that enables a person to... bet with another person" | **€20,000–€230,000** (25% duty on commission also applies) |
| B2C gaming / lottery | Casino games, lotteries | Applications open later |
| B2B | Sale/supply of "gambling products" or "gambling related services" | Applications expected **2027–2028** ([AllCasinos GRAI guide](https://allcasinos.ie/gambling-regulatory-authority-ireland-grai-guide/)) |
| Charitable/philanthropic | Fundraising gambling | — |

Licences run 3 years; renewal fees and the annual **Social Impact Fund** levy (a percentage of turnover, payable by all B2C and B2B licensees) are still to be prescribed ([A&L Goodbody guide](https://www.algoodbody.com/insights-publications/algs-guide-to-the-gambling-regulation-act-2024); [GRAI fee guidance](https://grai-cms-production-bucket.s3.eu-west-2.amazonaws.com/cms-media/application-fees-guidance.pdf)).

### 1.3 Does a tips/analytics/predictions app need a licence? (The critical question)

**No — on the current text, a consumer app that only suggests bets is not a licensable gambling activity.** The statutory hooks, from the Act itself:

- s.2: "**gambling activity**" means "(a) providing a betting activity, a game or a lottery, or (b) selling or supplying... a gambling product or a gambling related service" ([Act, s.2](https://www.irishstatutebook.ie/eli/2024/act/35/section/2/enacted/en/html)). A tips app does none of (a): it takes no stakes and pays no winnings.
- A **remote betting intermediary** licence is needed to "provide a facility that enables another person to make a bet with a person, by remote means" ([GRAI glossary](https://www.grai.ie/licensing-regulation/glossary)). Recommending a bet and deep-linking to a bookmaker is not providing the betting facility — the bookmaker is.
- s.2: "**gambling related service**" means "any service provided, directly or indirectly, in the course of business which relates to a gambling activity or a gambling product, or is ancillary to a gambling activity or a gambling product and includes providing, for the operation of a gambling activity — (a) **odds to licensees**, (b) online hosting services, (c) support and maintenance..., (d) risk management services, (e) fraud management services, (f) safeguarding measures, (g) software installation/maintenance, and (h) any other service the Authority prescribes" ([Act, s.2](https://www.irishstatutebook.ie/eli/2024/act/35/section/2/enacted/en/html)). Under s.70, selling or supplying such a service without a **B2B licence** is an offence (class A fine / up to 12 months summary; up to 5 years on indictment) ([Act, s.70](https://www.irishstatutebook.ie/eli/2024/act/35/section/70/enacted/en/html)).

**Where the line sits, concretely:**

1. **Selling tips/analytics to consumers** — outside the enumerated B2B list, which is aimed at services "for the operation of a gambling activity" supplied to operators. **Caveat (grey zone):** the chapeau "relates to... or is ancillary to a gambling activity" is broad and untested, and s.2(h) lets GRAI prescribe additional services. No commentator or GRAI guidance reviewed treats consumer tipping as licensable, and ss.70–72 were deliberately **excluded from the February 2026 commencement** ([S.I. 31/2026](https://www.irishstatutebook.ie/eli/2026/si/31/made/en/print)), so there is currently nothing to apply for even if it were. Flag for re-review when B2B licensing commences (2027–2028).
2. **Selling your model/odds feed to a bookmaker** — squarely "providing odds to licensees" → **B2B licence required** once s.70 commences. Note the Act's expansive jurisdiction: B2B licensing catches suppliers to Irish B2C licensees *and* any B2B operator located in Ireland even if it only sells abroad ([A&L Goodbody guide](https://www.algoodbody.com/files/uploads/news_insights_pub/ALG_s_Guide_to_the_Gambling_Regulation_Act_2024_v3.pdf)).
3. **Paid tipster service** — legal without a licence today. Real-world evidence: Ireland's most-followed tipster runs Pro Sports Advice Ltd at **€19–€149/month plus a €3,999 "platinum lifetime" tier** with no gambling licence; the legal trouble in that story was *promoting an unlicensed offshore casino* (Gambana, "licensed" from Anjouan, Comoros), not the tipping itself ([Irish Times, 6 Apr 2026](https://www.irishtimes.com/ireland/2026/04/06/racing-tipster-deletes-series-of-posts-promoting-gambling-site-that-claims-to-be-regulated-from-small-african-island/)).
4. **Affiliate links to bookmakers** — not a licensable activity and there is **no affiliate registration regime** in the Act (confirmed by absence across the Act text, GRAI licensing pages and the major law-firm guides — [A&L Goodbody](https://www.algoodbody.com/insights-publications/algs-guide-to-the-gambling-regulation-act-2024); [Arthur Cox](https://www.arthurcox.com/knowledge/whats-new-under-the-gambling-regulation-act-2024/)). But affiliates are regulated *indirectly*: see §2.
5. **White-label betting / bet placement inside the app** (one-tap bet slips executed by you, holding customer funds, revenue share as the merchant of record) — you become the operator or intermediary → full B2C licensing, segregated customer accounts, duties, the works. Avoid.
6. **Prediction markets / anything that looks like facilitating wagers** — GRAI treats these as unlicensed gambling (the July 2026 enforcement, above).

**UK parallel (relevant since you'll likely cover UK racing):** tipping is likewise not "providing facilities for gambling" under the Gambling Act 2005, so UK tipsters/affiliates need no Gambling Commission licence; operators are made responsible for their affiliates' compliance, and the ASA/CAP code polices tipster advertising ([ASA/CAP tipster guidance](https://www.asa.org.uk/advice-online/betting-and-gaming-tipsters.html)).

---

## 2. Advertising and inducement rules that could touch the app

### 2.1 The rules (Part 6, Chapter 1 & Chapter 3 of the Act)

- **s.143:** "A licensee shall, in advertising relevant content **or causing another person to advertise relevant content on the licensee's behalf**, comply with obligations imposed... under this Part" ([Act, s.143](https://www.irishstatutebook.ie/eli/2024/act/35/section/143/enacted/en/html)). This is the affiliate hook: the *bookmaker* is on the hook for its affiliates, so affiliate agreements will flow the Act's rules down to your app contractually.
- **s.149 watershed:** no arrangements to advertise "relevant content" on broadcast/on-demand media between **5:30am and 9:00pm** ([Act (revised), s.149](https://revisedacts.lawreform.ie/eli/2024/act/35/section/149/revised/en/html)).
- **s.146 social media / video platforms:** gambling ads only to users who have an account **and follow/subscribe to the licensee** ([A&L Goodbody guide](https://www.algoodbody.com/files/uploads/news_insights_pub/ALG_s_Guide_to_the_Gambling_Regulation_Act_2024_v3.pdf); [iptechblog](https://www.iptechblog.com/2026/02/raising-the-stakes-new-gambling-advertising-rules-in-ireland/)).
- **s.147 electronic comms (email/SMS/push):** consent + easy opt-out (aligned with ePrivacy).
- **s.148 prohibited material:** nothing appealing to children, encouraging excessive gambling, or misleading about the social/financial advantages of gambling.
- **s.150:** GRAI can seek **High Court orders to stop advertising activity** — including advertising of unlicensed gambling (the mechanism GRAI cited against the tipster promoting Gambana).
- **s.157 inducements:** "A licensee may not offer a person or specific group of persons an inducement" — i.e. targeted/VIP offers banned; general-public offers allowed subject to ministerial regulations. "Inducement" = "a benefit or advantage, the intent or effect of which is, either directly or indirectly, to encourage participation in gambling" ([Act, s.157](https://www.irishstatutebook.ie/eli/2024/act/35/section/157/enacted/en/html)).

### 2.2 Commencement status — important and time-sensitive

As of August 2026, **ss.143–151 (all the advertising rules incl. the watershed), s.157 (inducements) and s.159 (sponsorship) have NOT been commenced** — they were expressly carved out of S.I. 31/2026 ([S.I. text](https://www.irishstatutebook.ie/eli/2026/si/31/made/en/print); corroborated as of Aug 2026 by [Totally Dublin](https://www.totallydublin.ie/uncategorized/what-actually-changed-the-day-irelands-new-betting-licences-took-effect/) and [Arthur Cox](https://www.arthurcox.com/knowledge/whats-new-under-the-gambling-regulation-act-2024/)). Commencement is expected "soon"/within 2026 ([Racing Post](https://www.racingpost.com/news/ireland/incoming-gambling-advertising-watershed-likely-to-come-into-effect-in-2026-according-to-leading-irish-legal-firm-atwG28G0qNX2/); [RTÉ](https://www.rte.ie/news/2026/0719/1584077-gambling-regulator/)). **Stale-by date: check for new commencement orders before launch.**

### 2.3 What this means for the app

- The statutory duties bind **licensees**, not tips apps. A non-licensee showing odds and editorial tips is not "advertising relevant content" in a way the Act directly polices — but the moment you carry bookmaker promotions for money you are the "another person" in s.143 and every affiliate contract will require compliance (watershed timing on any push/email promos, 18+ targeting, no misleading claims, only general-public offers).
- **Only link to GRAI-licensed operators** (register of licensees is published by GRAI). Promoting unlicensed operators is the single biggest legal risk for an Irish tips product — it's GRAI's stated enforcement priority and carries injunction and reputational risk ([Irish Times](https://www.irishtimes.com/ireland/2026/04/06/racing-tipster-deletes-series-of-posts-promoting-gambling-site-that-claims-to-be-regulated-from-small-african-island/)).
- The **ASAI Code** (Ireland's advertising self-regulation) and, for UK-facing marketing, the **ASA/CAP tipster rules** apply: no implying guaranteed wins, profit claims must be independently verifiable (tips logged with an independent body *before* the off), odds quoted must remain available a reasonable time, and no exploiting financial anxiety ([ASA/CAP](https://www.asa.org.uk/advice-online/betting-and-gaming-tipsters.html); [A&L Goodbody](https://www.algoodbody.com/files/uploads/news_insights_pub/ALG_s_Guide_to_the_Gambling_Regulation_Act_2024_v3.pdf)).
- **Google Ads note:** from **1 July 2026** Google's gambling ads policy for Ireland requires GRAI licences, with re-certification by **1 September 2026** ([Google policy update](https://support.google.com/adspolicy/answer/17079109?hl=en-GB)). If your app's paid marketing is classified as gambling-adjacent promotion, expect friction on ad platforms even as a non-operator.

---

## 3. Tax

- **Winnings are tax-free for individuals.** TCA 1997 **s.613(2)**: "Winnings from betting (including pool betting), lotteries, sweepstakes or games with prizes shall not be chargeable gains" ([Irish Statute Book](https://www.irishstatutebook.ie/eli/1997/act/39/section/613/enacted/en/html)). No income tax, USC, PRSI or CGT on punters' winnings ([BetInIreland tax guide](https://www.betinireland.ie/irish-gambling-regulations/taxes/)).
- **Betting is not a trade** — *Graham v Green* [1925] 9 TC 309 (habitual, systematic horse-race bettor held not trading), consistently followed in Ireland and the UK; even a full-time skilled gambler is generally outside income tax, partly because taxing winnings would make losses deductible ([Croner Taxwise on professional gambling](https://www.cronertaxwise.com/community/tqotw-professional-gambling/); [High Stakes Guide](https://www.highstakesguide.com/ie/guides/gambling-winnings-tax-ireland/)). **Residual risk:** if the app's operator bets its own bank systematically as a business (or the betting is interwoven with a commercial service — e.g. you bet to demonstrate the product), Revenue could argue the *organised commercial activity* is a trade. Anyone near that line should take paid advice; the pure-punter position remains safe.
- **Betting duty is the operator's problem, not the punter's or the app's:** 2% duty on bets with licensed bookmakers (in-shop and remote — foreign operators serving Ireland included), and **25% Betting Intermediary Duty on exchange commission**, all collected by Revenue ([Revenue — betting duty](https://www.revenue.ie/en/companies-and-charities/excise-and-licences/betting-duty/what-is-betting-duty.aspx); [Revenue — remote betting duty](https://www.revenue.ie/en/companies-and-charities/excise-and-licences/remote-betting-duty/what-is-remote-betting-duty.aspx)). Finance Act 2025 (post-Budget 2026) left both rates unchanged ([BetInIreland](https://www.betinireland.ie/irish-gambling-regulations/taxes/)).
- **App revenue is ordinary taxable income.** Subscriptions/affiliate commissions are trading income: Irish income tax (20%/40% + USC + PRSI) as a sole trader, or 12.5% corporation tax on trading profits via a company; standard-rate VAT applies to digital subscription services sold to Irish consumers (verify VAT treatment and thresholds with an accountant — not independently verified in this research).

---

## 4. Apple App Store and Google Play (2025–26)

### Apple

- **Guideline 5.3.4:** "Apps that offer real money gaming (e.g. sports betting, poker, casino games, **horse racing**) or lotteries must have necessary licensing and permissions in the locations where the app is used, must be geo-restricted to those locations, and must be free on the App Store. Illegal gambling aids, including card counters, are not permitted" ([Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)). A tips app that never takes money for bets and never pays winnings is **outside 5.3.4** — there is no guideline requiring a licence for tips/odds content, and none was found in the current guidelines.
- **Age rating:** Apple overhauled ratings in 2025 (4+, 9+, 13+, 16+, 18+); gambling-themed content ("frequent/intense simulated gambling", real-money gambling) sits at the top tier — expect **17+/18+** and honest answers required under guideline 2.3.6 ([Apple age ratings](https://developer.apple.com/help/app-store-connect/reference/app-information/age-ratings-values-and-definitions/); [Casino.org on 17+ ratings](https://www.casino.org/news/apple-is-requiring-gambling-apps-to-come-with-17-ratings/)). Practical consequence: reduced discoverability and parental-control blocking, not rejection.
- Watch-outs: don't describe the app in ways that read as facilitating gambling; rejections under 5.3 are common when reviewers can't tell the difference ([ShopApper on 5.3 rejections](https://shopapper.com/fix-apple-gambling-app-rejection-guideline-5-3/)).

### Google Play

- **Real-money gambling apps** require Google's certification: valid local licence per territory, free to install, **AO/IARC 18+ rating**, geo-blocking outside licensed territories, responsible-gambling info, no Play Billing ([Play RMG policy](https://support.google.com/googleplay/android-developer/answer/9877032?hl=en)). Ireland is one of Google's long-standing permitted RMG countries (with UK, France, Brazil, later expanded to 15+ more) ([CrustLab summary](https://crustlab.com/blog/google-allows-gambling-apps-in-multiple-countries/)); from **26 August 2026** Google is refreshing its certification forms and standards ([PPC Newsfeed](https://ppcnewsfeed.com/ppc-news/2026-07/update-gambling-games-policy-august/)).
- **Gambling-adjacent (tips/odds/news) apps** don't need RMG certification, but: they must not target minors, must not show gambling ads to under-18s, and Google lists "dedicated sports odds tracker apps with integrated gambling ads" among **common violations** ([Play common violations](https://support.google.com/googleplay/android-developer/answer/13381106?hl=en); [Play RMG policy](https://support.google.com/googleplay/android-developer/answer/9877032?hl=en)). Translation: an odds/tips app is fine; stuffing it with bookmaker ad units is the thing that gets flagged. Affiliate *links* with clear content are lower-risk than programmatic gambling ads, but expect scrutiny; Play's new age-restricted-content policy also pushes such apps toward 18+ gating.
- Google's ad network (for promoting your app) now requires GRAI licensing evidence for Irish gambling advertising, per §2.3.

### The PWA escape hatch

Both stores' gambling policies govern **store-distributed native apps only**. A responsive web app / PWA (installable from the browser) is subject to neither Apple 5.3 nor Play's RMG/gambling-related rules — this is the standard route for gambling-adjacent products that want to avoid store friction, at the cost of App Store discoverability, some iOS push/UX limitations, and no store payment rails (which you don't want anyway — Stripe for subscriptions avoids Apple/Google 15–30% cuts). This is a strong argument for launching web-first, exactly as many odds-comparison sites do. (Analysis; store-policy scope per the policy documents above.)

---

## 5. Data and IP law for racing data

### 5.1 Sui generis database right — the racing cases

- Directive 96/9/EC gives a 15-year "sui generis" right against extraction/re-utilisation of substantial parts of a database where there was **substantial investment in obtaining, verifying or presenting** its contents.
- ***British Horseracing Board v William Hill*, CJEU C-203/02 (9 Nov 2004):** the ECJ held the investment test covers obtaining *existing* independent materials — **not resources spent *creating* the data**. BHB's official lists of runners and riders were *created* by BHB, so William Hill's use of racecard data did not infringe BHB's database right ([EUR-Lex judgment](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62002CJ0203); [Swan Turton analysis](https://swanturton.com/database-protection-narrowed-british-horseracing-board-v-william-hill/)). The companion *Fixtures Marketing* cases (e.g. C-444/02, same day) held football fixture lists similarly unprotected ([EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62002CJ0444)).
- **Implication:** core racecard facts (declared runners, riders, draw, race conditions) and race *results* as facts are weakly protected by database right in the EU/UK. **But do not treat this as open season:** compiled value-added datasets (ratings, sectional times, form databases assembled from many sources — e.g. Racing Post's or Timeform's databases) involve genuine *obtaining/verification/presentation* investment and can still qualify; copyright can subsist in editorial content (comments, analysis, ratings); and the UK retains its own domestic database right post-Brexit.

### 5.2 Scraping: contract beats (absent) IP

- ***Ryanair v PR Aviation*, CJEU C-30/14 (2015):** where a database is **not** protected by copyright or the sui generis right, the Database Directive's user freedoms don't apply either — so the owner may **restrict use by contract**. Screen-scraping in breach of accepted website terms can be actionable as breach of contract even with no IP infringement ([IPKat](https://ipkitten.blogspot.com/2015/01/breaking-cjeu-says-that-owner-of-online.html); [Kluwer Copyright Blog](https://legalblogs.wolterskluwer.com/copyright-blog/ryanair-ltd-v-pr-aviation-bv-contracts-rights-and-users-in-a-low-cost-database-law/)).
- **Racing Post's terms** restrict the site to "personal and non-commercial use" and prohibit reproduction/redistribution and use "in connection with any business or commercial undertaking" ([Racing Post T&Cs](https://help.racingpost.com/hc/en-us/articles/208996085-Terms-and-conditions)). Scraping it for a commercial app = contract breach risk plus practical risk (IP blocking, account termination), even if a database-right claim would be arguable post-*BHB*. UK adds Computer Misuse Act 1990 exposure for circumventing technical access controls ([Bristows](https://inquisitiveminds.bristows.com/post/102hhpm/web-crawling-and-scraping-data-what-is-prohibited-commercial-use)).
- **Practical posture:** use licensed feeds/APIs for anything commercial (the data-sources workstream covers options); if scraping at all, prefer public non-logged-in pages of official bodies, keep volumes low, and get legal advice before building the business on it.

### 5.3 GDPR

- Jockey, trainer and owner **names are personal data** (GDPR Art 4(1): any information relating to an identified/identifiable natural person). Horses aren't data subjects, but a form database is full of human identifiers and performance statistics.
- The workable lawful basis is **legitimate interests (Art 6(1)(f))**: professionals in a public sport reasonably expect their public performance statistics to be processed; privacy impact is minimal for facts like rides, wins and public ratings ([Irwin Mitchell on sports data & GDPR](https://www.irwinmitchell.com/news-and-insights/expert-comment/post/102hi9n/data-protection-in-sport-tackling-gdpr-issues); [Brodies](https://brodies.com/insights/media-broadcasting-and-sports/sports-technology-and-the-gdpr-data-privacy-concerns-in-sports-analysis/)). Do and document a Legitimate Interest Assessment; publish a privacy notice covering third-party (jockey/trainer) data; honour objection rights; avoid anything health-adjacent (injury data is special-category).
- Cautionary tale: **"Project Red Card"** — hundreds of UK footballers asserting claims over betting/gaming companies' use of their performance data ([INPLP](https://inplp.com/latest-news/article/athletes-performance-data-project-red-card/)). It has not produced a ruling outlawing sports stats, but signals that data-subject activism reaches betting-data products.
- Your own users: standard GDPR duties (Irish DPC is the regulator) — plus, given the subject matter, treat any behavioural data suggesting problem gambling with care.

---

## 6. Responsible gambling

- **No statutory RG obligations attach to a non-licensee tips app today.** The Act's player-protection duties — credit-card ban, targeted-inducement ban, net-spend alerts, monetary-limit facility, staff RG training, prominent RG information — bind licensees ([GRAI player safety](https://www.grai.ie/gambling-safety/protecting-the-public/players-safety)).
- **National Gambling Exclusion Register (NGER):** GRAI-run, centralised self-exclusion covering all Irish-licensed online operators (durations from 6 months to lifetime); licensees must check it in real time or stop offering gambling. **Not yet live as of August 2026** (ss.44–49 uncommenced); expected alongside the fuller rollout in late 2026 ([Citizens Information](https://www.citizensinformation.ie/en/justice/civil-law/gambling-regulatory-authority/); [Totally Dublin](https://www.totallydublin.ie/uncategorized/what-actually-changed-the-day-irelands-new-betting-licences-took-effect/)). A tips app has no NGER duty, but an ethical (and reputationally smart) design choice is to let users self-suppress bookmaker links/tips and never to email lapsed users with "come back and bet" messaging — that would collide with the spirit of s.157 once commenced.
- **Support infrastructure (Ireland's GamCare/GambleAware equivalents):** the national problem-gambling helpline is **1800 936 725**, with services via **GamblingCare.ie**; HSE addiction services and Gamblers Anonymous Ireland also operate ([Citizens Information](https://www.citizensinformation.ie/en/health/health-services/addiction-treatment-services/help-for-gambling-addiction/)). The **Social Impact Fund**, financed by a turnover-based levy on all B2C/B2B licensees, will fund research, awareness and treatment ([A&L Goodbody](https://www.algoodbody.com/insights-publications/algs-guide-to-the-gambling-regulation-act-2024)).
- **Norms to build in from day one:** 18+ age gate; visible RG messaging and helpline links; no "guaranteed winners" claims (ASA/CAP-verified tipping records if you advertise performance — tips logged before the off with an independent verifier) ([ASA/CAP tipsters](https://www.asa.org.uk/advice-online/betting-and-gaming-tipsters.html)); staking guidance framed around bankroll discipline rather than chasing losses. These are also the norms bookmaker affiliate programmes will contractually require.

---

## Open items / could not verify

- **Whether ss.143–151 (advertising) and s.157 (inducements) have been commenced after early August 2026** — no commencement order beyond S.I. 31/2026 was found up to the Law Reform Commission's consolidation date of 6 July 2026, and press as of July–August 2026 reports them still pending; **re-check before launch** (a single S.I. changes this).
- **Exact B2B application opening date** — GRAI has said only "2027–2028" phased rollout; no confirmed date.
- **VAT treatment of tipster subscriptions** — standard-rate VAT assumed; not verified against Revenue guidance.
- **GRAI's formal view on tipsters/affiliates** — GRAI has published no guidance note on tipsters or affiliates; the analysis in §1.3 rests on the statutory text and observed practice, not a regulator statement.
- Apple's post-2025 age-rating tier for a *tips-only* (no simulated gambling) app — likely 17+/18+ by self-declaration, but Apple's questionnaire outcome could be 16+; not verifiable without submission.

---

## Sources

**Primary law / regulator**
- Gambling Regulation Act 2024 (full text): https://www.irishstatutebook.ie/eli/2024/act/35/enacted/en/html
- s.2 definitions: https://www.irishstatutebook.ie/eli/2024/act/35/section/2/enacted/en/html · s.70: https://www.irishstatutebook.ie/eli/2024/act/35/section/70/enacted/en/html · s.89: https://www.irishstatutebook.ie/eli/2024/act/35/section/89/enacted/en/html · s.143: https://www.irishstatutebook.ie/eli/2024/act/35/section/143/enacted/en/html · s.157: https://www.irishstatutebook.ie/eli/2024/act/35/section/157/enacted/en/html
- S.I. No. 31/2026 (Commencement Order, effective 5 Feb 2026): https://www.irishstatutebook.ie/eli/2026/si/31/made/en/print
- Revised Act (Law Reform Commission, updated to 6 July 2026): https://revisedacts.lawreform.ie/eli/2024/act/35/front/revised/en/html
- GRAI — B2C licences: https://www.grai.ie/licensing-regulation/business-to-consumer-licenses · Glossary & scenarios: https://www.grai.ie/licensing-regulation/glossary · Player safety: https://www.grai.ie/gambling-safety/protecting-the-public/players-safety
- GRAI — Licence Application Fees Guidance (tiered fees, S.I. 37/2026): https://grai-cms-production-bucket.s3.eu-west-2.amazonaws.com/cms-media/application-fees-guidance.pdf
- TCA 1997 s.613 (winnings not chargeable gains): https://www.irishstatutebook.ie/eli/1997/act/39/section/613/enacted/en/html
- Revenue — Betting Duty: https://www.revenue.ie/en/companies-and-charities/excise-and-licences/betting-duty/what-is-betting-duty.aspx · Remote Betting Duty: https://www.revenue.ie/en/companies-and-charities/excise-and-licences/remote-betting-duty/what-is-remote-betting-duty.aspx

**Law-firm / expert commentary**
- A&L Goodbody, Guide to the Gambling Regulation Act 2024: https://www.algoodbody.com/insights-publications/algs-guide-to-the-gambling-regulation-act-2024 (PDF: https://www.algoodbody.com/files/uploads/news_insights_pub/ALG_s_Guide_to_the_Gambling_Regulation_Act_2024_v3.pdf)
- Arthur Cox, What's new under the Gambling Regulation Act 2024: https://www.arthurcox.com/knowledge/whats-new-under-the-gambling-regulation-act-2024/
- DLA Piper, Raising the Stakes — licensing framework operational: https://www.dlapiper.com/en-us/insights/blogs/mse-today/2026/raising-the-stakes
- Squire Patton Boggs / iptechblog, New gambling advertising rules in Ireland (Feb 2026): https://www.iptechblog.com/2026/02/raising-the-stakes-new-gambling-advertising-rules-in-ireland/
- IMGL Magazine, Ireland's advertising restrictions: https://www.imgl.org/publications/imgl-magazine-volume-3-no-1/irelands-advertising-restrictions-will-affect-operators/

**News / enforcement**
- RTÉ, Prediction market firm could face proceedings by watchdog (19 Jul 2026): https://www.rte.ie/news/2026/0719/1584077-gambling-regulator/
- Irish Times, Racing tipster deletes posts promoting gambling site (6 Apr 2026): https://www.irishtimes.com/ireland/2026/04/06/racing-tipster-deletes-series-of-posts-promoting-gambling-site-that-claims-to-be-regulated-from-small-african-island/
- Racing Post, Advertising watershed likely 2026: https://www.racingpost.com/news/ireland/incoming-gambling-advertising-watershed-likely-to-come-into-effect-in-2026-according-to-leading-irish-legal-firm-atwG28G0qNX2/
- Licentium, GRAI remote betting licences from 1 July 2026: https://www.licentium.io/post/ireland-grai-remote-betting-licences-1-july-2026
- EEGaming, GRAI starts issuing remote betting licences: https://eegaming.org/latest-news/2026/07/06/142060/grai-starts-issuing-remote-betting-licences/
- Yogonet, Applications open (Feb 2026): https://www.yogonet.com/international/news/2026/02/05/117460-irelands-new-gambling-licensing-regime-now-open-for-applications
- Totally Dublin, What actually changed on 1 July 2026: https://www.totallydublin.ie/uncategorized/what-actually-changed-the-day-irelands-new-betting-licences-took-effect/

**App stores**
- Apple App Review Guidelines (5.3, 2.3.6): https://developer.apple.com/app-store/review/guidelines/
- Apple age ratings reference: https://developer.apple.com/help/app-store-connect/reference/app-information/age-ratings-values-and-definitions/
- Google Play Real-Money Gambling policy: https://support.google.com/googleplay/android-developer/answer/9877032?hl=en
- Google Play common violations for gambling apps: https://support.google.com/googleplay/android-developer/answer/13381106?hl=en
- Google Ads gambling policy update for Ireland (1 Jul 2026): https://support.google.com/adspolicy/answer/17079109?hl=en-GB

**Data / IP / GDPR**
- CJEU C-203/02 BHB v William Hill: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A62002CJ0203 (analysis: https://swanturton.com/database-protection-narrowed-british-horseracing-board-v-william-hill/)
- CJEU C-444/02 Fixtures Marketing v OPAP: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62002CJ0444
- CJEU C-30/14 Ryanair v PR Aviation: https://ipkitten.blogspot.com/2015/01/breaking-cjeu-says-that-owner-of-online.html · https://legalblogs.wolterskluwer.com/copyright-blog/ryanair-ltd-v-pr-aviation-bv-contracts-rights-and-users-in-a-low-cost-database-law/
- Racing Post terms and conditions: https://help.racingpost.com/hc/en-us/articles/208996085-Terms-and-conditions
- Irwin Mitchell, Data protection in sport: https://www.irwinmitchell.com/news-and-insights/expert-comment/post/102hi9n/data-protection-in-sport-tackling-gdpr-issues
- INPLP, Project Red Card: https://inplp.com/latest-news/article/athletes-performance-data-project-red-card/

**Tax / responsible gambling**
- Croner Taxwise, Professional gambling (Graham v Green): https://www.cronertaxwise.com/community/tqotw-professional-gambling/
- BetInIreland, Gambling tax Ireland: https://www.betinireland.ie/irish-gambling-regulations/taxes/
- Citizens Information, GRAI / help for gambling addiction: https://www.citizensinformation.ie/en/justice/civil-law/gambling-regulatory-authority/ · https://www.citizensinformation.ie/en/health/health-services/addiction-treatment-services/help-for-gambling-addiction/
- ASA/CAP, Betting and gaming: Tipsters: https://www.asa.org.uk/advice-online/betting-and-gaming-tipsters.html
