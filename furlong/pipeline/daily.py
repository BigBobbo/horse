"""The daily run: from today's racecards to a published list of suggestions.

Timing follows the operational research (docs/research/gap-daily-pipeline-
timing-and-price-decay.md). Irish declarations close at 10:00 two days
before racing and GB Flat likewise, so a day's fields are known the evening
before and everything here is a choice about *price availability*, not data
availability:

    19:45  ingest final racecards for tomorrow
    09:00  publish suggestions (Best Odds Guaranteed is live from 08:00-09:00
           at most firms, the overnight pricing errors have been corrected,
           and the professional tipster wave lands around 09:30)
    10:15  rescore after non-runners and Irish reserves declare

Every suggestion carries a price floor because advised prices decay within
minutes of publication: Hugh Taylor's advised average of 10.41 was 7.35 by
the time followers got on, and Smart Betting Club measured ROI losses of
4.5 to 24.5 percentage points within fifteen minutes.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from furlong.config import Settings
from furlong.db import init_db
from furlong.features.builder import FEATURE_COLUMNS, compute_features
from furlong.modeling.market import market_probabilities
from furlong.modeling.train import attach_market, train_on_frames
from furlong.features.dataset import build_dataset
from furlong.value.engine import Suggestion, find_value
from furlong.value.staking import apply_daily_cap, stake_for
from furlong import repo

PUBLISH_LOCAL_TIME = "09:00"

# The blend must be fitted against the same kind of price it will be applied
# to. Betfair SP is the sharpest market in the data, but it does not exist
# when the daily run happens -- live suggestions are priced against the
# morning exchange, which is materially softer. Fitting alpha and beta on
# BSP and applying them to morning prices systematically underweights the
# model: measured on the synthetic world, alpha fitted on BSP is 0.195
# against 0.273 fitted on morning prices, and the corresponding information
# gain over the market is +0.0015 against +0.0042.
LIVE_MARKET_SOURCE = "exchange"


@dataclass
class DailyOutcome:
    date: str
    suggestions: list[Suggestion] = field(default_factory=list)
    races_considered: int = 0
    runners_considered: int = 0
    stakes: list = field(default_factory=list)
    dry_run: bool = False
    message: str | None = None
    written: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "races_considered": self.races_considered,
            "runners_considered": self.runners_considered,
            "n_suggestions": len(self.suggestions),
            "suggestions": [
                {**s.to_dict(), "stake_units": round(float(p.stake_units), 3),
                 "stake_capped_by": p.capped_by}
                for s, p in zip(self.suggestions, self.stakes)
            ],
        }

    def render_terminal(self) -> str:
        if self.message:
            return self.message
        header = (
            f"Furlong suggestions for {self.date} "
            f"({self.races_considered} races, {self.runners_considered} runners considered)"
        )
        if not self.suggestions:
            return (
                f"{header}\n"
                "  No qualifying value bets today. Not betting is a position: on most "
                "days the market is not wrong enough to be worth the risk."
            )
        lines = [header, ""]
        lines.append(
            f"  {'Race':<28} {'Runner':<18} {'Model':>6} {'Mkt':>6} "
            f"{'Price':>7} {'Floor':>7} {'Edge':>7} {'Stake':>6}  Venue"
        )
        for suggestion, plan in zip(self.suggestions, self.stakes):
            meta = getattr(suggestion, "_display", {})
            venue = suggestion.bookmaker or suggestion.venue
            lines.append(
                f"  {meta.get('race', ''):<28} {meta.get('horse', ''):<18} "
                f"{suggestion.blend_prob:>6.1%} {suggestion.market_prob:>6.1%} "
                f"{suggestion.advised_odds:>7.2f} {suggestion.price_floor:>7.2f} "
                f"{suggestion.ev:>+7.1%} {plan.stake_units:>6.2f}  {venue}"
            )
        total = sum(p.stake_units for p in self.stakes)
        lines += [
            "",
            f"  {len(self.suggestions)} suggestion(s), {total:.2f} units staked "
            f"(1 unit = 1% of bankroll).",
            "  Do not take a price below the floor: the value is in the price, and it "
            "decays within minutes.",
        ]
        if self.written:
            lines.append(f"  Written: {', '.join(self.written.values())}")
        return "\n".join(lines)


def _group_sizes(frame: pd.DataFrame) -> np.ndarray:
    _, idx, counts = np.unique(frame["race_id"].to_numpy(), return_index=True,
                               return_counts=True)
    return counts[np.argsort(idx)]


def latest_race_date(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT MAX(date) AS d FROM races").fetchone()
    return row["d"] if row and row["d"] else None


def score_date(settings: Settings, conn: sqlite3.Connection, date: str,
               model_kind: str = "gbm") -> pd.DataFrame:
    """Score every declared runner on ``date`` with model and blended probabilities.

    The model is trained on everything strictly before ``date`` -- the same
    discipline as the backtest, applied live.
    """
    history = build_dataset(conn, where="ra.date < ?", params=(date,))
    if history.frame.empty:
        raise ValueError(f"no completed races before {date} to train on")
    history_frame = attach_market(conn, history.frame, prefer=LIVE_MARKET_SOURCE)

    dates = sorted(history_frame["date"].unique())
    split_idx = max(1, int(len(dates) * 0.85))
    train = history_frame[history_frame["date"].isin(set(dates[:split_idx]))]
    valid = history_frame[history_frame["date"].isin(set(dates[split_idx:]))]
    if valid.empty:
        valid = train

    # Today's runners need features computed against the full history.
    all_runs = repo.load_runs(conn, where="ra.date <= ?", params=(date,))
    features = compute_features(all_runs)
    today = features[
        (features["date"] == date) & (features["status"] == "declared")
    ].copy()
    if today.empty:
        return today

    today = today.sort_values(["start_time_utc", "race_id", "runner_id"]).reset_index(drop=True)
    market = market_probabilities(conn, today, prefer=LIVE_MARKET_SOURCE)
    today = today.merge(market, on="runner_id", how="left", validate="one_to_one")

    trained = train_on_frames(train, valid, valid, kind=model_kind)
    groups = _group_sizes(today)
    model_probs, blend_probs = trained.predict(
        today[FEATURE_COLUMNS].to_numpy(dtype=float), groups,
        today["market_prob"].to_numpy(dtype=float),
    )
    today["model_prob"] = model_probs
    today["blend_prob"] = blend_probs
    return today


def _decorate(conn: sqlite3.Connection, suggestions: list[Suggestion]) -> None:
    """Attach human-readable race/runner labels for terminal and web output."""
    if not suggestions:
        return
    ids = [s.runner_id for s in suggestions]
    placeholders = ", ".join("?" for _ in ids)
    rows = conn.execute(
        f"""SELECT r.id AS runner_id, h.name AS horse, c.name AS course,
                   ra.start_time_utc AS off, ra.going AS going,
                   ra.distance_m AS distance_m, c.country AS country,
                   t.name AS trainer, j.name AS jockey
            FROM runners r
            JOIN races ra ON ra.id = r.race_id
            JOIN courses c ON c.id = ra.course_id
            JOIN horses h ON h.id = r.horse_id
            LEFT JOIN trainers t ON t.id = r.trainer_id
            LEFT JOIN jockeys j ON j.id = r.jockey_id
            WHERE r.id IN ({placeholders})""",
        ids,
    ).fetchall()
    lookup = {row["runner_id"]: dict(row) for row in rows}
    for suggestion in suggestions:
        info = lookup.get(suggestion.runner_id, {})
        off = str(info.get("off", ""))[11:16]
        suggestion._display = {
            "race": f"{info.get('course', '?')} {off}",
            "horse": info.get("horse", "?"),
            "course": info.get("course"),
            "country": info.get("country"),
            "off": off,
            "trainer": info.get("trainer"),
            "jockey": info.get("jockey"),
            "going": info.get("going"),
        }


def run_daily(settings: Settings, date: str | None = None, dry_run: bool = False,
              out_dir: str | None = None, model_kind: str = "gbm") -> DailyOutcome:
    """Produce (and persist) today's suggestions."""
    conn = init_db(settings.database_path)

    from furlong.sources.base import get_source

    target = date or latest_race_date(conn)
    if target is None:
        conn.close()
        return DailyOutcome(date="", message="No racing data available. Run `furlong generate` "
                                             "or configure a data source first.")

    source = get_source(settings)
    source.sync_daily(settings, conn, target)

    declared = conn.execute(
        """SELECT COUNT(*) AS n FROM runners r JOIN races ra ON ra.id = r.race_id
           WHERE ra.date = ? AND r.status = 'declared'""",
        (target,),
    ).fetchone()["n"]
    if not declared:
        conn.close()
        return DailyOutcome(
            date=target,
            message=f"No declared runners for {target}: nothing to advise. "
                    "(Racecards are normally available from 10:00 two days before racing.)",
        )

    scored = score_date(settings, conn, target, model_kind=model_kind)
    if scored.empty:
        conn.close()
        return DailyOutcome(date=target, message=f"No runners to score for {target}.")

    race_ids = sorted(set(int(r) for r in scored["race_id"]))
    odds = repo.load_latest_odds(conn, race_ids)
    suggestions = find_value(scored, odds, settings)
    _decorate(conn, suggestions)

    plans = [
        stake_for(
            s.blend_prob, s.advised_odds, settings,
            commission=settings.exchange_commission if s.venue == "exchange" else 0.0,
        )
        for s in suggestions
    ]
    plans = apply_daily_cap(plans, settings)

    outcome = DailyOutcome(
        date=target,
        suggestions=suggestions,
        stakes=plans,
        races_considered=len(race_ids),
        runners_considered=len(scored),
        dry_run=dry_run,
    )

    if not dry_run:
        _persist(conn, target, suggestions, plans)
        outcome.written = _write_outputs(settings, outcome, out_dir)
    conn.commit()
    conn.close()
    return outcome


def _persist(conn: sqlite3.Connection, date: str, suggestions: list[Suggestion],
             plans: list) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for suggestion, plan in zip(suggestions, plans):
        conn.execute(
            """INSERT INTO suggestions (date, race_id, runner_id, model_prob, blend_prob,
                   market_prob, fair_odds, advised_odds, price_floor, venue, bookmaker,
                   ev, stake_units, status, created_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
               ON CONFLICT(date, runner_id) DO UPDATE SET
                   model_prob=excluded.model_prob, blend_prob=excluded.blend_prob,
                   market_prob=excluded.market_prob,
                   fair_odds=excluded.fair_odds, advised_odds=excluded.advised_odds,
                   price_floor=excluded.price_floor, venue=excluded.venue,
                   bookmaker=excluded.bookmaker, ev=excluded.ev,
                   stake_units=excluded.stake_units""",
            (date, suggestion.race_id, suggestion.runner_id, suggestion.model_prob,
             suggestion.blend_prob, suggestion.market_prob, suggestion.fair_odds,
             suggestion.advised_odds, suggestion.price_floor, suggestion.venue,
             suggestion.bookmaker, suggestion.ev, plan.stake_units, now),
        )


def _write_outputs(settings: Settings, outcome: DailyOutcome,
                   out_dir: str | None) -> dict:
    directory = Path(out_dir or (Path(settings.data_dir) / "suggestions"))
    directory.mkdir(parents=True, exist_ok=True)
    payload = outcome.to_dict()
    for suggestion, entry in zip(outcome.suggestions, payload["suggestions"]):
        entry.update(getattr(suggestion, "_display", {}))
    json_path = directory / f"suggestions-{outcome.date}.json"
    json_path.write_text(json.dumps(payload, indent=2))
    return {"json": str(json_path)}
