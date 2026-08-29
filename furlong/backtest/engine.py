"""Walk-forward backtest at Betfair SP minus commission.

The only backtest worth running is one that could not have known the
future. Each fold trains on everything before a cut-off, fits the blend on
a validation window that also predates the cut-off, and bets the fold's
races at BSP minus commission. Fold boundaries are asserted at runtime, not
merely intended: ``_assert_no_leakage`` raises if any training or
validation race is dated on or after the first race of the test fold.

Prices are BSP because that is the honest benchmark: it carries no
bookmaker margin, it is what a bettor could actually have taken at the off,
and beating it is the definition of edge. Backtesting against industry SP
(margin included) or against the morning price you would not have got is
how paper edges are manufactured.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from furlong.config import Settings
from furlong.db import init_db
from furlong.features.builder import FEATURE_COLUMNS
from furlong.features.dataset import Dataset, build_dataset
from furlong.modeling.train import attach_market, train_on_frames
from furlong.value.devig import expected_value
from furlong.value.staking import kelly_fraction

# Minimum races before the first fold may bet. Benter put the development
# minimum at 500-1000 races *with full past-performance depth for every
# runner*; in practice the binding constraint is per-horse form history, so
# a model trained on fewer than roughly a season of racing has no business
# advising bets. Measured on the synthetic world, delta R-squared is
# reliably negative below ~800 training races and turns positive above it.
MIN_TRAIN_RACES = 1500
VALID_FRACTION = 0.2


class LeakageError(AssertionError):
    """Raised when a fold's training data would include the future."""


def _assert_no_leakage(train: pd.DataFrame, valid: pd.DataFrame,
                       test: pd.DataFrame) -> None:
    test_start = pd.to_datetime(test["date"]).min()
    for name, frame in (("train", train), ("valid", valid)):
        if frame.empty:
            continue
        if pd.to_datetime(frame["date"]).max() >= test_start:
            raise LeakageError(
                f"{name} fold contains races on or after the test fold start "
                f"({test_start.date()})"
            )
    overlap = set(train["race_id"]) & set(test["race_id"])
    if overlap:
        raise LeakageError(f"{len(overlap)} race(s) appear in both train and test")


@dataclass
class BacktestResult:
    bets: pd.DataFrame
    all_runners: pd.DataFrame
    folds: list = field(default_factory=list)
    settings_snapshot: dict = field(default_factory=dict)

    @property
    def n_bets(self) -> int:
        return len(self.bets)

    def roi(self) -> float:
        if self.bets.empty:
            return 0.0
        return float(self.bets["pl"].sum() / self.bets["stake"].sum())

    def naive_roi(self) -> float:
        """Return from backing every runner at BSP: the do-nothing baseline."""
        if self.all_runners.empty:
            return 0.0
        return float(self.all_runners["naive_pl"].mean())

    def summary(self) -> str:
        if self.bets.empty:
            return "Backtest produced no qualifying bets."
        won = int(self.bets["won"].sum())
        return (
            f"Backtest over {len(self.folds)} fold(s): {self.n_bets:,} bets, "
            f"{won:,} winners ({won / self.n_bets:.1%})\n"
            f"  ROI {self.roi():+.2%} (flat-stake {self.bets['pl_flat'].mean():+.2%}) "
            f"vs naive back-everything {self.naive_roi():+.2%}\n"
            f"  Mean CLV {self.bets['clv'].mean():.3f} · "
            f"avg advised odds {self.bets['odds'].mean():.2f}"
        )


def run_backtest(settings: Settings, model_kind: str = "gbm",
                 n_folds: int = 3) -> BacktestResult:
    """Walk forward through the data in ``n_folds`` chronological folds."""
    conn = init_db(settings.database_path)
    frame = attach_market(conn, build_dataset(conn).frame, prefer="bsp")
    conn.close()

    # Fold boundaries are dates, never race indices: a single race day must
    # never be split across train and test, or the model would train on races
    # run the same afternoon as the ones it is betting.
    race_order = (
        frame[["race_id", "date"]].drop_duplicates().sort_values("date")
        .reset_index(drop=True)
    )
    dates = np.array(sorted(frame["date"].unique()))
    races_by_date = race_order.groupby("date").size().reindex(dates, fill_value=0)
    cumulative_races = races_by_date.cumsum().to_numpy()
    n_races = len(race_order)

    first_test_idx = int(np.searchsorted(cumulative_races, MIN_TRAIN_RACES, side="left")) + 1
    if first_test_idx >= len(dates) - 1:
        raise ValueError(
            f"not enough races to backtest ({n_races}); need more than {MIN_TRAIN_RACES}"
        )
    available = len(dates) - first_test_idx
    n_folds = max(1, min(n_folds, available // 10))
    date_edges = np.linspace(first_test_idx, len(dates), n_folds + 1).astype(int)

    bets: list[dict] = []
    naive_rows: list[dict] = []
    folds: list[dict] = []

    for i in range(n_folds):
        test_start_idx, test_end_idx = date_edges[i], date_edges[i + 1]
        if test_end_idx <= test_start_idx:
            continue
        history_dates = set(dates[:test_start_idx])
        test_dates = set(dates[test_start_idx:test_end_idx])

        history = frame[frame["date"].isin(history_dates)]
        test = frame[frame["date"].isin(test_dates)]
        if test.empty or history.empty:
            continue

        # The validation window (for fitting the blend) is the tail of history,
        # also split on a date boundary.
        hist_dates = sorted(history_dates)
        split_idx = max(1, int(len(hist_dates) * (1 - VALID_FRACTION)))
        train = history[history["date"].isin(set(hist_dates[:split_idx]))]
        valid = history[history["date"].isin(set(hist_dates[split_idx:]))]
        if valid.empty:
            valid = train.tail(0)
        train_ids = set(train["race_id"])
        valid_ids = set(valid["race_id"])
        test_races = test["race_id"].drop_duplicates()

        _assert_no_leakage(train, valid, test)

        trained = train_on_frames(train, valid, test, kind=model_kind)
        groups = _group_sizes(test)
        model_probs, blend_probs = trained.predict(
            test[FEATURE_COLUMNS].to_numpy(dtype=float), groups,
            test["market_prob"].to_numpy(dtype=float),
        )

        fold_bets, fold_naive = _simulate_fold(test, model_probs, blend_probs, settings)
        bets.extend(fold_bets)
        naive_rows.extend(fold_naive)
        folds.append({
            "fold": i + 1,
            "train_races": int(len(train_ids)),
            "valid_races": int(len(valid_ids)),
            "test_races": int(len(test_races)),
            "test_start": str(test["date"].min()),
            "test_end": str(test["date"].max()),
            "delta_r2": float(trained.metrics.delta_r2),
            "blend_alpha": float(trained.blend.alpha),
            "blend_beta": float(trained.blend.beta),
            "bets": len(fold_bets),
        })

    return BacktestResult(
        bets=pd.DataFrame(bets),
        all_runners=pd.DataFrame(naive_rows),
        folds=folds,
        settings_snapshot={
            "model": model_kind,
            "commission": settings.exchange_commission,
            "min_edge": settings.min_edge,
            "min_prob": settings.min_prob,
            "max_odds": settings.max_odds,
            "kelly_fraction": settings.kelly_fraction,
        },
    )


def _group_sizes(frame: pd.DataFrame) -> np.ndarray:
    _, idx, counts = np.unique(frame["race_id"].to_numpy(), return_index=True,
                               return_counts=True)
    return counts[np.argsort(idx)]


def _simulate_fold(test: pd.DataFrame, model_probs: np.ndarray, blend_probs: np.ndarray,
                   settings: Settings) -> tuple[list[dict], list[dict]]:
    """Place the value bets for one fold at BSP minus commission."""
    commission = settings.exchange_commission
    odds = test["market_odds"].to_numpy(dtype=float)
    won = (test["win_flag"] == 1).to_numpy(dtype=float)

    bets: list[dict] = []
    naive: list[dict] = []
    # A runner with no quoted price carries an inferred probability and a
    # placeholder "price" that nobody could ever have taken. Betting or
    # scoring those would manufacture profit out of missing data.
    priced = (
        test["market_priced"].to_numpy(dtype=bool) if "market_priced" in test
        else np.ones(len(test), dtype=bool)
    )

    for i, (_, row) in enumerate(test.iterrows()):
        if not priced[i]:
            continue
        price = float(odds[i])
        win = bool(won[i])
        naive_pl = (price - 1.0) * (1 - commission) if win else -1.0
        naive.append({
            "runner_id": int(row["runner_id"]), "date": row["date"],
            "odds": price, "won": win, "naive_pl": naive_pl,
        })

        prob = float(blend_probs[i])
        if prob < settings.min_prob or price > settings.max_odds:
            continue
        ev = expected_value(prob, price, commission)
        if ev < settings.min_edge:
            continue

        stake = min(
            kelly_fraction(prob, price, commission) * settings.kelly_fraction,
            settings.max_stake_pct,
        ) / 0.01  # in units of 1% of bankroll
        if stake <= 0:
            continue

        pl_per_unit = (price - 1.0) * (1 - commission) if win else -1.0
        bets.append({
            "runner_id": int(row["runner_id"]),
            "race_id": int(row["race_id"]),
            "date": row["date"],
            "country": row["country"],
            "odds": price,
            "model_prob": float(model_probs[i]),
            "blend_prob": prob,
            "market_prob": float(row["market_prob"]),
            "ev": ev,
            "stake": stake,
            "won": win,
            "pl": stake * pl_per_unit,
            "pl_flat": pl_per_unit,
            # In a BSP backtest the advised price *is* the closing price, so
            # CLV is 1.0 by construction. Live suggestions taken at a morning
            # price produce a genuine CLV; see furlong.value.settlement.
            "clv": 1.0,
        })
    return bets, naive
