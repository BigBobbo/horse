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
                         prefer: str = "bsp", devig_method: str = "shin",
                         allowed: tuple[str, ...] | None = None) -> pd.DataFrame:
    """Return per-runner market probabilities and the source used.

    ``frame`` must have ``runner_id`` and ``race_id`` columns in race-grouped
    order. Returns a frame with ``runner_id``, ``market_prob``,
    ``market_odds``, ``market_source`` and ``market_priced`` -- the last a
    flag saying whether this runner had a real quoted price. Rows with
    ``market_priced == False`` carry an inferred probability and a
    placeholder price: they must never be treated as tradeable.

    ``allowed`` restricts which sources may be used. The live path passes
    ("exchange", "book") because Betfair SP does not exist before the off.
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
        chosen_source, raw_odds = _choose_source(
            runner_ids, bsp, exchange, best_book, prefer, allowed
        )
        n = len(runner_ids)

        if chosen_source is None:
            # No prices at all. Fall back to the field, and mark every runner
            # unpriced so nothing downstream mistakes 1/n for a real quote.
            probs = np.full(n, 1.0 / n)
            odds_out = np.full(n, float(n))
            priced = np.zeros(n, dtype=bool)
        else:
            priced = np.array([o is not None for o in raw_odds])
            probs = np.empty(n)
            if priced.all():
                probs = _devig_for_source(np.array(raw_odds, dtype=float),
                                          chosen_source, devig_method)
            else:
                # Partial coverage: keep the priced runners' own probability
                # *level* (de-vigged against a full book of the same shape)
                # and share what is left over the unpriced ones. Normalising
                # the priced subset to sum to one would inflate three runners
                # quoted at 10.0 from 10% each to 33% each.
                known_odds = np.array([o for o in raw_odds if o is not None],
                                      dtype=float)
                known_probs = _partial_book_probabilities(
                    known_odds, chosen_source, devig_method
                )
                n_unknown = int((~priced).sum())
                residual = max(0.0, 1.0 - float(known_probs.sum()))
                probs[priced] = known_probs
                probs[~priced] = residual / max(n_unknown, 1)
                total = probs.sum()
                if total > 0:
                    probs = probs / total
            odds_out = np.array([
                o if o is not None else float(1.0 / max(p, 1e-6))
                for o, p in zip(raw_odds, probs)
            ], dtype=float)

        for runner_id, prob, odd, is_priced in zip(runner_ids, probs, odds_out, priced):
            records.append({
                "runner_id": runner_id,
                "market_prob": float(prob),
                "market_odds": float(odd),
                "market_source": chosen_source or "uniform",
                "market_priced": bool(is_priced),
            })
    if not records:
        # Preserve the schema so downstream merges do not fail on an empty day.
        return pd.DataFrame(columns=[
            "runner_id", "market_prob", "market_odds", "market_source", "market_priced",
        ])
    return pd.DataFrame.from_records(records)


def _partial_book_probabilities(odds: np.ndarray, source: str, method: str) -> np.ndarray:
    """De-vig a partial book without destroying its probability level.

    The margin is estimated from the priced runners' own overround per
    runner and removed proportionally, leaving the sum below one so the
    unpriced runners can take the remainder.
    """
    implied = 1.0 / odds
    if source in ("bsp", "exchange"):
        return implied  # margin-free venues: implied probabilities stand
    # Bookmaker: strip the average per-runner margin observed on this book.
    # A full book of this shape would sum to book_sum * (n_total / n_priced),
    # which is unknown, so use the per-runner margin as the best estimate.
    per_runner_margin = float(implied.sum()) / max(len(implied), 1)
    scale = 1.0 / (1.0 + per_runner_margin) if per_runner_margin > 0 else 1.0
    return implied * scale


def _choose_source(runner_ids: list[int], bsp: dict, exchange: dict, book: dict,
                   prefer: str, allowed: tuple[str, ...] | None = None
                   ) -> tuple[str | None, list[float | None]]:
    """Pick the best-populated permitted price source for a race.

    The preferred source wins outright at 90% coverage or better; otherwise
    the source with the *most* coverage is used, not merely the first one
    with any.
    """
    permitted = [s for s in MARKET_SOURCES if allowed is None or s in allowed]
    if prefer in permitted:
        order = [prefer] + [s for s in permitted if s != prefer]
    else:
        order = permitted
    tables = {"bsp": bsp, "exchange": exchange, "book": book}

    best: tuple[float, str, list[float | None]] | None = None
    for source in order:
        table = tables[source]
        values = [table.get(rid) for rid in runner_ids]
        values = [v if (v is not None and v > 1.0) else None for v in values]
        coverage = sum(v is not None for v in values) / max(len(values), 1)
        if coverage >= 0.9:
            return source, values
        if coverage > 0 and (best is None or coverage > best[0]):
            best = (coverage, source, values)
    if best is not None:
        return best[1], best[2]
    return None, [None] * len(runner_ids)


def _devig_for_source(odds: np.ndarray, source: str, method: str) -> np.ndarray:
    if source == "bsp":
        # BSP is already margin-free; just normalise to sum to one.
        implied = 1.0 / odds
        return implied / implied.sum()
    if source == "exchange":
        implied = 1.0 / odds
        return implied / implied.sum()
    return devig(odds, method=method)
