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

## 7. Two more places to look, both closed

Sections 2-6 all concern one market: the Betfair win market at the close. Two
obvious escapes remained, and both were free to test on data already
imported. `furlong efficiency` runs them.

### The place market (the Dr Z test)

Hausch, Ziemba and Rubinstein's system — the best-documented profitable
racing system before Benter — treated the win market as efficient, used it to
price the place market, and bet the difference. Place pools are thinner and
carry more casual money. The import brought in **253,054 place prices**
alongside the win prices, so the test costs nothing.

No Harville formula is assumed. Runners are binned by *win*-market
probability and each bin's actual place rate is compared with the place
market's own de-vigged probability:

| places | bins | largest \|z\| | backing everything at place BSP |
|---|---|---|---|
| 2 | 10 | 0.98 | **+0.47%** ± 1.60 (1 SE) |
| 3 | 10 | 2.76 | **−3.14%** ± 0.72 |
| 4 | 10 | — | **−2.18%** ± 1.56 |

One bin showed +9.8% — and its standard error is 14.1, so z = 0.70 on average
odds of 49.65. The two bins that *are* significant are both negative: the
favourite–longshot bias, running the wrong way to bet on. Whatever Dr Z found
in the 1980s has been arbitraged away.

### Segments

Perhaps efficiency is not uniform: Irish racing is a thinner market inside a
liquid one, jumps differ from flat, small fields from big. Backing every
runner at BSP, by segment:

| slice | best segment | return |
|---|---|---|
| country | IRE | −3.29% ± 3.29 |
| code | NH | −2.34% ± 3.01 |
| field size | ≤7 | −1.72% ± 1.78 |
| odds band | 11–21 | −0.91% ± 1.65 |
| country × odds band | IRE / 11–21 | **+1.31% ± 3.16** |

The best segment found anywhere is Irish runners at 11–21, at +1.31% with a
standard error of 3.16 — z = 0.41, which is nothing. Every other slice is
negative. Across odds bands, where self-calibration is a real test, the
market is accurate to within 0.6 of a percentage point.

**A note on the calibration column.** It reads `n/a` for country, code and
field size, and that is deliberate. Proportional de-vigging forces each
race's book to sum to 1, so any slice made of *whole races* has a mean quoted
probability equal to its win rate by construction — it would report perfect
calibration on any market however wrong. Only slices that cut across a race,
like an odds band, can say anything. The first version of this tool printed
0.00 for all of them, which looked like the strongest result in the report
and was an artefact; a test caught it.

## 8. The one avenue that is not closed — and how far it goes

Everything above is measured against Betfair SP, the *closing* price. The
open question was always the market you would actually bet into, hours
earlier. The UK/IRE hub files carry BSP alone, so they cannot answer it.

Betfair's Australian and New Zealand files can. They carry
`WIN_PREPLAY_WEIGHTED_AVERAGE_PRICE_TAKEN` alongside `WIN_BSP` — a real
pre-off price and the close, for the same runners, on the same exchange.
Wrong jurisdiction, right mechanism. Over 192,564 runners and 19,810 races
from 2024 to 2026:

| BSP band | n | CLV of the pre-off price | return at BSP | return pre-off |
|---|---|---|---|---|
| 1–3 | 9,574 | **1.022** | −2.51% ± 1.17 | **−0.34% ± 1.20** |
| 3–6 | 29,979 | 1.010 | −0.01% ± 1.07 | +0.87% ± 1.08 |
| 6–11 | 36,571 | 1.001 | −4.28% ± 1.38 | −4.07% ± 1.39 |
| 11–21 | 39,842 | 0.992 | −1.15% ± 1.88 | −1.70% ± 1.88 |
| 21+ | 76,598 | 0.947 | −1.36% ± 3.88 | −8.49% ± 3.23 |

**The pre-off market is genuinely not the close.** Favourites shorten into
the off and longshots drift, at z = −47 and z = +166 respectively. This is
the first positive-direction finding in the whole investigation, and it is
not marginal: it is one of the largest effects here.

**And it is worth almost exactly the commission.** Backing every favourite at
the pre-off price returns −0.34% ± 1.20 — indistinguishable from zero, and
not positive. A CLV of 1.022 against a 2% commission is a wash. The market
is predictably wrong and still does not pay.

That is worth stating precisely, because it is the sharpest thing this
project learned. **Positive closing line value is necessary and not
sufficient.** The system was built to treat CLV as the headline metric on the
grounds that it separates skill from luck in tens of bets rather than
thousands — that reasoning stands. But a CLV of 1.02 obtained by backing
every favourite is free to anyone and pays nobody. What has to beat
commission is CLV *over and above* the generic drift, and that is what a
model would have to supply — the same model that earns α = 0.

### One trap worth naming

`WIN_PREPLAY_MAX_PRICE_TAKEN` — the best price any backer got pre-off —
returns **+39.6%** if you "back everything" at it. That is not an edge; it is
hindsight selection of the best fill in every market. It is recorded here
because a figure like that is exactly what a backtest looks like when it
quietly assumes a price nobody could systematically take.

### What would settle it

The free daily archives at `promo.betfair.com/betfairsp/prices` carry
**MORNINGWAP** for GB and Irish racing back to 2008 — a genuine morning
price, far earlier than a pre-off volume-weighted average, and therefore a
better test than the ANZ proxy above. `furlong ingest-bsp` already parses it
and `furlong efficiency` already reports it; the host is geo-blocked from the
machine this was developed on, so the files have to be fetched in a browser:

```bash
furlong ingest-bsp ~/Downloads/dwbfpricesukwin*.csv
furlong efficiency          # the drift table fills in
```

If the morning drift for UK and Irish favourites is materially larger than
the 2.2% seen in Australia, the question reopens. If it is the same size,
this is finished.

## 9. Where this leaves the project

The gate is the deliverable. A system that says "no" on 27,381 real races,
when a professional model says no on the same races, is working — that is the
outcome `docs/OPERATIONS.md` describes as *close to definitive, and it cost
nothing*.

Five independent things now say the same thing, and none of them is a
modelling failure:

1. Our model earns α = 0 against Betfair SP.
2. **Betfair's own published model earns α = 0 against it too.**
3. Every feature we compute is priced to within a fraction of a percentage
   point, with fewer anomalies than chance predicts.
4. The place market — the classic soft one, with a profitable precedent —
   is priced just as tightly.
5. No segment of the market is beatable by backing at BSP: the best slice
   found anywhere is +1.31% ± 3.16.

**The last avenue is now partly answered too.** Section 8 shows the earlier
market really is softer than the close — but by about the size of the
commission, which makes the generic drift free to everyone and profitable to
nobody. The remaining question is narrow and specific: is the *morning* drift
in GB and Irish racing materially bigger than the 2.2% measured in Australia?
That takes one browser download and two commands, and it is the only thing
left that could reopen this.

The runner-up is form data — going, official ratings, trainer and jockey
records — with section 6 as the standing caution: a new feature has to carry
information the market does not already hold, not a better copy of what it
does.

The honest position is that this system has been shown to work as a piece of
software, has been pointed at the market it was built for, and has found no
edge to sell. That is a real answer to the question the project set out to
ask, and it cost nothing but time.
