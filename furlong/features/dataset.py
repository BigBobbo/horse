"""Training dataset assembly: grouped matrices with chronological splits."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import numpy as np
import pandas as pd

from furlong import repo
from furlong.features.builder import FEATURE_COLUMNS, compute_features

PURGE_DAYS = 10  # embargo gap between chronological splits


@dataclass
class Dataset:
    """Feature rows for completed races, grouped per race, in time order."""

    frame: pd.DataFrame  # id columns + FEATURE_COLUMNS + win_flag

    @property
    def X(self) -> np.ndarray:
        return self.frame[FEATURE_COLUMNS].to_numpy(dtype=float)

    @property
    def y(self) -> np.ndarray:
        return (self.frame["win_flag"].fillna(0) == 1).to_numpy(dtype=float)

    @property
    def race_ids(self) -> np.ndarray:
        return self.frame["race_id"].to_numpy()

    def group_sizes(self) -> np.ndarray:
        _, idx, counts = np.unique(self.race_ids, return_index=True, return_counts=True)
        return counts[np.argsort(idx)]  # preserve chronological race order


def build_dataset(conn: sqlite3.Connection, where: str = "", params: tuple = ()) -> Dataset:
    """Features for all completed runs (races with results, runners that ran)."""
    runs = repo.load_runs(conn, where=where, params=params)
    features = compute_features(runs)
    completed = (
        (features["status"] == "ran")
        & features["finish_pos"].notna()
        & features["win_flag"].notna()
    )
    frame = features[completed].copy()

    # drop degenerate races (walkovers, missing winners)
    race_ok = frame.groupby("race_id")["win_flag"].agg(["sum", "count"])
    good_races = race_ok[(race_ok["sum"] == 1) & (race_ok["count"] >= 2)].index
    frame = frame[frame["race_id"].isin(good_races)]
    frame = frame.sort_values(["start_time_utc", "race_id", "runner_id"]).reset_index(drop=True)
    return Dataset(frame=frame)


@dataclass
class Splits:
    train: pd.Index
    valid: pd.Index
    test: pd.Index


def chronological_splits(dataset: Dataset, train_frac: float = 0.6,
                         valid_frac: float = 0.2, purge_days: int = PURGE_DAYS) -> Splits:
    """Split whole races chronologically with a purge gap between segments."""
    frame = dataset.frame
    race_dates = frame.groupby("race_id")["date"].first().sort_values()
    dates = pd.to_datetime(race_dates.values)
    n_races = len(race_dates)
    if n_races < 10:
        raise ValueError("not enough races to split")

    train_end = dates[int(n_races * train_frac) - 1]
    valid_end = dates[int(n_races * (train_frac + valid_frac)) - 1]
    gap = pd.Timedelta(days=purge_days)

    race_date_map = pd.to_datetime(frame.groupby("race_id")["date"].first())
    train_races = race_date_map[race_date_map <= train_end].index
    valid_races = race_date_map[
        (race_date_map > train_end + gap) & (race_date_map <= valid_end)
    ].index
    test_races = race_date_map[race_date_map > valid_end + gap].index

    return Splits(
        train=frame.index[frame["race_id"].isin(train_races)],
        valid=frame.index[frame["race_id"].isin(valid_races)],
        test=frame.index[frame["race_id"].isin(test_races)],
    )
