"""The rpscrape-schema SQLite importer (raceform.db).

The fixture reproduces the schema published with the dataset, including its
awkward conventions: fractional starting prices, stones-and-pounds weights,
letter codes for non-finishers, and the country in brackets after the course.
"""

import sqlite3

import pytest

from furlong.db import init_db
from furlong.sources.raceform_db import (
    import_raceform_db,
    inspect,
    parse_fractional_sp,
    parse_position,
    parse_weight_lbs,
)

SCHEMA = """
CREATE TABLE data (
    date NUMERIC, course TEXT, race_id INTEGER, off TEXT,
    race_name TEXT, type TEXT, class TEXT, pattern TEXT,
    rating_band TEXT, age_band TEXT, sex_rest TEXT, dist TEXT,
    going TEXT, ran INTEGER, num INTEGER, pos INTEGER,
    draw INTEGER, ovr_btn NUMERIC, btn NUMERIC, horse TEXT,
    age INTEGER, sex TEXT, wgt TEXT, hg TEXT,
    time TEXT, sp TEXT, jockey TEXT, trainer TEXT,
    prize INTEGER, [or] INTEGER, rpr INTEGER, ts INTEGER,
    sire TEXT, dam TEXT, damsire TEXT, owner TEXT, comment TEXT
);
"""

ROWS = [
    # an Irish flat race: winner, runner-up, and one pulled up
    ("2024-05-01", "Curragh (IRE)", 5001, "2:35", "Irish Handicap", "Flat", "Class 3",
     "", "", "3yo+", "", "1m", "Good", 3, 1, 1, 4, 0, 0, "Harp Melody", 5, "g",
     "9-7", "", "1:40.2", "5/1", "P Townend", "W P Mullins", 12000, 95, 105, 98,
     "Sire A", "Dam A", "Damsire A", "Owner A", "made all"),
    ("2024-05-01", "Curragh (IRE)", 5001, "2:35", "Irish Handicap", "Flat", "Class 3",
     "", "", "3yo+", "", "1m", "Good", 3, 2, 2, 1, 1.5, 1.5, "Liffey Runner", 4, "f",
     "9-5", "b", "1:40.4", "7/2", "R Moore", "A P O'Brien", 4000, 92, 102, 95,
     "Sire B", "Dam B", "Damsire B", "Owner B", "kept on"),
    ("2024-05-01", "Curragh (IRE)", 5001, "2:35", "Irish Handicap", "Flat", "Class 3",
     "", "", "3yo+", "", "1m", "Good", 3, 3, "PU", 2, None, None, "Shannon Mist", 6,
     "m", "9-0", "", "", "12/1", "S Foley", "J Harrington", 0, 84, None, None,
     "Sire C", "Dam C", "Damsire C", "Owner C", "pulled up"),
    # a British jumps race
    ("2024-05-02", "Ascot", 5002, "3:10", "Novices Hurdle", "Hurdle", "Class 2",
     "", "", "4yo+", "", "2m4f", "Good To Firm", 2, 1, 1, None, 0, 0, "English Rose",
     4, "f", "11-2", "", "4:50.1", "Evens", "F Dettori", "J Gosden", 20000, 101, 110,
     101, "Sire D", "Dam D", "Damsire D", "Owner D", "always travelling"),
    ("2024-05-02", "Ascot", 5002, "3:10", "Novices Hurdle", "Hurdle", "Class 2",
     "", "", "4yo+", "", "2m4f", "Good To Firm", 2, 2, 2, None, 6, 6, "Windsor Lad",
     5, "g", "11-0", "p", "4:51.3", "4/5", "J Doyle", "M Johnston", 7000, 96, 104,
     97, "Sire E", "Dam E", "Damsire E", "Owner E", "no extra"),
    # a French card, which must be filtered out
    ("2024-05-03", "Auteuil (FR)", 5003, "2:35", "Prix Isopani", "Hurdle", "",
     "", "", "3yo", "", "2m2f", "Very Soft", 2, 1, 1, None, 0, 0, "Paris Star", 3,
     "g", "10-0", "", "", "3/1", "J Reveley", "F Nicolle", 30000, None, None, None,
     "Sire F", "Dam F", "Damsire F", "Owner F", ""),
    ("2024-05-03", "Auteuil (FR)", 5003, "2:35", "Prix Isopani", "Hurdle", "",
     "", "", "3yo", "", "2m2f", "Very Soft", 2, 2, 2, None, 3, 3, "Seine Runner", 3,
     "g", "10-0", "", "", "5/2", "A Duchene", "G Macaire", 12000, None, None, None,
     "Sire G", "Dam G", "Damsire G", "Owner G", ""),
]


@pytest.fixture
def raceform_db(tmp_path):
    path = tmp_path / "raceform.db"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO data VALUES (" + ",".join("?" * 37) + ")", ROWS
    )
    conn.commit()
    conn.close()
    return path


# -- the dataset's awkward column conventions -------------------------------

def test_fractional_starting_prices():
    assert parse_fractional_sp("5/1") == pytest.approx(6.0)
    assert parse_fractional_sp("7/2") == pytest.approx(4.5)
    assert parse_fractional_sp("4/5") == pytest.approx(1.8)     # odds-on
    assert parse_fractional_sp("100/30") == pytest.approx(4.333, abs=1e-3)
    for evens in ("Evens", "EvS", "evens", "1/1"):
        assert parse_fractional_sp(evens) == pytest.approx(2.0)
    assert parse_fractional_sp("") is None
    assert parse_fractional_sp(None) is None
    assert parse_fractional_sp("nonsense") is None


def test_stones_and_pounds_weights():
    assert parse_weight_lbs("11-2") == 156.0     # 11 stone 2 lb
    assert parse_weight_lbs("9-7") == 133.0
    assert parse_weight_lbs("10-0") == 140.0
    assert parse_weight_lbs("") is None
    assert parse_weight_lbs(None) is None


def test_non_finisher_codes():
    assert parse_position("1") == 1
    assert parse_position("12") == 12
    assert parse_position("1D") == 1             # dead-heat suffix
    for code in ("PU", "F", "UR", "BD", "RO", "SU", "DSQ", ""):
        assert parse_position(code) is None


# -- inspection ------------------------------------------------------------

def test_inspect_reports_shape(raceform_db):
    report = inspect(raceform_db)
    assert report["rows"] == len(ROWS)
    assert report["races"] == 3
    assert report["first"] == "2024-05-01"
    assert report["last"] == "2024-05-03"
    assert "ovr_btn" in report["columns"]


# -- import ----------------------------------------------------------------

def test_import_filters_to_uk_and_ireland(raceform_db, settings):
    result = import_raceform_db(settings, raceform_db)
    assert result.races == 2
    assert result.runners == 5
    assert result.skipped_foreign == 1

    conn = init_db(settings.database_path)
    courses = {r["name"]: r["country"] for r in
               conn.execute("SELECT name, country FROM courses")}
    conn.close()
    assert courses == {"Curragh": "IRE", "Ascot": "GB"}


def test_import_maps_race_detail(raceform_db, settings):
    import_raceform_db(settings, raceform_db)
    conn = init_db(settings.database_path)
    rows = conn.execute(
        """SELECT c.name course, ra.race_type, ra.going, ra.race_class,
                  ra.field_size, ra.start_time_utc
           FROM races ra JOIN courses c ON c.id = ra.course_id ORDER BY ra.date"""
    ).fetchall()
    conn.close()
    curragh, ascot = rows
    assert curragh["race_type"] == "flat" and curragh["going"] == "good"
    assert curragh["race_class"] == 3
    assert curragh["field_size"] == 3
    # "2:35" must be padded to a valid ISO time
    assert curragh["start_time_utc"].endswith("T02:35:00+00:00")
    assert ascot["race_type"] == "nh"
    assert ascot["going"] == "good_to_firm"


def test_import_parses_runner_detail(raceform_db, settings):
    import_raceform_db(settings, raceform_db)
    conn = init_db(settings.database_path)
    rows = conn.execute(
        """SELECT h.name, r.status, r.finish_pos, r.win_flag, r.weight_lbs,
                  r.official_rating, r.beaten_lengths, r.draw
           FROM runners r JOIN horses h ON h.id = r.horse_id"""
    ).fetchall()
    conn.close()
    by_name = {r["name"]: r for r in rows}

    assert by_name["Harp Melody"]["win_flag"] == 1
    assert by_name["Harp Melody"]["weight_lbs"] == 133.0      # 9-7
    assert by_name["Harp Melody"]["official_rating"] == 95
    assert by_name["Harp Melody"]["draw"] == 4
    assert by_name["Windsor Lad"]["beaten_lengths"] == 6.0    # ovr_btn, not btn
    # pulled up: not a finishing position
    assert by_name["Shannon Mist"]["status"] == "nonrunner"
    assert by_name["Shannon Mist"]["finish_pos"] is None


def test_import_records_starting_prices(raceform_db, settings):
    import_raceform_db(settings, raceform_db)
    conn = init_db(settings.database_path)
    prices = {
        r["name"]: r["odds_decimal"] for r in conn.execute(
            """SELECT h.name, o.odds_decimal FROM odds_snapshots o
               JOIN runners r ON r.id = o.runner_id
               JOIN horses h ON h.id = r.horse_id"""
        )
    }
    conn.close()
    assert prices["Harp Melody"] == pytest.approx(6.0)    # 5/1
    assert prices["Liffey Runner"] == pytest.approx(4.5)  # 7/2
    assert prices["English Rose"] == pytest.approx(2.0)   # Evens
    assert prices["Windsor Lad"] == pytest.approx(1.8)    # 4/5


def test_date_range_filter(raceform_db, settings):
    result = import_raceform_db(settings, raceform_db, since="2024-05-02")
    assert result.races == 1          # Ascot only; the French card is filtered too
    assert result.runners == 2


def test_reimport_is_idempotent(raceform_db, settings):
    import_raceform_db(settings, raceform_db)
    import_raceform_db(settings, raceform_db)
    conn = init_db(settings.database_path)
    assert conn.execute("SELECT COUNT(*) n FROM races").fetchone()["n"] == 2
    assert conn.execute("SELECT COUNT(*) n FROM runners").fetchone()["n"] == 5
    conn.close()


def test_missing_database_reports_clearly(settings, tmp_path):
    result = import_raceform_db(settings, tmp_path / "absent.db")
    assert result.races == 0
    assert "not found" in result.errors[0]


def test_imported_data_reaches_the_feature_builder(raceform_db, settings):
    from furlong.features.dataset import build_dataset

    import_raceform_db(settings, raceform_db)
    conn = init_db(settings.database_path)
    dataset = build_dataset(conn)
    conn.close()
    assert len(dataset.frame) > 0
    assert dataset.frame.groupby("race_id")["win_flag"].sum().eq(1).all()
