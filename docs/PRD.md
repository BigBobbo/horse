# PRD — Furlong: Irish-first Horse-Racing Value Engine

**Version:** 1.0 · **Date:** 2026-08-29 · **Status:** Approved for build
**Basis:** the twelve research reports in `docs/research/` (synthesis: `docs/research/00-SYNTHESIS.md`).

---

## 1. Product overview

Furlong is an application that, on a given day, produces **bet suggestions for Irish (and UK) horse racing** by combining:

1. **Historical results** — a local, point-in-time-correct racing database built from pluggable sources;
2. **A predictive model** — a per-race probability model (conditional logit baseline + gradient-boosted model) blended with market odds Benter-style;
3. **Perceived value vs available odds** — a de-vigged, commission-aware expected-value engine over bookmaker and exchange prices, with fractional-Kelly staking and price-floor semantics.

It ships as a Python package with a CLI (`furlong`) and a web UI (FastAPI), designed to run as a daily pipeline (evening ingest → 09:00–09:30 IST publish → 10:15 non-runner rescore, per the operational research).

### 1.1 Goals (v1)

- G1: A complete, tested, end-to-end pipeline: ingest → features → model → blend → value → suggestions → tracking → performance reporting.
- G2: Real-data-ready: connectors for The Racing API (racecards/results/odds) and Betfair BSP files implemented against their documented formats, configured by env vars — no code changes needed to go live.
- G3: Provable correctness without paid keys: a deterministic **synthetic racing world** with known ground truth validates the entire system (the model must find the planted inefficiency; near-fair markets must show ≈ −commission returns).
- G4: Honesty by design: CLV-vs-BSP tracking from day one, min-edge/min-prob filters, fractional Kelly, drawdown-aware reporting, responsible-gambling surfaces, price floors on every suggestion.
- G5: A single demo command that takes a fresh checkout to a browsable app with suggestions and a backtest report.

### 1.2 Non-goals (v1)

- No real-money bet placement (Betfair execution is stubbed behind an interface; live keys and `placeOrders` are a deliberate later step).
- No payments/subscriptions, no native mobile apps (web-first per the app-store research).
- No scraping of Racing Post/Oddschecker or any ToS-protected site.
- No multi-user auth (single-operator tool; SaaS hardening is post-v1).

### 1.3 Product principles (from research)

- **The blend is the model** — market odds are a feature/benchmark, never ignored (Benter ΔR² doctrine).
- **Exchange-first execution**; bookmaker prices are display + BOG-aware EV only.
- **CLV is the KPI**; P/L needs 7k–23k bets to prove anything.
- **No bet is a position** — most races produce no suggestion.
- **Point-in-time or it didn't happen** — every feature must be computable strictly before the race.

---

## 2. Architecture

```
furlong/
  config.py          settings (env + file), commission/staking params
  db.py              SQLite schema + connection + migrations
  models.py          typed domain entities
  sources/           data connectors
    base.py          Source interface (racecards, results, odds)
    synthetic.py     deterministic synthetic racing world (ground truth)
    racing_api.py    The Racing API client (env: RACING_API_USERNAME/PASSWORD)
    betfair_bsp.py   Betfair BSP CSV ingest (free files, GB+IRE 2008→)
    csv_import.py    user-provided historic results (rpscrape/Kaggle-like)
  features/
    builder.py       point-in-time feature computation
    dataset.py       grouped training matrices, chronological splits
  modeling/
    conditional_logit.py   numpy/scipy MLE softmax baseline
    gbm.py                 LightGBM model with per-race softmax
    blend.py               Benter second-stage (alpha·log f + beta·log q)
    evaluate.py            log-loss, McFadden R², ΔR², calibration
  value/
    devig.py         proportional / power / Shin overround removal
    engine.py        EV computation, filters, best-price, BOG
    staking.py       fractional Kelly, caps, flat stakes
    settlement.py    results, non-runners, Rule 4, CLV
  backtest/
    engine.py        walk-forward simulator at BSP − commission
    report.py        ROI, drawdown, losing runs, CLV, HTML/JSON reports
  pipeline/
    daily.py         daily suggestion run
    rescore.py       non-runner rescore
  web/
    app.py           FastAPI + Jinja UI + JSON API
    templates/
  cli.py             `furlong` entry point
tests/               pytest suite incl. fixtures + golden files
docs/                PRD, research, ops guide, go-live checklist
```

Storage: SQLite (zero-ops, single-operator scale — ~35–60 races/day). All times UTC internally, Europe/Dublin for display/scheduling.

---

## 3. Data model (core tables)

- `courses(id, name, country, surface_types)`
- `horses(id, name)` · `trainers(id, name)` · `jockeys(id, name)`
- `races(id, source_id, course_id, start_time_utc, date, race_type, distance_m, going, race_class, field_size, status)`
- `runners(id, race_id, horse_id, trainer_id, jockey_id, draw, weight_lbs, official_rating, age, status[declared|nonrunner|ran], finish_pos, beaten_lengths, win_flag)`
- `odds_snapshots(id, runner_id, source[book|exchange], bookmaker, ts_utc, odds_decimal)`
- `bsp_prices(runner_id, market[win|place], bsp, ppwap, morning_wap, pp_max, pp_min)`
- `model_runs(id, ts, model_kind, params_json, metrics_json, artifact_path)`
- `suggestions(id, date, race_id, runner_id, model_prob, blend_prob, fair_odds, advised_odds, price_floor, source, ev, stake_units, status[open|withdrawn|settled], created_ts)`
- `bets/settlements(suggestion_id, result, pl_units, bsp_at_off, clv, rule4_deduction)`

---

## 4. Epics and tasks

Every task lists **Validation criteria (VC)** — objective checks (automated tests unless stated). A task is done only when its VC pass and the full suite is green.

### Epic 1 — Foundations

- **T1.1 Scaffolding & CLI skeleton.** `pyproject.toml` (package `furlong`, console script), pytest wiring, package layout.
  **VC:** `pip install -e .` succeeds; `furlong --help` lists subcommands (`init-db, generate, ingest-bsp, import-csv, build-features, train, backtest, daily, rescore, settle, report, web, demo`); `pytest` runs.
- **T1.2 Configuration.** Env-driven settings with defaults + `.env.example`: DB path, data dir, commission (default 0.02 exchange), staking (kelly_fraction 0.25, bankroll units 200, min_edge 0.05, min_prob 0.05, max_odds 21), API credentials, timezone.
  **VC:** unit tests: defaults load; env overrides win; missing key raises a clear error only when the relevant source is used.
- **T1.3 Database layer.** Schema above, `furlong init-db`, idempotent creation, FK integrity.
  **VC:** tests: fresh init creates all tables; second init is a no-op; FK violation raises.

### Epic 2 — Data layer

- **T2.1 Domain entities + repositories.** Typed entities and persistence helpers (upserts keyed on source ids).
  **VC:** round-trip tests (persist → load → equality) for race/runner/odds/BSP; upsert dedupe test.
- **T2.2 Synthetic racing world.** Deterministic generator: ~600 horses with latent ability + form cycles + going/distance preferences, trainers/jockeys with skill effects, IRE+GB courses, multi-season calendars; winners sampled from softmax of true strength; **bookmaker odds = distorted truth** (~116% overround, favourite-longshot bias, noise); **exchange odds ≈ truth** (~101% book). Ground-truth probabilities retained for tests.
  **VC:** same seed → byte-identical output; each race has exactly one winner; mean bookmaker book 112–124%, exchange 100–103%; favourites win 28–38% of races; longshot bias measurable (bookmaker implied prob of longshots > true prob on average).
- **T2.3 Betfair BSP ingest.** Parser for `dwbfprices{ire|uk}{win|place}DDMMYYYY.csv` (documented columns: event/course/time, selection, BSP, PPWAP, morning WAP, PP max/min, win flag) + downloader (graceful offline skip) + matching to runners by (date, course, horse name).
  **VC:** fixture files ingest to expected row counts and values; name-normalisation tests (case, country suffix `(IRE)`); offline download returns actionable message, non-zero rows untouched.
- **T2.4 The Racing API connector.** Client for racecards (`/racecards`), results (`/results`), odds endpoints with HTTP basic auth, 2 req/s throttle, retry/backoff; mapper to canonical models.
  **VC:** recorded JSON fixtures parse into races/runners/odds (no network in tests); throttle test with fake clock; missing-credential error is clear and only on use.
- **T2.5 Historic CSV importer.** Column-mapped importer for rpscrape/Kaggle-style results CSVs (date, course, race, horse, trainer, jockey, draw, OR, position, odds…), with a documented mapping file.
  **VC:** sample fixture imports; bad rows reported not fatal; re-import is idempotent.

### Epic 3 — Feature engineering

- **T3.1 Point-in-time feature builder.** Per runner at race time T, computed from strictly-before-T data: career starts/wins/places (shrunk rates), last-N form (weighted finish positions & beaten lengths), days since run (+ bands), course/distance/going fit (shrunk), trainer & jockey 90-day and career strike rates (empirical-Bayes shrunk to global mean), field size, draw percentile (flat), weight/OR where present, first-timer flags.
  **VC:** **leakage test** — append future results, features at T unchanged; hand-computed mini-history matches; first-timer gets priors not NaNs; shrinkage: 1-win-from-1 trainer < raw 100%.
- **T3.2 Training dataset assembly.** Grouped per-race matrices; chronological season splits with purge gap; feature-list from config.
  **VC:** no race straddles splits; group sizes = runner counts; deterministic ordering; train max date < valid min date < test min date.

### Epic 4 — Modeling

- **T4.1 Conditional logit baseline.** Numpy/scipy MLE of softmax-linear model with L2; per-race probabilities.
  **VC:** probabilities sum to 1 per race (1e-9); on synthetic data, ability-correlated features get positive weights; test log-loss beats uniform-probability baseline.
- **T4.2 GBDT model.** LightGBM (binary objective, per-race softmax of scores; deterministic seed).
  **VC:** test log-loss ≤ conditional logit + 1%; deterministic across runs; artifact save/load parity of predictions.
- **T4.3 Benter blend.** Stage-2 MLE of `p ∝ exp(α·log f + β·log q)` on validation (f = fundamental model, q = de-vigged exchange probs); fitted α, β persisted.
  **VC:** blended test log-loss ≤ min(model-only, market-only) within tolerance; **ΔR² (McFadden vs market-only) > 0 on synthetic data** (the planted inefficiency must be found); with a deliberately useless model, β→dominates and blend ≈ market (sanity test).
- **T4.4 Evaluation & calibration report.** Log-loss, Brier, McFadden R², ΔR² vs market, reliability table (predicted vs actual by prob decile); `furlong train` emits metrics JSON + model artifact + model_runs row.
  **VC:** metrics JSON schema stable; reliability deciles monotone on synthetic test set (allowing noise); train command end-to-end test.

### Epic 5 — Value & staking

- **T5.1 De-vig methods.** Proportional, power, and Shin's method for bookmaker books; exchange decimal→prob with commission haircut on net winnings.
  **VC:** hand-computed cases; Shin: probs sum to 1, z ≥ 0, z=0 reduces to proportional, longshots shrink more than favourites vs proportional (the point of Shin).
- **T5.2 EV engine.** `EV = p·(odds−1)·(1−c) − (1−p)` per venue; filters: min_edge, min_prob (longshot exclusion per Bolton–Chapman), max_odds; best-price selection across venues; BOG flag on bookmaker prices; outputs fair odds + edge %.
  **VC:** hand-computed EV incl. commission; a runner with p below min_prob never suggested regardless of edge; best-price picks the max post-commission EV venue.
- **T5.3 Staking.** Fractional Kelly (`f = edge/(odds−1) × fraction`), per-bet cap (default 2% bank), per-day cap, floor-to-zero on negative edge; flat-stakes mode.
  **VC:** formula tests; caps bind; zero stake at ≤0 edge; total daily stakes ≤ cap.
- **T5.4 Settlement rules.** Win/lose settlement, non-runner → void (stake returned), Rule 4 deductions on wins when a qualifying NR occurred (standard deduction table), dead-heat halving.
  **VC:** table-driven tests for each rule incl. Rule 4 bands and dead heats.

### Epic 6 — Backtesting

- **T6.1 Walk-forward engine.** Season-by-season: train on past, refit blend on recent window, bet the value strategy at BSP−commission on the test season; full per-bet log.
  **VC:** fold-boundary assertion (no future leakage) built into the engine and tested; deterministic under seed; runs over synthetic multi-season world in CI time.
- **T6.2 Backtest metrics & report.** ROI, strike rate, turnover, max drawdown, longest losing run, CLV distribution, per-odds-band and per-country breakdowns; JSON + HTML report.
  **VC:** metrics recomputed independently from the bet log match report; **on synthetic data: value strategy ROI > 0 and > random-selection baseline; random backing at near-fair exchange odds ≈ −commission ± 2pp** (proves the harness doesn't hallucinate edge).

### Epic 7 — Daily pipeline

- **T7.1 `furlong daily`.** For date D: load cards + latest odds from configured source, features, model+blend, value engine, staking → suggestions persisted + emitted (terminal table, JSON, HTML) with advised price, **price floor** ("no value below X"), stake units, model prob vs market prob, and top-3 factor rationale; publish timestamp; explicit "no qualifying bets today" path.
  **VC:** end-to-end on synthetic "today": suggestions produced and persisted; every suggestion has price_floor > 1.0 and edge ≥ min_edge at advised odds; a no-racing date exits 0 with the message; JSON schema test.
- **T7.2 Non-runner rescore.** `furlong rescore --date D`: mark NRs, renormalise probabilities, re-run value engine; suggestions whose edge collapsed → status `withdrawn` with reason; report of changes.
  **VC:** test: removing the market leader changes remaining probs; a suggestion invalidated by the NR is withdrawn; settled suggestions untouched.
- **T7.3 Ops scheduling.** Documented cadence (19:45 ingest / 09:00–09:30 publish / 10:15 rescore, Europe/Dublin) with sample cron lines; `--dry-run` flag.
  **VC:** docs present in ops guide; `furlong daily --dry-run` exits 0 without writing.

### Epic 8 — Tracking & CLV

- **T8.1 Suggestion settlement + CLV.** `furlong settle --date D`: join results + BSP; P/L at advised odds and at BSP; **CLV = advised_odds / BSP** (and margin-adjusted edge retained); aggregates monthly.
  **VC:** small fixture hand-calc matches (incl. a void and a Rule 4 case); CLV > 1 iff advised beat BSP.
- **T8.2 Performance reporting.** `furlong report`: cumulative P/L, ROI, CLV trend, drawdown series, monthly table; feeds the web dashboard.
  **VC:** series consistency test (sum of monthly = cumulative); JSON schema.

### Epic 9 — Web app

- **T9.1 UI pages.** FastAPI + Jinja: **Today** (suggestions with value badges, price floors, stakes), **Races** (per-race card: model % vs de-vigged market % per runner, fair odds, best odds), **Performance** (ROI/CLV/drawdown), **About** (methodology honesty page: expected variance, losing-run table from research; responsible gambling: 18+, Irish helpline 1800 936 725, GamblingCare.ie). RG footer sitewide.
  **VC:** TestClient: all routes 200; suggestion content from DB appears; RG footer asserted on every page; empty-day renders gracefully.
- **T9.2 JSON API.** `/api/suggestions?date=`, `/api/races/{id}`, `/api/performance`.
  **VC:** schema tests; 404 semantics; date validation.

### Epic 10 — Demo, docs, delivery

- **T10.1 `furlong demo`.** One command: synthetic world (≥3 seasons) → train → backtest → today's suggestions → settled history for the dashboard; prints summary (model ΔR², backtest ROI, CLV, #suggestions today) and next steps.
  **VC:** fresh-checkout integration test: demo completes in CI time; afterwards `furlong web` serves populated pages; summary contains the four headline numbers.
- **T10.2 Documentation.** README (quickstart, commands, architecture); `docs/OPERATIONS.md` (daily cadence, real-data provisioning: The Racing API key, Smartform, Betfair BSP/delayed key, costs per research); `docs/GO-LIVE-CHECKLIST.md` (legal: tips-only scope, GRAI-licensed links only, re-check advertising commencements; data licences; Betfair £499 live key; paper-trade gate: positive CLV over ≥200 suggestions before real stakes).
  **VC:** every CLI command documented; checklist cross-references research docs; a newcomer path from clone → demo → real data is complete.
- **T10.3 Quality gate.** Full pytest suite green; adversarial code review pass (bugs, leakage, edge cases) with findings fixed; final end-to-end demo run captured in README.
  **VC:** `pytest -q` exit 0 with all tests passing; review findings addressed or explicitly waived in the PR/commit message; demo output pasted in README matches a real run.

---

## 5. Milestones

1. **M1 Data foundation** — Epics 1–2 (DB, synthetic world, real-format connectors).
2. **M2 Brain** — Epics 3–4 (features, models, blend; ΔR² > 0 on synthetic).
3. **M3 Judgment** — Epics 5–6 (value, staking, honest backtest).
4. **M4 Product** — Epics 7–9 (daily pipeline, tracking, web UI).
5. **M5 Ship** — Epic 10 (demo, docs, quality gate).

## 6. Acceptance for the whole build

- All task VCs pass; `pytest` fully green.
- `furlong demo` then `furlong web` yields a working app showing: today's suggestions with value/staking, race probability views, and a performance dashboard with CLV — from a fresh clone with zero external keys.
- Switching `FURLONG_SOURCE=racing_api` + credentials (no code changes) routes the same daily pipeline to real data.
- Documentation makes the go-live path (data, legal, execution) explicit and references the research.

## 7. Risks & guardrails (build-time)

- **Leakage** is the project-killing bug class → dedicated leakage tests (T3.1, T6.1) and point-in-time discipline everywhere.
- **Fantasy backtests** → the synthetic world's near-fair exchange must produce ≈ −commission for naive strategies (T6.2) before any positive result is believed.
- **Silent unit drift** (odds vs probs, gross vs net commission) → typed helpers in one module (`value/devig.py`), property tests.
- **Name matching across sources** (BSP ↔ cards) → normalisation utilities with tests (T2.3).
