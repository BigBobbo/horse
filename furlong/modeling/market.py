"""Assembling the market's view of each race as fair probabilities.

Priority order for a race's market probabilities:

1. Betfair SP (the closing line, margin-free) — the honest benchmark for
   backtesting and for fitting the blend on historical races.
2. Latest exchange price — used for live/pre-off races where no BSP exists.
3. Best available bookmaker price, de-vigged with Shin's method.

Rows in a race with no price at all fall back to a uniform share of the
race's residual probability, which is what Benter did with unratable
runners: with no information, defer to the field.
"""

from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from furlong import repo
from furlong.value.devig import devig

MARKET_SOURCES = ("bsp", "exchange", "book")


def market_probabilities(conn: sqlite3.Connection, frame: pd.DataFrame,
                         prefer: str = "bsp", devig_method: str = "shin") -> pd.DataFrame:
    """Return per-runner market probabilities and the source used.

    ``frame`` must have ``runner_id`` and ``race_id`` columns in race-grouped
    order. Returns a frame with ``runner_id``, ``market_prob``,
    ``market_odds`` and ``market_source``.
    """
    race_ids = sorted(set(int(r) for r in frame["race_id"]))
    bsp = repo.load_bsp(conn, "win").set_index("runner_id")["bsp"].to_dict()
    odds = repo.load_latest_odds(conn, race_ids)

    exchange = (
        odds[odds["venue"] == "exchange"].set_index("runner_id")["odds_decimal"].to_dict()
        if len(odds) else {}
    )
    if len(odds):
        book_rows = odds[odds["venue"] == "book"]
        # best (largest) price across bookmakers is what a punter can take
        best_book = book_rows.groupby("runner_id")["odds_decimal"].max().to_dict()
    else:
        best_book = {}

    records: list[dict] = []
    for race_id, group in frame.groupby("race_id", sort=False):
        runner_ids = [int(r) for r in group["runner_id"]]
        chosen_source, raw_odds = _choose_source(runner_ids, bsp, exchange, best_book, prefer)
        n = len(runner_ids)

        if chosen_source is None:
            probs = np.full(n, 1.0 / n)
            odds_out = np.full(n, float(n))
        else:
            known = np.array([o is not None for o in raw_odds])
            probs = np.empty(n)
            if known.all():
                probs = _devig_for_source(np.array(raw_odds, dtype=float),
                                          chosen_source, devig_method)
            else:
                known_probs = _devig_for_source(
                    np.array([o for o in raw_odds if o is not None], dtype=float),
                    chosen_source, devig_method,
                )
                # Unpriced runners share a residual; the priced ones keep their
                # relative shape (Benter: defer to the field when uninformed).
                n_unknown = int((~known).sum())
                residual = min(0.05 * n_unknown, 0.5)
                probs[known] = known_probs * (1.0 - residual)
                probs[~known] = residual / max(n_unknown, 1)
            odds_out = np.array([
                o if o is not None else float(1.0 / max(p, 1e-6))
                for o, p in zip(raw_odds, probs)
            ], dtype=float)

        for runner_id, prob, odd in zip(runner_ids, probs, odds_out):
            records.append({
                "runner_id": runner_id,
                "market_prob": float(prob),
                "market_odds": float(odd),
                "market_source": chosen_source or "uniform",
            })
    return pd.DataFrame.from_records(records)


def _choose_source(runner_ids: list[int], bsp: dict, exchange: dict, book: dict,
                   prefer: str) -> tuple[str | None, list[float | None]]:
    """Pick the best-populated price source for a race."""
    order = [prefer] + [s for s in MARKET_SOURCES if s != prefer]
    tables = {"bsp": bsp, "exchange": exchange, "book": book}
    best: tuple[str, list[float | None]] | None = None
    for source in order:
        table = tables[source]
        values = [table.get(rid) for rid in runner_ids]
        values = [v if (v is not None and v > 1.0) else None for v in values]
        coverage = sum(v is not None for v in values) / max(len(values), 1)
        if coverage >= 0.9:
            return source, values
        if coverage > 0 and best is None:
            best = (source, values)
    return best if best else (None, [None] * len(runner_ids))


def _devig_for_source(odds: np.ndarray, source: str, method: str) -> np.ndarray:
    if source == "bsp":
        # BSP is already margin-free; just normalise to sum to one.
        implied = 1.0 / odds
        return implied / implied.sum()
    if source == "exchange":
        implied = 1.0 / odds
        return implied / implied.sum()
    return devig(odds, method=method)
