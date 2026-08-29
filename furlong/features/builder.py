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
FIT_SHRINK_M = 6.0

WINDOW_DAYS = 90
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

FEATURE_COLUMNS = [
    "career_starts",
    "career_win_rate",
    "career_place_rate",
    "days_since_run",
    "first_timer",
    "won_last",
    "last_finish_norm",
    "recent_form",
    "going_fit",
    "dist_fit",
    "trainer_sr_career",
    "trainer_sr_window",
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
    """Per-entity expanding + windowed sums, read strictly before each row's date."""

    def __init__(self, df: pd.DataFrame, entity_col: str, completed: np.ndarray,
                 value_cols: dict[str, np.ndarray]):
        self.n = len(df)
        self.entity = df[entity_col].fillna(-1).to_numpy()
        self.dates = _date_ints(df["date"])
        self.completed = completed
        self.values = value_cols
        self.results: dict[str, np.ndarray] = {}
        self._compute()

    def _compute(self) -> None:
        order = np.lexsort((self.dates, self.entity))
        out: dict[str, np.ndarray] = {}
        for key in self.values:
            out[f"{key}_before"] = np.zeros(self.n)
            out[f"{key}_window"] = np.zeros(self.n)
        out["n_before"] = np.zeros(self.n)
        out["n_window"] = np.zeros(self.n)

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
            lo = np.searchsorted(dates, dates - WINDOW_DAYS, side="left")
            out["n_before"][idx] = cum_n[hi]
            out["n_window"][idx] = cum_n[hi] - cum_n[lo]
            for key, values in self.values.items():
                masked = np.where(self.completed[idx], np.nan_to_num(values[idx]), 0.0)
                cum_v = np.concatenate(([0.0], np.cumsum(masked)))
                out[f"{key}_before"][idx] = cum_v[hi]
                out[f"{key}_window"][idx] = cum_v[hi] - cum_v[lo]
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
    horse_values = {"win": win, "placed": placed, "perf": perf}
    for b in range(len(GOING_ORDER)):
        indicator = (going_bucket == b).astype(float)
        horse_values[f"going{b}_perf"] = perf * indicator
        horse_values[f"going{b}_n"] = indicator
    for b in range(N_DIST_BUCKETS):
        indicator = (dist_bucket == b).astype(float)
        horse_values[f"dist{b}_perf"] = perf * indicator
        horse_values[f"dist{b}_n"] = indicator
    horse_stats = _EntityStats(df, "horse_id", completed, horse_values).results

    trainer_stats = _EntityStats(df, "trainer_id", completed, {"win": win}).results
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
    trainer_sr_window = (trainer_stats["win_window"] + WINDOW_SHRINK_M * base_rate) / (
        trainer_stats["n_window"] + WINDOW_SHRINK_M
    )
    jockey_sr_career = (jockey_stats["win_before"] + JOCKEY_SHRINK_M * base_rate) / (
        jockey_stats["n_before"] + JOCKEY_SHRINK_M
    )
    jockey_sr_window = (jockey_stats["win_window"] + WINDOW_SHRINK_M * base_rate) / (
        jockey_stats["n_window"] + WINDOW_SHRINK_M
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

    features = pd.DataFrame({
        "career_starts": np.log1p(career_starts),
        "career_win_rate": career_win_rate,
        "career_place_rate": career_place_rate,
        "days_since_run": days_since_filled,
        "first_timer": first_timer,
        "won_last": last["won_last"].to_numpy(),
        "last_finish_norm": last["last_finish_norm"].fillna(0.5).to_numpy(),
        "recent_form": last["recent_form"].fillna(0.5).to_numpy(),
        "going_fit": going_fit,
        "dist_fit": dist_fit,
        "trainer_sr_career": trainer_sr_career,
        "trainer_sr_window": trainer_sr_window,
        "trainer_runs_window": np.log1p(trainer_stats["n_window"]),
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
