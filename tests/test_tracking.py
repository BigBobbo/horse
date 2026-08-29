import json

import pytest

from furlong.backtest.performance import compute_performance, write_performance_report
from furlong.config import Settings
from furlong.db import init_db
from furlong.pipeline.daily import run_daily
from furlong.sources.synthetic import generate_world, resolve_open_card
from furlong.value.settlement import settle_suggestions


@pytest.fixture(scope="module")
def settled_world(tmp_path_factory):
    """The full loop: publish suggestions, run the races, settle them."""
    settings = Settings(data_dir=tmp_path_factory.mktemp("settled") / "data")
    generate_world(settings, seed=17, n_horses=400, days=420, open_last_day=True)
    outcome = run_daily(settings)
    resolve_open_card(settings, seed=99)
    result = settle_suggestions(settings, date=outcome.date)
    return settings, outcome, result


def test_open_card_resolves_into_results(settled_world):
    settings, outcome, _ = settled_world
    conn = init_db(settings.database_path)
    scheduled = conn.execute(
        "SELECT COUNT(*) n FROM races WHERE status='scheduled'"
    ).fetchone()["n"]
    winners = conn.execute(
        """SELECT r.race_id, SUM(r.win_flag) w FROM runners r JOIN races ra ON ra.id=r.race_id
           WHERE ra.date=? GROUP BY r.race_id""", (outcome.date,)
    ).fetchall()
    bsp = conn.execute(
        """SELECT COUNT(*) n FROM bsp_prices b JOIN runners r ON r.id=b.runner_id
           JOIN races ra ON ra.id=r.race_id WHERE ra.date=?""", (outcome.date,)
    ).fetchone()["n"]
    conn.close()
    assert scheduled == 0
    assert winners and all(row["w"] == 1 for row in winners)
    assert bsp > 0, "BSP must exist once the races have been run"


def test_settlement_covers_every_suggestion(settled_world):
    settings, outcome, result = settled_world
    assert result.settled == len(outcome.suggestions)
    assert result.won + result.lost + result.void == result.settled
    assert "Settled" in result.summary()


def test_settlement_pl_is_arithmetically_right(settled_world):
    settings, _, _ = settled_world
    conn = init_db(settings.database_path)
    rows = conn.execute(
        """SELECT s.stake_units, s.advised_odds, s.venue, t.result, t.pl_units,
                  t.rule4_deduction
           FROM settlements t JOIN suggestions s ON s.id = t.suggestion_id"""
    ).fetchall()
    conn.close()
    assert rows
    for row in rows:
        commission = settings.exchange_commission if row["venue"] == "exchange" else 0.0
        if row["result"] == "won":
            expected = (
                row["stake_units"] * (row["advised_odds"] - 1)
                * (1 - row["rule4_deduction"]) * (1 - commission)
            )
        elif row["result"] == "lost":
            expected = -row["stake_units"]
        else:
            expected = 0.0
        if row["result"] != "deadheat":
            assert row["pl_units"] == pytest.approx(expected, abs=1e-9)


def test_clv_is_recorded_against_bsp(settled_world):
    settings, _, result = settled_world
    conn = init_db(settings.database_path)
    rows = conn.execute(
        """SELECT s.advised_odds, t.bsp_at_off, t.clv FROM settlements t
           JOIN suggestions s ON s.id = t.suggestion_id WHERE t.clv IS NOT NULL"""
    ).fetchall()
    conn.close()
    assert rows, "expected CLV to be computable once BSP is ingested"
    for row in rows:
        assert row["clv"] == pytest.approx(row["advised_odds"] / row["bsp_at_off"])
    assert result.mean_clv is not None


def test_settled_suggestions_are_not_settled_twice(settled_world):
    settings, outcome, _ = settled_world
    again = settle_suggestions(settings, date=outcome.date)
    assert again.settled == 0, "already-settled suggestions must be left alone"


# -- performance reporting --------------------------------------------------

def test_performance_metrics_are_consistent(settled_world):
    settings, _, _ = settled_world
    conn = init_db(settings.database_path)
    metrics = compute_performance(conn)
    conn.close()

    assert metrics["n_settled"] > 0
    assert metrics["n_won"] + metrics["n_void"] <= metrics["n_settled"]
    assert metrics["strike_rate"] == pytest.approx(
        metrics["n_won"] / metrics["n_settled"]
    )
    # Monthly profits must sum to the headline figure. The tolerance allows
    # for the 5-decimal rounding applied to the per-month rows for display.
    monthly_total = sum(row["profit"] for row in metrics["monthly"])
    assert monthly_total == pytest.approx(metrics["profit_units"], abs=1e-4)
    # the cumulative series must end at the same place
    assert metrics["cumulative"][-1]["cumulative_pl"] == pytest.approx(
        metrics["profit_units"], abs=1e-4
    )


def test_performance_reports_clv_and_significance(settled_world):
    settings, _, _ = settled_world
    conn = init_db(settings.database_path)
    metrics = compute_performance(conn)
    conn.close()

    assert metrics["n_with_clv"] > 0
    assert metrics["mean_clv"] > 0
    assert 0.0 <= metrics["pct_beat_close"] <= 1.0
    # A handful of bets can never establish an edge, and the report must not
    # pretend otherwise -- not even when every one of them lost, which gives a
    # standard error of exactly zero.
    assert metrics["roi_is_significant"] is False
    assert metrics["flat_stake_roi_se"] >= 0


def test_performance_report_written_to_disk(settled_world):
    settings, _, _ = settled_world
    paths = write_performance_report(settings)
    payload = json.loads(open(paths["json"]).read())
    assert payload["n_settled"] > 0
    assert "mean_clv" in payload


def test_empty_performance_report(settings):
    conn = init_db(settings.database_path)
    metrics = compute_performance(conn)
    conn.close()
    assert metrics["n_settled"] == 0
    assert "no settled suggestions" in metrics["note"]


# -- the significance guard -------------------------------------------------

def test_significance_requires_a_real_sample():
    from furlong.backtest.report import MIN_BETS_FOR_SIGNIFICANCE, is_significant

    # a big ROI on a tiny sample is never significant
    assert is_significant(0.50, 0.05, n_bets=10) is False
    # zero variance (every bet the same result) must not read as certainty
    assert is_significant(-1.0, 0.0, n_bets=1000) is False
    assert is_significant(0.10, float("nan"), n_bets=1000) is False
    # a genuine result on a real sample does pass
    assert is_significant(0.10, 0.02, n_bets=MIN_BETS_FOR_SIGNIFICANCE) is True
    # ...but not when it is inside two standard errors
    assert is_significant(0.03, 0.02, n_bets=MIN_BETS_FOR_SIGNIFICANCE) is False
