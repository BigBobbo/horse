# Gap-fill research: The Tote and World Pool opportunity for an Irish racing-picks app

**Date of research: 28 August 2026.** All facts checked against primary or near-primary sources on this date; anything that could not be verified is explicitly flagged. Web-search engines were partially unavailable from the research environment; where a figure comes from a search-result snippet rather than a fully fetched page it is marked "(via search snippet)".

---

## Key takeaways

- **The pari-mutuel route is real but two-tier.** Ordinary Irish meetings have tiny Tote pools (average ~€188k per *fixture* across all pools in 2025; implied win pool per race of roughly €5k–€12k), while the 5–6 Irish World Pool days per year carry ~€26–28m per day of commingled turnover — roughly two orders of magnitude more. A Benter-style "bet into the pool" strategy is only executable at scale on World Pool days; on ordinary days the pools are a niche for small-stakes exotic value.
- **Takeout is the hurdle, and it is lower on World Pool days.** UK Tote domestic deductions run 19.25% (Win) to 30% (Scoop6/Swinger); on World Pool races Win/Place/Quinella/Quinella-Place drop to 17.5% and Exacta to 19.5% (Trifecta 25%). A model needs ~20%+ edge pre-takeout to clear domestic Win pools, ~18% on World Pool days — before considering that Tote win dividends historically *beat* SP more often than not (operator-published data).
- **Winners are structurally welcome, with one new caveat.** The Tote's public position is that it does not restrict winners or bet sizes (pari-mutuel operators earn the same margin either way), and its Partner API explicitly offers *enhanced dividends* to API bettors. But from 23 February 2026 the Tote Guarantee (SP-match) boost is capped at £200 per selection per customer with account-specific limits — the subsidy element, not the pool payout, is now clamped for sharp players.
- **Ireland's regulatory ground just shifted (July–August 2026).** GRAI remote-betting licences commenced 1 July 2026; the UK Tote's operating company **TDCO Ltd (trading as "Tote") was granted Irish remote-betting licence GRAI-0796-RB-26-0001 on 26 August 2026** — two days before this research. Betfair's exchange (Remote Betting Intermediary, 11 Aug 2026) and Smarkets (12 Aug 2026) are also on the register. Pool betting in Ireland now requires a GRAI betting licence with pool betting specified per event class.
- **Integration is genuinely open.** The Tote Partner API is a documented public-facing GraphQL API (docs at developers.services.tote.co.uk, endpoint live and verified 28 Aug 2026) covering pool data *and bet placement*, with a test environment and subscriptions; onboarding is by application (connectivity@tote.co.uk), commercials unpublished. A self-serve affiliate programme (affiliates.tote.co.uk, RavenTrack platform) pays revenue share/CPA/fixed fee and explicitly contemplates partners marketing in both the UK and Ireland.
- **Tote Ireland itself is small and financially thin**: turnover €68.97m in 2024 (down 4%), net income to HRI just €0.9m; 2025 handle recovered to €81.3m including €7.9m through World Pool. Its seven-year alliance with the UK Tote (from 1 Jan 2021) put both totes on one platform (tote.ie / tote.co.uk share a help centre, pools and products).

---

## 1. Structure: who operates Tote betting on Irish racing (2025–26)

**Tote Ireland Ltd** is a 100% subsidiary of Horse Racing Ireland ("Operation of a totalisator at race meetings" — HRI Annual Report 2024, Note 39, Principal Subsidiaries). The totalisator has been state/industry-owned since the Totalisator Act 1929, run by the Racing Board from 1945 and by HRI today ([Wikipedia: Tote Ireland](https://en.wikipedia.org/wiki/Tote_Ireland); [HRI Annual Report 2024 PDF](https://www.hri.ie/HRI/media/HRI/Comms/Documents/Annual-Report-2024-DUAL-ENGLISH-IRISH.pdf)).

**UK Tote Group** bought the British Tote from Betfred in October 2019 for **£115m** (Betfred had paid £265m at privatisation in July 2011); it is a consortium of 150+ racing investors, chaired by Alex Frost ([Wikipedia: Horserace Totalisator Board](https://en.wikipedia.org/wiki/Horserace_Totalisator_Board)).

**The alliance.** In April 2020 Tote Ireland and the UK Tote announced a **seven-year strategic alliance commencing 1 January 2021** (so nominally running to end-2027) to develop joint international offerings and pool liquidity ([TDN, 28 Apr 2020](https://www.thoroughbreddailynews.com/irish-and-uk-totes-form-alliance/)). Tote Ireland has commingled into UK pools since 2001 ([Wikipedia: Tote Ireland](https://en.wikipedia.org/wiki/Tote_Ireland)). In practice the two now run on one platform: the official Tote help centre (help.tote.co.uk) documents products "accessible through Tote.co.uk and Tote.ie to customers in both the UK and Ireland", with Irish minimum stakes quoted in cents (e.g. the Irish Jackpot, a 4-leg pool on races 3–6 of every Irish meeting, which replaced the Quadpot on Irish cards — [Tote help: What is an Irish Jackpot](http://help.tote.co.uk/en/articles/7011602-what-is-an-irish-jackpot)). **Could not verify:** whether the 2020 alliance has been formally extended, renegotiated, or converted into an acquisition; no 2025–26 announcement was found.

**World Pool governance.** In June 2023 the UK Tote signed a **five-year deal with the Hong Kong Jockey Club to be the exclusive World Pool partner for the UK and Ireland** ([Wikipedia: Horserace Totalisator Board](https://en.wikipedia.org/wiki/Horserace_Totalisator_Board)). On World Pool days the host pools are HKJC's; Tote/Tote Ireland customers bet into them.

**How an Irish resident bets into each.** Irish residents use **tote.ie** (same product set, Irish pools + commingled UK/World Pool bets) or on-course Tote windows at all 26 Irish racecourses. Both tote.ie and tote.co.uk geo-block visitors from outside their served regions (both returned "Unavailable in Region" pages to this US-egress research session — verified 28 Aug 2026), so which storefront an Irish IP is routed to could not be directly observed; the shared help centre and the new Irish licence (next paragraph) indicate a single Tote platform serving both markets.

**GRAI licensing status (current to 27–28 Aug 2026).** The Gambling Regulatory Authority of Ireland was established under the Gambling Regulation Act 2024 and became operational **5 March 2025** ([Wikipedia: GRAI](https://en.wikipedia.org/wiki/Gambling_Regulatory_Authority_of_Ireland)). Its first invitation for **remote betting licence applications opened February 2026**, and **remote betting and betting-intermediary licences commenced 1 July 2026** ([GRAI news](https://www.grai.ie/news), incl. the GRAI 2025 Annual Report announcement of 30 Jul 2026). The public licence register (CSV downloaded 28 Aug 2026, register dated 27 Aug 2026, 29 licences) shows:

| Licensee | Trading name | Licence | Type | Issued |
|---|---|---|---|---|
| **TDCO Limited** | **Tote** | GRAI-0796-RB-26-0001 | B2C Remote Betting | **2026-08-26** (expires 2029-08-25) |
| Betfair International plc | Betfair Exchange | GRAI-1074-RBI-26-0001 | Remote Betting Intermediary | 2026-08-11 |
| Smarkets (Malta) Ltd | SBK, Smarkets | GRAI-0691-RBI-26-0001 | Remote Betting Intermediary | 2026-08-12 |
| PPB Counterparty Services | Betfair, Paddy Power | GRAI-1003-RB-26-0001 | B2C Remote Betting | 2026-08-11 |

Source: [GRAI register](https://www.grai.ie/register) (CSV via /register/download). TDCO Ltd is the UK Tote's operating company — i.e. **the UK Tote is now directly GRAI-licensed for remote betting in Ireland as of 26 August 2026**. Tote Ireland Ltd does not yet appear on the register (in-person licensing is being phased; existing licence holders were told to continue under legacy regimes during transition — [GRAI licence application guidance](https://www.grai.ie/licensing-regulation/business-to-consumer-licenses/licensing-phasing)).

**Pool betting under the new Act:** pool betting may only be offered under an in-person or remote **betting** licence with the pool-betting events specified (licence max 3 years; no "remote betting intermediary" licence may cover pool betting; racecourses are "relevant premises" exempt from premises assessment) — [GRAI Pool Betting Guidance PDF](https://grai-cms-production-bucket.s3.eu-west-2.amazonaws.com/cms-media/pool-betting-guidance.pdf). Note for the app: a tips/suggestions app that takes no bets needs no betting licence, but Irish advertising/affiliate rules under the 2024 Act apply (see the companion legal report).

## 2. Takeout / deduction rates, 2025–26

**UK Tote domestic pools** (per the [Horseracing Bettors Forum deductions page](https://ukhbf.org/betting-deductions-takeouts/), site © 2026 — HBF is the independent bettors' body, but the page carries no explicit last-verified date; treat as current-best-public):

| Pool | Deduction |
|---|---|
| Win | **19.25%** |
| Place | **20%** |
| Exacta | **25%** |
| Trifecta | **25%** |
| Swinger | **30%** |
| Double / Treble | **20%** |
| Placepot | **27%** |
| Quadpot | **26%** |
| Jackpot | **29%** |
| Scoop6 | **30%** |

(The same page lists Betfair Exchange commission 5% headline, Betdaq 2%, Smarkets 2% for comparison.)

**Irish pools.** Third-party sources state the **Placepot deduction is 30% on Irish races vs 27% UK** ([tix.bet deductions guide, via search snippet](https://www.tix.bet/knowledge/deductions/); also freebets.com via search snippet). **Could not verify the current official Tote Ireland deductions for Win/Place/Exacta/Trifecta/Superfecta/Jackpot** — tote.ie (where the rules live) is geo-blocked from the research environment, the HRI Factbook/Annual Report do not publish deduction schedules, and no Oireachtas or GRAI document lists them. This is the single most important number to confirm from an Irish IP or by emailing Tote Ireland; the working assumption should be "UK-like or slightly higher" (the 30%-vs-27% Placepot differential is the one documented data point).

**World Pool days** (official — [Tote help: Worldpool deduction rates](http://help.tote.co.uk/en/articles/5332509-worldpool-deduction-rates)):

| World Pool bet | Takeout |
|---|---|
| Win, Place, Quinella, Swinger/Quinella Place | **17.5%** |
| Exacta | **19.5%** |
| Trifecta/Tierce | **25%** |

These are the HKJC host-pool rates; UK domestic pools running alongside (e.g. Placepot) keep their normal deductions.

**Effective economics check (Tote Ireland accounts).** HRI's audited 2024 group accounts show Tote Ireland turnover **€68.973m** and "winnings paid by Tote Ireland" **€64.667m** — an aggregate 93.8% paid back, i.e. only ~6.2% net hold on the accounting definition of turnover (which includes commingling commissions), and **net income of just €0.9m** (2023: €0.4m) ([HRI Annual Report 2024](https://www.hri.ie/HRI/media/HRI/Comms/Documents/Annual-Report-2024-DUAL-ENGLISH-IRISH.pdf), Income & Expenditure and Income from Racing sections). The gap between headline ~20–30% deductions and ~6% net hold reflects commingling flows and guest-operator shares; the practical implication is that Tote Ireland is a low-margin utility, not a fat-margin monopolist.

## 3. Pool sizes: what an Irish value bettor can actually get down

**Totals (HRI Factbook 2025 / HRI 2025 statistics, published 28 Jan 2026):**
- Total Tote handle on Irish racing 2025: **€81.3m, +7.2%** — €10.6m on-course (+1.9%), €62.8m off-course on Irish pools (+9.0%), **€7.9m through World Pool (+1.3%)** ([TDN report of HRI 2025 stats](https://www.thoroughbreddailynews.com/eade-hails-broad-appeal-of-irish-racing-as-key-metrics-rise/); [HRI Factbook 2025 PDF](https://www.hri.ie/HRI/media/HRI/Comms/Documents/HRI-Factbook-2025-FINAL-VERSION.pdf)).
- Irish-pools-only handle (excluding commingling-out): **€73.40m in 2025** over **390 fixtures** → **average €188k per fixture**; 2024: €68.00m, average €174,363 (Factbook 2025, "Average Tote Total Betting" table).

**By pool type, Irish pools 2025 (Factbook 2025, €000):** Win 32,236 (44%); Place 9,889 (13%); Exacta 10,034 (14%); Trifecta 7,760 (11%); Placepot 9,857 (13%); Superfecta 2,894 (4%); Jackpot 727 (1%). Total 73,398.

**By racecourse, 2025 (total Tote handle, Irish pools):** Galway €6.90m over 13 fixtures (**~€531k/fixture** — festival effect); Leopardstown €8.36m/23 (~€364k); Punchestown €6.14m/21 (~€293k); Curragh €4.29m/24 (~€179k; 2024 was €6.13m — the fall likely reflects World Pool days moving out of the "Irish pools" line); Dundalk €7.13m/41 (~€174k); typical country tracks (Ballinrobe, Sligo, Thurles, Tramore, Wexford, Roscommon…) €1.0–1.6m per year, i.e. **€100k–160k per fixture**.

**Implied per-race capacity.** With Win = 44% of handle, an ordinary €150k fixture carries ~€66k of win-pool money across ~7–8 races → **win pools of roughly €5k–12k per race at ordinary meetings** (bigger for feature races, much smaller for the first/last). Exacta/Trifecta pools per race are commonly €1k–3k. A bettor staking even €100–200 in such a win pool is 1–3% of the pool and materially moves their own dividend; exotics tolerate only tens of euro. This matches the accepted history: Ireland's largest-ever single-race pool was €437,686 (Galway Plate day, 2004) and largest single-day €1.91m (Galway, 2005) ([Wikipedia: Tote Ireland](https://en.wikipedia.org/wiki/Tote_Ireland)).

**World Pool days are a different sport entirely:**
- **Irish Derby Day 2024 (Curragh): HK$235m ≈ €28m across 9 races** (avg ~€3.1m/race, all bet types), up from HK$220.7m (€26.3m) in 2023; the Derby itself took HK$35.4m (€4.2m), +4% ([TDN, 2 Jul 2024](https://www.thoroughbreddailynews.com/irish-derby-day-records-highest-ever-turnover-on-world-pool/)).
- **Leopardstown Irish Champion Stakes Day: €27.7m (2023), €27.9m (2022), €22.9m (2021)** across seven World Pool bet types ([TDN, 13 Sep 2023](https://www.thoroughbreddailynews.com/irish-champion-stakes-day-popular-on-world-pool-with-e27-7m-wagered/)).
- Royal Ascot 2025: **HK$1,574.4m (~£150m) over five days, +10% YoY**, single-day record HK$330.7m ([TDN, 25 Jun 2025](https://www.thoroughbreddailynews.com/world-pool-betting-figures-at-royal-ascot-rise-10-to-150m/)).
- World Pool globally 2025: **HK$9.3bn (~€1bn) on overseas races, +20%** (HK$7.8bn/€855m in 2024); **329 races, 57 racedays outside Hong Kong, 10 jurisdictions**; HK$10.9bn including Hong Kong G1s; record single overseas race The Everest 2025 at **HK$83.0m (€9.1m)** ([TDN, 6 Jan 2026](https://www.thoroughbreddailynews.com/world-pool-turnover-on-overseas-races-soars-to-hk9-3-billion-in-2025/); [TDN, 18 Oct 2025](https://www.thoroughbreddailynews.com/ka-ying-risings-everest-smashes-turnover-record-in-world-pool/)).

On a ~€3m/race World Pool card, a €1,000–5,000 win bet is noise (0.03–0.2% of the race's turnover) — this is the only Irish-racing context in which "get a real bet down without moving the price" is true of the Tote. Note the contrast with the €7.9m *Irish-channel* World Pool figure: most World Pool money on Irish races is Hong Kong and international money, which is precisely why the pools are deep.

## 4. World Pool calendar: Irish fixtures 2023 → 2026

- **2023:** Irish Derby Day (2 Jul) — first Curragh World Pool day (combined Irish+German Derby day turnover HK$246.9m/€28.9m) ([TDN, 5 Jul 2023](https://www.thoroughbreddailynews.com/irish-and-german-derbys-make-strong-world-pool-showing/)); Leopardstown Champion Stakes Day.
- **2024:** the **entire Irish Champions Weekend** joined for the first time — Leopardstown (14 Sep) plus Irish St Leger Day at the Curragh (15 Sep) — alongside Irish Derby Day ([TDN, 8 Aug 2024](https://www.thoroughbreddailynews.com/world-pool-to-be-active-during-irish-champions-weekend/)).
- **2025:** **Irish 2,000 Guineas Day (Curragh, 24 May 2025) added, all races commingled**, within a 24-fixture H1-2025 World Pool programme spanning bettors from 28+ countries ([TDN, 20 Mar 2025](https://www.thoroughbreddailynews.com/irish-2000-guineas-card-added-to-world-pool-schedule/)); plus Irish Derby Day and Irish Champions Weekend → **5 Irish World Pool days in 2025** (Guineas, Derby, Leopardstown ICW, Curragh St Leger day; a 5th if Guineas Sunday included — not verified).
- **2026:** **Irish Oaks Day (Curragh, 18 Jul 2026) added for the first time** — World Pool now commingles **27 jurisdictions** ([TDN, 28 May 2026](https://www.thoroughbreddailynews.com/hkjc-confirms-world-pool-fixtures-for-july-and-august/)); the Irish Derby festival ran as a World Pool fixture in June 2026 ([TDN, 28 Jun 2026](https://www.thoroughbreddailynews.com/benvenuto-cellini-leads-obrien-1-2-3-for-irish-derby-number-18/)); nine further new fixtures (UK/AUS/SA, incl. the St Leger's first commingling on 12 Sep) were announced for late 2026 ([TDN, 6 Aug 2026](https://www.thoroughbreddailynews.com/world-pool-to-debut-nine-new-fixtures-during-final-months-of-2026/)). **Could not verify** the explicit September 2026 announcement for Irish Champions Festival days, but they have been annual fixtures since 2023/24 and their continuation is implied by the calendar's growth; treat as highly likely rather than confirmed.

So the practical 2026 Irish World Pool set is ~**6 days**: Irish 2,000 Guineas day, Irish Derby day(s), Irish Oaks day, and the two Irish Champions Festival days.

## 5. Do World Pool/Tote prices beat SP and Betfair?

Evidence found (all operator-linked — flag accordingly):
- **Royal Ascot 2021 (Tote-published, reported by TDN):** Tote+ win dividends **beat SP on 21 of 35 races** and matched it (via Tote Guarantee) on the rest; a £1 bet on every winner returned **+11% vs SP**; Tote Exacta paid **+34%** and Trifecta vs tricast **+87%** on average ([TDN, 15 Jul 2021](https://www.thoroughbreddailynews.com/hkjc-world-first-aims-to-enhance-global-participation/); [TDN "10 things", 14 Jun 2021](https://www.thoroughbreddailynews.com/10-things-to-know-about-the-world-pool-at-royal-ascot/) — the latter also cites Adayar's Derby win paying £20.24 on the Tote vs 16/1 SP, and Epsom Derby pool growth from £1.7m to £26m+ under World Pool).
- **Early 2025 (sharpbetting.co.uk, a Tote-partnered content site):** "Tote Trifecta payouts exceeded fixed-odds tricast returns over 70% of the time… averaging close to 30% higher" ([sharpbetting article](https://sharpbetting.co.uk/articles/Tote-API-Betting-Unlocking-Value-in-Pool-Wagering)).
- **Could not find any independent academic or press study comparing World Pool dividends with Betfair SP** (as opposed to bookmaker SP). This matters: beating industry SP (a margin-laden price) is a low bar; Betfair SP is the honest benchmark and the comparison is unverified. The structural argument cuts both ways — 17.5% World Pool takeout vs ~2–5% exchange commission is a huge headwind, but HK money re-weights pools toward HK opinion, so UK/Irish-form-driven mispricings can and do leave individual horses paying more than BSP. Treat "World Pool beats SP" as directionally supported, "beats BSP" as unproven.

## 6. Are winners welcome?

- **Structurally yes.** A pari-mutuel operator's margin is the deduction; it is indifferent to who wins. The Tote's own marketing states it "welcomes winning customers and does not restrict bet sizes" ([TDN "10 things", Jun 2021](https://www.thoroughbreddailynews.com/10-things-to-know-about-the-world-pool-at-royal-ascot/)) and its API page advertises that "betting via the API unlocks larger dividends on winning bets across all UK and Irish pools" ([tote.co.uk/racing/data-api, via search snippet](https://tote.co.uk/racing/data-api)) — the opposite of a bookmaker's treatment of sharps. No forum/Reddit reports of the Tote restricting winning accounts were found (searched; absence of evidence, noted as such).
- **One real clamp, new in 2026:** from **23 February 2026** the **Tote Guarantee** (the promise that the Tote Win dividend never pays less than SP on UK *and Irish* racing — [Tote help: Win/Place](http://help.tote.co.uk/en/articles/3236711-tote-win-place)) is capped at a **maximum boost of £200 per selection per customer**, and "individual customers may receive different limits based on their account activity" — i.e. account-level discretionary limits on the subsidy. The Tote says this affects 0.0002% of bets ([Tote help: Update to Tote Guarantee payout limits](http://help.tote.co.uk/en/articles/13750742-update-to-tote-guarantee-payout-limits-from-23-february-2026)). The raw pool dividend is unaffected; only the SP top-up is limited.
- **Rebates/loyalty:** the Tote's "Stayers Club" weekly bonus scheme **ended 27 July 2026** with no replacement announced ([Tote help: Stayers Club](http://help.tote.co.uk/en/articles/16097541-stayers-club)). The API "enhanced rates"/dividend uplifts (including on multi-leg pools) are the de-facto high-volume rebate channel. HKJC-style cash rebates for HK high-rollers do not apply to UK/Irish Tote customers (not offered; no evidence found).
- Historic context: UK Tote Group chairman Alex Frost pledged in 2018 "a 25% reduction in the take-out" ([TDN, 29 May 2018](https://www.thoroughbreddailynews.com/a-collective-vision-to-revitalise-the-tote/)); the UKHBF table (Win still 19.25%) suggests headline domestic deductions have not fallen — the value has instead been delivered via Tote+/Guarantee/API enhancements.

## 7. Integration and monetization: Partner API and affiliates

**Tote Partner API (verified live 28 Aug 2026).**
- Public documentation: [developers.services.tote.co.uk](https://developers.services.tote.co.uk/) — sections for Getting Started, Guides (bet placement incl. singles, multiples, permutations, async; settlement; banker bets; best practices), GraphQL data fetching/pagination, **Subscriptions** (push updates), Code Examples, and ~23 bet types.
- "The Tote Partner API provides a GraphQL endpoint that can be used to query the Tote for information on Events, Products and Bets **as well as placing bets**" ([Introduction](https://developers.services.tote.co.uk/getting-started/introduction/)).
- Production endpoint: `https://hub.production.racing.tote.co.uk/partner/gateway/graphql` (GraphQL over HTTP POST; schema browser at `/graphql/ui`; SDL download via `?sdl`) ([Endpoint](https://developers.services.tote.co.uk/getting-started/endpoint/)). Direct probe on 28 Aug 2026 returned HTTP 401 without credentials — live, auth-gated.
- Onboarding: by application to **connectivity@tote.co.uk**; a test environment exists. **Could not verify:** eligibility criteria, fees, rate limits, or commercial terms — none are published; expect a B2B conversation. The consumer-facing pitch ("historical data extraction across racing pools and betting at enhanced rates… larger dividends on winning bets across all UK and Irish pools" — tote.co.uk/racing/data-api, via search snippet) suggests the Tote actively courts algorithmic bettors, not just white-label operators.
- Third-party integrations: no public directory found. sharpbetting.co.uk (Tote-partnered) describes algorithmic and website-based API betting; specific consumer apps using the API **could not be verified**.

**Affiliate programme (verified 28 Aug 2026).** Self-serve portal at [affiliates.tote.co.uk](https://affiliates.tote.co.uk/account/register) ("Tote Affiliates", powered by RavenTrack, © 2026), with open registration and full Standard Partner Terms on the signup page:
- Remuneration: **Revenue Share, CPA, Revenue Share + CPA, or Fixed Fee**, per a negotiated "Commercial Summary Sheet" (percentages not published).
- Revenue share runs on **Net Gambling Revenue** (pool turnover minus dividends *including* Tote Guarantee/dividend enhancements) for a **"Lifetime Revenue Period" ending at the earlier of 3 years from the customer's first qualifying deposit** or the customer lapsing (375 days inactive).
- Terms explicitly require partner marketing aimed at customers "in UK and Ireland" to comply with Gambling Commission (and applicable) rules — i.e. **Irish traffic is in scope for the affiliate programme**.

This is the app's cleanest monetization for Tote-framed picks: affiliate links to tote.ie/tote.co.uk (subject to GRAI advertising rules), with the Partner API as the later, deeper integration (live pool odds in-app, one-click bet handoff, or even automated betting for the developer's own account).

## 8. Product implications for the picks app

1. **Two products in one.** On ~360 ordinary Irish fixtures/year, Tote pools cannot absorb meaningful money; Tote framing there should be *informational* (e.g. "Placepot value", small-stakes exotics where the model's edge in trifecta-ordering is largest and competition is softest). On the ~6 Irish World Pool days (plus ~40 UK/international World Pool days a user can also bet), the app can legitimately pitch Benter-style pool value: 17.5% win takeout, HK-weighted prices that systematically misprice Irish form, and no winner restrictions.
2. **The value-vs-odds engine should treat Tote/World Pool as a third odds surface** alongside bookmaker fixed odds and Betfair: model probability vs (a) projected Tote dividend (current pool odds are available via the Partner API), (b) BSP, (c) best book price. On World Pool days the interesting signal is *divergence between the HK-driven pool and the UK/Irish market*.
3. **Tote Guarantee still de-risks the win pool** for recreational users (never worse than SP on UK & Irish racing) — a genuine marketing line — but the app should not promise it uncapped: £200-per-selection boost cap and account-level limits since 23 Feb 2026.
4. **Late pool volatility is the execution risk**: pari-mutuel dividends are unknown at bet time; the HK late money on World Pool races moves projected dividends sharply in the last minutes. The app should display "projected dividend" with uncertainty, not a fixed price.
5. **Small pools cut both ways for a tipping product:** if even a few hundred app users follow a pick into a €8k Irish win pool, they crush their own dividend. Tote-pool value framing for a *mass* user base only works on World Pool days; on ordinary days it must be positioned as micro-stakes fun or the picks will self-defeat. (This is arguably a feature for a *small*, paid user base.)

## 9. Explicitly unverified / stale-risk items

- **Tote Ireland's current official deduction rates for Win/Place/Exacta/Trifecta/Superfecta/Jackpot** — not found in any accessible source; confirm from an Irish IP (tote.ie rules) or from Tote Ireland directly. Only the Irish Placepot 30% (vs 27% UK) is documented, by third parties.
- **UKHBF deduction table freshness** — site is © 2026 but the table itself is undated; cross-check against tote.co.uk betting rules from a UK/Irish IP.
- **Status of the HRI–UK Tote alliance beyond 2027** and any Tote Ireland sale/operational-takeover discussions — no 2025–26 source found.
- **Irish Champions Festival 2025/2026 World Pool turnover** — per-day figures were not published in accessible outlets (2023 Leopardstown €27.7m is the latest found).
- **World Pool vs Betfair SP** — no independent study found; all dividend-comparison stats are Tote/HKJC-sourced.
- **Partner API commercials** (fees, revenue-share on API betting's "enhanced dividends", eligibility) and **affiliate commission percentages** — negotiated, unpublished.
- **Whether TDCO's GRAI licence includes pool betting on its remote betting licence** — the register CSV's activity field says only "Remote Betting"; the pool-betting specification is not visible in the public CSV.
- Tote+ 10% dividend boost for digital customers is sourced to 2021 marketing; current status unverified.

---

## Sources

**Official / primary**
- HRI Factbook 2025 (betting statistics tables): https://www.hri.ie/HRI/media/HRI/Comms/Documents/HRI-Factbook-2025-FINAL-VERSION.pdf
- HRI Annual Report 2024 (Tote Ireland audited figures, subsidiaries): https://www.hri.ie/HRI/media/HRI/Comms/Documents/Annual-Report-2024-DUAL-ENGLISH-IRISH.pdf
- GRAI — licence application guidance / phasing: https://www.grai.ie/licensing-regulation/business-to-consumer-licenses/licensing-phasing
- GRAI — Pool Betting Guidance (PDF): https://grai-cms-production-bucket.s3.eu-west-2.amazonaws.com/cms-media/pool-betting-guidance.pdf
- GRAI — news (remote licences commenced 1 Jul 2026; first applications Feb 2026; 2025 Annual Report): https://www.grai.ie/news
- GRAI — licence register (CSV, 27 Aug 2026): https://www.grai.ie/register
- Tote help centre — Worldpool deduction rates: http://help.tote.co.uk/en/articles/5332509-worldpool-deduction-rates
- Tote help centre — Tote Guarantee payout limits from 23 Feb 2026: http://help.tote.co.uk/en/articles/13750742-update-to-tote-guarantee-payout-limits-from-23-february-2026
- Tote help centre — Win & Place (Guarantee on UK and Irish racing): http://help.tote.co.uk/en/articles/3236711-tote-win-place
- Tote help centre — Irish Jackpot (tote.ie availability): http://help.tote.co.uk/en/articles/7011602-what-is-an-irish-jackpot
- Tote help centre — Placepot; Stayers Club closure: http://help.tote.co.uk/en/articles/3440362-placepot ; http://help.tote.co.uk/en/articles/16097541-stayers-club
- Tote Partner API docs: https://developers.services.tote.co.uk/getting-started/introduction/ ; https://developers.services.tote.co.uk/getting-started/endpoint/
- Tote Partner API endpoint (liveness check): https://hub.production.racing.tote.co.uk/partner/gateway/graphql
- Tote Affiliates portal + Standard Partner Terms: https://affiliates.tote.co.uk/account/register
- Tote data/API marketing page (via search snippet; geo-blocked direct): https://tote.co.uk/racing/data-api
- Irish Tote dividends published daily: https://www.hri-ras.ie/results/

**Racing press (Thoroughbred Daily News)**
- Irish & UK Totes form alliance (28 Apr 2020): https://www.thoroughbreddailynews.com/irish-and-uk-totes-form-alliance/
- World Pool 2025 turnover HK$9.3bn (6 Jan 2026): https://www.thoroughbreddailynews.com/world-pool-turnover-on-overseas-races-soars-to-hk9-3-billion-in-2025/
- HRI 2025 statistics (28 Jan 2026): https://www.thoroughbreddailynews.com/eade-hails-broad-appeal-of-irish-racing-as-key-metrics-rise/
- Irish 2,000 Guineas added to 2025 World Pool (20 Mar 2025): https://www.thoroughbreddailynews.com/irish-2000-guineas-card-added-to-world-pool-schedule/
- Irish Champions Weekend fully in World Pool (8 Aug 2024): https://www.thoroughbreddailynews.com/world-pool-to-be-active-during-irish-champions-weekend/
- Irish Derby Day record World Pool turnover (2 Jul 2024): https://www.thoroughbreddailynews.com/irish-derby-day-records-highest-ever-turnover-on-world-pool/
- Irish Champion Stakes Day €27.7m (13 Sep 2023): https://www.thoroughbreddailynews.com/irish-champion-stakes-day-popular-on-world-pool-with-e27-7m-wagered/
- Irish/German Derbys World Pool debut (Jul 2023): https://www.thoroughbreddailynews.com/irish-and-german-derbys-make-strong-world-pool-showing/
- Royal Ascot 2025 World Pool £150m (25 Jun 2025): https://www.thoroughbreddailynews.com/world-pool-betting-figures-at-royal-ascot-rise-10-to-150m/
- Everest 2025 single-race record (18 Oct 2025): https://www.thoroughbreddailynews.com/ka-ying-risings-everest-smashes-turnover-record-in-world-pool/
- 2026 July–Aug World Pool fixtures incl. Irish Oaks (28 May 2026): https://www.thoroughbreddailynews.com/hkjc-confirms-world-pool-fixtures-for-july-and-august/
- Nine new late-2026 fixtures incl. St Leger (6 Aug 2026): https://www.thoroughbreddailynews.com/world-pool-to-debut-nine-new-fixtures-during-final-months-of-2026/
- Fillies' Classics return Q2 2026 (24 Mar 2026): https://www.thoroughbreddailynews.com/fillies-classics-return-as-british-world-pool-races-in-q2/
- 10 things about World Pool at Royal Ascot (14 Jun 2021): https://www.thoroughbreddailynews.com/10-things-to-know-about-the-world-pool-at-royal-ascot/
- HKJC world first / dividend comparison stats (15 Jul 2021): https://www.thoroughbreddailynews.com/hkjc-world-first-aims-to-enhance-global-participation/
- Tote trainers revenue-share scheme & Tote Guarantee launch (12 Mar 2022): https://www.thoroughbreddailynews.com/trainers-to-benefit-from-new-tote-scheme/
- Frost/Alizeti takeout pledge (29 May 2018): https://www.thoroughbreddailynews.com/a-collective-vision-to-revitalise-the-tote/
- Irish Derby 2026 (World Pool context, 28 Jun 2026): https://www.thoroughbreddailynews.com/benvenuto-cellini-leads-obrien-1-2-3-for-irish-derby-number-18/

**Independent / reference**
- Horseracing Bettors Forum — deductions & takeouts table: https://ukhbf.org/betting-deductions-takeouts/
- Wikipedia — Tote Ireland: https://en.wikipedia.org/wiki/Tote_Ireland
- Wikipedia — Horserace Totalisator Board (UK Tote history, World Pool, ownership): https://en.wikipedia.org/wiki/Horserace_Totalisator_Board
- Wikipedia — Gambling Regulatory Authority of Ireland: https://en.wikipedia.org/wiki/Gambling_Regulatory_Authority_of_Ireland
- tix.bet — Tote deductions incl. Irish Placepot 30% (via search snippet): https://www.tix.bet/knowledge/deductions/
- sharpbetting.co.uk — Tote API betting (Tote-partnered content): https://sharpbetting.co.uk/articles/Tote-API-Betting-Unlocking-Value-in-Pool-Wagering
