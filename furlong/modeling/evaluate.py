"""Evaluation metrics for race-conditional probability models.

The headline metric is Benter's Delta R-squared: the gain in McFadden
R-squared of the blended model over a market-only model. A model whose
Delta R-squared is not clearly positive has no information the market does
not already have, whatever its raw accuracy looks like.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

EPS = 1e-12


def log_likelihood(probs: np.ndarray, y: np.ndarray) -> float:
    return float(np.sum(y * np.log(np.clip(probs, EPS, None))))


def log_loss_per_race(probs: np.ndarray, y: np.ndarray, n_races: int) -> float:
    return -log_likelihood(probs, y) / max(n_races, 1)


def uniform_log_likelihood(group_sizes: np.ndarray) -> float:
    """Log-likelihood of the naive 1/field-size model (McFadden's null)."""
    return float(np.sum(np.log(1.0 / np.asarray(group_sizes, dtype=float))))


def mcfadden_r2(probs: np.ndarray, y: np.ndarray, group_sizes: np.ndarray) -> float:
    null_ll = uniform_log_likelihood(group_sizes)
    if null_ll == 0:
        # No races, or every race a one-runner walkover: the naive model is
        # already perfect, so there is no explanatory power to measure.
        return float("nan")
    return 1.0 - log_likelihood(probs, y) / null_ll


def brier_score(probs: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((probs - y) ** 2))


def top_pick_strike_rate(probs: np.ndarray, y: np.ndarray,
                         group_sizes: np.ndarray) -> float:
    """Share of races won by the model's highest-probability runner."""
    hits, start = 0, 0
    for size in group_sizes:
        end = start + size
        chunk = probs[start:end]
        hits += int(y[start:end][int(np.argmax(chunk))] == 1)
        start = end
    return hits / max(len(group_sizes), 1)


def reliability_table(probs: np.ndarray, y: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    """Predicted vs actual win rate by probability decile."""
    frame = pd.DataFrame({"prob": probs, "won": y})
    frame["bin"] = pd.qcut(frame["prob"], n_bins, labels=False, duplicates="drop")
    table = frame.groupby("bin", observed=True).agg(
        predicted=("prob", "mean"), actual=("won", "mean"), n=("won", "size")
    ).reset_index()
    return table


@dataclass
class ModelMetrics:
    """Metrics for a model, its market benchmark, and their blend."""

    n_races: int
    n_runners: int
    model_log_loss: float
    market_log_loss: float
    blend_log_loss: float
    model_r2: float
    market_r2: float
    blend_r2: float
    delta_r2: float
    brier: float
    top_pick_strike_rate: float
    market_top_pick_strike_rate: float
    blend_params: dict
    feature_importance: dict = field(default_factory=dict)
    reliability: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "n_races": self.n_races,
            "n_runners": self.n_runners,
            "log_loss": {
                "model": self.model_log_loss,
                "market": self.market_log_loss,
                "blend": self.blend_log_loss,
            },
            "mcfadden_r2": {
                "model": self.model_r2,
                "market": self.market_r2,
                "blend": self.blend_r2,
            },
            "delta_r2": self.delta_r2,
            "brier": self.brier,
            "top_pick_strike_rate": self.top_pick_strike_rate,
            "market_top_pick_strike_rate": self.market_top_pick_strike_rate,
            "blend_params": self.blend_params,
            "feature_importance": self.feature_importance,
            "reliability": self.reliability,
        }

    def summary(self) -> str:
        lines = [
            f"Races {self.n_races:,} · runners {self.n_runners:,}",
            f"  log-loss/race   model {self.model_log_loss:.4f} · "
            f"market {self.market_log_loss:.4f} · blend {self.blend_log_loss:.4f}",
            f"  McFadden R2     model {self.model_r2:.4f} · "
            f"market {self.market_r2:.4f} · blend {self.blend_r2:.4f}",
            f"  Delta R2 (blend over market): {self.delta_r2:+.4f}"
            f"  {'[model adds information]' if self.delta_r2 > 0.001 else '[no edge over market]'}",
            f"  Blend weights   alpha (model) {self.blend_params.get('alpha', 0):.3f} · "
            f"beta (market) {self.blend_params.get('beta', 0):.3f}",
            f"  Top pick SR     blend {self.top_pick_strike_rate:.3f} · "
            f"market {self.market_top_pick_strike_rate:.3f}",
        ]
        if self.feature_importance:
            top = list(self.feature_importance.items())[:5]
            lines.append("  Top features    " + ", ".join(f"{k} {v:.2f}" for k, v in top))
        return "\n".join(lines)


def evaluate(model_probs: np.ndarray, market_probs: np.ndarray, blend_probs: np.ndarray,
             y: np.ndarray, group_sizes: np.ndarray, blend_params: dict,
             feature_importance: dict | None = None) -> ModelMetrics:
    n_races = len(group_sizes)
    market_r2 = mcfadden_r2(market_probs, y, group_sizes)
    blend_r2 = mcfadden_r2(blend_probs, y, group_sizes)
    return ModelMetrics(
        n_races=n_races,
        n_runners=len(y),
        model_log_loss=log_loss_per_race(model_probs, y, n_races),
        market_log_loss=log_loss_per_race(market_probs, y, n_races),
        blend_log_loss=log_loss_per_race(blend_probs, y, n_races),
        model_r2=mcfadden_r2(model_probs, y, group_sizes),
        market_r2=market_r2,
        blend_r2=blend_r2,
        delta_r2=blend_r2 - market_r2,
        brier=brier_score(blend_probs, y),
        top_pick_strike_rate=top_pick_strike_rate(blend_probs, y, group_sizes),
        market_top_pick_strike_rate=top_pick_strike_rate(market_probs, y, group_sizes),
        blend_params=blend_params,
        feature_importance=feature_importance or {},
        reliability=reliability_table(blend_probs, y).to_dict(orient="records"),
    )
