"""Stake sizing: fractional Kelly with hard caps.

Kelly maximises expected log-wealth; for a single bet at decimal odds ``o``
with win probability ``p`` the optimal fraction of bankroll is
``edge / (o - 1)``. Nobody sane bets full Kelly: Benter's own warning is
that overestimating your advantage by a factor of two turns full Kelly into
*negative* growth, and MacLean/Ziemba/Blazenko show half-Kelly keeps ~75%
of the growth at ~half the volatility. Furlong defaults to quarter-Kelly
with a per-bet cap and a per-day cap.

Stakes are expressed in units of the configured bankroll, where 1 unit =
1% of bankroll, so a user's absolute stake is their own decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from furlong.config import Settings

UNIT_FRACTION = 0.01  # one staking unit = 1% of bankroll


@dataclass
class StakePlan:
    stake_units: float
    kelly_fraction_of_bank: float
    capped_by: str | None  # 'per_bet' | 'per_day' | None


def kelly_fraction(prob: float, odds: float, commission: float = 0.0) -> float:
    """Full-Kelly fraction of bankroll for one bet (0 if there is no edge)."""
    net = (odds - 1.0) * (1.0 - commission)
    if net <= 0:
        return 0.0
    edge = prob * net - (1.0 - prob)
    if edge <= 0:
        return 0.0
    return edge / net


def stake_for(prob: float, odds: float, settings: Settings,
              commission: float | None = None) -> StakePlan:
    """Fractional-Kelly stake in units, capped per bet."""
    commission = settings.exchange_commission if commission is None else commission
    full = kelly_fraction(prob, odds, commission)
    fraction = full * settings.kelly_fraction
    capped_by = None
    if fraction > settings.max_stake_pct:
        fraction = settings.max_stake_pct
        capped_by = "per_bet"
    return StakePlan(
        stake_units=fraction / UNIT_FRACTION,
        kelly_fraction_of_bank=fraction,
        capped_by=capped_by,
    )


def flat_stake(settings: Settings, units: float = 1.0) -> StakePlan:
    """Flat staking, for users who prefer it and for clean backtest baselines."""
    return StakePlan(stake_units=units, kelly_fraction_of_bank=units * UNIT_FRACTION,
                     capped_by=None)


def apply_race_cap(plans: list[StakePlan], race_ids: list, settings: Settings
                   ) -> list[StakePlan]:
    """Cap the total staked on any one race at the per-bet limit.

    Runners in the same race are mutually exclusive, so staking each as an
    independent Kelly bet over-commits: three qualifiers in one race would
    risk three times the intended fraction on a single outcome.
    """
    cap_units = settings.max_stake_pct / UNIT_FRACTION
    totals: dict = {}
    for plan, race_id in zip(plans, race_ids):
        totals[race_id] = totals.get(race_id, 0.0) + plan.stake_units

    out: list[StakePlan] = []
    for plan, race_id in zip(plans, race_ids):
        total = totals[race_id]
        if total <= cap_units or total <= 0:
            out.append(plan)
            continue
        scale = cap_units / total
        out.append(StakePlan(
            stake_units=plan.stake_units * scale,
            kelly_fraction_of_bank=plan.kelly_fraction_of_bank * scale,
            capped_by="per_race",
        ))
    return out


def apply_daily_cap(plans: list[StakePlan], settings: Settings) -> list[StakePlan]:
    """Scale a day's stakes down proportionally if they breach the daily cap."""
    total_units = sum(plan.stake_units for plan in plans)
    cap_units = settings.max_daily_stake_pct / UNIT_FRACTION
    if total_units <= cap_units or total_units <= 0:
        return plans
    scale = cap_units / total_units
    return [
        StakePlan(
            stake_units=plan.stake_units * scale,
            kelly_fraction_of_bank=plan.kelly_fraction_of_bank * scale,
            capped_by="per_day",
        )
        for plan in plans
    ]
