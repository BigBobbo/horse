"""Point-in-time feature computation.

Every feature for a runner in a race dated D is computed from runs dated
STRICTLY BEFORE D (same-day earlier races are excluded too). This is
enforced structurally: per-entity cumulative statistics are read via a
``searchsorted`` on race dates with ``side='left'``, so a row can never see
itself, same-day peers, or the future. The leakage test in
``tests/test_features.py`` verifies that appending future results leaves
past feature rows unchanged.

The market (odds) is deliberately NOT a feature here — market information
enters at the second-stage blend (see ``furlong.modeling.blend``), per the
Benter two-stage design.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Shrinkage constants (empirical-Bayes: rate = (successes + M*prior) / (n + M))
HORSE_SHRINK_M = 8.0
TRAINER_SHRINK_M = 20.0
JOCKEY_SHRINK_M = 20.0
WINDOW_SHRINK_M = 10.0
SHORT_WINDOW_SHRINK_M = 6.0
FIT_SHRINK_M = 6.0
GOING_SLOPE_RIDGE = 12.0

WINDOW_DAYS = 90
SHORT_WINDOW_DAYS = 30   # trainer form cycles turn faster than a quarter
RECENT_FORM_RUNS = 5
RECENT_FORM_DECAY = 0.7

# Fixed priors (constants, so features are independent of the batch they are
# computed in — a data-derived prior would leak information across time).
BASE_WIN_RATE = 0.10    # ~1 / average field size in UK+IRE racing
BASE_PLACE_RATE = 0.30

GOING_SCALE = {"heavy": -2.0, "soft": -1.0, "good": 0.0, "good_to_firm": 1.0, "firm": 2.0}
GOING_ORDER = ["heavy", "soft", "good", "good_to_firm", "firm"]

DIST_EDGES = [0.0, 1200.0, 1600.0, 2800.0, np.inf]  # sprint / mile / middle / staying
N_DIST_BUCKETS = len(DIST_EDGES) - 1

# Elo-style ability rating. Benter lists "adjustment for the strength of
# opposition" as essential: a win against good horses means far more than a
# win in a weak race, and raw strike rates cannot see the difference.
ELO_K = 24.0
ELO_SCALE = 90.0        # rating points per unit of latent strength
ELO_START = 0.0
ELO_TRAINER_K = 3.0     # trainers/jockeys move much more slowly than horses

FEATURE_COLUMNS = [
    "elo",
    "elo_vs_field",
    "elo_rank_pct",
    "trainer_elo",
    "jockey_elo",
    "career_starts",
    "career_win_rate",
    "career_place_rate",
    "days_since_run",
    "first_timer",
    "won_last",
    "last_finish_norm",
    "recent_form",
    "going_fit",
    "going_slope",
    "going_slope_today",
    "dist_fit",
    "trainer_sr_career",
    "trainer_sr_window",
    "trainer_sr_short",
    "trainer_form_delta",
    "trainer_runs_window",
    "jockey_sr_career",
    "jockey_sr_window",
    "draw_pct",
    "field_size_norm",
    "race_class_norm",
    "is_flat",
    "or_within_race",
]


def _perf(finish_pos: np.ndarray, field_size: np.ndarray) -> np.ndarray:
    """Normalised performance in [0, 1]: winner 1.0, last 0.0."""
    denom = np.maximum(field_size - 1, 1)
    return 1.0 - (finish_pos - 1) / denom


def _date_ints(series: pd.Series) -> np.ndarray:
    return pd.to_datetime(series).values.astype("datetime64[D]").astype(np.int64)


class _EntityStats:
    """Per-entity expanding + windowed sums, read strictly before each row's date.

    ``windows`` are lookback lengths in days; each produces ``<key>_w<days>``
    sums alongside the expanding ``<key>_before`` totals.
    """

    def __init__(self, df: pd.DataFrame, entity_col: str, completed: np.ndarray,
                 value_cols: dict[str, np.ndarray],
                 windows: tuple[int, ...] = (WINDOW_DAYS,)):
        self.n = len(df)
        self.entity = df[entity_col].fillna(-1).to_numpy()
        self.dates = _date_ints(df["date"])
        self.completed = completed
        self.values = value_cols
        self.windows = windows
        self.results: dict[str, np.ndarray] = {}
        self._compute()

    def _compute(self) -> None:
        order = np.lexsort((self.dates, self.entity))
        out: dict[str, np.ndarray] = {}
        for key in self.values:
            out[f"{key}_before"] = np.zeros(self.n)
            for w in self.windows:
                out[f"{key}_w{w}"] = np.zeros(self.n)
        out["n_before"] = np.zeros(self.n)
        for w in self.windows:
            out[f"n_w{w}"] = np.zeros(self.n)

        entity_sorted = self.entity[order]
        boundaries = np.flatnonzero(np.diff(entity_sorted)) + 1
        group_starts = np.concatenate(([0], boundaries))
        group_ends = np.concatenate((boundaries, [len(order)]))

        for gs, ge in zip(group_starts, group_ends):
            idx = order[gs:ge]
            if self.entity[idx[0]] == -1:
                continue
            dates = self.dates[idx]
            comp = self.completed[idx].astype(float)
            cum_n = np.concatenate(([0.0], np.cumsum(comp)))
            hi = np.searchsorted(dates, dates, side="left")
            los = {w: np.searchsorted(dates, dates - w, side="left") for w in self.windows}
            out["n_before"][idx] = cum_n[hi]
            for w, lo in los.items():
                out[f"n_w{w}"][idx] = cum_n[hi] - cum_n[lo]
            for key, values in self.values.items():
                masked = np.where(self.completed[idx], np.nan_to_num(values[idx]), 0.0)
                cum_v = np.concatenate(([0.0], np.cumsum(masked)))
                out[f"{key}_before"][idx] = cum_v[hi]
                for w, lo in los.items():
                    out[f"{key}_w{w}"][idx] = cum_v[hi] - cum_v[lo]
        self.results = out


def _last_run_features(df: pd.DataFrame, completed: np.ndarray) -> pd.DataFrame:
    """Per horse: previous completed run's date, finish, and decayed recent form.

    Same-day safety: a horse running twice on one day is rare and the
    ``last run`` here still refers to a strictly-earlier date because
    history rows are looked up by date via searchsorted below.
    """
    n = len(df)
    horse = df["horse_id"].to_numpy()
    dates = _date_ints(df["date"])
    perf = np.where(
        completed,
        _perf(df["finish_pos"].fillna(0).to_numpy(dtype=float),
              df["field_size"].fillna(2).to_numpy(dtype=float)),
        np.nan,
    )
    win = np.where(completed, (df["win_flag"].fillna(0) == 1).to_numpy(), False)

    last_date = np.full(n, np.nan)
    last_perf = np.full(n, np.nan)
    last_won = np.zeros(n)
    recent_form = np.full(n, np.nan)

    order = np.lexsort((dates, horse))
    horse_sorted = horse[order]
    boundaries = np.flatnonzero(np.diff(horse_sorted)) + 1
    group_starts = np.concatenate(([0], boundaries))
    group_ends = np.concatenate((boundaries, [len(order)]))

    for gs, ge in zip(group_starts, group_ends):
        idx = order[gs:ge]
        g_dates = dates[idx]
        g_perf = perf[idx]
        g_win = win[idx]
        completed_pos = np.flatnonzero(~np.isnan(g_perf))
        if len(completed_pos) == 0:
            continue
        comp_dates = g_dates[completed_pos]
        for j, row in enumerate(idx):
            k = np.searchsorted(comp_dates, g_dates[j], side="left")
            if k == 0:
                continue
            prior = completed_pos[:k]
            last = prior[-1]
            last_date[row] = g_dates[last]
            last_perf[row] = g_perf[last]
            last_won[row] = float(g_win[last])
            recent = prior[-RECENT_FORM_RUNS:]
            weights = RECENT_FORM_DECAY ** np.arange(len(recent) - 1, -1, -1)
            recent_form[row] = float(np.average(g_perf[recent], weights=weights))

    days_since = dates - last_date
    return pd.DataFrame({
        "days_since_run": days_since,
        "last_finish_norm": last_perf,
        "won_last": last_won,
        "recent_form": recent_form,
    }, index=df.index)


def _elo_features(df: pd.DataFrame, completed: np.ndarray) -> pd.DataFrame:
    """Opposition-adjusted ability ratings, updated strictly after each race.

    Multi-runner Elo: each runner's expected win share is the softmax of the
    field's current ratings; after the race every rating moves by
    ``K * (actual - expected)``. Races are processed in start-time order and
    a rating is read *before* its own race is applied, so the feature is
    point-in-time safe by construction.
    """
    n = len(df)
    horse = df["horse_id"].to_numpy()
    trainer = df["trainer_id"].fillna(-1).to_numpy()
    jockey = df["jockey_id"].fillna(-1).to_numpy()
    won = (df["win_flag"].fillna(0) == 1).to_numpy(dtype=float)

    elo = np.full(n, np.nan)
    elo_vs_field = np.zeros(n)
    elo_rank_pct = np.full(n, 0.5)
    trainer_elo = np.zeros(n)
    jockey_elo = np.zeros(n)

    horse_r: dict = {}
    trainer_r: dict = {}
    jockey_r: dict = {}

    order = np.lexsort((df["race_id"].to_numpy(), _date_ints(df["date"])))
    race_ids = df["race_id"].to_numpy()
    start = 0
    ordered_races = race_ids[order]
    boundaries = np.flatnonzero(np.diff(ordered_races)) + 1
    for gs, ge in zip(np.concatenate(([0], boundaries)),
                      np.concatenate((boundaries, [len(order)]))):
        idx = order[gs:ge]
        ratings = np.array([horse_r.get(horse[i], ELO_START) for i in idx])
        t_ratings = np.array([trainer_r.get(trainer[i], ELO_START) for i in idx])
        j_ratings = np.array([jockey_r.get(jockey[i], ELO_START) for i in idx])

        elo[idx] = ratings
        elo_vs_field[idx] = ratings - ratings.mean()
        if len(idx) > 1:
            ranks = ratings.argsort().argsort()
            elo_rank_pct[idx] = ranks / (len(idx) - 1)
        trainer_elo[idx] = t_ratings
        jockey_elo[idx] = j_ratings

        if not completed[idx].all():
            continue  # declared-only race: nothing to learn from yet
        expected = _softmax_np(ratings / ELO_SCALE)
        actual = won[idx]
        if actual.sum() != 1:
            continue  # dead heat or missing winner: skip the update
        delta = ELO_K * (actual - expected)
        for k, i in enumerate(idx):
            horse_r[horse[i]] = ratings[k] + delta[k]
            if trainer[i] != -1:
                trainer_r[trainer[i]] = t_ratings[k] + ELO_TRAINER_K * (actual[k] - expected[k])
            if jockey[i] != -1:
                jockey_r[jockey[i]] = j_ratings[k] + ELO_TRAINER_K * (actual[k] - expected[k])

    return pd.DataFrame({
        "elo": elo / ELO_SCALE,
        "elo_vs_field": elo_vs_field / ELO_SCALE,
        "elo_rank_pct": elo_rank_pct,
        "trainer_elo": trainer_elo / ELO_SCALE,
        "jockey_elo": jockey_elo / ELO_SCALE,
    }, index=df.index)


def _softmax_np(x: np.ndarray) -> np.ndarray:
    shifted = x - x.max()
    exp = np.exp(shifted)
    return exp / exp.sum()


def compute_features(runs: pd.DataFrame) -> pd.DataFrame:
    """Compute point-in-time features for every row of ``runs``.

    ``runs`` must contain the columns produced by ``repo.load_runs``. Rows
    may include future/declared runners (finish_pos NaN); they receive
    features from strictly-earlier completed rows and contribute nothing
    to anyone else's history.
    """
    df = runs.reset_index(drop=True).copy()
    n = len(df)
    completed = (
        df["finish_pos"].notna() & (df["status"] == "ran") & df["field_size"].notna()
    ).to_numpy()

    finish = df["finish_pos"].fillna(0).to_numpy(dtype=float)
    field = df["field_size"].fillna(2).to_numpy(dtype=float)
    perf = _perf(finish, field)
    win = (df["win_flag"].fillna(0) == 1).to_numpy(dtype=float)
    placed = (df["finish_pos"].fillna(99) <= 3).to_numpy(dtype=float)

    going_scale = df["going"].map(GOING_SCALE).fillna(0.0).to_numpy()
    going_bucket = df["going"].map({g: i for i, g in enumerate(GOING_ORDER)}).fillna(2).to_numpy(int)
    dist_bucket = np.digitize(df["distance_m"].fillna(1600).to_numpy(), DIST_EDGES[1:-1])

    # --- horse expanding stats (career + per-going + per-distance buckets)
    horse_values = {
        "win": win,
        "placed": placed,
        "perf": perf,
        # sums for a per-horse regression of performance on the going scale
        "going_x": going_scale,
        "going_x2": going_scale ** 2,
        "going_xy": going_scale * perf,
    }
    for b in range(len(GOING_ORDER)):
        indicator = (going_bucket == b).astype(float)
        horse_values[f"going{b}_perf"] = perf * indicator
        horse_values[f"going{b}_n"] = indicator
    for b in range(N_DIST_BUCKETS):
        indicator = (dist_bucket == b).astype(float)
        horse_values[f"dist{b}_perf"] = perf * indicator
        horse_values[f"dist{b}_n"] = indicator
    horse_stats = _EntityStats(df, "horse_id", completed, horse_values).results

    trainer_stats = _EntityStats(
        df, "trainer_id", completed, {"win": win},
        windows=(WINDOW_DAYS, SHORT_WINDOW_DAYS),
    ).results
    jockey_stats = _EntityStats(df, "jockey_id", completed, {"win": win}).results

    base_rate = BASE_WIN_RATE

    career_starts = horse_stats["n_before"]
    career_win_rate = (horse_stats["win_before"] + HORSE_SHRINK_M * base_rate) / (
        career_starts + HORSE_SHRINK_M
    )
    place_base = BASE_PLACE_RATE
    career_place_rate = (horse_stats["placed_before"] + HORSE_SHRINK_M * place_base) / (
        career_starts + HORSE_SHRINK_M
    )
    overall_perf = np.where(
        career_starts > 0, horse_stats["perf_before"] / np.maximum(career_starts, 1), 0.5
    )

    # going fit: shrunk mean perf on goings within 1 step of today's, minus overall
    going_sum = np.zeros(n)
    going_n = np.zeros(n)
    for b in range(len(GOING_ORDER)):
        weight = (np.abs(going_scale - GOING_SCALE[GOING_ORDER[b]]) <= 1.0).astype(float)
        going_sum += weight * horse_stats[f"going{b}_perf_before"]
        going_n += weight * horse_stats[f"going{b}_n_before"]
    going_fit = (going_sum + FIT_SHRINK_M * overall_perf) / (going_n + FIT_SHRINK_M) - overall_perf

    # Ridge-shrunk least-squares slope of past performance on the going scale:
    # a direct estimate of "does this horse improve on softer/firmer ground?".
    # Neighbourhood averages (going_fit) cannot express a monotone preference.
    n_prior = career_starts
    sum_x = horse_stats["going_x_before"]
    sum_xx = horse_stats["going_x2_before"]
    sum_y = horse_stats["perf_before"]
    sum_xy = horse_stats["going_xy_before"]
    denom = n_prior * sum_xx - sum_x ** 2 + GOING_SLOPE_RIDGE
    going_slope = np.where(n_prior >= 2, (n_prior * sum_xy - sum_x * sum_y) / denom, 0.0)
    going_slope_today = going_slope * going_scale

    dist_sum = np.zeros(n)
    dist_n = np.zeros(n)
    for b in range(N_DIST_BUCKETS):
        weight = (dist_bucket == b).astype(float)
        dist_sum += weight * horse_stats[f"dist{b}_perf_before"]
        dist_n += weight * horse_stats[f"dist{b}_n_before"]
    dist_fit = (dist_sum + FIT_SHRINK_M * overall_perf) / (dist_n + FIT_SHRINK_M) - overall_perf

    trainer_sr_career = (trainer_stats["win_before"] + TRAINER_SHRINK_M * base_rate) / (
        trainer_stats["n_before"] + TRAINER_SHRINK_M
    )
    trainer_sr_window = (trainer_stats[f"win_w{WINDOW_DAYS}"] + WINDOW_SHRINK_M * base_rate) / (
        trainer_stats[f"n_w{WINDOW_DAYS}"] + WINDOW_SHRINK_M
    )
    trainer_sr_short = (
        trainer_stats[f"win_w{SHORT_WINDOW_DAYS}"] + SHORT_WINDOW_SHRINK_M * base_rate
    ) / (trainer_stats[f"n_w{SHORT_WINDOW_DAYS}"] + SHORT_WINDOW_SHRINK_M)
    # Hot/cold signal: the short window relative to the yard's own long-run level.
    trainer_form_delta = trainer_sr_short - trainer_sr_career
    jockey_sr_career = (jockey_stats["win_before"] + JOCKEY_SHRINK_M * base_rate) / (
        jockey_stats["n_before"] + JOCKEY_SHRINK_M
    )
    jockey_sr_window = (jockey_stats[f"win_w{WINDOW_DAYS}"] + WINDOW_SHRINK_M * base_rate) / (
        jockey_stats[f"n_w{WINDOW_DAYS}"] + WINDOW_SHRINK_M
    )

    last = _last_run_features(df, completed)
    days_since = last["days_since_run"].to_numpy()
    first_timer = np.isnan(days_since).astype(float)
    days_since_filled = np.log1p(np.minimum(np.nan_to_num(days_since, nan=365.0), 400.0))

    is_flat = (df["race_type"] == "flat").to_numpy(dtype=float)
    draw = df["draw"].to_numpy(dtype=float)
    draw_pct = np.where(
        is_flat.astype(bool) & ~np.isnan(draw),
        (draw - 1) / np.maximum(field - 1, 1),
        0.5,
    )

    official_rating = df["official_rating"].to_numpy(dtype=float)
    or_series = pd.Series(official_rating, index=df.index)
    race_mean_or = or_series.groupby(df["race_id"]).transform("mean")
    or_within_race = (or_series - race_mean_or).fillna(0.0).to_numpy()

    elo = _elo_features(df, completed)

    features = pd.DataFrame({
        "elo": elo["elo"].fillna(0.0).to_numpy(),
        "elo_vs_field": elo["elo_vs_field"].to_numpy(),
        "elo_rank_pct": elo["elo_rank_pct"].to_numpy(),
        "trainer_elo": elo["trainer_elo"].to_numpy(),
        "jockey_elo": elo["jockey_elo"].to_numpy(),
        "career_starts": np.log1p(career_starts),
        "career_win_rate": career_win_rate,
        "career_place_rate": career_place_rate,
        "days_since_run": days_since_filled,
        "first_timer": first_timer,
        "won_last": last["won_last"].to_numpy(),
        "last_finish_norm": last["last_finish_norm"].fillna(0.5).to_numpy(),
        "recent_form": last["recent_form"].fillna(0.5).to_numpy(),
        "going_fit": going_fit,
        "going_slope": going_slope,
        "going_slope_today": going_slope_today,
        "dist_fit": dist_fit,
        "trainer_sr_career": trainer_sr_career,
        "trainer_sr_window": trainer_sr_window,
        "trainer_sr_short": trainer_sr_short,
        "trainer_form_delta": trainer_form_delta,
        "trainer_runs_window": np.log1p(trainer_stats[f"n_w{WINDOW_DAYS}"]),
        "jockey_sr_career": jockey_sr_career,
        "jockey_sr_window": jockey_sr_window,
        "draw_pct": draw_pct,
        "field_size_norm": field / 16.0,
        "race_class_norm": df["race_class"].fillna(4).to_numpy(dtype=float) / 7.0,
        "is_flat": is_flat,
        "or_within_race": or_within_race / 10.0,
    }, index=df.index)

    id_cols = df[["runner_id", "race_id", "horse_id", "date", "start_time_utc",
                  "win_flag", "finish_pos", "status", "country"]].copy()
    return pd.concat([id_cols, features], axis=1)
