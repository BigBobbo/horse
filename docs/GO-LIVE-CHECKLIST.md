# Go-live checklist

Work through this before staking money, and again before taking a single
paying subscriber. Every item traces to a research report in
`docs/research/`; the citation is given so you can re-check a claim that may
have moved. Several items are explicitly time-sensitive — Irish gambling law
is being commenced in stages during 2026–2028.

---

## 1. Prove the model before you fund it

- [ ] **Backtest is clean.** `furlong backtest` runs without a `LeakageError`,
      folds are chronologically separated, and the report's
      `roi_is_significant` is not being read as proof on a small sample.
- [ ] **The model adds information.** `furlong train` reports the α = 0
      likelihood-ratio test as significant, and the backtest's folds show
      `"priced": true`. The engine enforces this itself — below
      `FURLONG_BLEND_SIGNIFICANCE` it advises nothing — so the item here is
      that you have **not raised the threshold to make suggestions appear**.
      A blend can differ from the market while knowing nothing it does not:
      with `alpha` at zero and `beta` below one it simply flattens the
      market's prices and every longshot clears the edge filter. That is what
      27,381 real Betfair-priced races produced, and it looked like a +2.22%
      ROI on 10,747 bets. (`REAL-DATA-FINDINGS.md`)
- [ ] **You have run the free real-data screen** — `furlong import-betfair-hub
      --download --with-benchmark`, then `train` and `backtest` — and read the
      result against the published benchmark in the same files. If Betfair's
      own model also earns zero `alpha` against BSP, the closing line is the
      bar; if yours does and theirs does not, the problem is your features.
- [ ] **Paper-trade for at least 200 suggestions**, recording the advised
      price at publication.
- [ ] **Closing line value is positive** over those 200: mean CLV above 1.0,
      and beating the close more often than not. This is the gate. Profit
      over 200 bets is noise — proving a 4% edge from P/L alone needs
      7,000–23,000 bets. (`market-economics.md`)
- [ ] **You have sized the bankroll for the drawdown**, not the expectation:
      200–300 units, with a 24–31 bet losing run treated as normal.
      (`market-economics.md`, §6)
- [ ] Staking is fractional Kelly (default quarter), never full. Overestimate
      your edge by 2× at full Kelly and growth turns negative.
      (`prediction-modeling.md`)

## 2. Data licensing

- [ ] **Production data comes from a licensed feed**, not scraping. The
      Racing API's terms explicitly permit apps and machine learning but
      prohibit reselling raw data; Racing Post's terms restrict use to
      personal, non-commercial purposes. (`irish-racing-data.md`)
- [ ] You understand that *BHB v William Hill* (ECJ C-203/02) removed
      database-right protection from racecard facts, but *Ryanair v PR
      Aviation* means a site's terms still bind you by contract. Scraped
      history is fine for private model development, not for a product.
      (`legal-regulatory-ireland.md`)
- [ ] If you licensed ratings (Timeform via PA Betting Services, Racing Post
      B2B), you have checked whether you may *display* them or only use them
      internally.
- [ ] Betfair historic data is licensed for your own use; you are not
      redistributing it.

## 3. Irish legal and regulatory

- [ ] **You take no bets and hold no customer money.** That is what keeps a
      tips/analytics product outside the Gambling Regulation Act 2024's
      licensing categories. The moment you accept stakes, match bettors, or
      run a white-label book, you need a GRAI licence (remote betting
      application fees run €20,000–€400,000). (`legal-regulatory-ireland.md`)
- [ ] **You link only to GRAI-licensed operators.** Since 1 July 2026 it is
      illegal for remote operators to serve Ireland unlicensed, and
      promoting them is GRAI's stated enforcement priority. Check the public
      register before adding any affiliate link.
- [ ] ⚠️ **Re-check the advertising commencements.** Sections 143–151 (the
      5:30am–9pm watershed, social-media follower rules) and section 157
      (inducements) were on the statute book but **not commenced** as of
      August 2026. A single statutory instrument changes this. Verify before
      launching any marketing.
- [ ] ⚠️ **Re-check B2B licensing** if you ever sell odds or model output
      *to a bookmaker* — that is "providing odds to licensees" and needs a
      B2B licence once section 70 commences (expected 2027–2028).
- [ ] No profit guarantees, no "guaranteed winners" language. If you
      advertise performance, tips must be logged with an independent
      verifier *before* the off (ASA/CAP rules; Tipstrr is the cheap route
      to an audited public record). (`edge-apps-global.md`)
- [ ] Tax: individual winnings are not taxable in Ireland (TCA 1997 s.613(2);
      *Graham v Green*), but subscription revenue is ordinary trading income
      and carries 23% VAT on Irish B2C digital services. Take advice if you
      bet a company bank systematically. (`legal-regulatory-ireland.md`)

## 4. Responsible gambling

- [ ] 18+ age gate before any suggestion is visible.
- [ ] Helpline **1800 936 725** and GamblingCare.ie on every page (Furlong's
      base template does this; assert it stays true if you re-skin).
- [ ] The expectations page is not buried. Users see the losing-run and
      bankroll numbers before they see a bet.
- [ ] Users can suppress bookmaker links, and lapsed users are never emailed
      "come back and bet" messaging — that would collide with the spirit of
      section 157 once commenced.
- [ ] ⚠️ The National Gambling Exclusion Register was not live as of August
      2026. When it goes live, check whether any obligation reaches
      affiliates.

## 5. Execution reality

- [ ] **You expect bookmaker accounts to be restricted.** They will be, and
      quickly. Design the flow so a restricted user still gets value via the
      exchange. (`odds-and-betting-apis.md`)
- [ ] **The exchange is the primary venue.** Betfair permits bots explicitly;
      a live App Key is **£499 one-off** and cannot be used read-only.
      Develop against the free delayed key. Commission of 2% is attainable
      on the Basic rewards plan and is already baked into the EV calculation.
- [ ] **You have measured Irish liquidity for the races you intend to bet.**
      Irish midweek win markets are materially thinner than UK equivalents;
      exchange racing turnover fell 4.3% in 2025. Do not assume you can get
      a size on at Ballinrobe on a Tuesday. Measure traded volume via the API
      before scaling stakes.
- [ ] Best Odds Guaranteed starts 08:00–09:00 on race day at most firms —
      hence the 09:00 publish time. BOG is real EV but is withdrawn from
      restricted accounts, so it accelerates limiting.
- [ ] For pool play: Tote pools on ordinary Irish days are tiny (win pools
      roughly €5k–12k a race), so a few followers move the dividend against
      each other. Only World Pool days (~6 Irish fixtures a year, €26–28m a
      day, 17.5% win takeout) absorb real money. (`gap-tote-world-pool-ireland.md`)

## 6. If you commercialise

- [ ] Web-first. Apple 5.3.4 and Google Play's real-money gambling policy
      govern store-distributed apps; a PWA avoids both and the 15–30% cut.
      (`legal-regulatory-ireland.md`)
- [ ] Cover **UK and Irish racing from day one**. Ireland-only fails on
      content cadence (many winter weekdays have no Irish racing at all) and
      on addressable market — perhaps 1,000–3,000 people in Ireland pay for
      racing analytics of any kind. Irish-*first* positioning is the open
      wedge; Ireland-*only* is not a business.
      (`gap-irish-demand-and-subscriber-economics.md`)
- [ ] Price in the verified band: serious punter tools cluster at £30–36/month,
      tipster output at £19–29. (`edge-apps-uk-ireland.md`)
- [ ] Affiliate reality: Betfair closed its UK & Ireland affiliate programme
      in May 2025, and most bookmaker programmes use **negative carryover**,
      which is structurally hostile to a product that refers winners. The UK
      Tote programme (no negative carryover) and Matchbook (commission-based,
      so aligned) are the natural partners.
      (`gap-affiliate-monetization-and-bet-tracking.md`)
- [ ] Publish a full, timestamped, odds-referenced bet log from day one. In
      this market, verification *is* the product.

---

## Sign-off

| Gate | Evidence | Date |
|---|---|---|
| Model adds information (ΔR² > 0) | | |
| 200+ paper suggestions, mean CLV > 1.0 | | |
| Data licences in order | | |
| Legal re-check (commencements) | | |
| RG features live | | |
| Bankroll and staking agreed | | |
