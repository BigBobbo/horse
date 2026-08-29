import numpy as np
import pandas as pd
import pytest

from furlong.config import Settings
from furlong.value.devig import (
    devig,
    devig_power,
    devig_proportional,
    devig_shin,
    expected_value,
    fair_odds,
    net_return_multiple,
    overround,
)
from furlong.value.engine import find_value, price_floor_for, price_runner
from furlong.value.settlement import (
    RULE_4_TABLE,
    combined_rule4,
    rule4_deduction,
    settle_bet,
)
from furlong.value.staking import apply_daily_cap, kelly_fraction, stake_for


# -- de-vigging -------------------------------------------------------------

def test_overround_and_proportional_devig():
    odds = np.array([2.0, 4.0, 5.0])  # 0.5 + 0.25 + 0.2 = 0.95 (an underround)
    assert overround(odds) == pytest.approx(0.95)
    fair = devig_proportional(odds)
    assert fair.sum() == pytest.approx(1.0)
    assert fair[0] == pytest.approx(0.5 / 0.95)


def test_devig_methods_all_normalise():
    odds = np.array([1.8, 3.5, 6.0, 12.0, 30.0])
    assert overround(odds) > 1.1
    for method in ("proportional", "power", "shin"):
        fair = devig(odds, method=method)
        assert fair.sum() == pytest.approx(1.0, abs=1e-9)
        assert (fair > 0).all()


def test_shin_and_power_shrink_longshots_more_than_proportional():
    """The point of Shin/power: longshots carry more of the bookmaker's margin."""
    odds = np.array([1.8, 3.5, 6.0, 12.0, 40.0])
    prop = devig_proportional(odds)
    shin = devig_shin(odds)
    power = devig_power(odds)
    # longshot (last) loses relatively more probability than the favourite
    assert shin[-1] < prop[-1]
    assert power[-1] < prop[-1]
    assert shin[0] > prop[0]
    assert power[0] > prop[0]


def test_shin_reduces_to_proportional_on_a_fair_book():
    odds = np.array([2.0, 4.0, 4.0])  # sums to exactly 1.0
    np.testing.assert_allclose(devig_shin(odds), devig_proportional(odds), atol=1e-9)


def test_devig_rejects_bad_input():
    with pytest.raises(ValueError):
        devig(np.array([1.0, 2.0]))
    with pytest.raises(ValueError, match="unknown de-vig method"):
        devig(np.array([2.0, 2.0]), method="magic")


# -- expected value ---------------------------------------------------------

def test_expected_value_hand_computed():
    # 25% chance at 5.0 with no commission: 0.25*4 - 0.75 = +0.25
    assert expected_value(0.25, 5.0, 0.0) == pytest.approx(0.25)
    # with 2% commission on net winnings: 0.25*4*0.98 - 0.75 = +0.23
    assert expected_value(0.25, 5.0, 0.02) == pytest.approx(0.23)
    # a fair bet is exactly zero EV
    assert expected_value(0.20, 5.0, 0.0) == pytest.approx(0.0)


def test_net_return_multiple_and_fair_odds():
    assert net_return_multiple(5.0, 0.02) == pytest.approx(3.92)
    # break-even odds for a 25% chance with no commission is 4.0
    assert fair_odds(0.25, 0.0) == pytest.approx(4.0)
    # commission pushes the break-even price out
    assert fair_odds(0.25, 0.05) > 4.0
    assert expected_value(0.25, fair_odds(0.25, 0.05), 0.05) == pytest.approx(0.0, abs=1e-9)


def test_price_runner_charges_commission_only_on_exchange():
    assert price_runner(0.25, 5.0, "book", 0.02) == pytest.approx(0.25)
    assert price_runner(0.25, 5.0, "exchange", 0.02) == pytest.approx(0.23)


def test_price_floor_is_the_break_even_for_min_edge():
    floor = price_floor_for(0.25, min_edge=0.05, commission=0.0)
    assert expected_value(0.25, floor, 0.0) == pytest.approx(0.05)
    assert floor > fair_odds(0.25, 0.0)  # stricter than break-even


# -- the value engine -------------------------------------------------------

def _frame(probs, market_probs=None):
    n = len(probs)
    return pd.DataFrame({
        "runner_id": range(1, n + 1),
        "race_id": [10] * n,
        "blend_prob": probs,
        "model_prob": probs,
        "market_prob": market_probs if market_probs is not None else probs,
    })


def _odds(pairs):
    return pd.DataFrame([
        {"runner_id": rid, "venue": venue, "bookmaker": book, "odds_decimal": odds}
        for rid, venue, book, odds in pairs
    ])


def test_find_value_selects_only_qualifying_bets():
    settings = Settings(min_edge=0.05, min_prob=0.05, max_odds=21.0,
                        exchange_commission=0.02)
    frame = _frame([0.30, 0.25, 0.10])
    odds = _odds([
        (1, "book", "GreenBook", 4.0),   # EV = 0.30*3 - 0.7 = +0.20 -> qualifies
        (2, "book", "GreenBook", 3.8),   # EV = 0.25*2.8 - 0.75 = -0.05 -> no
        (3, "book", "GreenBook", 10.0),  # EV = 0.10*9 - 0.9 = 0.0 -> no
    ])
    suggestions = find_value(frame, odds, settings)
    assert [s.runner_id for s in suggestions] == [1]
    assert suggestions[0].ev == pytest.approx(0.20)
    assert suggestions[0].advised_odds == 4.0


def test_longshot_filter_blocks_huge_apparent_edges():
    """A 100/1 shot the model likes must never be suggested (min_prob)."""
    settings = Settings(min_edge=0.05, min_prob=0.05, max_odds=200.0)
    frame = _frame([0.04])
    odds = _odds([(1, "book", "GreenBook", 101.0)])  # EV = 0.04*100 - 0.96 = +3.04
    assert find_value(frame, odds, settings) == []

    # the same edge at an acceptable probability does qualify
    frame2 = _frame([0.06])
    odds2 = _odds([(1, "book", "GreenBook", 30.0)])
    assert len(find_value(frame2, odds2, settings)) == 1


def test_max_odds_ceiling():
    settings = Settings(min_edge=0.05, min_prob=0.01, max_odds=21.0)
    frame = _frame([0.06])
    odds = _odds([(1, "book", "GreenBook", 25.0)])
    assert find_value(frame, odds, settings) == []


def test_best_price_across_venues_wins():
    settings = Settings(min_edge=0.05, min_prob=0.05, exchange_commission=0.02)
    frame = _frame([0.30])
    odds = _odds([
        (1, "book", "GreenBook", 4.0),      # EV +0.20
        (1, "book", "HarpBet", 4.4),        # EV +0.32
        (1, "exchange", None, 4.5),         # EV = 0.30*3.5*0.98 - 0.7 = +0.329
    ])
    suggestions = find_value(frame, odds, settings)
    assert len(suggestions) == 1
    best = suggestions[0]
    assert best.venue == "exchange"
    assert best.advised_odds == 4.5
    assert len(best.alternatives) == 3


def test_suggestion_price_floor_is_binding():
    settings = Settings(min_edge=0.10, min_prob=0.05)
    frame = _frame([0.30])
    odds = _odds([(1, "book", "GreenBook", 5.0)])
    suggestion = find_value(frame, odds, settings)[0]
    assert suggestion.price_floor < suggestion.advised_odds
    # at exactly the floor the bet still clears min_edge
    assert price_runner(0.30, suggestion.price_floor, "book", 0.0) == pytest.approx(0.10)
    # a shade below it does not
    assert price_runner(0.30, suggestion.price_floor - 0.05, "book", 0.0) < 0.10


def test_find_value_handles_empty_inputs():
    settings = Settings()
    assert find_value(pd.DataFrame(), pd.DataFrame(), settings) == []
    assert find_value(_frame([0.3]), pd.DataFrame(), settings) == []


# -- staking ---------------------------------------------------------------

def test_kelly_fraction_hand_computed():
    # p=0.30 at 5.0, no commission: edge = 0.3*4 - 0.7 = 0.5; f = 0.5/4 = 0.125
    assert kelly_fraction(0.30, 5.0, 0.0) == pytest.approx(0.125)
    # no edge -> no bet
    assert kelly_fraction(0.20, 5.0, 0.0) == pytest.approx(0.0)
    assert kelly_fraction(0.10, 5.0, 0.0) == 0.0


def test_stake_applies_kelly_fraction_and_per_bet_cap():
    settings = Settings(kelly_fraction=0.25, max_stake_pct=0.02,
                        exchange_commission=0.0)
    # quarter of 0.125 = 0.03125 -> above the 2% cap
    plan = stake_for(0.30, 5.0, settings)
    assert plan.kelly_fraction_of_bank == pytest.approx(0.02)
    assert plan.capped_by == "per_bet"
    assert plan.stake_units == pytest.approx(2.0)  # 1 unit = 1% of bank

    # a smaller edge stays under the cap
    small = stake_for(0.22, 5.0, settings)
    assert small.capped_by is None
    assert 0 < small.kelly_fraction_of_bank < 0.02


def test_zero_stake_when_no_edge():
    settings = Settings(kelly_fraction=0.25)
    assert stake_for(0.10, 5.0, settings).stake_units == 0.0


def test_daily_cap_scales_stakes_proportionally():
    settings = Settings(max_daily_stake_pct=0.05)  # 5 units per day
    plans = [stake_for(0.30, 5.0, Settings(kelly_fraction=0.25, max_stake_pct=0.02,
                                           exchange_commission=0.0))
             for _ in range(5)]  # 5 x 2 units = 10 units, over the cap
    capped = apply_daily_cap(plans, settings)
    assert sum(p.stake_units for p in capped) == pytest.approx(5.0)
    assert all(p.capped_by == "per_day" for p in capped)

    # under the cap, plans pass through untouched
    few = apply_daily_cap(plans[:2], settings)
    assert sum(p.stake_units for p in few) == pytest.approx(4.0)


# -- settlement ------------------------------------------------------------

def test_settle_win_and_loss():
    won = settle_bet(stake_units=2.0, advised_odds=5.0, won=True)
    assert won.result == "won"
    assert won.pl_units == pytest.approx(8.0)  # 2 units * 4.0 net

    lost = settle_bet(stake_units=2.0, advised_odds=5.0, won=False)
    assert lost.result == "lost"
    assert lost.pl_units == pytest.approx(-2.0)


def test_settle_applies_commission_on_exchange_wins():
    out = settle_bet(stake_units=1.0, advised_odds=5.0, won=True, commission=0.02)
    assert out.pl_units == pytest.approx(3.92)


def test_non_runner_is_void_with_stake_returned():
    out = settle_bet(stake_units=3.0, advised_odds=6.0, won=False, voided=True)
    assert out.result == "void"
    assert out.pl_units == 0.0


def test_clv_measures_advised_against_bsp():
    beat = settle_bet(stake_units=1.0, advised_odds=6.0, won=False, bsp=5.0)
    assert beat.clv == pytest.approx(1.2)   # took 6.0, closed 5.0
    missed = settle_bet(stake_units=1.0, advised_odds=4.0, won=True, bsp=5.0)
    assert missed.clv == pytest.approx(0.8)
    assert settle_bet(1.0, 4.0, True, bsp=None).clv is None


def test_rule4_table_bands():
    assert rule4_deduction(1.25) == 0.75    # odds-on withdrawal, biggest cut
    assert rule4_deduction(2.50) == 0.40
    assert rule4_deduction(4.00) == 0.25
    assert rule4_deduction(11.00) == 0.05
    assert rule4_deduction(12.0) == 0.0     # above the threshold, no deduction
    assert rule4_deduction(None) == 0.0
    # the table is monotone: shorter withdrawals mean bigger deductions
    deductions = [d for _, d in RULE_4_TABLE]
    assert deductions == sorted(deductions, reverse=True)


def test_combined_rule4_is_capped():
    assert combined_rule4([2.5, 4.0]) == pytest.approx(0.65)
    assert combined_rule4([1.25, 1.25, 1.25]) == 0.75   # capped
    assert combined_rule4([]) == 0.0


def test_settle_applies_rule4_to_winnings():
    # 1 unit at 5.0 with a 25% Rule 4: net odds 4.0 * 0.75 = 3.0
    out = settle_bet(stake_units=1.0, advised_odds=5.0, won=True, rule4=0.25)
    assert out.pl_units == pytest.approx(3.0)
    assert out.rule4_deduction == 0.25
    # losers are unaffected by Rule 4
    lost = settle_bet(stake_units=1.0, advised_odds=5.0, won=False, rule4=0.25)
    assert lost.pl_units == pytest.approx(-1.0)


def test_dead_heat_splits_the_stake():
    # 2 units at 5.0 dead-heating with one other: half wins at 4.0, half loses
    out = settle_bet(stake_units=2.0, advised_odds=5.0, won=True, dead_heat_runners=2)
    assert out.result == "deadheat"
    assert out.pl_units == pytest.approx(1.0 * 4.0 - 1.0)


# -- regressions from the adversarial review --------------------------------

def test_rule4_applies_to_bookmakers_but_never_to_the_exchange():
    """Rule 4 is a Tattersalls bookmaker rule; the exchange re-forms instead.

    Also covers the price source: a withdrawn horse has no Betfair SP,
    precisely because it was withdrawn, so the deduction must come from its
    last bookmaker snapshot.
    """
    import tempfile
    from pathlib import Path

    from furlong import repo as repo_mod
    from furlong.db import init_db
    from furlong.repo import RaceRecord, RunnerRecord
    from furlong.value.settlement import settle_suggestions

    settings = Settings(data_dir=Path(tempfile.mkdtemp()), exchange_commission=0.0)
    conn = init_db(settings.database_path)

    outcomes = {}
    for venue, bookmaker, day in (("exchange", None, "01"), ("book", "GreenBook", "02")):
        date = f"2026-05-{day}"
        race_id = repo_mod.upsert_race(conn, RaceRecord(
            source_id=f"R-{venue}", course="Curragh", country="IRE", date=date,
            start_time_utc=f"{date}T14:00:00+00:00", race_type="flat",
            distance_m=1600, going="good", status="result",
        ))
        winner = repo_mod.upsert_runner(conn, race_id, RunnerRecord(
            horse=f"Winner {venue}", status="ran", finish_pos=1, win_flag=1))
        withdrawn = repo_mod.upsert_runner(conn, race_id, RunnerRecord(
            horse=f"Withdrawn {venue}", status="nonrunner"))
        # the withdrawn horse was a short-priced bookmaker favourite, and has
        # no BSP row because it never ran
        repo_mod.add_odds_snapshot(conn, withdrawn, "book", f"{date}T09:00:00",
                                   1.5, "GreenBook")
        conn.execute(
            """INSERT INTO suggestions (date, race_id, runner_id, model_prob, blend_prob,
                   fair_odds, advised_odds, price_floor, venue, bookmaker, ev,
                   stake_units, status, created_ts)
               VALUES (?, ?, ?, 0.4, 0.4, 3.0, 5.0, 4.0, ?, ?, 0.5, 1.0, 'open', ?)""",
            (date, race_id, winner, venue, bookmaker, f"{date}T09:00:00"),
        )
        conn.commit()
        settle_suggestions(settings, date=date)
        outcomes[venue] = conn.execute(
            """SELECT t.rule4_deduction, t.pl_units FROM settlements t
               JOIN suggestions s ON s.id = t.suggestion_id WHERE s.venue = ?""",
            (venue,),
        ).fetchone()
    conn.close()

    assert outcomes["exchange"]["rule4_deduction"] == 0.0
    assert outcomes["exchange"]["pl_units"] == pytest.approx(4.0)
    # 1.5 falls in the 0.65 band, so net winnings are cut to 35%
    assert outcomes["book"]["rule4_deduction"] == pytest.approx(0.65)
    assert outcomes["book"]["pl_units"] == pytest.approx(4.0 * 0.35)


def test_void_bets_carry_no_clv():
    """A withdrawn runner never had a closing line to beat."""
    out = settle_bet(stake_units=1.0, advised_odds=6.0, won=False, voided=True, bsp=5.0)
    assert out.result == "void"
    assert out.clv is None


def test_per_race_cap_limits_mutually_exclusive_bets():
    from furlong.value.staking import apply_race_cap

    settings = Settings(max_stake_pct=0.02)
    plans = [stake_for(0.30, 5.0, Settings(kelly_fraction=0.25, max_stake_pct=0.02,
                                           exchange_commission=0.0))
             for _ in range(3)]
    # three qualifiers in the SAME race must not risk 3x the per-bet cap
    capped = apply_race_cap(plans, [7, 7, 7], settings)
    assert sum(p.stake_units for p in capped) == pytest.approx(2.0)
    assert all(p.capped_by == "per_race" for p in capped)

    # spread across different races, each keeps its own stake
    separate = apply_race_cap(plans, [1, 2, 3], settings)
    assert sum(p.stake_units for p in separate) == pytest.approx(6.0)
