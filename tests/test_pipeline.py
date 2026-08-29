import json

import pytest

from furlong.config import Settings
from furlong.db import init_db
from furlong.pipeline.daily import run_daily
from furlong.pipeline.rescore import run_rescore
from furlong.sources.synthetic import generate_world


@pytest.fixture(scope="module")
def daily_settings(tmp_path_factory) -> Settings:
    """A world with an open final card for the daily pipeline to work on."""
    settings = Settings(data_dir=tmp_path_factory.mktemp("daily") / "data")
    generate_world(settings, seed=31, n_horses=400, days=420, open_last_day=True)
    return settings


@pytest.fixture(scope="module")
def daily_outcome(daily_settings):
    return run_daily(daily_settings, dry_run=False)


def _open_card_date(settings) -> str:
    conn = init_db(settings.database_path)
    date = conn.execute(
        "SELECT MAX(date) AS d FROM races WHERE status='scheduled'"
    ).fetchone()["d"]
    conn.close()
    return date


# -- the open card ----------------------------------------------------------

def test_world_leaves_an_open_card(daily_settings):
    conn = init_db(daily_settings.database_path)
    date = _open_card_date(daily_settings)
    declared = conn.execute(
        """SELECT COUNT(*) n FROM runners r JOIN races ra ON ra.id=r.race_id
           WHERE ra.date=? AND r.status='declared'""", (date,)
    ).fetchone()["n"]
    results = conn.execute(
        "SELECT COUNT(*) n FROM runners WHERE finish_pos IS NOT NULL AND race_id IN "
        "(SELECT id FROM races WHERE date=?)", (date,)
    ).fetchone()["n"]
    bsp = conn.execute(
        """SELECT COUNT(*) n FROM bsp_prices b JOIN runners r ON r.id=b.runner_id
           JOIN races ra ON ra.id=r.race_id WHERE ra.date=?""", (date,)
    ).fetchone()["n"]
    conn.close()
    assert declared > 0
    assert results == 0, "an open card must have no results"
    assert bsp == 0, "Betfair SP does not exist before the off"


def test_no_horse_runs_twice_on_the_same_day(daily_settings):
    conn = init_db(daily_settings.database_path)
    dupes = conn.execute(
        """SELECT ra.date, r.horse_id, COUNT(*) n FROM runners r
           JOIN races ra ON ra.id = r.race_id
           GROUP BY ra.date, r.horse_id HAVING n > 1"""
    ).fetchall()
    conn.close()
    assert dupes == []


# -- the daily run ----------------------------------------------------------

def test_daily_produces_suggestions(daily_outcome, daily_settings):
    assert daily_outcome.date == _open_card_date(daily_settings)
    assert daily_outcome.races_considered > 0
    assert daily_outcome.runners_considered > 0
    assert len(daily_outcome.suggestions) == len(daily_outcome.stakes)


def test_every_suggestion_is_internally_consistent(daily_outcome, daily_settings):
    from furlong.value.devig import expected_value

    assert daily_outcome.suggestions, "expected at least one value bet on the open card"
    for suggestion in daily_outcome.suggestions:
        commission = (
            daily_settings.exchange_commission if suggestion.venue == "exchange" else 0.0
        )
        assert suggestion.price_floor > 1.0
        assert suggestion.advised_odds >= suggestion.price_floor - 1e-9
        assert suggestion.blend_prob >= daily_settings.min_prob
        assert suggestion.advised_odds <= daily_settings.max_odds
        recomputed = expected_value(suggestion.blend_prob, suggestion.advised_odds,
                                    commission)
        assert recomputed == pytest.approx(suggestion.ev, abs=1e-9)
        assert recomputed >= daily_settings.min_edge


def test_price_floor_is_the_advice_that_survives_decay(daily_outcome, daily_settings):
    """At the floor the bet is marginal; below it, it is not a bet."""
    from furlong.value.devig import expected_value

    for suggestion in daily_outcome.suggestions:
        commission = (
            daily_settings.exchange_commission if suggestion.venue == "exchange" else 0.0
        )
        at_floor = expected_value(suggestion.blend_prob, suggestion.price_floor, commission)
        below = expected_value(suggestion.blend_prob, suggestion.price_floor - 0.05,
                               commission)
        assert at_floor == pytest.approx(daily_settings.min_edge, abs=1e-6)
        assert below < daily_settings.min_edge


def test_daily_stakes_respect_the_daily_cap(daily_outcome, daily_settings):
    total = sum(plan.stake_units for plan in daily_outcome.stakes)
    cap_units = daily_settings.max_daily_stake_pct / 0.01
    assert total <= cap_units + 1e-6


def test_suggestions_are_persisted(daily_outcome, daily_settings):
    conn = init_db(daily_settings.database_path)
    rows = conn.execute(
        "SELECT * FROM suggestions WHERE date = ?", (daily_outcome.date,)
    ).fetchall()
    conn.close()
    assert len(rows) == len(daily_outcome.suggestions)
    assert all(row["status"] == "open" for row in rows)
    assert all(row["price_floor"] > 1.0 for row in rows)


def test_daily_writes_json_with_stable_schema(daily_outcome):
    path = daily_outcome.written["json"]
    payload = json.loads(open(path).read())
    assert payload["date"] == daily_outcome.date
    assert payload["n_suggestions"] == len(daily_outcome.suggestions)
    if payload["suggestions"]:
        entry = payload["suggestions"][0]
        assert {"runner_id", "advised_odds", "price_floor", "ev", "stake_units",
                "blend_prob", "venue", "horse", "race"} <= set(entry)


def test_terminal_output_warns_about_price_decay(daily_outcome):
    text = daily_outcome.render_terminal()
    assert "Floor" in text
    assert "decays within minutes" in text


def test_dry_run_writes_nothing(daily_settings):
    settings = Settings(data_dir=daily_settings.data_dir, min_edge=0.05)
    conn = init_db(settings.database_path)
    before = conn.execute("SELECT COUNT(*) n FROM suggestions").fetchone()["n"]
    conn.close()

    outcome = run_daily(settings, dry_run=True)
    assert outcome.dry_run

    conn = init_db(settings.database_path)
    after = conn.execute("SELECT COUNT(*) n FROM suggestions").fetchone()["n"]
    conn.close()
    assert after == before
    assert outcome.written == {}


def test_no_racing_date_exits_gracefully(daily_settings):
    outcome = run_daily(daily_settings, date="2019-01-01")
    assert outcome.suggestions == []
    assert "No declared runners" in outcome.message


def test_empty_database_is_handled(settings):
    init_db(settings.database_path).close()
    outcome = run_daily(settings)
    assert "No racing data" in outcome.message


def test_high_edge_threshold_produces_no_bets(daily_settings):
    """Not betting is a valid outcome and must be stated plainly."""
    strict = Settings(data_dir=daily_settings.data_dir, min_edge=5.0)
    outcome = run_daily(strict, dry_run=True)
    assert outcome.suggestions == []
    assert "No qualifying value bets" in outcome.render_terminal()


# -- the rescore ------------------------------------------------------------

def test_rescore_voids_a_withdrawn_selection(daily_settings, daily_outcome):
    assert daily_outcome.suggestions
    target = daily_outcome.suggestions[0]

    conn = init_db(daily_settings.database_path)
    conn.execute("UPDATE runners SET status='nonrunner' WHERE id=?", (target.runner_id,))
    conn.commit()
    conn.close()

    outcome = run_rescore(daily_settings, date=daily_outcome.date)
    assert outcome.non_runners >= 1
    assert any(v["runner_id"] == target.runner_id for v in outcome.voided)

    conn = init_db(daily_settings.database_path)
    row = conn.execute(
        "SELECT status, reason FROM suggestions WHERE runner_id=? AND date=?",
        (target.runner_id, daily_outcome.date),
    ).fetchone()
    # restore for other tests in the module
    conn.execute("UPDATE runners SET status='declared' WHERE id=?", (target.runner_id,))
    conn.execute("UPDATE suggestions SET status='open', reason=NULL WHERE runner_id=? AND date=?",
                 (target.runner_id, daily_outcome.date))
    conn.commit()
    conn.close()
    assert row["status"] == "withdrawn"
    assert row["reason"] == "non-runner"
    assert "VOID" in outcome.render_terminal()


def test_rescore_raises_probabilities_when_an_unbacked_rival_comes_out(
        daily_settings, daily_outcome):
    """The withdrawn horse is usually one we never backed.

    Renormalising over our own selections alone would leave their chances
    untouched, which is exactly what the 10:15 run exists to prevent.
    """
    suggestion = daily_outcome.suggestions[0]
    conn = init_db(daily_settings.database_path)
    # pick a rival in the same race that carries NO suggestion of its own
    rival = conn.execute(
        """SELECT r.id FROM runners r
           WHERE r.race_id = ? AND r.id != ? AND r.status = 'declared'
             AND r.id NOT IN (SELECT runner_id FROM suggestions WHERE date = ?)
           LIMIT 1""",
        (suggestion.race_id, suggestion.runner_id, daily_outcome.date),
    ).fetchone()
    assert rival is not None, "expected an unbacked rival in the race"

    before = conn.execute(
        "SELECT blend_prob, ev FROM suggestions WHERE runner_id=? AND date=?",
        (suggestion.runner_id, daily_outcome.date),
    ).fetchone()
    conn.execute("UPDATE runners SET status='nonrunner' WHERE id=?", (rival["id"],))
    conn.commit()
    conn.close()

    outcome = run_rescore(daily_settings, date=daily_outcome.date)

    conn = init_db(daily_settings.database_path)
    after = conn.execute(
        "SELECT blend_prob, ev, price_floor FROM suggestions WHERE runner_id=? AND date=?",
        (suggestion.runner_id, daily_outcome.date),
    ).fetchone()
    conn.execute("UPDATE runners SET status='declared' WHERE id=?", (rival["id"],))
    conn.commit()
    conn.close()

    assert outcome.repriced >= 1, "no suggestion was repriced by the withdrawal"
    assert after["blend_prob"] > before["blend_prob"] + 1e-9
    assert after["ev"] > before["ev"] + 1e-9
    # a stronger chance means the bet still stands at a shorter price
    assert after["price_floor"] < suggestion.price_floor + 1e-9

    # restore the pre-test probabilities for the other tests in this module
    run_rescore(daily_settings, date=daily_outcome.date)


def test_rescore_withdraws_suggestions_whose_edge_collapsed(daily_settings,
                                                            daily_outcome):
    """A suggestion that no longer clears min_edge must be pulled, with a reason."""
    suggestion = daily_outcome.suggestions[-1]
    conn = init_db(daily_settings.database_path)
    original = conn.execute(
        "SELECT blend_prob FROM race_scores WHERE runner_id=? AND date=?",
        (suggestion.runner_id, daily_outcome.date),
    ).fetchone()["blend_prob"]
    # collapse the scored probability: the value is gone
    conn.execute(
        "UPDATE race_scores SET blend_prob=0.001 WHERE runner_id=? AND date=?",
        (suggestion.runner_id, daily_outcome.date),
    )
    conn.commit()
    conn.close()

    outcome = run_rescore(daily_settings, date=daily_outcome.date)

    conn = init_db(daily_settings.database_path)
    row = conn.execute(
        "SELECT status, reason FROM suggestions WHERE runner_id=? AND date=?",
        (suggestion.runner_id, daily_outcome.date),
    ).fetchone()
    # restore state for the other tests in this module
    conn.execute("UPDATE race_scores SET blend_prob=? WHERE runner_id=? AND date=?",
                 (original, suggestion.runner_id, daily_outcome.date))
    conn.execute(
        "UPDATE suggestions SET status='open', reason=NULL WHERE runner_id=? AND date=?",
        (suggestion.runner_id, daily_outcome.date),
    )
    conn.commit()
    conn.close()

    assert row["status"] == "withdrawn"
    assert "edge fell" in row["reason"]
    assert any(w["runner_id"] == suggestion.runner_id for w in outcome.withdrawn)


def test_daily_persists_the_whole_scored_card(daily_settings, daily_outcome):
    """Every runner is scored, not only the ones worth backing."""
    conn = init_db(daily_settings.database_path)
    scored = conn.execute(
        "SELECT COUNT(*) n FROM race_scores WHERE date=?", (daily_outcome.date,)
    ).fetchone()["n"]
    suggested = conn.execute(
        "SELECT COUNT(*) n FROM suggestions WHERE date=?", (daily_outcome.date,)
    ).fetchone()["n"]
    conn.close()
    assert scored == daily_outcome.runners_considered
    assert scored > suggested


def test_rescore_with_no_open_suggestions(daily_settings):
    outcome = run_rescore(daily_settings, date="2019-01-01")
    assert "No open suggestions" in outcome.message


def test_blend_is_fitted_against_the_market_it_will_face(daily_settings):
    """The live market is the morning exchange, not Betfair SP.

    BSP does not exist when the daily run happens. Fitting the blend on BSP
    (a sharper market) and applying it to morning prices would systematically
    underweight the model, so the history used to fit the blend must be
    priced from the same source the suggestions are priced against.
    """
    from furlong.db import init_db
    from furlong.modeling.market import market_probabilities
    from furlong.pipeline.daily import LIVE_MARKET_SOURCE, score_date

    assert LIVE_MARKET_SOURCE == "exchange"

    conn = init_db(daily_settings.database_path)
    date = _open_card_date(daily_settings)
    scored = score_date(daily_settings, conn, date)
    # today's runners must be priced from the live source
    expected = market_probabilities(conn, scored, prefer=LIVE_MARKET_SOURCE)
    conn.close()

    merged = scored.merge(expected, on="runner_id", suffixes=("", "_expected"))
    assert (merged["market_source"] != "bsp").all(), "BSP cannot exist pre-race"
    assert merged["market_prob"].sub(merged["market_prob_expected"]).abs().max() < 1e-9


# -- degenerate inputs ------------------------------------------------------

def test_first_day_of_data_fails_with_a_clear_message(settings):
    """No history is a normal day-one state, not an IndexError."""
    from furlong.db import init_db
    from furlong.repo import RaceRecord, RunnerRecord
    from furlong import repo as repo_mod
    from furlong.pipeline.daily import score_date

    conn = init_db(settings.database_path)
    race_id = repo_mod.upsert_race(conn, RaceRecord(
        source_id="R1", course="Curragh", country="IRE", date="2026-05-01",
        start_time_utc="2026-05-01T14:00:00+00:00", race_type="flat",
        distance_m=1600, going="good", status="scheduled",
    ))
    for name in ("A", "B", "C"):
        repo_mod.upsert_runner(conn, race_id, RunnerRecord(horse=name))
    conn.commit()

    with pytest.raises(ValueError, match="no completed races before"):
        score_date(settings, conn, "2026-05-01")
    conn.close()


def test_walkover_is_never_advised_as_a_certainty(daily_settings, daily_outcome):
    """A one-runner race scores its runner at 100%; that is a bug, not a bet."""
    conn = init_db(daily_settings.database_path)
    # strip a race down to a single standing runner
    race_id = daily_outcome.suggestions[0].race_id
    rivals = conn.execute(
        "SELECT id FROM runners WHERE race_id=? ORDER BY id", (race_id,)
    ).fetchall()
    keep = rivals[0]["id"]
    for row in rivals[1:]:
        conn.execute("UPDATE runners SET status='nonrunner' WHERE id=?", (row["id"],))
    conn.commit()
    conn.close()

    outcome = run_daily(daily_settings, date=daily_outcome.date, dry_run=True)

    conn = init_db(daily_settings.database_path)
    for row in rivals[1:]:
        conn.execute("UPDATE runners SET status='declared' WHERE id=?", (row["id"],))
    conn.commit()
    conn.close()

    assert all(s.race_id != race_id for s in outcome.suggestions)
    assert all(s.blend_prob <= daily_settings.max_prob for s in outcome.suggestions)
