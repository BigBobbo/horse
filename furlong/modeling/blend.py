"""Benter's second stage: blending model probabilities with market odds.

Benter (1994) found his fundamental model's probabilities were
systematically biased toward its own opinion, and that the decisive step
was combining them with the public's implied probabilities:

    p_i = exp(alpha * log f_i + beta * log q_i) / sum_j exp(...)

where ``f`` is the out-of-sample fundamental-model probability and ``q`` the
market's (de-vigged) implied probability. ``alpha`` and ``beta`` are fitted
by maximum likelihood on held-out races.

This doubles as calibration: if the model carries no information beyond the
market, ``alpha`` collapses toward zero and the blend reproduces the market.
The value of a model is therefore measured as the gain in McFadden R-squared
of the blend over a market-only model (Benter's Delta R-squared).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from furlong.modeling.conditional_logit import race_softmax

EPS = 1e-9


def normalise_by_race(probs: np.ndarray, group_sizes: np.ndarray) -> np.ndarray:
    """Rescale probabilities so each race sums to one."""
    out = np.empty_like(probs, dtype=float)
    start = 0
    for size in group_sizes:
        end = start + size
        chunk = np.clip(probs[start:end], EPS, None)
        out[start:end] = chunk / chunk.sum()
        start = end
    return out


@dataclass
class BlendParams:
    alpha: float  # weight on the fundamental model's log-probabilities
    beta: float   # weight on the market's log-probabilities

    def to_dict(self) -> dict:
        return {"alpha": self.alpha, "beta": self.beta}

    @classmethod
    def from_dict(cls, data: dict) -> "BlendParams":
        return cls(alpha=float(data["alpha"]), beta=float(data["beta"]))


def blend_probabilities(model_probs: np.ndarray, market_probs: np.ndarray,
                        group_sizes: np.ndarray, params: BlendParams) -> np.ndarray:
    """Apply the fitted blend to produce final per-race probabilities."""
    log_f = np.log(np.clip(model_probs, EPS, None))
    log_q = np.log(np.clip(market_probs, EPS, None))
    return race_softmax(params.alpha * log_f + params.beta * log_q, group_sizes)


def fit_blend(model_probs: np.ndarray, market_probs: np.ndarray, y: np.ndarray,
              group_sizes: np.ndarray) -> BlendParams:
    """Maximum-likelihood fit of (alpha, beta) on held-out races."""
    log_f = np.log(np.clip(model_probs, EPS, None))
    log_q = np.log(np.clip(market_probs, EPS, None))
    y = np.asarray(y, dtype=float)

    def objective(theta: np.ndarray) -> float:
        probs = race_softmax(theta[0] * log_f + theta[1] * log_q, group_sizes)
        return -float(np.sum(y * np.log(np.clip(probs, EPS, None))))

    best: tuple[float, np.ndarray] | None = None
    for start in ([0.5, 0.5], [1.0, 1.0], [0.0, 1.0], [1.0, 0.0]):
        result = minimize(objective, np.array(start), method="Nelder-Mead",
                          options={"maxiter": 2000, "xatol": 1e-6, "fatol": 1e-9})
        if best is None or result.fun < best[0]:
            best = (float(result.fun), result.x)

    alpha, beta = best[1]
    # Negative weights are never meaningful: they would mean "bet against our
    # own model" or "fade the market", which no honest fit should produce.
    return BlendParams(alpha=max(float(alpha), 0.0), beta=max(float(beta), 0.0))
