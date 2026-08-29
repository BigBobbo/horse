"""The value engine: model probability versus available odds.

For each runner the engine compares the blended probability with the best
available price at each venue and computes expected value net of exchange
commission. Bets are only suggested when they clear all three filters:

* ``min_edge``   — expected value per unit staked (the value threshold);
* ``min_prob``   — Bolton & Chapman's longshot exclusion. Relative
  probability errors are largest on longshots, and the favourite-longshot
  bias means bookmaker prices there are the worst value in racing;
* ``max_odds``   — a hard ceiling, for the same reason;
* ``max_prob``   — a sanity ceiling. A runner priced at near-certainty means
  a walkover or a mis-parsed card, and a "100% chance" bet is a bug report,
  not an opportunity.

Each suggestion carries a **price floor**: the shortest price at which the
bet still clears ``min_edge``. Advised prices decay within minutes of
publication (the research is unambiguous), so telling a user "do not take
below X" is the difference between advice and fiction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from furlong.config import Settings
from furlong.value.devig import expected_value, fair_odds

BOG_ELIGIBLE = True  # bookmaker prices in UK/IRE racing normally carry BOG from ~8am


@dataclass
class PricedRunner:
    runner_id: int
    race_id: int
    venue: str            # 'book' | 'exchange'
    bookmaker: str | None
    odds: float
    ev: float
    commission: float


@dataclass
class Suggestion:
    runner_id: int
    race_id: int
    model_prob: float
    blend_prob: float
    fair_odds: float
    advised_odds: float
    price_floor: float
    venue: str
    bookmaker: str | None
    ev: float
    market_prob: float
    edge_vs_market: float
    alternatives: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "runner_id": int(self.runner_id),
            "race_id": int(self.race_id),
            "model_prob": round(float(self.model_prob), 5),
            "blend_prob": round(float(self.blend_prob), 5),
            "fair_odds": round(float(self.fair_odds), 3),
            "advised_odds": round(float(self.advised_odds), 3),
            "price_floor": round(float(self.price_floor), 3),
            "venue": self.venue,
            "bookmaker": self.bookmaker,
            "ev": round(float(self.ev), 5),
            "market_prob": round(float(self.market_prob), 5),
            "edge_vs_market": round(float(self.edge_vs_market), 5),
        }


def price_floor_for(prob: float, min_edge: float, commission: float) -> float:
    """Shortest decimal price at which the bet still clears ``min_edge``.

    Solving ``prob * (o - 1) * (1 - c) - (1 - prob) = min_edge`` for o.
    """
    prob = min(max(prob, 1e-9), 1.0 - 1e-9)
    return 1.0 + (min_edge + 1.0 - prob) / (prob * (1.0 - commission))


def price_runner(prob: float, odds: float, venue: str, commission: float) -> float:
    """Expected value per unit staked. Bookmaker bets pay no commission."""
    effective_commission = commission if venue == "exchange" else 0.0
    return expected_value(prob, odds, effective_commission)


def evaluate_prices(frame: pd.DataFrame, odds_frame: pd.DataFrame,
                    settings: Settings) -> pd.DataFrame:
    """Price every (runner, venue) combination and return them ranked by EV.

    ``frame`` needs ``runner_id``, ``race_id``, ``blend_prob``.
    ``odds_frame`` needs ``runner_id``, ``venue``, ``bookmaker``, ``odds_decimal``.
    """
    if odds_frame.empty:
        return pd.DataFrame(columns=[
            "runner_id", "race_id", "venue", "bookmaker", "odds_decimal", "ev",
        ])
    probs = frame.set_index("runner_id")["blend_prob"].to_dict()
    races = frame.set_index("runner_id")["race_id"].to_dict()

    rows = []
    for record in odds_frame.itertuples(index=False):
        prob = probs.get(record.runner_id)
        if prob is None or record.odds_decimal <= 1.0:
            continue
        rows.append({
            "runner_id": record.runner_id,
            "race_id": races.get(record.runner_id),
            "venue": record.venue,
            "bookmaker": getattr(record, "bookmaker", None),
            "odds_decimal": float(record.odds_decimal),
            "ev": price_runner(prob, float(record.odds_decimal), record.venue,
                               settings.exchange_commission),
        })
    priced = pd.DataFrame(rows)
    if priced.empty:
        return priced
    return priced.sort_values("ev", ascending=False).reset_index(drop=True)


def find_value(frame: pd.DataFrame, odds_frame: pd.DataFrame,
               settings: Settings) -> list[Suggestion]:
    """Select the qualifying value bets from priced runners.

    At most one suggestion per runner (the best-EV venue). Runners failing
    the probability or odds filters are excluded before pricing decisions
    are made, so a huge apparent edge on a 100/1 shot can never qualify.
    """
    if frame.empty:
        return []

    priced = evaluate_prices(frame, odds_frame, settings)
    if priced.empty:
        return []

    info = frame.set_index("runner_id")
    suggestions: list[Suggestion] = []

    for runner_id, group in priced.groupby("runner_id", sort=False):
        if runner_id not in info.index:
            continue
        row = info.loc[runner_id]
        prob = float(row["blend_prob"])
        if prob < settings.min_prob:
            continue
        # A near-certainty means the race has been stripped to one runner, or
        # the card parsed badly -- not that we have found a free bet.
        if prob > settings.max_prob:
            continue

        eligible = group[group["odds_decimal"] <= settings.max_odds]
        if eligible.empty:
            continue
        best = eligible.loc[eligible["ev"].idxmax()]
        if float(best["ev"]) < settings.min_edge:
            continue

        commission = settings.exchange_commission if best["venue"] == "exchange" else 0.0
        market_prob = float(row.get("market_prob", np.nan))
        suggestions.append(Suggestion(
            runner_id=int(runner_id),
            race_id=int(row["race_id"]),
            model_prob=float(row.get("model_prob", prob)),
            blend_prob=prob,
            fair_odds=fair_odds(prob, commission),
            advised_odds=float(best["odds_decimal"]),
            price_floor=price_floor_for(prob, settings.min_edge, commission),
            venue=str(best["venue"]),
            bookmaker=best["bookmaker"] if pd.notna(best["bookmaker"]) else None,
            ev=float(best["ev"]),
            market_prob=market_prob,
            edge_vs_market=prob - market_prob if not np.isnan(market_prob) else float("nan"),
            alternatives=[
                {
                    "venue": r.venue,
                    "bookmaker": r.bookmaker if pd.notna(r.bookmaker) else None,
                    "odds": float(r.odds_decimal),
                    "ev": float(r.ev),
                }
                for r in group.itertuples(index=False)
            ],
        ))

    suggestions.sort(key=lambda s: s.ev, reverse=True)
    return suggestions
