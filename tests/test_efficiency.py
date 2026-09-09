"""The market-efficiency sweep.

The point of these fixtures is that the sweep has to be able to say *yes*.
A tool that reports "efficient" on a market that is demonstrably loose has
proved nothing, so the loose fixture matters more than the tight one.
"""

import numpy as np
import pandas as pd
import pytest

from furlong.backtest.efficiency import (
    MIN_SEGMENT,
    best_segment,
    place_efficiency,
    prepare,
    render,
    sweep,
)


def _market(n_races=1200, field=8, seed=0, overround=1.02, soft_country=None):
    """Races priced from the true probabilities, plus a book margin.

    ``soft_country`` names a country whose prices are deliberately too long,
    so backing everything there is profitable -- the case the sweep must
    catch.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for race in range(n_races):
        country = "IRE" if race % 3 == 0 else "GB"
        strength = rng.gamma(2.0, 1.0, size=field)
        true_p = strength / strength.sum()
        margin = overround
        if soft_country and country == soft_country:
            margin = 0.90          # prices 10% too long: a real edge
        winner = rng.choice(field, p=true_p)
        for i in range(field):
            rows.append({
                "race_id": race, "win_flag": int(i == winner),
                "finish_pos": 1 if i == winner else 5,
                "date": "2026-01-01", "race_type": "flat" if race % 2 else "nh",
                "race_class": 4, "field_size": field, "country": country,
                "course": "Curragh",
                # An overround (margin > 1) shortens the odds; margin < 1
                # leaves them longer than fair, which is a backer's edge.
                "win_bsp": float(1.0 / (true_p[i] * margin)),
                "place_bsp": None,
            })
    return pd.DataFrame(rows)


def test_a_fair_market_shows_only_the_commission():
    frame = prepare(_market(seed=1, overround=1.0), commission=0.02)
    rows = sweep(frame, "country")
    assert rows, "expected both countries to clear the minimum segment size"
    for row in rows:
        # Backing everything in a fair book loses the commission on winnings,
        # which is small and negative -- never positive.
        assert row["roi_pp"] < 1.0
        # A country takes whole races, so no calibration figure is offered.
        assert row["calibration_pp"] is None


def test_a_soft_segment_is_caught():
    """The test that gives the negative result its meaning."""
    frame = prepare(_market(n_races=2000, seed=2, soft_country="IRE"))
    rows = {r["segment"]: r for r in sweep(frame, "country")}
    assert rows["IRE"]["roi_pp"] > 5.0, "a 10% price advantage was not detected"
    # Two standard errors, not an invented larger bar: an 11% edge over ~5,000
    # runners at racing odds is worth about this much evidence, and demanding
    # more would be the same mistake this project keeps warning users about.
    assert rows["IRE"]["z"] > 2.0
    assert rows["GB"]["roi_pp"] < 1.0


def test_calibration_is_withheld_where_de_vigging_makes_it_meaningless():
    """A slice of whole races is calibrated by construction, not by merit.

    Proportional de-vigging forces each race's book to sum to 1, so grouping
    by country or code always reports 0.00 however wrong the prices are.
    Printing that as the market's accuracy would be an artefact dressed as a
    result -- the same trap as a race-constant feature in `calibration`.
    """
    soft = prepare(_market(n_races=2000, seed=3, soft_country="IRE"))
    by_country = sweep(soft, "country")
    assert by_country, "expected country segments"
    assert all(r["whole_races"] for r in by_country)
    assert all(r["calibration_pp"] is None for r in by_country), (
        "whole-race slices must not report a calibration figure"
    )
    # The return column still catches the soft market, which is the point:
    ire = next(r for r in by_country if r["segment"] == "IRE")
    assert ire["roi_pp"] > 5.0


def test_calibration_is_reported_where_a_slice_splits_races():
    """An odds band cuts across a race, so its calibration is a real test."""
    frame = prepare(_market(n_races=2000, seed=11))
    rows = sweep(frame, "odds_band")
    assert rows, "expected odds-band segments"
    assert not any(r["whole_races"] for r in rows)
    assert all(r["calibration_pp"] is not None for r in rows)


def test_small_segments_are_not_reported():
    """A few hundred bets at racing odds can only produce a fake finding."""
    frame = prepare(_market(n_races=200, seed=4))
    assert len(frame) < MIN_SEGMENT * 2
    assert sweep(frame, "country") == []


def test_every_return_is_reported_with_its_standard_error():
    frame = prepare(_market(n_races=1500, seed=5))
    for row in sweep(frame, "country"):
        assert row["se_pp"] > 0
        assert row["z"] == pytest.approx(row["roi_pp"] / row["se_pp"], rel=1e-6)


def test_unknown_and_missing_columns_are_skipped_not_crashed():
    frame = prepare(_market(n_races=1500, seed=6))
    assert sweep(frame, "no_such_column") == []
    assert sweep(pd.DataFrame(), "country") == []


def test_place_efficiency_measures_against_the_win_market():
    """Place probabilities are measured, never assumed from a formula."""
    rng = np.random.default_rng(7)
    rows = []
    for race in range(4000):
        strength = rng.gamma(2.0, 1.0, size=8)
        true_p = strength / strength.sum()
        order = rng.choice(8, size=8, replace=False, p=true_p / true_p.sum())
        placed = set(order[:3])
        # A place book priced from the realised place rate: efficient.
        for i in range(8):
            rows.append({
                "race_id": race, "win_flag": int(i == order[0]),
                "finish_pos": 1 if i == order[0] else (2 if i in placed else 6),
                "date": "2026-01-01", "race_type": "flat", "race_class": 4,
                "field_size": 8, "country": "GB", "course": "X",
                "win_bsp": float(1.0 / true_p[i]),
                "place_bsp": float(1.0 / min(0.99, true_p[i] * 2.6)),
            })
    result = place_efficiency(prepare(pd.DataFrame(rows)))
    assert result, "place bins should have been produced"
    assert {r["places"] for r in result} == {3}
    assert all(r["n"] > 0 for r in result)
    # Actual place rate must rise with win probability -- the ordering the
    # whole comparison rests on.
    by_bin = sorted(result, key=lambda r: r["bin"])
    assert by_bin[0]["actual"] < by_bin[-1]["actual"]


def test_place_efficiency_is_empty_without_place_prices():
    frame = prepare(_market(n_races=1500, seed=8))
    assert place_efficiency(frame) == []


def test_render_names_the_best_segment_found():
    frame = prepare(_market(n_races=1500, seed=9))
    report = {"runners": len(frame), "races": int(frame["race_id"].nunique()),
              "commission": 0.02, "sweeps": {"country": sweep(frame, "country")},
              "place": []}
    text = render(report)
    assert "Best segment found" in text
    assert best_segment(report)["segment"] in ("GB", "IRE")
