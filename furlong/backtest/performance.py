"""Live performance reporting: what the advised bets actually did.

Closing line value leads, profit follows. Beating the closing price is
detectable in tens of bets; proving a 4% edge from profit alone needs
7,000-23,000. A report that leads with P/L over a few hundred bets is
telling the reader a story about variance and calling it skill.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from furlong.backtest.report import is_significant
from furlong.config import Settings
from furlong.db import init_db

SETTLED_QUERY = """
SELECT s.id, s.date, s.runner_id, s.race_id, s.advised_odds, s.price_floor,
       s.stake_units, s.venue, s.bookmaker, s.blend_prob, s.market_prob,
       s.ev, t.result, t.pl_units, t.bsp_at_off, t.clv, t.rule4_deduction,
       h.name AS horse, c.name AS course, c.country AS country
FROM suggestions s
JOIN settlements t ON t.suggestion_id = s.id
JOIN runners r ON r.id = s.runner_id
JOIN horses h ON h.id = r.horse_id
JOIN races ra ON ra.id = s.race_id
JOIN courses c ON c.id = ra.course_id
ORDER BY s.date, s.id
"""


def load_settled(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(SETTLED_QUERY, conn)


def compute_performance(conn: sqlite3.Connection) -> dict:
    settled = load_settled(conn)
    open_count = conn.execute(
        "SELECT COUNT(*) n FROM suggestions WHERE status='open'"
    ).fetchone()["n"]
    withdrawn_count = conn.execute(
        "SELECT COUNT(*) n FROM suggestions WHERE status='withdrawn'"
    ).fetchone()["n"]

    if settled.empty:
        return {
            "n_settled": 0, "n_open": int(open_count),
            "n_withdrawn": int(withdrawn_count),
            "note": "no settled suggestions yet",
            "monthly": [], "cumulative": [],
        }

    staked = settled[settled["result"] != "void"]
    total_staked = float(staked["stake_units"].sum())
    profit = float(settled["pl_units"].sum())
    clv_values = settled["clv"].dropna()

    settled = settled.sort_values(["date", "id"]).reset_index(drop=True)
    settled["cumulative_pl"] = settled["pl_units"].cumsum()
    peak = np.maximum.accumulate(
        np.concatenate(([0.0], settled["cumulative_pl"].to_numpy()))
    )[1:]
    drawdown = peak - settled["cumulative_pl"].to_numpy()

    streak = longest = 0
    for result in settled["result"]:
        streak = 0 if result in ("won", "deadheat", "void") else streak + 1
        longest = max(longest, streak)

    monthly = (
        settled.assign(month=pd.to_datetime(settled["date"]).dt.to_period("M").astype(str))
        .groupby("month")
        .agg(bets=("id", "size"),
             winners=("result", lambda s: int((s == "won").sum())),
             staked=("stake_units", "sum"),
             profit=("pl_units", "sum"),
             mean_clv=("clv", "mean"))
        .reset_index()
    )
    monthly["roi"] = monthly["profit"] / monthly["staked"].replace(0, np.nan)

    flat_returns = np.where(
        settled["result"].isin(["won", "deadheat"]),
        settled["advised_odds"] - 1.0,
        np.where(settled["result"] == "void", 0.0, -1.0),
    )
    flat_roi = float(flat_returns.mean())
    flat_se = (
        float(flat_returns.std(ddof=1) / np.sqrt(len(flat_returns)))
        if len(flat_returns) > 1 else float("nan")
    )

    return {
        "n_settled": int(len(settled)),
        "n_open": int(open_count),
        "n_withdrawn": int(withdrawn_count),
        "n_won": int((settled["result"] == "won").sum()),
        "n_void": int((settled["result"] == "void").sum()),
        "strike_rate": float((settled["result"] == "won").mean()),
        "staked_units": total_staked,
        "profit_units": profit,
        "roi": profit / total_staked if total_staked else 0.0,
        "flat_stake_roi": flat_roi,
        "flat_stake_roi_se": flat_se,
        "roi_is_significant": is_significant(flat_roi, flat_se, len(settled)),
        # The headline metric: did we beat the closing price?
        "mean_clv": float(clv_values.mean()) if len(clv_values) else None,
        "pct_beat_close": (
            float((clv_values > 1.0).mean()) if len(clv_values) else None
        ),
        "n_with_clv": int(len(clv_values)),
        "max_drawdown_units": float(drawdown.max()),
        "longest_losing_run": int(longest),
        "monthly": monthly.round(5).to_dict(orient="records"),
        "cumulative": settled[["date", "cumulative_pl"]].round(4).to_dict(orient="records"),
        "by_country": _breakdown(settled, "country"),
    }


def _breakdown(settled: pd.DataFrame, column: str) -> list[dict]:
    grouped = settled.groupby(column).agg(
        bets=("id", "size"),
        winners=("result", lambda s: int((s == "won").sum())),
        staked=("stake_units", "sum"),
        profit=("pl_units", "sum"),
        mean_clv=("clv", "mean"),
    )
    grouped["roi"] = grouped["profit"] / grouped["staked"].replace(0, np.nan)
    return grouped.reset_index().round(5).to_dict(orient="records")


def write_performance_report(settings: Settings, out_dir: str | None = None) -> dict[str, str]:
    conn = init_db(settings.database_path)
    metrics = compute_performance(conn)
    conn.close()

    directory = Path(out_dir or (Path(settings.data_dir) / "reports"))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "performance.json"
    path.write_text(json.dumps(metrics, indent=2, default=str))
    return {"json": str(path)}
