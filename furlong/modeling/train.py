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
from furlong.modeling.blend import BlendParams, blend_probabilities, fit_blend
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
                  prefer: str = "bsp") -> pd.DataFrame:
    """Add market_prob/market_odds/market_source columns to a feature frame."""
    market = market_probabilities(conn, frame, prefer=prefer)
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


def train_on_frames(train: pd.DataFrame, valid: pd.DataFrame, test: pd.DataFrame,
                    kind: str = "gbm") -> TrainedModel:
    """Fit the model on train, the blend on valid, and evaluate on test."""
    model = fit_model(kind, train, valid)

    groups_valid = _group_sizes(valid)
    valid_model_probs = model.predict_proba(
        valid[FEATURE_COLUMNS].to_numpy(dtype=float), groups_valid
    )
    blend = fit_blend(
        valid_model_probs,
        valid["market_prob"].to_numpy(dtype=float),
        (valid["win_flag"] == 1).to_numpy(dtype=float),
        groups_valid,
    )

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
    return TrainedModel(kind=kind, model=model, blend=blend, metrics=metrics)


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
        blend_path.write_text(json.dumps(trained.blend.to_dict(), indent=2))

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
