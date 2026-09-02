"""Training orchestration: fit a model, fit the blend, evaluate, persist."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from furlong.config import Settings
from furlong.db import init_db
from furlong.features.builder import FEATURE_COLUMNS
from furlong.features.dataset import Dataset, build_dataset, chronological_splits
from furlong.modeling.blend import (
    BlendParams, blend_probabilities, fit_blend, model_adds_information)
from furlong.modeling.conditional_logit import ConditionalLogit
from furlong.modeling.evaluate import ModelMetrics, evaluate
from furlong.modeling.gbm import GbmModel
from furlong.modeling.market import market_probabilities


@dataclass
class TrainedModel:
    """A fitted model plus the blend weights that pair it with the market."""

    kind: str
    model: object
    blend: BlendParams
    metrics: ModelMetrics
    artifact_path: str | None = None
    # Likelihood-ratio test of alpha = 0 on the blend window: the statistic
    # and its p-value. These decide whether the system may advise anything
    # at all; see adds_information().
    blend_lr_statistic: float = 0.0
    blend_lr_p: float = 1.0

    def adds_information(self, max_p: float = 0.05) -> bool:
        """Whether the model contributed anything the market did not have.

        A blend can differ from the market while knowing nothing it does not.
        With alpha at zero and beta below one the blend is a pure flattening
        of the market's own prices: every longshot's probability rises,
        thousands of them clear the edge filter, and the engine advises a
        large book of bets whose only thesis is that the market's shape is
        wrong. Betfair SP is margin-free and settles at about a 0.2%
        overround, so that thesis is close to betting on nothing at all.
        Measured on real racing this was not a hypothetical: one backtest
        fold fitted alpha to exactly zero and still advised 9,020 bets.

        The test is therefore against a market-only fit with beta free, so
        that any reshaping of the market is credited to the market and only
        genuine model information can pass.
        """
        return self.blend_lr_p < max_p

    def predict(self, X: np.ndarray, group_sizes: np.ndarray,
                market_probs: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Return (model probabilities, blended probabilities)."""
        model_probs = self.model.predict_proba(X, group_sizes)
        blended = blend_probabilities(model_probs, market_probs, group_sizes, self.blend)
        return model_probs, blended


def _group_sizes(frame: pd.DataFrame) -> np.ndarray:
    _, idx, counts = np.unique(frame["race_id"].to_numpy(), return_index=True,
                               return_counts=True)
    return counts[np.argsort(idx)]


def attach_market(conn: sqlite3.Connection, frame: pd.DataFrame,
                  prefer: str = "bsp",
                  allowed: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Add market probability columns to a feature frame."""
    market = market_probabilities(conn, frame, prefer=prefer, allowed=allowed)
    merged = frame.merge(market, on="runner_id", how="left", validate="one_to_one")
    if merged["market_prob"].isna().any():
        raise RuntimeError("market probabilities missing for some runners")
    return merged


def fit_model(kind: str, train: pd.DataFrame, valid: pd.DataFrame) -> object:
    X_train = train[FEATURE_COLUMNS].to_numpy(dtype=float)
    y_train = (train["win_flag"] == 1).to_numpy(dtype=float)
    groups_train = _group_sizes(train)

    if kind == "logit":
        return ConditionalLogit().fit(X_train, y_train, groups_train)
    if kind == "gbm":
        model = GbmModel()
        X_valid = valid[FEATURE_COLUMNS].to_numpy(dtype=float) if len(valid) else None
        y_valid = (valid["win_flag"] == 1).to_numpy(dtype=float) if len(valid) else None
        return model.fit(X_train, y_train, groups_train, X_valid, y_valid,
                         feature_names=list(FEATURE_COLUMNS))
    raise ValueError(f"unknown model kind {kind!r}: expected 'gbm' or 'logit'")


def _split_frame_by_date(frame: pd.DataFrame, first_fraction: float = 0.5
                         ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a frame in two on a date boundary, earliest dates first.

    Splitting on dates rather than rows is what stops a single race day
    landing on both sides, which would leak one runner's result into the
    features of its own rivals.
    """
    if frame.empty:
        return frame, frame
    dates = sorted(frame["date"].unique())
    if len(dates) < 2:
        return frame, frame
    cut = min(max(1, int(len(dates) * first_fraction)), len(dates) - 1)
    first = frame[frame["date"].isin(set(dates[:cut]))]
    second = frame[frame["date"].isin(set(dates[cut:]))]
    if first.empty or second.empty:
        return frame, frame
    return first, second


def _split_validation(valid: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the validation window in two on a date boundary.

    The first half stops the boosting; the second fits the blend. Sharing one
    set does both jobs badly: the model's probabilities on its own
    early-stopping set are optimistically biased, so alpha -- the weight the
    blend puts on the model against the market -- comes out too high, and
    alpha is what actually prices every bet.
    """
    return _split_frame_by_date(valid, 0.5)


def _blend_inputs(model, frame: pd.DataFrame):
    groups = _group_sizes(frame)
    model_probs = model.predict_proba(
        frame[FEATURE_COLUMNS].to_numpy(dtype=float), groups)
    return (model_probs,
            frame["market_prob"].to_numpy(dtype=float),
            (frame["win_flag"] == 1).to_numpy(dtype=float),
            groups)


def train_on_frames(train: pd.DataFrame, valid: pd.DataFrame, test: pd.DataFrame,
                    kind: str = "gbm") -> TrainedModel:
    """Fit the model on train, the blend on held-out validation, evaluate on test."""
    early_stop, blend_window = _split_validation(valid)
    model = fit_model(kind, train, early_stop)

    # The blend window is held out from the model's own fit, so the weights
    # come from it and so does the test of whether they mean anything.
    blend_model_probs, blend_market, blend_y, groups_blend = _blend_inputs(
        model, blend_window)
    blend = fit_blend(blend_model_probs, blend_market, blend_y, groups_blend)
    lr_statistic, lr_p = model_adds_information(
        blend_model_probs, blend_market, blend_y, groups_blend)

    groups_test = _group_sizes(test)
    X_test = test[FEATURE_COLUMNS].to_numpy(dtype=float)
    y_test = (test["win_flag"] == 1).to_numpy(dtype=float)
    market_test = test["market_prob"].to_numpy(dtype=float)
    model_probs = model.predict_proba(X_test, groups_test)
    blended = blend_probabilities(model_probs, market_test, groups_test, blend)

    importance = (
        model.feature_importance(list(FEATURE_COLUMNS)) if kind == "gbm" else
        dict(sorted(
            zip(FEATURE_COLUMNS, np.abs(model.coef_) / max(np.abs(model.coef_).sum(), 1e-9)),
            key=lambda kv: -kv[1],
        ))
    )
    metrics = evaluate(model_probs, market_test, blended, y_test, groups_test,
                       blend.to_dict(), importance)
    metrics.blend_lr_statistic = lr_statistic
    metrics.blend_lr_p = lr_p
    return TrainedModel(kind=kind, model=model, blend=blend, metrics=metrics,
                        blend_lr_statistic=lr_statistic, blend_lr_p=lr_p)


def train_and_evaluate(settings: Settings, model_kind: str = "gbm",
                       persist: bool = True) -> ModelMetrics:
    """Full training run against the configured database."""
    conn = init_db(settings.database_path)
    dataset = build_dataset(conn)
    frame = attach_market(conn, dataset.frame, prefer="bsp")
    dataset = Dataset(frame=frame)
    splits = chronological_splits(dataset)

    trained = train_on_frames(
        frame.loc[splits.train], frame.loc[splits.valid], frame.loc[splits.test],
        kind=model_kind,
    )

    if persist:
        artifact_dir = Path(settings.data_dir) / "models"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = None
        if model_kind == "gbm":
            artifact_path = str(artifact_dir / "gbm.txt")
            trained.model.save(artifact_path)
        blend_path = artifact_dir / f"{model_kind}_blend.json"
        blend_path.write_text(json.dumps(
            {**trained.blend.to_dict(),
             "lr_statistic": trained.blend_lr_statistic,
             "lr_p_value": trained.blend_lr_p}, indent=2))

        conn.execute(
            """INSERT INTO model_runs (ts_utc, model_kind, params_json, metrics_json,
               artifact_path) VALUES (?, ?, ?, ?, ?)""",
            (datetime.now(timezone.utc).isoformat(), model_kind,
             json.dumps({"features": list(FEATURE_COLUMNS)}),
             json.dumps(trained.metrics.to_dict()), artifact_path),
        )
        conn.commit()

    conn.close()
    return trained.metrics
