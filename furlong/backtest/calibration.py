"""Is the market already calibrated against our features?

The alpha = 0 test says whether the model beats the market. It does not say
*why*, and "why" is what decides the next move: a model that loses because
its features are weak needs better features, while a model that loses because
the market has already priced those features needs a different market.

This answers the second question directly. For each feature, runners are
sorted into bins and each bin's actual win rate is compared with the mean
probability the market assigned. If the market is efficient with respect to
a feature, the two agree in every bin however strongly the feature sorts
winners -- and the gap between them, in percentage points, is the entire
edge available from knowing it.

Measured on 253,783 Betfair-priced UK and Irish runners, recent form sorts
win rate from 7.2% to 17.9% and the market's implied probability tracks it to
within 0.15 percentage points in every bin. That is the finding this module
exists to make reproducible.

Read it with the standard error, never without: with eight bins over a
handful of features, one or two z-scores above 2 are what pure noise looks
like, and `flagged` counts them against that expectation rather than
reporting each as a discovery.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from furlong.config import Settings
from furlong.db import init_db
from furlong.features.builder import FEATURE_COLUMNS
from furlong.features.dataset import build_dataset
from furlong.modeling.train import attach_market

DEFAULT_BINS = 8

# |z| above this is worth a second look -- not a discovery. See flagged_note.
Z_FLAG = 2.0


@dataclass
class FeatureCalibration:
    feature: str
    bins: list[dict]
    # True when the feature takes one value for every runner in a race
    # (field size, race class, code). Such a feature cannot price anything --
    # it cancels in the per-race softmax -- and it is trivially calibrated,
    # because binning by it groups whole races and a book sums to 1 by
    # construction. Reported, but never as available edge.
    race_constant: bool = False

    @property
    def max_abs_z(self) -> float:
        return max((abs(b["z"]) for b in self.bins if b["z"] is not None), default=0.0)

    @property
    def spread_pp(self) -> float:
        """How strongly the feature sorts winners, in percentage points."""
        rates = [b["actual"] for b in self.bins]
        return (max(rates) - min(rates)) * 100 if rates else 0.0

    @property
    def worst_gap_pp(self) -> float:
        """The largest bin gap between actual and market-implied win rate."""
        return max((abs(b["diff_pp"]) for b in self.bins), default=0.0)


def calibrate(frame: pd.DataFrame, features: list[str] | None = None,
              bins: int = DEFAULT_BINS) -> list[FeatureCalibration]:
    """Bin each feature and compare actual win rate with the market's."""
    columns = features or list(FEATURE_COLUMNS)
    frame = frame[frame["market_priced"] & (frame["market_prob"] > 0)].copy()
    frame["won"] = (frame["win_flag"] == 1).astype(float)

    results: list[FeatureCalibration] = []
    for column in columns:
        if column not in frame:
            continue
        values = frame[column].to_numpy(dtype=float)
        # A feature that is constant on this source -- as trainer and going
        # features are on a results-and-prices archive -- has nothing to bin.
        if not np.isfinite(values).any() or len(np.unique(values[np.isfinite(values)])) < 2:
            continue
        try:
            labels = pd.qcut(frame[column], bins, labels=False, duplicates="drop")
        except ValueError:
            continue
        spread_within_race = (
            frame.groupby("race_id")[column].transform("std").fillna(0.0)
        )
        race_constant = bool(spread_within_race.max() < 1e-9)

        rows = []
        for label, group in frame.groupby(labels, sort=True):
            n = len(group)
            actual = float(group["won"].mean())
            implied = float(group["market_prob"].mean())
            # Binomial standard error on the observed rate. The market's mean
            # is treated as fixed: it is an average over 30,000 quoted prices,
            # so its own error is negligible beside the win-rate estimate.
            se = math.sqrt(actual * (1 - actual) / n) if n and 0 < actual < 1 else None
            diff_pp = (actual - implied) * 100
            rows.append({
                "bin": int(label),
                "n": n,
                "actual": actual,
                "implied": implied,
                "diff_pp": diff_pp,
                "se_pp": se * 100 if se else None,
                "z": diff_pp / (se * 100) if se else None,
            })
        if rows:
            results.append(FeatureCalibration(feature=column, bins=rows,
                                              race_constant=race_constant))

    # Race-constant features last: they are trivially calibrated and cannot
    # price anything, so they must not head a table about available edge.
    results.sort(key=lambda r: (r.race_constant, -r.spread_pp))
    return results


def flagged_note(results: list[FeatureCalibration]) -> str:
    """What the count of large z-scores means against the count of tests run."""
    scored = [r for r in results if not r.race_constant]
    tests = sum(1 for r in scored for b in r.bins if b["z"] is not None)
    flagged = sum(1 for r in scored for b in r.bins
                  if b["z"] is not None and abs(b["z"]) > Z_FLAG)
    # Two-sided normal tail at |z| > 2.
    expected = tests * 0.0455
    verdict = ("about what noise alone produces"
               if flagged <= expected * 1.5 else
               "more than noise alone produces -- worth investigating")
    return (f"{flagged} of {tests} bins exceed |z| > {Z_FLAG:.0f}; "
            f"{expected:.1f} expected by chance. That is {verdict}.")


def run_calibration(settings: Settings, features: list[str] | None = None,
                    bins: int = DEFAULT_BINS) -> dict:
    conn = init_db(settings.database_path)
    frame = attach_market(conn, build_dataset(conn).frame, prefer="bsp")
    conn.close()
    results = calibrate(frame, features=features, bins=bins)
    priced = int((frame["market_priced"] & (frame["market_prob"] > 0)).sum())
    return {
        "runners": priced,
        "features": [{"feature": r.feature, "spread_pp": r.spread_pp,
                      "worst_gap_pp": r.worst_gap_pp, "max_abs_z": r.max_abs_z,
                      "race_constant": r.race_constant, "bins": r.bins}
                     for r in results],
        "note": flagged_note(results),
    }


def render(report: dict, top: int = 8) -> str:
    lines = [
        f"Market calibration over {report['runners']:,} priced runners",
        "  How strongly each feature sorts winners, and how much of that the "
        "market has already priced.",
        "",
        f"  {'feature':<26}{'sorts (pp)':>12}{'worst gap':>12}{'max |z|':>10}",
    ]
    for entry in report["features"][:top]:
        marker = "  (race-constant)" if entry["race_constant"] else ""
        lines.append(
            f"  {entry['feature']:<26}{entry['spread_pp']:>12.1f}"
            f"{entry['worst_gap_pp']:>12.2f}{entry['max_abs_z']:>10.2f}{marker}"
        )
    lines += [
        "",
        "  'sorts' is the spread in actual win rate from the lowest to the "
        "highest bin.",
        "  'worst gap' is the largest bin difference between the actual win "
        "rate and the",
        "  market's implied one, in percentage points -- the edge available "
        "from the feature.",
        "",
        f"  {report['note']}",
    ]
    return "\n".join(lines)
