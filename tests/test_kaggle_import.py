"""The Kaggle UK+IRE dataset importer.

Fixtures mimic the dataset's two-file-per-year shape and its documented
column names. Real files vary between vintages, which is why every field is
resolved through candidate names and `--inspect` exists.
"""

import pytest

from furlong.db import init_db
from furlong.sources.kaggle_import import (
    _odds,
    _position,
    find_pairs,
    import_kaggle_dataset,
    inspect,
)

RACES = """rid,course,date,time,metric,condition,rclass,countryCode,title,hurdles,runners
101,Curragh,2015-05-01,14:30,1600,Good,3,IRE,Handicap,,3
102,Ascot,2015-05-02,15:05,2400,Good To Firm,2,GB,Novices Hurdle,hurdle,3
103,Leopardstown,2015-05-03,16:00,2000,Soft,4,IRE,Maiden,,1
"""

HORSES = """rid,horseName,age,saddle,decimalPrice,trainerName,jockeyName,position,weight,RPR,TR,OR,positionL
101,Harp Melody,5,4,0.25,W P Mullins,P Townend,1,140,105,98,95,0
101,Liffey Runner,4,1,0.20,A P O'Brien,R Moore,2,138,102,95,92,1.5
101,Shannon Mist,6,2,0.10,J Harrington,S Foley,PU,136,,,84,
102,English Rose,4,3,0.50,J Gosden,F Dettori,1,142,110,101,101,0
102,Windsor Lad,5,2,0.125,M Johnston,J Doyle,2,140,104,97,96,2.0
102,Berkshire Boy,6,1,0.05,N Henderson,N de Boinville,3,138,99,93,90,6.0
103,Lone Runner,4,1,0.90,D Weld,C O'Donoghue,1,140,100,95,90,0
"""


@pytest.fixture
def dataset_dir(tmp_path):
    (tmp_path / "races_2015.csv").write_text(RACES)
    (tmp_path / "horses_2015.csv").write_text(HORSES)
    return tmp_path


# -- helpers ---------------------------------------------------------------

def test_position_parses_only_finishers():
    assert _position("1") == 1
    assert _position(" 12 ") == 12
    # non-finishers: pulled up, fell, unseated, brought down, refused
    for code in ("PU", "F", "UR", "BD", "RO", "", None):
        assert _position(code) is None


def test_odds_accepts_both_vintages():
    """Some vintages store a probability (0.25), others a decimal price (5.0)."""
    assert _odds("0.25") == pytest.approx(4.0)
    assert _odds("0.10") == pytest.approx(10.0)
    assert _odds("5.0") == pytest.approx(5.0)
    assert _odds("0") is None
    assert _odds("") is None


# -- discovery and inspection ----------------------------------------------

def test_find_pairs(dataset_dir):
    pairs = find_pairs(dataset_dir)
    assert len(pairs) == 1
    assert pairs[0][0].name == "races_2015.csv"
    assert pairs[0][1].name == "horses_2015.csv"


def test_find_pairs_ignores_unmatched_files(tmp_path):
    (tmp_path / "races_2015.csv").write_text(RACES)
    (tmp_path / "notes.csv").write_text("a,b\n1,2\n")
    assert find_pairs(tmp_path) == []  # no matching horses file


def test_inspect_reports_detected_columns(dataset_dir):
    report = inspect(dataset_dir)
    assert report["pairs"] == 1
    assert report["races"]["mapped"]["course"] == "course"
    assert report["races"]["mapped"]["distance"] == "metric"
    assert report["races"]["mapped"]["going"] == "condition"
    assert report["runners"]["mapped"]["horse"] == "horseName"
    assert report["runners"]["mapped"]["decimal_odds"] == "decimalPrice"
    assert report["runners"]["mapped"]["official_rating"] == "OR"


def test_inspect_on_empty_directory(tmp_path):
    assert inspect(tmp_path)["pairs"] == 0


# -- import ----------------------------------------------------------------

def test_import_joins_races_to_runners(settings, dataset_dir):
    result = import_kaggle_dataset(settings, dataset_dir)
    # the one-runner race is skipped: it is not a race
    assert result.races == 2
    assert result.runners == 6

    conn = init_db(settings.database_path)
    rows = conn.execute(
        """SELECT c.name AS course, c.country, ra.going, ra.race_type, ra.distance_m,
                  ra.field_size FROM races ra JOIN courses c ON c.id = ra.course_id
           ORDER BY ra.date"""
    ).fetchall()
    conn.close()

    curragh, ascot = rows
    assert curragh["course"] == "Curragh" and curragh["country"] == "IRE"
    assert curragh["going"] == "good" and curragh["race_type"] == "flat"
    assert curragh["distance_m"] == 1600
    assert curragh["field_size"] == 3
    # "Novices Hurdle" is jumps, and "Good To Firm" must not match plain "good"
    assert ascot["race_type"] == "nh"
    assert ascot["going"] == "good_to_firm"


def test_import_maps_results_and_non_finishers(settings, dataset_dir):
    import_kaggle_dataset(settings, dataset_dir)
    conn = init_db(settings.database_path)
    rows = conn.execute(
        """SELECT h.name, r.status, r.finish_pos, r.win_flag, r.official_rating, r.draw
           FROM runners r JOIN horses h ON h.id = r.horse_id ORDER BY h.name"""
    ).fetchall()
    conn.close()
    by_name = {r["name"]: r for r in rows}

    assert by_name["Harp Melody"]["win_flag"] == 1
    assert by_name["Harp Melody"]["official_rating"] == 95
    assert by_name["Harp Melody"]["draw"] == 4
    assert by_name["Liffey Runner"]["finish_pos"] == 2
    # pulled up: no finishing position, so not a completed run
    assert by_name["Shannon Mist"]["status"] == "nonrunner"
    assert by_name["Shannon Mist"]["finish_pos"] is None


def test_import_records_starting_prices(settings, dataset_dir):
    import_kaggle_dataset(settings, dataset_dir)
    conn = init_db(settings.database_path)
    row = conn.execute(
        """SELECT o.odds_decimal, o.bookmaker FROM odds_snapshots o
           JOIN runners r ON r.id = o.runner_id
           JOIN horses h ON h.id = r.horse_id WHERE h.name = 'Harp Melody'"""
    ).fetchone()
    conn.close()
    assert row["bookmaker"] == "SP"
    assert row["odds_decimal"] == pytest.approx(4.0)  # 0.25 probability -> 4.0


def test_reimport_is_idempotent(settings, dataset_dir):
    import_kaggle_dataset(settings, dataset_dir)
    import_kaggle_dataset(settings, dataset_dir)
    conn = init_db(settings.database_path)
    assert conn.execute("SELECT COUNT(*) n FROM races").fetchone()["n"] == 2
    assert conn.execute("SELECT COUNT(*) n FROM runners").fetchone()["n"] == 6
    conn.close()


def test_year_filter(settings, tmp_path):
    (tmp_path / "races_2015.csv").write_text(RACES)
    (tmp_path / "horses_2015.csv").write_text(HORSES)
    (tmp_path / "races_2016.csv").write_text(RACES.replace("2015-", "2016-")
                                             .replace("10", "20").replace("rid", "rid", 1))
    (tmp_path / "horses_2016.csv").write_text(HORSES.replace("10", "20"))
    result = import_kaggle_dataset(settings, tmp_path, years=("2015",))
    assert result.files == 1


def test_missing_directory_reports_clearly(settings, tmp_path):
    result = import_kaggle_dataset(settings, tmp_path / "nothing-here")
    assert result.races == 0
    assert "no races_YYYY.csv" in result.errors[0]


def test_imported_data_flows_into_features(settings, dataset_dir):
    """The whole point: imported history must be usable by the model layer."""
    from furlong.features.dataset import build_dataset

    import_kaggle_dataset(settings, dataset_dir)
    conn = init_db(settings.database_path)
    dataset = build_dataset(conn)
    conn.close()
    # two races survive, each with one winner among the runners that completed
    assert set(dataset.frame["race_id"].unique()).__len__() == 2
    assert dataset.frame.groupby("race_id")["win_flag"].sum().eq(1).all()
