import textwrap

from furlong import repo
from furlong.db import init_db
from furlong.repo import RaceRecord, RunnerRecord
from furlong.sources.betfair_bsp import (
    ingest_files,
    market_from_filename,
    normalise_horse_name,
    parse_event_dt,
)


def test_normalise_horse_name():
    assert normalise_horse_name("Sea The Stars (IRE)") == "SEATHESTARS"
    assert normalise_horse_name("L'Escargot") == "LESCARGOT"
    assert normalise_horse_name("  tiger roll (IRE) ") == "TIGERROLL"
    assert normalise_horse_name("Red Rum") == "REDRUM"


def test_market_from_filename():
    assert market_from_filename("dwbfpricesirewin01072024.csv") == "win"
    assert market_from_filename("/x/dwbfpricesukplace01072024.csv") == "place"


def test_parse_event_dt():
    assert parse_event_dt("01-07-2024 14:30") == "2024-07-01"
    assert parse_event_dt("garbage") is None


def _seed_race(settings):
    conn = init_db(settings.database_path)
    race_id = repo.upsert_race(conn, RaceRecord(
        source_id="R1", course="Curragh", country="IRE", date="2024-07-01",
        start_time_utc="2024-07-01T14:30:00+00:00", race_type="flat",
        distance_m=1600, going="good", status="result",
    ))
    ids = {}
    for name in ("Sea The Stars", "Tiger Roll"):
        ids[name] = repo.upsert_runner(conn, race_id, RunnerRecord(
            horse=name, status="ran", finish_pos=1, win_flag=1,
        ))
    conn.commit()
    conn.close()
    return ids


def test_ingest_matches_and_reports_unmatched(settings, tmp_path):
    ids = _seed_race(settings)
    csv_file = tmp_path / "dwbfpricesirewin01072024.csv"
    csv_file.write_text(textwrap.dedent("""\
        EVENT_ID,MENU_HINT,EVENT_NAME,EVENT_DT,SELECTION_ID,SELECTION_NAME,WIN_LOSE,BSP,PPWAP,MORNINGWAP,PPMAX,PPMIN,IPMAX,IPMIN,MORNINGTRADEDVOL,PPTRADEDVOL,IPTRADEDVOL
        1234,IRE / Curr 1st Jul,1m Stks,01-07-2024 14:30,111,Sea The Stars (IRE),1,2.88,2.9,3.1,3.2,2.7,2.9,1.01,1000,50000,20000
        1234,IRE / Curr 1st Jul,1m Stks,01-07-2024 14:30,112,Tiger Roll,0,15.0,14.5,16.0,17.0,13.0,60,14,500,9000,3000
        1234,IRE / Curr 1st Jul,1m Stks,01-07-2024 14:30,113,Unknown Horse,0,8.0,8.2,8.4,9.0,7.8,20,8,100,2000,500
    """))

    result = ingest_files(settings, [csv_file])
    assert result.files == 1
    assert result.rows_ingested == 2
    assert result.rows_unmatched == 1

    conn = init_db(settings.database_path)
    row = conn.execute(
        "SELECT bsp, ppwap, morning_wap FROM bsp_prices WHERE runner_id=? AND market='win'",
        (ids["Sea The Stars"],),
    ).fetchone()
    assert row["bsp"] == 2.88
    assert row["ppwap"] == 2.9
    assert row["morning_wap"] == 3.1
    conn.close()


def test_reingest_is_idempotent(settings, tmp_path):
    _seed_race(settings)
    csv_file = tmp_path / "dwbfpricesirewin01072024.csv"
    csv_file.write_text(
        "EVENT_ID,MENU_HINT,EVENT_NAME,EVENT_DT,SELECTION_ID,SELECTION_NAME,WIN_LOSE,BSP,PPWAP,MORNINGWAP,PPMAX,PPMIN,IPMAX,IPMIN,MORNINGTRADEDVOL,PPTRADEDVOL,IPTRADEDVOL\n"
        "1,IRE / Curr,1m,01-07-2024 14:30,111,Sea The Stars (IRE),1,2.88,2.9,3.1,,,,,,,\n"
    )
    ingest_files(settings, [csv_file])
    ingest_files(settings, [csv_file])
    conn = init_db(settings.database_path)
    n = conn.execute("SELECT COUNT(*) n FROM bsp_prices").fetchone()["n"]
    assert n == 1
    conn.close()


def test_null_bsp_handled(settings, tmp_path):
    ids = _seed_race(settings)
    csv_file = tmp_path / "dwbfpricesirewin01072024.csv"
    csv_file.write_text(
        "EVENT_ID,MENU_HINT,EVENT_NAME,EVENT_DT,SELECTION_ID,SELECTION_NAME,WIN_LOSE,BSP,PPWAP,MORNINGWAP,PPMAX,PPMIN,IPMAX,IPMIN,MORNINGTRADEDVOL,PPTRADEDVOL,IPTRADEDVOL\n"
        "1,IRE / Curr,1m,01-07-2024 14:30,111,Sea The Stars (IRE),1,NULL,2.9,,,,,,,,\n"
    )
    result = ingest_files(settings, [csv_file])
    assert result.rows_ingested == 1
    conn = init_db(settings.database_path)
    row = conn.execute("SELECT bsp, ppwap FROM bsp_prices WHERE runner_id=?",
                       (ids["Sea The Stars"],)).fetchone()
    assert row["bsp"] is None
    assert row["ppwap"] == 2.9
    conn.close()
