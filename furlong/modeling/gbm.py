"""Gradient-boosted model with per-race softmax normalisation.

LightGBM trained on the binary win target, whose raw scores are then
softmax-normalised within each race so probabilities sum to one. This is
the modern replacement for the linear conditional logit while keeping the
same race-conditional probability structure.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from furlong.modeling.conditional_logit import race_softmax

DEFAULT_PARAMS = {
    "objective": "binary",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_data_in_leaf": 100,
    "feature_fraction": 0.85,
    "bagging_fraction": 0.85,
    "bagging_freq": 1,
    "lambda_l2": 1.0,
    "verbose": -1,
    "seed": 42,
    "deterministic": True,
    "force_row_wise": True,
    "num_threads": 1,
}


class GbmModel:
    """LightGBM scores, softmax-normalised per race."""

    def __init__(self, params: dict | None = None, num_boost_round: int = 400,
                 early_stopping_rounds: int = 40):
        self.params = {**DEFAULT_PARAMS, **(params or {})}
        self.num_boost_round = num_boost_round
        self.early_stopping_rounds = early_stopping_rounds
        self.booster = None

    def fit(self, X: np.ndarray, y: np.ndarray, group_sizes: np.ndarray,
            X_valid: np.ndarray | None = None, y_valid: np.ndarray | None = None,
            feature_names: list[str] | None = None) -> "GbmModel":
        import lightgbm as lgb

        train_set = lgb.Dataset(np.asarray(X, dtype=float), label=np.asarray(y, dtype=float),
                                feature_name=feature_names or "auto")
        valid_sets, callbacks = [], []
        if X_valid is not None and y_valid is not None and len(X_valid):
            valid_sets = [lgb.Dataset(np.asarray(X_valid, dtype=float),
                                      label=np.asarray(y_valid, dtype=float),
                                      reference=train_set)]
            callbacks = [lgb.early_stopping(self.early_stopping_rounds, verbose=False)]

        self.booster = lgb.train(
            self.params, train_set, num_boost_round=self.num_boost_round,
            valid_sets=valid_sets, callbacks=callbacks,
        )
        return self

    def raw_scores(self, X: np.ndarray) -> np.ndarray:
        if self.booster is None:
            raise RuntimeError("model is not fitted")
        return self.booster.predict(np.asarray(X, dtype=float), raw_score=True)

    def predict_proba(self, X: np.ndarray, group_sizes: np.ndarray) -> np.ndarray:
        return race_softmax(self.raw_scores(X), group_sizes)

    def feature_importance(self, feature_names: list[str]) -> dict[str, float]:
        if self.booster is None:
            raise RuntimeError("model is not fitted")
        gains = self.booster.feature_importance(importance_type="gain")
        total = float(gains.sum()) or 1.0
        return {
            name: float(gain) / total
            for name, gain in sorted(zip(feature_names, gains), key=lambda kv: -kv[1])
        }

    def save(self, path: str | Path) -> None:
        if self.booster is None:
            raise RuntimeError("model is not fitted")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.booster.save_model(str(path))

    @classmethod
    def load(cls, path: str | Path) -> "GbmModel":
        import lightgbm as lgb

        model = cls()
        model.booster = lgb.Booster(model_file=str(path))
        return model
