"""The 10:15 rescore: what changes when horses come out.

Non-runners are a first-order problem, not an edge case. British data puts
withdrawals at 8-9% of declarations (Flat turf 10-11%, driven by the
48-hour declaration window leaving two days for the ground to change), and
Irish racing adds up to three published reserves per race who declare in by
10:00 or 11:00 on the day. A card scored at 09:00 is therefore provisional.

When a runner comes out, the remaining probabilities must be renormalised
within the race, the value recomputed, and any suggestion whose edge has
collapsed withdrawn with a reason. Suggestions already settled are never
touched.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

from furlong.config import Settings
from furlong.db import init_db
from furlong.value.devig import expected_value
from furlong.value.engine import price_floor_for
from furlong.value.staking import stake_for


@dataclass
class RescoreOutcome:
    date: str
    non_runners: int = 0
    unchanged: int = 0
    repriced: int = 0
    withdrawn: list = field(default_factory=list)
    voided: list = field(default_factory=list)
    message: str | None = None

    def render_terminal(self) -> str:
        if self.message:
            return self.message
        lines = [
            f"Rescore for {self.date}: {self.non_runners} non-runner(s) affecting "
            f"{self.repriced + len(self.withdrawn) + len(self.voided)} suggestion(s)"
        ]
        for entry in self.voided:
            lines.append(f"  VOID      {entry['horse']}: withdrawn from the race")
        for entry in self.withdrawn:
            lines.append(
                f"  WITHDRAWN {entry['horse']}: edge fell to {entry['ev']:+.1%} "
                f"after non-runners (floor was {entry['price_floor']:.2f})"
            )
        if self.repriced:
            lines.append(f"  {self.repriced} suggestion(s) repriced and still qualifying")
        if self.unchanged and not self.non_runners:
            lines.append("  No non-runners: nothing to change.")
        return "\n".join(lines)


def _renormalise_race(conn: sqlite3.Connection, race_id: int,
                      date: str) -> dict[int, float]:
    """Redistribute a withdrawn runner's probability across those still standing.

    This reads the *whole* scored card, not just the runners we backed. The
    horse that comes out is usually one we never suggested, and its released
    probability still has to go somewhere -- renormalising over our own
    selections alone would leave their chances unchanged, which is the one
    thing the 10:15 run exists to prevent.
    """
    rows = conn.execute(
        """SELECT sc.runner_id, sc.blend_prob, r.status
           FROM race_scores sc JOIN runners r ON r.id = sc.runner_id
           WHERE sc.race_id = ? AND sc.date = ?""",
        (race_id, date),
    ).fetchall()
    if not rows:
        return {}

    standing = {r["runner_id"]: float(r["blend_prob"])
                for r in rows if r["status"] != "nonrunner"}
    total_standing = sum(standing.values())
    if total_standing <= 0:
        return {}
    # Standard market convention: the field is renormalised in proportion to
    # the remaining runners' existing chances.
    return {runner_id: min(prob / total_standing, 0.99)
            for runner_id, prob in standing.items()}


def run_rescore(settings: Settings, date: str) -> RescoreOutcome:
    """Re-run the value test for ``date`` after non-runners are known."""
    conn = init_db(settings.database_path)
    outcome = RescoreOutcome(date=date)

    open_suggestions = conn.execute(
        """SELECT s.id, s.runner_id, s.race_id, s.blend_prob, s.advised_odds, s.venue,
                  s.ev, s.price_floor, r.status AS runner_status, h.name AS horse
           FROM suggestions s
           JOIN runners r ON r.id = s.runner_id
           JOIN horses h ON h.id = r.horse_id
           WHERE s.date = ? AND s.status = 'open'""",
        (date,),
    ).fetchall()
    if not open_suggestions:
        conn.close()
        outcome.message = f"No open suggestions for {date}."
        return outcome

    outcome.non_runners = conn.execute(
        """SELECT COUNT(*) AS n FROM runners r JOIN races ra ON ra.id = r.race_id
           WHERE ra.date = ? AND r.status = 'nonrunner'""",
        (date,),
    ).fetchone()["n"]

    affected_races = {row["race_id"] for row in open_suggestions}
    new_probs: dict[int, float] = {}
    for race_id in affected_races:
        new_probs.update(_renormalise_race(conn, race_id, date))

    for row in open_suggestions:
        # Our own selection came out: the bet is void, not merely bad.
        if row["runner_status"] == "nonrunner":
            conn.execute(
                "UPDATE suggestions SET status='withdrawn', reason=? WHERE id=?",
                ("non-runner", row["id"]),
            )
            outcome.voided.append({"horse": row["horse"], "runner_id": row["runner_id"]})
            continue

        prob = new_probs.get(row["runner_id"], float(row["blend_prob"]))
        commission = settings.exchange_commission if row["venue"] == "exchange" else 0.0
        ev = expected_value(prob, float(row["advised_odds"]), commission)

        if ev < settings.min_edge or prob < settings.min_prob:
            conn.execute(
                "UPDATE suggestions SET status='withdrawn', reason=? WHERE id=?",
                (f"edge fell to {ev:+.3f} after non-runners", row["id"]),
            )
            outcome.withdrawn.append({
                "horse": row["horse"], "runner_id": row["runner_id"],
                "ev": ev, "price_floor": float(row["price_floor"]),
            })
            continue

        plan = stake_for(prob, float(row["advised_odds"]), settings, commission=commission)
        conn.execute(
            """UPDATE suggestions SET blend_prob=?, ev=?, price_floor=?, stake_units=?
               WHERE id=?""",
            (prob, ev, price_floor_for(prob, settings.min_edge, commission),
             plan.stake_units, row["id"]),
        )
        if abs(prob - float(row["blend_prob"])) > 1e-9:
            outcome.repriced += 1
        else:
            outcome.unchanged += 1

    conn.commit()
    conn.close()
    return outcome
