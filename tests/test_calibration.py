"""The market-calibration diagnostic.

It answers the question the alpha = 0 test cannot: when the model fails to
beat the market, is that because the features are weak or because the market
has already priced them? The fixtures below plant each answer and check the
tool reports it.
"""

import numpy as np
import pandas as pd
import pytest

from furlong.backtest.calibration import calibrate, flagged_note, render


def _frame(n_races=400, field=8, seed=0, edge=0.0, race_constant=False):
    """Races where ``signal`` sorts winners and the market prices all but ``edge``.

    ``edge`` is the fraction of the signal's effect the market fails to see,
    so 0.0 is a perfectly efficient market and 1.0 a blind one.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for race in range(n_races):
        signal = rng.normal(size=field)
        strength = np.exp(signal)
        true_p = strength / strength.sum()
        # The market sees the signal attenuated by `edge`.
        seen = np.exp(signal * (1 - edge))
        market = seen / seen.sum()
        winner = rng.choice(field, p=true_p)
        for i in range(field):
            rows.append({
                "runner_id": race * field + i, "race_id": race,
                "win_flag": int(i == winner),
                "market_prob": market[i], "market_priced": True,
                "signal": float(signal[i]),
                "constant": float(field),
                "noise": float(rng.normal()),
            })
    frame = pd.DataFrame(rows)
    if race_constant:
        frame["constant"] = frame["race_id"] % 5
    return frame


def test_an_efficient_market_shows_no_gap_however_strongly_the_feature_sorts():
    """The finding this exists to make reproducible.

    The feature sorts winners hard, and the market's implied probability
    tracks it bin for bin. Sorting power and available edge are different
    things, and conflating them is how a useless model looks promising.
    """
    results = calibrate(_frame(n_races=1500, seed=1, edge=0.0), features=["signal"])
    signal = next(r for r in results if r.feature == "signal")

    assert signal.spread_pp > 15, "the fixture's feature should sort winners hard"
    assert signal.worst_gap_pp < 2.0, (
        f"an efficient market left a {signal.worst_gap_pp:.2f}pp gap"
    )
    assert signal.max_abs_z < 4.0


def test_a_blind_market_is_caught():
    """When the market genuinely misses a feature, the gap must show."""
    efficient = calibrate(_frame(n_races=1500, seed=2, edge=0.0),
                          features=["signal"])[0]
    blind = calibrate(_frame(n_races=1500, seed=2, edge=0.6),
                      features=["signal"])[0]
    assert blind.worst_gap_pp > efficient.worst_gap_pp * 3
    assert blind.max_abs_z > 5.0


def test_race_constant_features_are_marked_and_ranked_last():
    """A feature constant within a race cannot price anything.

    It also looks perfectly calibrated no matter what, because binning by it
    groups whole races and a book sums to one by construction. Reporting it
    as the best-priced feature would be an artefact dressed as a result.
    """
    frame = _frame(n_races=400, seed=3, race_constant=True)
    results = calibrate(frame, features=["signal", "constant"])
    by_name = {r.feature: r for r in results}

    assert by_name["constant"].race_constant is True
    assert by_name["signal"].race_constant is False
    assert results[-1].feature == "constant", "race-constant features rank last"


def test_the_flag_count_is_read_against_the_count_of_tests():
    """One z above 2 in twenty bins is noise, and must be reported as noise."""
    frame = _frame(n_races=1200, seed=4, edge=0.0)
    results = calibrate(frame, features=["signal", "noise"])
    note = flagged_note(results)
    assert "expected by chance" in note
    assert "about what noise alone produces" in note


def test_race_constant_bins_are_excluded_from_the_flag_count():
    frame = _frame(n_races=400, seed=5, race_constant=True)
    both = flagged_note(calibrate(frame, features=["signal", "constant"]))
    only_signal = flagged_note(calibrate(frame, features=["signal"]))
    assert both.split(" of ")[1] == only_signal.split(" of ")[1]


def test_constant_and_unbinnable_features_are_skipped_not_crashed():
    frame = _frame(n_races=100, seed=6)
    frame["dead"] = 1.0                      # constant everywhere
    frame["absent"] = np.nan
    results = calibrate(frame, features=["signal", "dead", "absent", "missing"])
    assert [r.feature for r in results] == ["signal"]


def test_render_reports_the_runner_count_and_the_note():
    frame = _frame(n_races=300, seed=7)
    results = calibrate(frame, features=["signal"])
    report = {
        "runners": len(frame),
        "features": [{"feature": r.feature, "spread_pp": r.spread_pp,
                      "worst_gap_pp": r.worst_gap_pp, "max_abs_z": r.max_abs_z,
                      "race_constant": r.race_constant, "bins": r.bins}
                     for r in results],
        "note": flagged_note(results),
    }
    text = render(report)
    assert f"{len(frame):,} priced runners" in text
    assert "signal" in text
    assert "expected by chance" in text


def test_unpriced_runners_are_excluded():
    frame = _frame(n_races=300, seed=8)
    frame.loc[frame.index[:500], "market_priced"] = False
    results = calibrate(frame, features=["signal"])
    assert sum(b["n"] for b in results[0].bins) == len(frame) - 500


def test_an_empty_database_reports_cleanly(settings):
    """A fresh install has nothing to calibrate; that is not a crash."""
    from furlong.backtest.calibration import run_calibration
    from furlong.db import init_db

    init_db(settings.database_path).close()
    report = run_calibration(settings)
    assert report["runners"] == 0
    assert report["features"] == []
