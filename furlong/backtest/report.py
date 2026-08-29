"""Backtest reporting: the numbers that tell you whether to believe it.

Reports lead with the honest metrics — drawdown, longest losing run, and
the standard error on ROI — because a positive headline ROI over a few
hundred bets means very little. At a genuine 4% edge and average odds of
5.0, a 1,000-bet year still finishes in the red about a quarter of the
time, and proving the edge from profit alone takes 7,000 bets or more.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

from furlong.backtest.engine import BacktestResult

# A profit figure cannot be called significant on a handful of bets, and a
# run of identical outcomes (five losers, say) has zero sample variance --
# which would otherwise make any ROI look infinitely significant. The
# research is blunt about the real requirement: proving a 4% edge at odds
# around 5.0 needs 7,000+ bets. This threshold is only a floor below which
# the question is not worth asking.
MIN_BETS_FOR_SIGNIFICANCE = 100


def json_safe(value):
    """Recursively replace non-finite floats with None.

    NaN is a normal outcome here -- the mean CLV of bets with no Betfair SP
    yet, the standard error of a single bet -- but it is not valid JSON, and
    Starlette serialises with allow_nan=False, so leaving it in returns a
    500 from the API and writes report files no strict parser will read.
    """
    import math

    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.floating):
        return json_safe(float(value))
    if isinstance(value, np.integer):
        return int(value)
    return value


def is_significant(roi: float, standard_error: float, n_bets: int) -> bool:
    """Two-standard-error test, with sample-size and zero-variance guards."""
    if n_bets < MIN_BETS_FOR_SIGNIFICANCE:
        return False
    if not standard_error > 0 or standard_error != standard_error:  # 0 or NaN
        return False
    return abs(roi) > 2 * standard_error



def compute_metrics(result: BacktestResult) -> dict:
    bets = result.bets
    if bets.empty:
        return {"n_bets": 0, "note": "no qualifying bets"}

    pl = bets["pl"].to_numpy(dtype=float)
    stakes = bets["stake"].to_numpy(dtype=float)
    flat = bets["pl_flat"].to_numpy(dtype=float)
    cumulative = np.cumsum(pl)
    running_max = np.maximum.accumulate(np.concatenate(([0.0], cumulative)))[1:]
    drawdown = running_max - cumulative

    losing_streak = longest = 0
    for won in bets["won"].to_numpy():
        losing_streak = 0 if won else losing_streak + 1
        longest = max(longest, losing_streak)

    roi = float(pl.sum() / stakes.sum())
    flat_roi = float(flat.mean())
    # Standard error of the flat-stake ROI: the honesty check on the headline.
    flat_se = float(flat.std(ddof=1) / np.sqrt(len(flat))) if len(flat) > 1 else float("nan")

    by_odds = _breakdown(bets, pd.cut(bets["odds"], [1, 3, 6, 11, 21, np.inf]))
    by_country = _breakdown(bets, bets["country"])
    monthly = _breakdown(bets, pd.to_datetime(bets["date"]).dt.to_period("M").astype(str))

    return {
        "n_bets": int(len(bets)),
        "n_winners": int(bets["won"].sum()),
        "strike_rate": float(bets["won"].mean()),
        "total_staked_units": float(stakes.sum()),
        "profit_units": float(pl.sum()),
        "roi": roi,
        "flat_stake_roi": flat_roi,
        "flat_stake_roi_se": flat_se,
        "roi_is_significant": is_significant(flat_roi, flat_se, len(bets)),
        "naive_back_all_roi": result.naive_roi(),
        "edge_over_naive": flat_roi - result.naive_roi(),
        "max_drawdown_units": float(drawdown.max()),
        "longest_losing_run": int(longest),
        "mean_clv": float(bets["clv"].mean()),
        "avg_odds": float(bets["odds"].mean()),
        "avg_edge": float(bets["ev"].mean()),
        "bets_per_race_pct": None,
        "by_odds_band": by_odds,
        "by_country": by_country,
        "by_month": monthly,
        "folds": result.folds,
        "settings": result.settings_snapshot,
    }


def _breakdown(bets: pd.DataFrame, grouper) -> list[dict]:
    grouped = bets.groupby(grouper, observed=True).agg(
        bets=("pl", "size"),
        winners=("won", "sum"),
        staked=("stake", "sum"),
        profit=("pl", "sum"),
        flat_roi=("pl_flat", "mean"),
    )
    grouped["roi"] = grouped["profit"] / grouped["staked"].replace(0, np.nan)
    grouped = grouped.reset_index()
    grouped.columns = ["group", *grouped.columns[1:]]
    grouped["group"] = grouped["group"].astype(str)
    return grouped.round(5).to_dict(orient="records")


def write_report(result: BacktestResult, out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    metrics = compute_metrics(result)

    json_path = out / "backtest.json"
    json_path.write_text(json.dumps(json_safe(metrics), indent=2, default=str,
                                    allow_nan=False))

    if not result.bets.empty:
        result.bets.to_csv(out / "backtest_bets.csv", index=False)

    html_path = out / "backtest.html"
    html_path.write_text(_render_html(metrics))
    return {"json": str(json_path), "html": str(html_path)}


def _render_html(metrics: dict) -> str:
    if metrics.get("n_bets", 0) == 0:
        body = "<p>No qualifying bets were produced.</p>"
    else:
        significance = (
            "statistically significant at 2 SE"
            if metrics["roi_is_significant"]
            else "NOT statistically significant — treat as provisional"
        )
        body = f"""
        <table class="kv">
          <tr><th>Bets</th><td>{metrics['n_bets']:,}</td></tr>
          <tr><th>Winners</th><td>{metrics['n_winners']:,} ({metrics['strike_rate']:.1%})</td></tr>
          <tr><th>ROI (staked)</th><td>{metrics['roi']:+.2%}</td></tr>
          <tr><th>ROI (flat stakes)</th><td>{metrics['flat_stake_roi']:+.2%}
              &plusmn; {metrics['flat_stake_roi_se']:.2%} (1 SE) — {significance}</td></tr>
          <tr><th>Naive back-everything</th><td>{metrics['naive_back_all_roi']:+.2%}</td></tr>
          <tr><th>Edge over naive</th><td>{metrics['edge_over_naive']:+.2%}</td></tr>
          <tr><th>Max drawdown</th><td>{metrics['max_drawdown_units']:.1f} units</td></tr>
          <tr><th>Longest losing run</th><td>{metrics['longest_losing_run']} bets</td></tr>
          <tr><th>Average odds</th><td>{metrics['avg_odds']:.2f}</td></tr>
        </table>
        <h2>By odds band</h2>{_table(metrics['by_odds_band'])}
        <h2>By country</h2>{_table(metrics['by_country'])}
        <h2>By month</h2>{_table(metrics['by_month'])}
        <h2>Folds</h2>{_table(metrics['folds'])}
        """
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Furlong backtest</title>
<style>
 body {{ font: 15px/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 60rem;
        color: #1a1a1a; }}
 table {{ border-collapse: collapse; margin: 1rem 0; width: 100%; }}
 th, td {{ text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #ddd; }}
 table.kv th {{ width: 16rem; }}
 .caveat {{ background: #fff8e1; border-left: 4px solid #f0b429; padding: .8rem 1rem; }}
</style></head><body>
<h1>Furlong backtest</h1>
<p class="caveat"><strong>Read the standard error before the ROI.</strong> A few hundred
bets cannot establish an edge: at a genuine 4% edge and average odds of 5.0, one year in
four still finishes in the red. Closing line value converges far faster than profit.</p>
{body}
</body></html>"""


def _table(rows: list[dict]) -> str:
    if not rows:
        return "<p>(none)</p>"
    headers = list(rows[0].keys())
    head = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(
            f"<td>{html.escape(_fmt(row.get(h)))}</td>" for h in headers
        ) + "</tr>"
        for row in rows
    )
    return f"<table><tr>{head}</tr>{body}</table>"


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:,.4f}"
    return str(value)
