# What the real data said

The synthetic world proved the pipeline runs. This is what happened when it
was pointed at 27,381 real UK and Irish races.

**Headline: on results and closing prices alone, the model does not beat the
Betfair Starting Price, and neither does Betfair's own published model. The
engine therefore advises nothing, which is the correct output.**

---

## 1. The data

[Betfair's data-science team](https://betfair-datascientists.github.io/data/dataListing/)
publishes `UK_IE_Thoroughbred_Racing_Model_*.csv` — one file per year to 2025,
one per month since. It downloads without a login, from a host that is not
geo-blocked, under an explicit download disclaimer.

```bash
furlong import-betfair-hub --download --inspect
furlong import-betfair-hub --with-benchmark
```

| | |
|---|---|
| Races | 27,381 |
| Runners | 258,484 (253,784 priced, 4,700 non-runners) |
| Period | 2024-01-06 to 2026-08-30 |
| Split | GB 21,140 races · IRE 6,241 |
| Codes | Flat 17,284 · National Hunt 10,097 |
| Courses | 86, including Dundalk, the Curragh, Leopardstown, Naas |
| Prices | **Betfair SP for every runner that ran** |

It imports clean, and the imported database reproduces the known shape of
British and Irish racing:

| Check | Imported | Reality |
|---|---|---|
| Favourite strike rate | **34.5%** | ~33–35% |
| BSP book overround | **1.0019** | BSP is margin-free by construction |
| Backing every favourite at BSP | **−0.90%** | ≈ the book's own margin |
| Mean field size | 9.27 | — |
| Distance range | 1,006 m – 6,840 m | 5f to the Grand National trip |

### Why this beats the Kaggle archive

The Kaggle dataset was the plan of record. This is better on the axis that
decides the question:

- **BSP, not industry SP.** Betfair SP is the margin-free closing price and
  the benchmark this system was built to be measured against. Industry SP
  carries a ~116% book, so beating it is a much easier bar and a positive
  result there is flattered.
- **Current.** 2024 to last month, against Kaggle's stop in 2020.
- **No login.** It downloads from this machine; Kaggle does not.

### What it does not carry

No going, no trainer, no jockey, no draw, no official rating, no weight, and
no finishing position beyond win/placed/unplaced. That is the central caveat
on everything below: **14 of the 29 features are constant** on this data —
every trainer and jockey statistic (7), every going feature (3), the draw,
the official rating, and both trainer and jockey Elo. What is left is horse
Elo, career and recent form, distance and course fit, days since last run,
field size and class. The importer records the absence as an absence — going is
stored as `unknown`, not silently defaulted to `good` — and bands the
finishing position into won / placed / unplaced rather than inventing an
order (`betfair_hub.finish_band`).

## 2. The result

```
Races 5,285 · runners 48,252
  McFadden R2     model 0.0355 · market 0.1832 · blend 0.1831
  Delta R2 (blend over market): -0.0000  [no edge over market]
  Blend weights   alpha (model) 0.000 · beta (market) 1.011
  Alpha = 0 test  LR 0.00 on 1 df, p = 1.0000  [the engine will advise nothing]
```

Walk-forward, three folds, 27,381 races:

| Fold | Train races | alpha | beta | LR | p | Priced |
|---|---|---|---|---|---|---|
| 1 | 1,100 | 0.000 | 0.906 | 0.00 | 1.00 | no |
| 2 | 8,083 | 0.033 | 0.959 | 0.07 | 0.80 | no |
| 3 | 14,886 | 0.066 | 0.961 | 0.64 | 0.42 | no |

No fold produced a bet. Backing every runner over the same races returned
−4.01%.

## 3. Is the pipeline broken, or is the bar just that high?

This is the question the `--with-benchmark` flag exists to answer. The files
carry `RATED_PRICE`, Betfair's own model's rating for the same runners, built
by their data-science team with data far beyond what is in the file. It is
stored in `benchmark_ratings`, deliberately outside `odds_snapshots` so the
market layer can never reach it, and it is never a feature.

Blended against BSP on identical races:

| Races | | McFadden R² | alpha | Delta R² over BSP |
|---|---|---|---|---|
| all 27,381 | Betfair SP alone | 0.1871 | — | — |
| | Betfair's own model alone | 0.1231 | — | — |
| | Their model blended with BSP | 0.1871 | **0.000** | **−0.00001** |
| test split, 5,285 | Betfair SP alone | 0.1832 | — | — |
| | Their model alone | 0.1232 | — | — |
| | Their model blended with BSP | 0.1832 | **0.026** | **+0.00004** |

**Betfair's own published model earns a blend weight of essentially zero
against Betfair SP** — exactly zero over the full archive, 0.026 on the test
split. On its own it is a substantially worse predictor than the closing
price.

So the pipeline is not broken. Beating the closing line is simply that hard,
and a well-resourced professional model does not manage it either. Benter's
edge over the Hong Kong market was a Delta R² of 0.0178. Neither model here
produces a positive figure at all over the full archive, and their best
showing anywhere — +0.00004 on the test split — is four hundred times
smaller than his.

### The honest caveat in the other direction

Every number above is measured **against BSP, which is the closing price**.
That is the hardest bar in betting and not the one a real operation faces: you
bet in the morning, hours before the market has finished forming. The research
(`docs/research/gap-daily-pipeline-timing-and-price-decay.md`) is explicit
that the morning market is materially softer.

This dataset contains no morning prices, so it cannot answer that question.
What it establishes is narrower and still worth having:

- **No edge over the closing line on results-and-prices-only features.** Close
  to definitive, and it cost nothing.
- **Whether there is an edge over morning prices, with real form data, is
  untested.** That needs a form archive and a price history, which is what
  The Racing API plus the BSP archives buy.

## 4. What the real data caught

Running this found a defect the synthetic world never would have.

**The first backtest advised 10,747 bets at an apparent +2.22% flat ROI, with
alpha at exactly zero in the fold that produced 84% of them.** Zero alpha means
the model contributed nothing at all. The bets came entirely from beta = 0.906:
raising the market's probabilities to a power below one flattens them, every
longshot's implied probability rises, and thousands of them clear the edge
filter. Average advised odds were 15.10 — the engine had discovered nothing
but the shape of its own arithmetic.

The fix is a likelihood-ratio test of alpha = 0 on the blend window, against a
null that **keeps beta free**, so that any reshaping of the market is credited
to the market and only genuine model information can pass. Below
`FURLONG_BLEND_SIGNIFICANCE` (default 0.05) the engine prices nothing, in the
backtest and in the daily run alike.

A held-out Delta R² was tried first and rejected: the quantity being detected
is of order 0.002 and its sampling error over a few hundred races is several
times that, so it flipped sign between folds and the gate opened by luck. The
likelihood-ratio test scales its threshold with the sample, so on thin
evidence it simply fails to reject — which for a betting system is the right
way to be wrong.

Chasing that down surfaced a second, worse bug. `fit_blend` clamped negative
weights to zero *after* optimising. On a separable problem the unconstrained
fit ran to (alpha 96, beta −96.9) — a perfect in-sample fit — and the clamp
shipped **(96, 0)**, a point the optimiser never scored, whose log-loss was
four times worse than ignoring the model altogether. In production an alpha of
96 means backing the model's top pick at any price. The search is now confined
to non-negative weights from the start, with the market-only fit as a floor.

## 5. Why there is no edge: the market is calibrated against every feature

"The model does not beat the market" and "the market has already priced what
the model knows" are different statements, and only the second tells you what
to do next. `furlong calibration` answers it directly: sort runners into bins
by each feature, and compare each bin's actual win rate with the mean
probability the market assigned it.

```
Market calibration over 253,783 priced runners

  feature                     sorts (pp)   worst gap   max |z|
  recent_form                       11.0        0.15      0.79
  career_place_rate                  9.1        0.23      1.23
  last_finish_norm                   8.2        0.79      1.58
  career_win_rate                    6.2        0.27      1.45
  elo_rank_pct                       5.9        0.23      1.26
  elo_vs_field                       5.9        0.52      3.06
  elo                                5.1        0.29      1.80
  days_since_run                     3.6        0.42      2.34

  2 of 77 bins exceed |z| > 2; 3.5 expected by chance.
```

Recent form sorts win rate across **11 percentage points** — from 7.2% in the
worst bin to 17.9% in the best. The market's implied probability tracks that
to within **0.15 percentage points in every bin**. Elo, career strike rate and
days since last run are the same story.

The count at the bottom is the part to read twice. Across 77 bins, **two**
exceed |z| > 2 where chance alone predicts 3.5. There is not merely no large
mispricing; there are *fewer* apparent anomalies than noise would produce.

This is the answer to "are the features too thin?" — they are not thin, they
sort winners hard. They are **already in the price**.

## 6. One experiment that failed, and why it is worth recording

The obvious response to "half the features are constant" is to build new ones
from what the archive does have: a horse's own past starting prices are a
free, public record of its class, exactly what the missing official ratings
would supply.

It worked as a feature and failed as a design. The model's standalone
McFadden R² rose from 0.0355 to **0.0584**, a 64% improvement, and the new
`prior_log_bsp_vs_field` became the top feature by importance. Alpha stayed at
exactly zero on real data — and on the synthetic world, which has a *known*
planted inefficiency, delta R² fell from **+0.0055 to −0.0017**. The demo's
edge disappeared.

The reason is the two-stage design. The model got better at predicting winners
by copying the market's own historical opinion, which is worth nothing once
the market's *current* opinion is blended in at stage two — and the redundancy
actively cost information the model had of its own. The feature builder's
docstring states the rule this broke:

> The market (odds) is deliberately NOT a feature here — market information
> enters at the second-stage blend, per the Benter two-stage design.

The change was reverted. It is recorded because "this made the model better
and the system worse" is the least intuitive result here, and because the
synthetic world with its planted edge is what caught it — a real-data run
alone would have shown alpha at zero either way and taught nothing.

## 7. Where this leaves the project

The gate is the deliverable. A system that says "no" on 27,381 real races,
when a professional model says no on the same races, is working — that is the
outcome `docs/OPERATIONS.md` describes as *close to definitive, and it cost
nothing*.

What it does **not** license is the conclusion that horse racing is
unbeatable. The tested configuration is: no form data, closing prices, a
thirty-two month window. Each of those is a reason the answer might change:

1. **Morning prices, not the close.** Now the most promising of the three, on
   this evidence. Section 5 shows the *closing* price absorbing every feature
   to within a fraction of a percentage point — but it is the closing price's
   job to do that. The morning market is the one you would actually bet into,
   and nothing here has tested it.
2. **Form data.** Going, official ratings, trainer and jockey records, draw
   and weight are what Benter's variables were made of. Section 6 is the
   caution: new features have to carry information the market does not
   already hold, not a better copy of what it does.
3. **Longer history.** Thirty-two months is short for horse-level Elo to settle.

The Racing API (~£25/month) plus the free BSP archives buys 1 and 2 together.
Until then, the honest position is that this system has been shown to work as
a piece of software and has found no edge to sell.
