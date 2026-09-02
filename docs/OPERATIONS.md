# Operating Furlong

How to run the daily cycle, and how to swap the synthetic world for real
Irish and British racing data. Every timing and cost claim here traces to
`docs/research/` — the relevant report is cited inline.

---

## 1. The daily cycle

Irish declarations close at **10:00 two days before racing** (48 hours, both
codes, permanent since September 2021). GB Flat is also 48 hours; GB jumps
declare at 10:00 the day before. So a day's fields — runners, riders,
headgear — are known the previous evening, and vendor overnight files land
around 19:30. Everything after that is a choice about *price availability*,
not data availability.
(`docs/research/gap-daily-pipeline-timing-and-price-decay.md`)

| Time (Europe/Dublin) | Step | Command |
|---|---|---|
| 19:45 (day before) | Ingest final racecards and overnight prices | `furlong daily --date <tomorrow> --dry-run` to preview |
| 09:00–09:30 | **Publish suggestions** | `furlong daily` |
| 10:15 | Rescore after non-runners and Irish reserves | `furlong rescore --date <today>` |
| After racing | Ingest results and Betfair SP, then settle | `furlong ingest-bsp --download-date <today>` then `furlong settle --date <today>` |
| Weekly | Retrain and re-verify | `furlong train` and `furlong backtest` |

### Why 09:00–09:30

1. **Best Odds Guaranteed is live.** Most firms start BOG between 08:00 and
   09:00 on race day. A price advised at 20:00 the night before carries no
   BOG protection; the same price at 09:00 does.
2. **The overnight errors are gone but the market is not yet efficient.**
   Bookmakers price up around 16:00–18:00 the evening before at tiny limits
   (compilers spend about three minutes per horse). By 09:00 the obvious
   mistakes are corrected, but the professional tipster wave lands around
   09:30 and roughly 65% of turnover arrives in the final fifteen minutes.
3. **Most non-runners have surfaced.** GB withdrawal fines step up after
   09:00, and Irish reserves must declare in by 10:00 (November–January) or
   11:00 (rest of year) — hence the 10:15 rescore.

### Cron

```cron
# Europe/Dublin. Adjust paths; FURLONG_DATA_DIR must point at your database.
45 19 * * *  cd /srv/furlong && furlong daily --date "$(date -d tomorrow +\%F)" --dry-run
0  9  * * *  cd /srv/furlong && furlong daily
15 10 * * *  cd /srv/furlong && furlong rescore --date "$(date +\%F)"
30 22 * * *  cd /srv/furlong && furlong ingest-bsp --download-date "$(date +\%F)" && furlong settle --date "$(date +\%F)"
0  3  * * 1  cd /srv/furlong && furlong train && furlong backtest
```

### Price decay: why every suggestion carries a floor

This is the single most important operational fact in the research. When a
followed tipster publishes, the advised price is gone within minutes:

- Hugh Taylor's tips averaged an **advised 10.41 against an obtainable
  7.35** over a long trial — a 29% haircut on the decimal odds.
- Smart Betting Club tracked prices for fifteen minutes after release and
  measured ROI impacts from **−4.5% to −24.5%** for the worst-affected
  services; one service's paper +£2,688 became −£307.

Furlong therefore publishes a **price floor** with every suggestion — the
shortest price at which the bet still clears `min_edge` — and records the
advised price at publication so closing line value can be measured honestly.
Never take a price below the floor.

---

## 2. Switching to real data

No code changes are needed. Set environment variables (or a `.env` file)
and the same pipeline runs against live racing.

### Option A — The Racing API (recommended starting point)

Covers UK and Irish racecards, results and, from the Standard plan up,
odds from 20+ bookmakers. Pricing starts around **£24.99/month**; rate
limit 5 requests/second; today's cards refresh every 3 minutes.
Its terms explicitly permit building apps and doing machine learning, but
prohibit reselling raw data. (`docs/research/irish-racing-data.md`)

```bash
export FURLONG_SOURCE=racing_api
export FURLONG_RACING_API_USERNAME=your_username
export FURLONG_RACING_API_PASSWORD=your_password
furlong daily
```

Verify the field mapping in `furlong/sources/racing_api.py` against your
plan's live responses on first connection — the connector reads field names
defensively with fallbacks, but the exact payload varies by plan.

### Option B — Betfair Starting Price archives (free, and essential)

Betfair publishes free daily CSVs of Betfair SP for **GB and Irish racing
back to 28 May 2008** at <https://promo.betfair.com/betfairsp/prices>. This
is the canonical closing-price history and the honest benchmark for both
backtesting and CLV.

```bash
furlong ingest-bsp --download-date 2026-08-28        # if reachable from your network
furlong ingest-bsp ~/Downloads/dwbfpricesirewin28082026.csv   # or ingest manually
```

Betfair geo-blocks `promo.betfair.com` in some regions — including, at the
time of writing, the network this was developed on, which returns 403 for
every file. If the download returns a non-200 the command says so and
continues; fetch the files in a browser and pass the paths directly. Option C
below is reachable from everywhere and covers the same prices for 2024
onwards.

### Option C — Betfair's own UK+IRE files (free, no login, and the best screen)

**Start here.** Betfair's data-science team publishes its UK and Irish
thoroughbred model results at
[betfair-datascientists.github.io/data/dataListing](https://betfair-datascientists.github.io/data/dataListing/)
— one file per year to 2025, one per month since, covering 2024 to last
month. Each row is a runner with **Betfair Starting Price and the result**.

```bash
furlong import-betfair-hub --download --inspect   # fetch, then check the shape
furlong import-betfair-hub --with-benchmark       # import, keeping their ratings
furlong train && furlong backtest
```

That is 27,000+ races and 250,000+ priced runners, and it needs no account
anywhere. It is the right screen for three reasons:

- **BSP is the correct benchmark.** Betfair SP is the margin-free closing
  price — the thing this system settles at and measures CLV against. The
  imported book's overround is 1.0019.
- **It is current**, not a 2020 snapshot of a market that has since sharpened.
- **It carries a published benchmark.** `--with-benchmark` stores Betfair's
  own model's rated price in `benchmark_ratings` (deliberately outside
  `odds_snapshots`, so it can never be mistaken for a market quote and is
  never a feature). When your model finds no edge, that tells you whether the
  bar is high or your pipeline is broken.

**What it does not carry is form.** No going, no trainer, no jockey, no draw,
no official rating, no weight, and no finishing position beyond
win/placed/unplaced. **14 of the 29 features are constant on it** — every
trainer and jockey statistic, every going feature, the draw and the official
rating. Going imports as `unknown` rather than being defaulted to `good`, and
finishing positions are banded rather than invented.

So read it as a screen, and the asymmetry is what makes it worth running:

| Result | What it means |
|---|---|
| No edge | Expected, and informative. Check the benchmark: if Betfair's own model also earns zero alpha, the closing line is the bar, not your code. |
| Edge found | Worth paying for form data and morning prices. Not yet evidence of a live edge. |

[`docs/REAL-DATA-FINDINGS.md`](REAL-DATA-FINDINGS.md) records what happened
when this was actually run. Short version: neither Furlong nor Betfair's own
model beat BSP, the engine correctly advised nothing, and doing it caught two
real bugs.

### Option C2 — the Kaggle UK+IRE dataset (free, licensed, and now second choice)

[kaggle.com/datasets/hwaitt/horse-racing](https://www.kaggle.com/datasets/hwaitt/horse-racing)
is 759 MB of UK and Irish racing from 1990 to 2020 under **CC BY-NC 4.0** —
results, Racing Post Ratings, Topspeed, official ratings and Oddschecker odds.
Its advantage over Option C is the one that matters most for modelling: **it
has form data**. Its disadvantages are why it is no longer the first stop:

- **It ends in 2020, and the market has sharpened since.** The 2020 move to an
  "industrial" starting price cut overround-per-horse from 1.79% to 1.52%.
- **Its prices are industry SP, not Betfair SP.** SP carries a bookmaker
  margin of roughly 116% per book; BSP is margin-free. Beating SP is an easier
  bar than the one this system is built to measure, so results are **biased
  optimistic**, and closing line value cannot be measured at all.
- **It needs a Kaggle login to download.**

```bash
# a Kaggle login is required to download; extract the archive first
furlong import-kaggle ~/kaggle-racing --inspect   # check the column mapping
furlong import-kaggle ~/kaggle-racing --years 2015 2016 2017 2018 2019 2020
```

The dataset ships one pair of files per year (`races_YYYY.csv` and
`horses_YYYY.csv`, joined on the race id) and its column names have changed
between vintages, so every field is resolved through a list of candidate
names. **Always run `--inspect` first**: it prints what was detected and names
any required field it could not find. Prices import as starting prices under
the bookmaker name `SP`.

Importing both is the strongest free position available: form from Kaggle,
the honest closing price from Betfair.

### Option D — your own historic results

Any results CSV can be imported with a column mapping (rpscrape-style
exports and the Kaggle UK/IRE datasets both work):

```bash
furlong import-csv results.csv --mapping mapping.json
```

`mapping.json` maps Furlong's field names to your columns; the defaults are
in `furlong/sources/csv_import.py`. Note that scraped Racing Post data is
fine for private model development but cannot be redistributed — the site's
terms restrict use to personal, non-commercial purposes, and *Ryanair v PR
Aviation* means terms of use bind by contract even where database right
does not apply. (`docs/research/legal-regulatory-ireland.md`)

### Realistic monthly cost

| Stack | Contents | Cost |
|---|---|---|
| Budget | Free BSP archives + free delayed Betfair key + own CSV history | ~€0–10/month |
| **Mid (recommended)** | The Racing API Standard + free BSP archives | ~€45–90/month |
| Pro | Racing API Pro + Betwise Smartform (£195 + £65/mo, MySQL, UK+IRE from 2003) + Betfair historic packs | ~€210–350/month |

A live Betfair App Key for placing bets costs **£499 one-off** and cannot be
used read-only. Develop against the free delayed key first.

---

## 3. Before you stake real money

Run through `docs/GO-LIVE-CHECKLIST.md`. The short version: paper-trade
until you have **positive closing line value over at least 200 suggestions**.
CLV separates skill from luck in tens of bets; profit alone needs 7,000 to
23,000 bets at plausible edge sizes. (`docs/research/market-economics.md`)

## 4. Troubleshooting

**"not enough races to backtest"** — the backtest needs more than 1,500
races before its first fold. Measured on the synthetic world, ΔR² is
reliably negative below ~800 training races: a model with less history than
that has no business advising bets.

**"no completed races before <date> to train on"** — the daily run trains
only on races strictly before the target date. Import history first.

**No suggestions produced** — this is normal and often correct. On most
days the market is not wrong enough to be worth the risk. Check
`FURLONG_MIN_EDGE` (default 0.05) if you never see any.

**"Nothing priced ... the model failed to beat the market"** — not a bug, and
not the same thing as "no value today". Before pricing anything the engine
runs a likelihood-ratio test of `alpha = 0` on races held out from the blend
fit, against a null that keeps `beta` free. If the model cannot be shown to
know something the market does not (default threshold p < 0.05,
`FURLONG_BLEND_SIGNIFICANCE`), it advises nothing at all.

This exists because the alternative is worse. Without it, a blend with
`alpha = 0` and `beta = 0.906` — which is what 27,381 real Betfair-priced
races produced — flattens the market's own prices, lifts every longshot past
the edge filter, and advises five figures' worth of bets containing no model
information whatsoever. Raising the threshold to force suggestions is
choosing to bet on arithmetic. `furlong train` prints the test result; if the
p-value is near 1.0, the model needs better features or more history, not a
looser gate. See [`docs/REAL-DATA-FINDINGS.md`](REAL-DATA-FINDINGS.md).

**Suggestions look too good** — an ROI above about 15% over a few hundred
bets is almost always leakage or variance, not edge. Re-read the backtest
report's standard error line before believing it.
