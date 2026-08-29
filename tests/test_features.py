import numpy as np
import pandas as pd
import pytest

from furlong import repo
from furlong.features.builder import (
    BASE_WIN_RATE,
    FEATURE_COLUMNS,
    HORSE_SHRINK_M,
    TRAINER_SHRINK_M,
    compute_features,
)
from furlong.features.dataset import build_dataset, chronological_splits


def _mini_runs(rows):
    """Build a runs frame in the shape produced by repo.load_runs."""
    defaults = dict(
        race_source_id="", race_type="flat", distance_m=1600.0, going="good",
        race_class=3, race_status="result", course="Curragh", country="IRE",
        trainer_id=None, trainer=None, jockey_id=None, jockey=None,
        draw=None, weight_lbs=None, official_rating=None, age=None,
        status="ran", beaten_lengths=None,
    )
    frame = pd.DataFrame([{**defaults, **row} for row in rows])
    frame["start_time_utc"] = frame["date"] + "T14:00:00+00:00"
    return frame


def test_hand_computed_career_stats():
    runs = _mini_runs([
        dict(runner_id=1, race_id=1, horse_id=7, horse="A", date="2024-01-01",
             field_size=5, finish_pos=1, win_flag=1),
        dict(runner_id=2, race_id=2, horse_id=7, horse="A", date="2024-02-01",
             field_size=6, finish_pos=3, win_flag=0),
        dict(runner_id=3, race_id=3, horse_id=7, horse="A", date="2024-03-01",
             field_size=8, finish_pos=None, win_flag=None, status="declared"),
    ])
    features = compute_features(runs)
    target = features[features["runner_id"] == 3].iloc[0]

    assert target["career_starts"] == pytest.approx(np.log1p(2))
    expected_win_rate = (1 + HORSE_SHRINK_M * BASE_WIN_RATE) / (2 + HORSE_SHRINK_M)
    assert target["career_win_rate"] == pytest.approx(expected_win_rate)
    # days since last run: 2024-02-01 -> 2024-03-01 = 29 days
    assert target["days_since_run"] == pytest.approx(np.log1p(29))
    assert target["first_timer"] == 0.0
    assert target["won_last"] == 0.0  # last run was the 3rd-of-6
    # last_finish_norm for pos 3 of 6: 1 - 2/5 = 0.6
    assert target["last_finish_norm"] == pytest.approx(0.6)
    # recent form: decay-weighted mean of [1.0 (win of 5), 0.6], weights [0.7, 1.0]
    expected_form = (0.7 * 1.0 + 1.0 * 0.6) / 1.7
    assert target["recent_form"] == pytest.approx(expected_form)


def test_first_timer_gets_priors():
    runs = _mini_runs([
        dict(runner_id=1, race_id=1, horse_id=1, horse="Debutant", date="2024-05-01",
             field_size=10, finish_pos=None, win_flag=None, status="declared"),
    ])
    features = compute_features(runs)
    row = features.iloc[0]
    assert row["first_timer"] == 1.0
    assert row["career_win_rate"] == pytest.approx(BASE_WIN_RATE)
    assert row["recent_form"] == pytest.approx(0.5)


def test_same_day_races_excluded_from_history():
    runs = _mini_runs([
        dict(runner_id=1, race_id=1, horse_id=3, horse="B", date="2024-01-01",
             field_size=6, finish_pos=1, win_flag=1),
        dict(runner_id=2, race_id=2, horse_id=3, horse="B", date="2024-02-01",
             field_size=6, finish_pos=1, win_flag=1),
        dict(runner_id=3, race_id=3, horse_id=3, horse="B", date="2024-02-01",
             field_size=6, finish_pos=4, win_flag=0),
    ])
    features = compute_features(runs).set_index("runner_id")
    # both same-day rows see exactly one prior start (the January run)
    assert features.loc[2, "career_starts"] == pytest.approx(np.log1p(1))
    assert features.loc[3, "career_starts"] == pytest.approx(np.log1p(1))
    assert features.loc[3, "won_last"] == 1.0  # January win, not the same-day race


def test_trainer_shrinkage():
    runs = _mini_runs([
        dict(runner_id=1, race_id=1, horse_id=1, horse="A", trainer_id=5, trainer="T",
             date="2024-01-01", field_size=8, finish_pos=1, win_flag=1),
        dict(runner_id=2, race_id=2, horse_id=2, horse="B", trainer_id=5, trainer="T",
             date="2024-02-01", field_size=8, finish_pos=None, win_flag=None,
             status="declared"),
    ])
    features = compute_features(runs).set_index("runner_id")
    expected = (1 + TRAINER_SHRINK_M * BASE_WIN_RATE) / (1 + TRAINER_SHRINK_M)
    assert features.loc[2, "trainer_sr_career"] == pytest.approx(expected)
    assert features.loc[2, "trainer_sr_career"] < 0.2  # shrunk far from raw 100%


def test_no_leakage_from_future_results(world_conn):
    runs = repo.load_runs(world_conn)
    dates = sorted(runs["date"].unique())
    cutoff = dates[len(dates) // 2]

    truncated = runs[runs["date"] <= cutoff].reset_index(drop=True)
    features_full = compute_features(runs)
    features_trunc = compute_features(truncated)

    target_full = (
        features_full[features_full["date"] == cutoff]
        .set_index("runner_id")[FEATURE_COLUMNS]
        .sort_index()
    )
    target_trunc = (
        features_trunc[features_trunc["date"] == cutoff]
        .set_index("runner_id")[FEATURE_COLUMNS]
        .sort_index()
    )
    pd.testing.assert_frame_equal(target_full, target_trunc)


def test_features_have_no_nans(world_conn):
    dataset = build_dataset(world_conn)
    assert not dataset.frame[FEATURE_COLUMNS].isna().any().any()
    assert len(dataset.frame) > 1000


def test_dataset_groups_and_splits(world_conn):
    dataset = build_dataset(world_conn)
    sizes = dataset.group_sizes()
    assert sizes.sum() == len(dataset.frame)
    assert (sizes >= 2).all()
    # exactly one winner per group
    winners = dataset.frame.groupby("race_id")["win_flag"].sum()
    assert (winners == 1).all()

    splits = chronological_splits(dataset)
    frame = dataset.frame
    for index in (splits.train, splits.valid, splits.test):
        assert len(index) > 0
    train_races = set(frame.loc[splits.train, "race_id"])
    valid_races = set(frame.loc[splits.valid, "race_id"])
    test_races = set(frame.loc[splits.test, "race_id"])
    assert not (train_races & valid_races)
    assert not (valid_races & test_races)
    assert not (train_races & test_races)

    train_max = pd.to_datetime(frame.loc[splits.train, "date"]).max()
    valid_min = pd.to_datetime(frame.loc[splits.valid, "date"]).min()
    valid_max = pd.to_datetime(frame.loc[splits.valid, "date"]).max()
    test_min = pd.to_datetime(frame.loc[splits.test, "date"]).min()
    assert (valid_min - train_max).days > 10
    assert (test_min - valid_max).days > 10


# -- Elo ratings ------------------------------------------------------------

def test_elo_does_not_leak_across_races_on_the_same_day():
    """A trainer's 16:00 runner must not see their own 13:00 winner.

    Ratings are read as they stood at the end of the previous day, and the
    whole day's results are applied afterwards.
    """
    early_race = [
        dict(runner_id=1, race_id=1, horse_id=1, horse="A", trainer_id=5, trainer="T",
             date="2024-02-01", field_size=2, finish_pos=1, win_flag=1),
        dict(runner_id=2, race_id=1, horse_id=2, horse="B", trainer_id=6, trainer="U",
             date="2024-02-01", field_size=2, finish_pos=2, win_flag=0),
    ]
    late_race = [
        dict(runner_id=3, race_id=2, horse_id=3, horse="C", trainer_id=5, trainer="T",
             date="2024-02-01", field_size=2, finish_pos=None, win_flag=None,
             status="declared"),
        dict(runner_id=4, race_id=2, horse_id=4, horse="D", trainer_id=7, trainer="V",
             date="2024-02-01", field_size=2, finish_pos=None, win_flag=None,
             status="declared"),
    ]
    with_early = compute_features(_mini_runs(early_race + late_race)).set_index("runner_id")
    without_early = compute_features(_mini_runs(late_race)).set_index("runner_id")

    assert with_early.loc[3, "trainer_elo"] == pytest.approx(
        without_early.loc[3, "trainer_elo"]
    ), "same-day earlier race leaked into the trainer rating"


def test_elo_updates_across_days():
    """The rating must move once the day is over — otherwise it learns nothing."""
    day_one = [
        dict(runner_id=1, race_id=1, horse_id=1, horse="A", date="2024-02-01",
             field_size=2, finish_pos=1, win_flag=1),
        dict(runner_id=2, race_id=1, horse_id=2, horse="B", date="2024-02-01",
             field_size=2, finish_pos=2, win_flag=0),
    ]
    day_two = [
        dict(runner_id=3, race_id=2, horse_id=1, horse="A", date="2024-03-01",
             field_size=2, finish_pos=None, win_flag=None, status="declared"),
        dict(runner_id=4, race_id=2, horse_id=2, horse="B", date="2024-03-01",
             field_size=2, finish_pos=None, win_flag=None, status="declared"),
    ]
    features = compute_features(_mini_runs(day_one + day_two)).set_index("runner_id")
    assert features.loc[3, "elo"] > 0, "the winner's rating should have risen"
    assert features.loc[4, "elo"] < 0, "the loser's rating should have fallen"


def test_elo_still_updates_when_a_race_has_a_non_runner():
    """Withdrawals are routine; a race with one must not be discarded."""
    history = [
        dict(runner_id=1, race_id=1, horse_id=1, horse="A", date="2024-02-01",
             field_size=3, finish_pos=1, win_flag=1),
        dict(runner_id=2, race_id=1, horse_id=2, horse="B", date="2024-02-01",
             field_size=3, finish_pos=2, win_flag=0),
        dict(runner_id=3, race_id=1, horse_id=3, horse="C", date="2024-02-01",
             field_size=3, finish_pos=None, win_flag=None, status="nonrunner"),
    ]
    later = [
        dict(runner_id=4, race_id=2, horse_id=1, horse="A", date="2024-03-01",
             field_size=2, finish_pos=None, win_flag=None, status="declared"),
        dict(runner_id=5, race_id=2, horse_id=2, horse="B", date="2024-03-01",
             field_size=2, finish_pos=None, win_flag=None, status="declared"),
    ]
    features = compute_features(_mini_runs(history + later)).set_index("runner_id")
    assert features.loc[4, "elo"] > 0, "the winner learned nothing from a race with a NR"
    assert features.loc[5, "elo"] < 0


def test_elo_rank_pct_shares_ties():
    """A race of unraced horses must not be ranked by card position."""
    runs = _mini_runs([
        dict(runner_id=i, race_id=1, horse_id=i, horse=f"H{i}", date="2024-02-01",
             field_size=4, finish_pos=None, win_flag=None, status="declared")
        for i in range(1, 5)
    ])
    features = compute_features(runs)
    assert features["elo_rank_pct"].nunique() == 1
    assert features["elo_rank_pct"].iloc[0] == pytest.approx(0.5)


def test_performance_denominator_excludes_non_runners():
    """Finishing last of 10 that ran is 0.0, even if 12 were declared."""
    history = [
        dict(runner_id=i, race_id=1, horse_id=i, horse=f"H{i}", date="2024-01-01",
             field_size=3, finish_pos=i, win_flag=int(i == 1))
        for i in (1, 2)
    ] + [
        dict(runner_id=3, race_id=1, horse_id=3, horse="H3", date="2024-01-01",
             field_size=3, finish_pos=None, win_flag=None, status="nonrunner"),
    ]
    later = [
        dict(runner_id=4, race_id=2, horse_id=2, horse="H2", date="2024-02-01",
             field_size=5, finish_pos=None, win_flag=None, status="declared"),
    ]
    features = compute_features(_mini_runs(history + later)).set_index("runner_id")
    # H2 finished last of the two that ran: performance 0.0, not 1 - 1/2 = 0.5
    assert features.loc[4, "last_finish_norm"] == pytest.approx(0.0)
