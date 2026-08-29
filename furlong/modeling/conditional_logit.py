"""Conditional (multinomial) logit over the runners of each race.

The Bolton & Chapman (1986) model, still the field's baseline: each runner
gets a linear score, and the softmax of scores within a race gives win
probabilities that sum to one. Fitted by L2-penalised maximum likelihood.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def race_softmax(scores: np.ndarray, group_sizes: np.ndarray) -> np.ndarray:
    """Softmax applied within each race group (groups are contiguous)."""
    out = np.empty_like(scores, dtype=float)
    start = 0
    for size in group_sizes:
        end = start + size
        chunk = scores[start:end]
        shifted = chunk - chunk.max()
        exp = np.exp(shifted)
        out[start:end] = exp / exp.sum()
        start = end
    return out


class ConditionalLogit:
    """L2-penalised conditional logit with per-race softmax normalisation."""

    def __init__(self, l2: float = 1.0, max_iter: int = 300):
        self.l2 = l2
        self.max_iter = max_iter
        self.coef_: np.ndarray | None = None
        self.mean_: np.ndarray | None = None
        self.scale_: np.ndarray | None = None

    def _standardise(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mean_ = X.mean(axis=0)
            scale = X.std(axis=0)
            self.scale_ = np.where(scale > 1e-9, scale, 1.0)
        return (X - self.mean_) / self.scale_

    def fit(self, X: np.ndarray, y: np.ndarray, group_sizes: np.ndarray) -> "ConditionalLogit":
        Xs = self._standardise(np.asarray(X, dtype=float), fit=True)
        y = np.asarray(y, dtype=float)
        n_features = Xs.shape[1]

        def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
            probs = race_softmax(Xs @ beta, group_sizes)
            # Negative log-likelihood of the observed winners, plus L2 penalty.
            # For a per-group softmax with one winner per group the gradient of
            # the NLL is simply X^T (p - y).
            nll = -np.sum(y * np.log(np.clip(probs, 1e-12, None)))
            nll += 0.5 * self.l2 * float(beta @ beta)
            grad = Xs.T @ (probs - y) + self.l2 * beta
            return nll, grad

        result = minimize(
            objective, np.zeros(n_features), jac=True, method="L-BFGS-B",
            options={"maxiter": self.max_iter},
        )
        self.coef_ = result.x
        return self

    def predict_proba(self, X: np.ndarray, group_sizes: np.ndarray) -> np.ndarray:
        if self.coef_ is None:
            raise RuntimeError("model is not fitted")
        Xs = self._standardise(np.asarray(X, dtype=float))
        return race_softmax(Xs @ self.coef_, group_sizes)
