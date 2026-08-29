"""Converting odds into probabilities by removing the bookmaker's margin.

A bookmaker's implied probabilities sum to more than one (the overround).
Three standard methods to recover fair probabilities:

* ``proportional`` — divide by the book sum. Simple, but assumes the margin
  is spread evenly, which contradicts the favourite-longshot bias.
* ``power`` — solve for k such that sum(p_i^k) = 1. Takes proportionally
  more margin out of longshots.
* ``shin`` — Shin's (1993) model of a bookmaker protecting against insiders,
  the standard choice in the literature; also removes more margin from
  longshots, and reduces to proportional when the insider share z is zero.

Exchange prices carry no margin, but commission is charged on net winnings,
so the effective return on a winning bet at odds ``o`` is
``(o - 1) * (1 - commission)``.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

EPS = 1e-12


def odds_to_implied(odds: np.ndarray) -> np.ndarray:
    """Decimal odds -> raw implied probabilities (which sum to > 1 for a book)."""
    odds = np.asarray(odds, dtype=float)
    if np.any(odds <= 1.0):
        raise ValueError("decimal odds must exceed 1.0")
    return 1.0 / odds


def implied_to_odds(probs: np.ndarray) -> np.ndarray:
    probs = np.clip(np.asarray(probs, dtype=float), EPS, None)
    return 1.0 / probs


def overround(odds: np.ndarray) -> float:
    """Book sum: 1.16 means a 116% book (16% margin)."""
    return float(odds_to_implied(odds).sum())


def devig_proportional(odds: np.ndarray) -> np.ndarray:
    implied = odds_to_implied(odds)
    return implied / implied.sum()


def devig_power(odds: np.ndarray) -> np.ndarray:
    """Solve sum(p_i^k) = 1 for k >= 1; more margin removed from longshots."""
    implied = odds_to_implied(odds)
    if len(implied) == 1:
        return np.array([1.0])
    if abs(implied.sum() - 1.0) < 1e-9:
        return implied.copy()

    def excess(k: float) -> float:
        return float(np.sum(implied ** k) - 1.0)

    try:
        k = brentq(excess, 0.2, 20.0, xtol=1e-10)
    except ValueError:
        return devig_proportional(odds)
    fair = implied ** k
    return fair / fair.sum()


def devig_shin(odds: np.ndarray) -> np.ndarray:
    """Shin's method: recover fair probabilities given an insider share z.

    With book sum B and raw implied probabilities pi:
        p_i = (sqrt(z^2 + 4(1-z) * pi_i^2 / B) - z) / (2(1-z))
    z is solved so the fair probabilities sum to one.
    """
    implied = odds_to_implied(odds)
    book = float(implied.sum())
    if len(implied) == 1:
        return np.array([1.0])
    if book <= 1.0 + 1e-9:
        return implied / book

    def fair_for(z: float) -> np.ndarray:
        inner = z * z + 4.0 * (1.0 - z) * (implied ** 2) / book
        return (np.sqrt(np.clip(inner, 0.0, None)) - z) / (2.0 * (1.0 - z))

    def excess(z: float) -> float:
        return float(fair_for(z).sum() - 1.0)

    lo, hi = 1e-9, 0.5
    try:
        if excess(lo) * excess(hi) > 0:
            return devig_power(odds)
        z = brentq(excess, lo, hi, xtol=1e-12)
    except ValueError:
        return devig_power(odds)
    fair = fair_for(z)
    return fair / fair.sum()


DEVIG_METHODS = {
    "proportional": devig_proportional,
    "power": devig_power,
    "shin": devig_shin,
}


def devig(odds: np.ndarray, method: str = "shin") -> np.ndarray:
    """De-vig a complete set of odds for one race."""
    if method not in DEVIG_METHODS:
        raise ValueError(f"unknown de-vig method {method!r}: expected one of {sorted(DEVIG_METHODS)}")
    return DEVIG_METHODS[method](np.asarray(odds, dtype=float))


def net_return_multiple(odds: float, commission: float = 0.0) -> float:
    """Profit per unit staked on a winner, after exchange commission."""
    return (odds - 1.0) * (1.0 - commission)


def expected_value(prob: float, odds: float, commission: float = 0.0) -> float:
    """EV per unit staked: p * net win - (1 - p) * stake lost."""
    return prob * net_return_multiple(odds, commission) - (1.0 - prob)


def fair_odds(prob: float, commission: float = 0.0) -> float:
    """Break-even decimal odds for a probability, allowing for commission."""
    prob = min(max(prob, EPS), 1.0 - EPS)
    return 1.0 + (1.0 - prob) / (prob * (1.0 - commission))
