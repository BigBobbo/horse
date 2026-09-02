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
from scipy.stats import chi2

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


def _log_terms(model_probs: np.ndarray, market_probs: np.ndarray,
               y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (np.log(np.clip(model_probs, EPS, None)),
            np.log(np.clip(market_probs, EPS, None)),
            np.asarray(y, dtype=float))


def fit_blend(model_probs: np.ndarray, market_probs: np.ndarray, y: np.ndarray,
              group_sizes: np.ndarray) -> BlendParams:
    """Maximum-likelihood fit of (alpha, beta) on held-out races."""
    log_f, log_q, y = _log_terms(model_probs, market_probs, y)

    # Negative weights are never meaningful -- they would mean "bet against
    # our own model" or "fade the market" -- so the search happens on the
    # non-negative orthant. Clamping *inside* the objective rather than after
    # the fit is what makes that safe: clamping afterwards moves the answer
    # to a point the optimiser never scored. On a separable problem this fit
    # ran to (alpha 96, beta -96.9), a perfect in-sample fit, and the
    # post-hoc clamp shipped (96, 0) instead -- a blend whose log-loss was
    # four times worse than ignoring the model altogether.
    def objective(theta: np.ndarray) -> float:
        alpha, beta = max(float(theta[0]), 0.0), max(float(theta[1]), 0.0)
        probs = race_softmax(alpha * log_f + beta * log_q, group_sizes)
        return -float(np.sum(y * np.log(np.clip(probs, EPS, None))))

    # The market alone is the floor: whatever the search finds, shipping a
    # blend that fits worse than not blending at all is never right.
    best = (objective(np.array([0.0, 1.0])), np.array([0.0, 1.0]))
    for start in ([0.5, 0.5], [1.0, 1.0], [0.0, 1.0], [1.0, 0.0]):
        result = minimize(objective, np.array(start, dtype=float),
                          method="Nelder-Mead",
                          options={"maxiter": 2000, "xatol": 1e-6, "fatol": 1e-9})
        if np.isfinite(result.fun) and result.fun < best[0]:
            best = (float(result.fun), result.x)

    alpha, beta = best[1]
    return BlendParams(alpha=max(float(alpha), 0.0), beta=max(float(beta), 0.0))


def fit_market_only(market_probs: np.ndarray, y: np.ndarray,
                    group_sizes: np.ndarray) -> BlendParams:
    """Fit ``p ∝ q**beta`` with the model excluded (alpha pinned at zero).

    This is the null the model has to beat. It matters that beta stays free:
    a blend can differ from the raw market simply by flattening or sharpening
    it, and a comparison against beta = 1 would score that reshaping as if it
    were information the model supplied.
    """
    _, log_q, y = _log_terms(market_probs, market_probs, y)

    def objective(theta: np.ndarray) -> float:
        probs = race_softmax(max(float(theta[0]), 0.0) * log_q, group_sizes)
        return -float(np.sum(y * np.log(np.clip(probs, EPS, None))))

    best = (objective(np.array([1.0])), 1.0)
    for start in (0.5, 1.0, 1.5):
        result = minimize(objective, np.array([start]), method="Nelder-Mead",
                          options={"maxiter": 2000, "xatol": 1e-6, "fatol": 1e-9})
        if np.isfinite(result.fun) and result.fun < best[0]:
            best = (float(result.fun), float(result.x[0]))
    return BlendParams(alpha=0.0, beta=max(best[1], 0.0))


def blend_log_likelihood(model_probs: np.ndarray, market_probs: np.ndarray,
                         y: np.ndarray, group_sizes: np.ndarray,
                         params: BlendParams) -> float:
    """Conditional-logit log-likelihood of a blend on the given races."""
    probs = blend_probabilities(model_probs, market_probs, group_sizes, params)
    y = np.asarray(y, dtype=float)
    return float(np.sum(y * np.log(np.clip(probs, EPS, None))))


def model_adds_information(model_probs: np.ndarray, market_probs: np.ndarray,
                           y: np.ndarray, group_sizes: np.ndarray
                           ) -> tuple[float, float]:
    """Likelihood-ratio test of alpha = 0. Returns (statistic, p-value).

    The blend and the market-only fit are nested and differ by one free
    parameter, so 2*(LL_full - LL_restricted) is chi-squared on 1 degree of
    freedom. That is the honest way to ask whether the model contributes
    anything, and it is the question the whole two-stage design turns on.

    Held-out Delta R-squared cannot answer it. The quantity being detected is
    of order 0.002, and on the few hundred races a walk-forward fold can
    spare, its sampling error is several times that -- so it flips sign
    between folds, and a gate built on it opens by luck rather than by
    evidence. The likelihood-ratio test scales its own threshold with the
    sample: on thin evidence it simply fails to reject, which for a betting
    system is the right way to be wrong.
    """
    full = fit_blend(model_probs, market_probs, y, group_sizes)
    restricted = fit_market_only(market_probs, y, group_sizes)
    ll_full = blend_log_likelihood(model_probs, market_probs, y, group_sizes, full)
    ll_restricted = blend_log_likelihood(market_probs, market_probs, y, group_sizes,
                                         BlendParams(alpha=0.0, beta=restricted.beta))
    statistic = max(2.0 * (ll_full - ll_restricted), 0.0)
    return statistic, float(chi2.sf(statistic, df=1))
