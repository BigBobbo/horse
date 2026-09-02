"""The Betfair UK/IRE model-file importer.

The fixtures reproduce the awkward parts of the real files: two date
formats across vintages, race times in the publisher's Australian timezone,
a market id reused on a rescheduled day, duplicated runner rows, races the
settlement job never filled in, and a place market that never formed.
"""

import csv
import sqlite3
from datetime import datetime

import pytest

from furlong.db import init_db
from furlong.sources.betfair_hub import (
    finish_band,
    import_betfair_hub,
    inspect,
    parse_class,
    parse_country,
    parse_local_date,
    parse_market_name,
    parse_racetime_utc,
    published_names,
)

COLUMNS = [
    "LOCAL_RACE_DATE", "RACETIME", "COUNTRY_ID", "TRACK", "EVENT_ID",
    "WIN_MARKET_ID", "PLACE_MARKET_ID", "RACE_NAME", "WIN_MARKET_NAME",
    "RACE_NUMBER", "SELECTION_ID", "RUNNER_NAME", "RATED_PRICE",
    "WIN_BSP", "WIN_RESULT", "PLACE_BSP", "PLACE_RESULT",
]


def row(**kwargs) -> dict:
    base = {
        "LOCAL_RACE_DATE": "2024-05-01", "RACETIME": "2024-05-01 23:35:00",
        "COUNTRY_ID": "35", "TRACK": "Curragh", "EVENT_ID": "1",
        "WIN_MARKET_ID": "900", "PLACE_MARKET_ID": "901",
        "RACE_NAME": "Irish Handicap (Class C)", "WIN_MARKET_NAME": "1m Hcap",
        "RACE_NUMBER": "3", "SELECTION_ID": "1", "RUNNER_NAME": "Harp Melody",
        "RATED_PRICE": "3.10", "WIN_BSP": "4.2", "WIN_RESULT": "0",
        "PLACE_BSP": "1.7", "PLACE_RESULT": "0",
    }
    base.update(kwargs)
    return base


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def a_race(market="900", date="2024-05-01", n=6, winner=0, **shared):
    """A settled race: one winner, two placed, the rest unplaced."""
    out = []
    for i in range(n):
        out.append(row(
            WIN_MARKET_ID=market, LOCAL_RACE_DATE=date,
            SELECTION_ID=str(1000 + i), RUNNER_NAME=f"Horse {i}",
            WIN_BSP=f"{3.0 + i:.2f}",
            WIN_RESULT="1" if i == winner else "0",
            PLACE_BSP=f"{1.5 + i * 0.2:.2f}",
            PLACE_RESULT="1" if i in (winner, (winner + 1) % n) else "0",
            **shared,
        ))
    return out


# -- field parsers ---------------------------------------------------------

def test_slash_dates_are_read_day_first():
    # 6/01/2024 is 6 January, not 1 June: the yearly files are day-first.
    assert parse_local_date("6/01/2024") == "2024-01-06"
    assert parse_local_date("31/12/2025") == "2025-12-31"
    assert parse_local_date("2026-08-01") == "2026-08-01"
    assert parse_local_date("") is None
    assert parse_local_date("not a date") is None


def test_racetime_is_converted_from_the_publishers_timezone():
    # 00:25 on 7 January in Sydney (UTC+11) is 13:25 UTC on 6 January --
    # an ordinary British afternoon race, not an overnight one.
    assert parse_racetime_utc("7/01/2024 0:25", "2024-01-06") == "2024-01-06T13:25:00+00:00"
    # August: Sydney is UTC+10, so 22:33 is 12:33 UTC.
    assert (parse_racetime_utc("2026-08-01 22:33:00", "2026-08-01")
            == "2026-08-01T12:33:00+00:00")


def test_blank_racetime_falls_back_to_race_number_ordering():
    first = parse_racetime_utc("", "2025-03-04", race_number=1)
    third = parse_racetime_utc("", "2025-03-04", race_number=3)
    assert first.startswith("2025-03-04T12:")
    assert first < third


def test_market_name_gives_distance_and_code():
    metres, code = parse_market_name("1m4f Hcap")
    assert code == "flat"
    assert metres == pytest.approx(2414.0, abs=1.0)
    assert parse_market_name("2m4f Hcap Hrd")[1] == "nh"
    assert parse_market_name("2m Nov Chs")[1] == "nh"
    assert parse_market_name("2m NHF")[1] == "nh"
    assert parse_market_name("6f Nov Stks")[1] == "flat"
    assert parse_market_name("")[0] is None


def test_class_letters_map_to_british_class_numbers():
    assert parse_class("Old Newton Cup (Class B)") == 2
    assert parse_class("Something (Class G)") == 7
    assert parse_class("Handicap (Class 4)") == 4
    assert parse_class("A race with no class") is None


def test_country_ids():
    assert parse_country("1") == "GB"
    assert parse_country("35.0") == "IRE"
    assert parse_country("") is None
    assert parse_country("99") is None       # not GB or IRE: out of scope


def test_finish_band_orders_the_three_known_outcomes():
    won = finish_band(True, True, ran=10, places=3)
    placed = finish_band(False, True, ran=10, places=3)
    unplaced = finish_band(False, False, ran=10, places=3)
    assert won == 1
    assert won < placed < unplaced


def test_published_names_cover_yearly_then_monthly():
    names = published_names(datetime(2026, 3, 15))
    assert names[0].endswith("2024.csv")
    assert names[-1].endswith("2026-03.csv")
    assert sum(1 for n in names if "2026-" in n) == 3


# -- import ----------------------------------------------------------------

def test_import_writes_races_runners_and_bsp(tmp_path, settings):
    write_csv(tmp_path / "a.csv", a_race())
    result = import_betfair_hub(settings, tmp_path)
    assert result.races == 1
    assert result.runners == 6
    assert result.priced_runners == 6

    conn = init_db(settings.database_path)
    race = conn.execute("SELECT * FROM races").fetchone()
    assert race["country"] if "country" in race.keys() else True
    assert race["date"] == "2024-05-01"
    assert race["race_type"] == "flat"
    assert race["race_class"] == 3
    assert race["field_size"] == 6
    assert race["status"] == "result"
    # No going is published, and inventing "good" for 27,000 races would be
    # a silent fabrication.
    assert race["going"] == "unknown"

    wins = conn.execute("SELECT SUM(win_flag) AS n FROM runners").fetchone()["n"]
    assert wins == 1
    priced = conn.execute(
        "SELECT COUNT(*) AS n FROM bsp_prices WHERE market='win'").fetchone()["n"]
    assert priced == 6
    conn.close()


def test_a_market_id_reused_on_another_day_is_two_races(tmp_path, settings):
    # An abandoned meeting reappears under the same WIN_MARKET_ID on the
    # rescheduled day. Keying on the id alone would merge them into one
    # twelve-runner race with two winners.
    rows = a_race(market="900", date="2026-01-05") + a_race(market="900", date="2026-01-06")
    write_csv(tmp_path / "a.csv", rows)
    result = import_betfair_hub(settings, tmp_path)
    assert result.races == 2

    conn = init_db(settings.database_path)
    sizes = [r["field_size"] for r in conn.execute("SELECT field_size FROM races")]
    assert sizes == [6, 6]
    conn.close()


def test_duplicate_runner_rows_are_collapsed(tmp_path, settings):
    rows = a_race()
    write_csv(tmp_path / "a.csv", rows + [dict(rows[0]), dict(rows[1])])
    result = import_betfair_hub(settings, tmp_path)
    assert result.duplicate_rows == 2
    assert result.runners == 6


def test_races_with_no_result_are_skipped(tmp_path, settings):
    unsettled = [
        dict(r, WIN_RESULT="", WIN_BSP="", PLACE_BSP="", PLACE_RESULT="",
             WIN_MARKET_NAME="", COUNTRY_ID="")
        for r in a_race(market="950")
    ]
    write_csv(tmp_path / "a.csv", a_race(market="900") + unsettled)
    result = import_betfair_hub(settings, tmp_path)
    assert result.races == 1
    assert result.skipped_unsettled == 1


def test_races_without_exactly_one_winner_are_skipped(tmp_path, settings):
    rows = a_race(market="960")
    rows[1]["WIN_RESULT"] = "1"          # two winners: not a usable race
    write_csv(tmp_path / "a.csv", rows)
    result = import_betfair_hub(settings, tmp_path)
    assert result.races == 0
    assert result.skipped_no_winner == 1


def test_thin_books_are_skipped(tmp_path, settings):
    rows = a_race(market="970", n=4)
    for r in rows[1:]:                    # only the winner keeps a price
        r["WIN_BSP"] = ""
    write_csv(tmp_path / "a.csv", rows)
    result = import_betfair_hub(settings, tmp_path)
    assert result.races == 0
    assert result.skipped_thin == 1


def test_non_runners_are_recorded_but_not_priced(tmp_path, settings):
    rows = a_race(market="980")
    rows[-1].update(WIN_RESULT="-1", WIN_BSP="", PLACE_BSP="", PLACE_RESULT="-1")
    write_csv(tmp_path / "a.csv", rows)
    result = import_betfair_hub(settings, tmp_path)
    assert result.runners == 5
    assert result.non_runners == 1

    conn = init_db(settings.database_path)
    # The declared field is six, but five ran: the feature builder's
    # normalised performance must divide by the five.
    assert conn.execute("SELECT field_size FROM races").fetchone()["field_size"] == 5
    statuses = {r["status"] for r in conn.execute("SELECT status FROM runners")}
    assert statuses == {"ran", "nonrunner"}
    conn.close()


def test_foreign_countries_are_out_of_scope(tmp_path, settings):
    write_csv(tmp_path / "a.csv", a_race(market="990", COUNTRY_ID="99"))
    result = import_betfair_hub(settings, tmp_path)
    assert result.races == 0
    assert result.skipped_foreign == 1


def test_date_filters(tmp_path, settings):
    write_csv(tmp_path / "a.csv",
              a_race(market="900", date="2024-05-01")
              + a_race(market="901", date="2025-05-01"))
    result = import_betfair_hub(settings, tmp_path, since="2025-01-01")
    assert result.races == 1


def test_benchmark_prices_are_opt_in_and_invisible_to_the_market(tmp_path, settings):
    from furlong.modeling.market import MARKET_SOURCES

    write_csv(tmp_path / "a.csv", a_race())
    import_betfair_hub(settings, tmp_path, with_benchmark=True)

    conn = init_db(settings.database_path)
    rated = conn.execute("SELECT COUNT(*) AS n FROM benchmark_ratings").fetchone()["n"]
    assert rated == 6
    # Another model's published rating must never reach the market layer, or
    # Furlong would be measuring itself against a copy of its own input. It
    # is kept out of odds_snapshots entirely, and the venue CHECK there is
    # what makes that structural rather than a convention.
    assert conn.execute("SELECT COUNT(*) AS n FROM odds_snapshots").fetchone()["n"] == 0
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO odds_snapshots (runner_id, venue, ts_utc, odds_decimal) "
            "VALUES (1, 'benchmark', '2024-05-01T00:00:00+00:00', 3.1)")
    conn.close()
    assert "benchmark" not in MARKET_SOURCES


def test_import_is_idempotent(tmp_path, settings):
    write_csv(tmp_path / "a.csv", a_race())
    import_betfair_hub(settings, tmp_path)
    import_betfair_hub(settings, tmp_path)

    conn = init_db(settings.database_path)
    assert conn.execute("SELECT COUNT(*) AS n FROM races").fetchone()["n"] == 1
    assert conn.execute("SELECT COUNT(*) AS n FROM runners").fetchone()["n"] == 6
    assert conn.execute(
        "SELECT COUNT(*) AS n FROM bsp_prices").fetchone()["n"] == 12   # win + place
    conn.close()


def test_inspect_reports_shape_without_importing(tmp_path, settings):
    write_csv(tmp_path / "a.csv", a_race(market="900", date="2024-05-01"))
    write_csv(tmp_path / "b.csv", a_race(market="901", date="2025-06-02"))
    report = inspect(tmp_path)
    assert report["files"] == 2
    assert report["races"] == 2
    assert report["rows"] == 12
    assert report["first"] == "2024-05-01"
    assert report["last"] == "2025-06-02"
    assert ("IRE", 12) in report["countries"]

    conn = init_db(settings.database_path)
    assert conn.execute("SELECT COUNT(*) AS n FROM races").fetchone()["n"] == 0
    conn.close()


def test_missing_columns_are_reported_not_crashed(tmp_path, settings):
    with open(tmp_path / "bad.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["LOCAL_RACE_DATE", "TRACK"])
        writer.writerow(["2024-05-01", "Curragh"])
    result = import_betfair_hub(settings, tmp_path)
    assert result.races == 0
    assert any("missing column" in e for e in result.errors)
