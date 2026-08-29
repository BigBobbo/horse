"""Settling suggestions: results, non-runners, Rule 4, dead heats, and CLV.

Closing line value (advised odds / Betfair SP) is the metric that matters.
Proving a 4% edge from profit and loss alone needs 7,000-23,000 bets; CLV
separates skill from luck in tens. Every settled bet therefore records both
its P/L and its CLV against BSP.

Rule 4 (Tattersalls Rule 4c) deductions apply when a horse is withdrawn
after a price has been taken and there is no time to re-form the market.
The deduction scales with the withdrawn horse's price.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from furlong.config import Settings
from furlong.db import init_db

# Tattersalls Rule 4c: (upper bound of withdrawn horse's decimal odds,
# deduction from net winnings). Bands are inclusive of the upper bound.
RULE_4_TABLE: list[tuple[float, float]] = [
    (1.30, 0.75),
    (1.40, 0.70),
    (1.53, 0.65),
    (1.62, 0.60),
    (1.80, 0.55),
    (1.95, 0.50),
    (2.20, 0.45),
    (2.50, 0.40),
    (2.75, 0.35),
    (3.25, 0.30),
    (4.00, 0.25),
    (4.50, 0.20),
    (6.00, 0.15),
    (8.00, 0.10),
    (11.00, 0.05),
]
RULE_4_MIN_ODDS = 11.0  # no deduction for withdrawals priced above this


def rule4_deduction(withdrawn_odds: float | None) -> float:
    """Deduction from net winnings for one withdrawn runner (0 to 0.75)."""
    if withdrawn_odds is None or withdrawn_odds > RULE_4_MIN_ODDS:
        return 0.0
    for upper, deduction in RULE_4_TABLE:
        if withdrawn_odds <= upper:
            return deduction
    return 0.0


def combined_rule4(withdrawn_odds: list[float]) -> float:
    """Total deduction for multiple withdrawals, capped at 0.75 as per the rules."""
    total = sum(rule4_deduction(o) for o in withdrawn_odds)
    return min(total, 0.75)


@dataclass
class BetOutcome:
    result: str          # 'won' | 'lost' | 'void' | 'deadheat'
    pl_units: float
    clv: float | None
    rule4_deduction: float = 0.0


def settle_bet(stake_units: float, advised_odds: float, won: bool,
               commission: float = 0.0, voided: bool = False,
               rule4: float = 0.0, dead_heat_runners: int = 1,
               bsp: float | None = None) -> BetOutcome:
    """Settle one bet.

    ``voided`` covers non-runners: the stake is returned, P/L is zero.
    ``dead_heat_runners`` > 1 divides the stake by the number of horses
    dead-heating; the losing portion is lost.
    """
    clv = (advised_odds / bsp) if (bsp and bsp > 1.0) else None

    if voided:
        # A withdrawn runner has no closing line to have beaten, so it
        # contributes no CLV -- counting it would dilute the one metric that
        # converges fast enough to be worth watching.
        return BetOutcome(result="void", pl_units=0.0, clv=None, rule4_deduction=0.0)

    if not won:
        return BetOutcome(result="lost", pl_units=-stake_units, clv=clv,
                          rule4_deduction=rule4)

    net_odds = (advised_odds - 1.0) * (1.0 - rule4)
    gross_profit = stake_units * net_odds * (1.0 - commission)

    if dead_heat_runners > 1:
        # Only 1/n of the stake wins; the rest is lost.
        winning_part = stake_units / dead_heat_runners
        losing_part = stake_units - winning_part
        profit = winning_part * net_odds * (1.0 - commission) - losing_part
        return BetOutcome(result="deadheat", pl_units=profit, clv=clv,
                          rule4_deduction=rule4)

    return BetOutcome(result="won", pl_units=gross_profit, clv=clv,
                      rule4_deduction=rule4)


@dataclass
class SettlementResult:
    settled: int = 0
    won: int = 0
    lost: int = 0
    void: int = 0
    pl_units: float = 0.0
    mean_clv: float | None = None

    def summary(self) -> str:
        roi = ""
        if self.settled - self.void > 0:
            roi = f" · P/L {self.pl_units:+.2f}u"
        clv = f" · mean CLV {self.mean_clv:.3f}" if self.mean_clv else ""
        return (f"Settled {self.settled} suggestion(s): {self.won} won, "
                f"{self.lost} lost, {self.void} void{roi}{clv}")


def settle_suggestions(settings: Settings, date: str | None = None) -> SettlementResult:
    """Settle open suggestions against stored results and BSP."""
    conn = init_db(settings.database_path)
    where = "s.status = 'open'"
    params: tuple = ()
    if date:
        where += " AND s.date = ?"
        params = (date,)

    rows = conn.execute(
        f"""SELECT s.id, s.runner_id, s.race_id, s.advised_odds, s.stake_units, s.venue,
                   r.status AS runner_status, r.win_flag, r.finish_pos,
                   b.bsp AS bsp, ra.status AS race_status
            FROM suggestions s
            JOIN runners r ON r.id = s.runner_id
            JOIN races ra ON ra.id = s.race_id
            LEFT JOIN bsp_prices b ON b.runner_id = s.runner_id AND b.market = 'win'
            WHERE {where}""",
        params,
    ).fetchall()

    result = SettlementResult()
    clvs: list[float] = []
    now = datetime.now(timezone.utc).isoformat()

    for row in rows:
        if row["race_status"] != "result":
            continue  # race has not been run yet

        # Rule 4 is a Tattersalls *bookmaker* rule: the exchange voids and
        # re-forms the market instead, so an exchange bet is never deducted.
        # The withdrawn horse's price comes from the last odds snapshot taken
        # before it came out -- it has no Betfair SP, precisely because it
        # was withdrawn from the market.
        rule4 = 0.0
        if row["venue"] == "book":
            withdrawn = conn.execute(
                """SELECT (SELECT o.odds_decimal FROM odds_snapshots o
                           WHERE o.runner_id = r.id AND o.venue = 'book'
                           ORDER BY o.ts_utc DESC LIMIT 1) AS last_price
                   FROM runners r
                   WHERE r.race_id = ? AND r.status = 'nonrunner'""",
                (row["race_id"],),
            ).fetchall()
            rule4 = combined_rule4([w["last_price"] for w in withdrawn if w["last_price"]])

        dead_heat = conn.execute(
            "SELECT COUNT(*) n FROM runners WHERE race_id=? AND finish_pos=1",
            (row["race_id"],),
        ).fetchone()["n"] or 1

        commission = settings.exchange_commission if row["venue"] == "exchange" else 0.0
        outcome = settle_bet(
            stake_units=float(row["stake_units"]),
            advised_odds=float(row["advised_odds"]),
            won=bool(row["win_flag"]),
            commission=commission,
            voided=row["runner_status"] == "nonrunner",
            rule4=rule4,
            dead_heat_runners=int(dead_heat) if row["win_flag"] else 1,
            bsp=row["bsp"],
        )

        conn.execute(
            """INSERT INTO settlements (suggestion_id, result, pl_units, bsp_at_off,
                   clv, rule4_deduction, settled_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(suggestion_id) DO UPDATE SET
                   result=excluded.result, pl_units=excluded.pl_units,
                   bsp_at_off=excluded.bsp_at_off, clv=excluded.clv,
                   rule4_deduction=excluded.rule4_deduction,
                   settled_ts=excluded.settled_ts""",
            (row["id"], outcome.result, outcome.pl_units, row["bsp"], outcome.clv,
             outcome.rule4_deduction, now),
        )
        conn.execute("UPDATE suggestions SET status='settled' WHERE id=?", (row["id"],))

        result.settled += 1
        result.pl_units += outcome.pl_units
        if outcome.result in ("won", "deadheat"):
            result.won += 1
        elif outcome.result == "void":
            result.void += 1
        else:
            result.lost += 1
        if outcome.clv:
            clvs.append(outcome.clv)

    if clvs:
        result.mean_clv = sum(clvs) / len(clvs)
    conn.commit()
    conn.close()
    return result
