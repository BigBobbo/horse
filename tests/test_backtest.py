import json

import numpy as np
import pandas as pd
import pytest

from furlong.backtest.engine import (
    BacktestResult,
    LeakageError,
    _assert_no_leakage,
    run_backtest,
)
from furlong.backtest.report import compute_metrics, write_report


@pytest.fixture(scope="module")
def backtest_settings(tmp_path_factory):
    """A larger world than the shared fixture.

    The headline validation -- does the value strategy actually beat doing
    nothing -- is a statistical claim, and the research is emphatic that a
    few hundred bets prove nothing. 700 days gives ~5,000 races and several
    thousand bets, enough for the assertion to hold across seeds instead of
    passing by luck.
    """
    from furlong.config import Settings
    from furlong.sources.synthetic import generate_world

    settings = Settings(data_dir=tmp_path_factory.mktemp("backtest") / "data")
    generate_world(settings, seed=23, n_horses=450, days=700)
    return settings


@pytest.fixture(scope="module")
def backtest(backtest_settings) -> BacktestResult:
    return run_backtest(backtest_settings, model_kind="gbm", n_folds=3)


# -- leakage guards ---------------------------------------------------------

def _frame(dates, race_ids=None):
    race_ids = race_ids or list(range(len(dates)))
    return pd.DataFrame({"date": dates, "race_id": race_ids})


def test_leakage_guard_accepts_clean_folds():
    train = _frame(["2024-01-01", "2024-01-02"], [1, 2])
    valid = _frame(["2024-01-03"], [3])
    test = _frame(["2024-01-05"], [4])
    _assert_no_leakage(train, valid, test)  # must not raise


def test_leakage_guard_rejects_future_in_training():
    train = _frame(["2024-01-01", "2024-01-10"], [1, 2])
    valid = _frame(["2024-01-03"], [3])
    test = _frame(["2024-01-05"], [4])
    with pytest.raises(LeakageError, match="train fold"):
        _assert_no_leakage(train, valid, test)


def test_leakage_guard_rejects_same_day_validation():
    """A validation race on the test fold's first day is still the future."""
    train = _frame(["2024-01-01"], [1])
    valid = _frame(["2024-01-05"], [2])
    test = _frame(["2024-01-05"], [3])
    with pytest.raises(LeakageError, match="valid fold"):
        _assert_no_leakage(train, valid, test)


def test_leakage_guard_rejects_shared_races():
    train = _frame(["2024-01-01"], [7])
    valid = _frame(["2024-01-02"], [8])
    test = _frame(["2024-01-05"], [7])
    with pytest.raises(LeakageError, match="both train and test"):
        _assert_no_leakage(train, valid, test)


def test_backtest_folds_are_chronologically_clean(backtest):
    """Every fold's test window starts after the previous one ends."""
    starts = [f["test_start"] for f in backtest.folds]
    ends = [f["test_end"] for f in backtest.folds]
    assert starts == sorted(starts)
    for i in range(1, len(starts)):
        assert starts[i] > ends[i - 1]


# -- the honesty checks -----------------------------------------------------

def test_naive_backing_everything_makes_no_money(backtest):
    """Backing every runner at a margin-free closing price is not a strategy.

    It is not asserted to be strictly negative: over tens of thousands of
    runners the standard error on this figure is still a couple of percent,
    which is itself the point -- see the variance discussion in
    docs/research/market-economics.md.
    """
    assert backtest.naive_roi() < 0.02


def test_value_strategy_beats_naive_baseline(backtest):
    """The planted inefficiency must show up as a real edge over doing nothing."""
    assert backtest.n_bets > 1000
    assert backtest.roi() > 0
    assert backtest.roi() > backtest.naive_roi() + 0.02


def test_backtest_is_deterministic(backtest_settings):
    first = run_backtest(backtest_settings, model_kind="gbm", n_folds=2)
    second = run_backtest(backtest_settings, model_kind="gbm", n_folds=2)
    assert first.n_bets == second.n_bets
    assert first.roi() == pytest.approx(second.roi())


def test_every_bet_cleared_the_filters(backtest, backtest_settings):
    bets = backtest.bets
    assert (bets["blend_prob"] >= backtest_settings.min_prob).all()
    assert (bets["odds"] <= backtest_settings.max_odds).all()
    assert (bets["ev"] >= backtest_settings.min_edge).all()
    assert (bets["stake"] > 0).all()


def test_bets_are_a_subset_of_runners(backtest):
    assert backtest.n_bets < len(backtest.all_runners)  # most races produce no bet


# -- reporting --------------------------------------------------------------

def test_metrics_match_an_independent_recount(backtest):
    metrics = compute_metrics(backtest)
    bets = backtest.bets
    assert metrics["n_bets"] == len(bets)
    assert metrics["n_winners"] == int(bets["won"].sum())
    assert metrics["profit_units"] == pytest.approx(bets["pl"].sum())
    assert metrics["roi"] == pytest.approx(bets["pl"].sum() / bets["stake"].sum())
    assert metrics["strike_rate"] == pytest.approx(bets["won"].mean())
    assert metrics["avg_odds"] == pytest.approx(bets["odds"].mean())


def test_drawdown_and_losing_run_recomputed(backtest):
    metrics = compute_metrics(backtest)
    pl = backtest.bets["pl"].to_numpy()
    cumulative = np.cumsum(pl)
    peak = np.maximum.accumulate(np.concatenate(([0.0], cumulative)))[1:]
    assert metrics["max_drawdown_units"] == pytest.approx((peak - cumulative).max())

    streak = longest = 0
    for won in backtest.bets["won"]:
        streak = 0 if won else streak + 1
        longest = max(longest, streak)
    assert metrics["longest_losing_run"] == longest
    assert longest > 5, "a real betting record always contains losing runs"


def test_report_flags_insignificant_results_honestly(backtest):
    metrics = compute_metrics(backtest)
    flat_roi, se = metrics["flat_stake_roi"], metrics["flat_stake_roi_se"]
    assert se > 0
    assert metrics["roi_is_significant"] == bool(abs(flat_roi) > 2 * se)


def test_write_report_produces_json_and_html(backtest, tmp_path):
    paths = write_report(backtest, tmp_path)
    payload = json.loads(open(paths["json"]).read())
    assert payload["n_bets"] == backtest.n_bets
    assert "by_country" in payload and payload["by_country"]

    html = open(paths["html"]).read()
    assert "Furlong backtest" in html
    assert "standard error" in html.lower()
    assert (tmp_path / "backtest_bets.csv").exists()


def test_empty_backtest_reports_cleanly(tmp_path):
    empty = BacktestResult(bets=pd.DataFrame(), all_runners=pd.DataFrame())
    assert "no qualifying bets" in empty.summary().lower()
    metrics = compute_metrics(empty)
    assert metrics["n_bets"] == 0
    paths = write_report(empty, tmp_path)
    assert "No qualifying bets" in open(paths["html"]).read()


def test_backtest_refuses_tiny_datasets(settings):
    from furlong.sources.synthetic import generate_world

    generate_world(settings, seed=3, n_horses=80, days=20)
    with pytest.raises(ValueError, match="not enough races"):
        run_backtest(settings, model_kind="gbm")
