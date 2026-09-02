# Furlong

An Irish-first horse-racing value engine. On a given day it suggests bets
from three inputs: historical results, a predictive model, and the value of
each runner against the odds actually available.

It takes no bets, holds no money, and places nothing on your behalf.

```bash
pip install -e .
furlong demo      # generate a world, train, backtest, publish, settle, report
furlong web       # browse the result at http://127.0.0.1:8000
```

`furlong demo` needs no API keys and takes about 30 seconds. It builds a
deterministic synthetic racing world with a known, planted market
inefficiency, then runs the entire pipeline against it — which is how the
system proves it works before anyone spends money.

---

## Why this exists, and what the research says

This project began as a greyhound predictor and was abandoned: the data and
betting integration were not there. The twelve research reports in
[`docs/research/`](docs/research/) checked whether horse racing is
different. It is, on every axis that killed the greyhound version — but the
same research is blunt about the limits:

- **A model alone is worthless.** Benter's decisive step was blending his
  model's probabilities with the public odds; his combined edge over the
  market was a ΔR² of just 0.0178, and that was enough to win close to a
  billion dollars. Furlong implements that two-stage design, and measures
  itself the same way.
- **Verified edges are small.** Independently audited value services sit at
  4–7% ROI. At a genuine 4% edge and average odds of 5.0, a 1,000-bet year
  still loses money about a quarter of the time.
- **Proving profit takes years.** 7,000–23,000 bets at plausible edges.
  Closing line value settles the question in tens of bets, so CLV is the
  headline metric everywhere in this app.
- **Bookmakers restrict winners.** 643,779 British accounts were restricted
  in a single year; roughly one in five affected punters was cut after
  fewer than ten bets. The durable venues are the exchange and the Tote.
- **Advised prices decay in minutes.** One well-known tipster's advised
  average of 10.41 was 7.35 by the time followers got on. Every Furlong
  suggestion therefore carries a **price floor**: below it, there is no bet.

Start with [`docs/research/00-SYNTHESIS.md`](docs/research/00-SYNTHESIS.md)
for the full picture, or [`docs/PRD.md`](docs/PRD.md) for what was built and
the validation criteria each piece had to meet.

## What a run looks like

```
[2/6] Training the model and fitting the market blend
Races 1,511 · runners 14,794
  log-loss/race   model 2.0002 · market 1.8837 · blend 1.8703
  McFadden R2     model 0.0982 · market 0.1507 · blend 0.1568
  Delta R2 (blend over market): +0.0060  [model adds information]
  Blend weights   alpha (model) 0.258 · beta (market) 0.859
  Alpha = 0 test  LR 13.21 on 1 df, p = 0.0003  [model beats the market]
  Top features    career_place_rate 0.13, field_size_norm 0.12, recent_form 0.08,
                  going_slope_today 0.07, elo_vs_field 0.06

[3/6] Walk-forward backtest at Betfair SP minus commission
  fold 1: train 1,198 races · alpha 0.165 · LR  0.68 p=0.409  priced no   (model did not beat the market)
  fold 2: train 2,902 races · alpha 0.059 · LR  0.35 p=0.552  priced no   (model did not beat the market)
  fold 3: train 4,631 races · alpha 0.318 · LR 15.78 p=0.000  priced yes  3,952 bets
Backtest over 3 fold(s): 3,952 bets, 672 winners (17.0%)
  ROI +21.86% (flat-stake +21.85%) vs naive back-everything +2.72%

[4/6] Publishing suggestions for the open card
  Race                Runner        Model    Mkt   Price   Floor    Edge  Stake  Venue
  Curragh 17:55       Horse 0315    30.9%  19.4%    5.63    3.40  +74.0%   1.33  ShamrockOdds
  Cheltenham 13:35    Horse 0392     8.8%   5.3%   18.68   12.17  +61.0%   0.87  exchange
  Cheltenham 18:30    Horse 0216    36.7%  32.3%    3.07    2.90  +11.2%   1.38  exchange
  ...
  9 suggestion(s), 7.05 units staked (1 unit = 1% of bankroll).

[5/6] Running the races and settling
  Settled 9 suggestion(s): 2 won, 7 lost · P/L +4.30u · mean CLV 1.034
```

Nine bets settling at +4.30 units means nothing on its own — that is what
"mean CLV 1.034" is there for. The bets beat the closing price by about 3%
on average, which is the part that would still be true if the results had
gone the other way.

The two folds that priced nothing matter as much as the one that did. Neither
had enough history for the model to be shown to beat the market, so neither
was allowed to advise anything. **On real racing, all three folds come out
that way** — see [`docs/REAL-DATA-FINDINGS.md`](docs/REAL-DATA-FINDINGS.md).

## How it works

**Point-in-time features.** Every feature for a runner is computed strictly
from races run *before* the one being priced — enforced structurally by
date searches, and verified by a test that appends future results and
asserts past feature rows are byte-identical. Opposition-adjusted Elo
ratings, a ridge-shrunk regression of past performance on the going scale,
empirical-Bayes-shrunk trainer and jockey strike rates, decayed recent
form, distance and course fit, days since last run.

**Two-stage model.** A LightGBM model (or a conditional-logit baseline)
produces per-race probabilities via softmax. Those are then blended with the
market's de-vigged probabilities by maximum likelihood, Benter-style.

If the model knows nothing the market does not, **the engine advises nothing
at all.** Before pricing anything it runs a likelihood-ratio test of `alpha =
0` on races held out from the blend fit, against a null that keeps `beta`
free — so a blend that merely flattens or sharpens the market's own prices is
credited to the market, not to the model. This is not decoration: on real
Betfair-priced racing the unguarded engine advised 10,747 bets from a fold
whose alpha was exactly zero, purely because `beta = 0.906` lifted every
longshot past the edge filter.

**Value engine.** De-vigging by Shin's method (or proportional/power),
commission-aware expected value, and three filters: minimum edge, minimum
probability (no longshots — that is where the favourite–longshot bias lives)
and a hard odds ceiling. Quarter-Kelly staking, capped per bet and per day.

**Honest evaluation.** Backtest folds are cut on date boundaries so a single
race day can never be split between training and betting, and a runtime
guard raises if it ever is. Bets are simulated at Betfair SP minus
commission. Reports lead with the standard error and refuse to call a result
significant on a small sample.

## Commands

| Command | What it does |
|---|---|
| `furlong demo` | The whole pipeline end to end on synthetic data |
| `furlong init-db` | Create the SQLite schema |
| `furlong generate` | Build a synthetic racing world |
| `furlong import-csv <file>` | Import historic results from a mapped CSV |
| `furlong import-betfair-hub` | Import Betfair's free UK+IRE files — BSP for every runner |
| `furlong import-kaggle <dir>` | Import the Kaggle UK+IRE dataset (`--inspect` first) |
| `furlong ingest-bsp <files>` | Ingest Betfair SP archives (free, GB+IRE from 2008) |
| `furlong train` | Fit the model and the market blend |
| `furlong backtest` | Walk-forward backtest, JSON + HTML report |
| `furlong daily` | Publish today's suggestions (`--dry-run` to preview) |
| `furlong rescore --date D` | Re-price after non-runners |
| `furlong settle --date D` | Settle against results and BSP, compute CLV |
| `furlong report` | Performance report |
| `furlong web` | The web UI |

## Using real data

No code changes — set environment variables and the same pipeline runs
against live Irish and British racing:

```bash
export FURLONG_SOURCE=racing_api
export FURLONG_RACING_API_USERNAME=...
export FURLONG_RACING_API_PASSWORD=...
furlong daily
```

Screen the method first, for free and with no account anywhere. Betfair's
data-science team publishes its
[UK and Irish thoroughbred files](https://betfair-datascientists.github.io/data/dataListing/):
27,000+ races from 2024 to last month, with **Betfair SP for every runner** —
the margin-free closing price this system settles at.

```bash
furlong import-betfair-hub --download --inspect
furlong import-betfair-hub --with-benchmark
furlong train && furlong backtest
```

**This has been run, and [`docs/REAL-DATA-FINDINGS.md`](docs/REAL-DATA-FINDINGS.md)
is what it said.** In short: over 27,381 real races the model earned a blend
weight of exactly zero and the engine advised nothing. So did Betfair's own
published model on the same races — its alpha against BSP is also zero. The
closing line is simply that hard, and the files carry no going, trainers,
jockeys, ratings or finishing positions, so **14 of the 29 features are
constant** on it.

The Kaggle UK+IRE dataset (1990–2020, CC BY-NC) is still worth importing
alongside it: it is the only free source here with real form data. Its prices
are industry SP, so it flatters results and cannot measure CLV, and it needs a
Kaggle login. See [`docs/OPERATIONS.md`](docs/OPERATIONS.md).

For running daily against live racing, the stack is The Racing API (from
about £25/month for UK+IRE racecards, results and 20+ bookmakers' odds) plus
Betfair's free BSP archives. [`docs/OPERATIONS.md`](docs/OPERATIONS.md) has
the daily schedule, the alternatives and the real costs.

## Before betting real money

Read [`docs/GO-LIVE-CHECKLIST.md`](docs/GO-LIVE-CHECKLIST.md). The short
version: paper-trade until you have positive closing line value over at
least 200 suggestions, only ever link to GRAI-licensed operators, and size
your bankroll for a 30-bet losing run, because you will have one.

## Development

```bash
pip install -e ".[dev]"
pytest                    # 200+ tests, a few minutes
```

The test suite is the argument that this works. It includes a leakage test,
a "useless model earns zero blend weight" test, a naive-baseline comparison,
and a check that no page can be served without responsible-gambling
information.

The sharpest tests are the ones written after the real data broke something:
that a monotone rescaling of the market cannot pass as information, that an
informative model on 25 races still fails closed, that the daily run never
reaches the value engine when the model failed its own test, and that the
blend fitter never ships weights it did not actually score.

## Layout

```
furlong/
  sources/     synthetic world, Betfair BSP + hub files, The Racing API, CSV
  features/    point-in-time feature builder and datasets
  modeling/    conditional logit, LightGBM, the Benter blend, evaluation
  value/       de-vigging, EV engine, Kelly staking, settlement
  backtest/    walk-forward engine, backtest and performance reports
  pipeline/    daily run, non-runner rescore, demo
  web/         FastAPI app and templates
docs/
  PRD.md, OPERATIONS.md, GO-LIVE-CHECKLIST.md,
  REAL-DATA-FINDINGS.md, research/
```

## Licence and disclaimer

MIT. **18+.** Gambling involves risk and most people who bet lose money over
time. Nothing here is a prediction of any result, and no strategy is
guaranteed to profit. If gambling is causing you harm, the Irish problem
gambling helpline is **1800 936 725** and support is available at
[GamblingCare.ie](https://www.gamblingcare.ie/).
