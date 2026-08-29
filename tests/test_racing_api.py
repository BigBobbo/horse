import json

import pytest

from furlong.config import ConfigError, Settings
from furlong.db import init_db
from furlong.sources.racing_api import (
    RacingApiClient,
    parse_distance_m,
    store_racecard,
    store_result,
)

RACECARD_FIXTURE = {
    "race_id": "rac_123456",
    "course": "Leopardstown",
    "region": "IRE",
    "date": "2026-06-10",
    "off_time": "14:05",
    "race_name": "Dublin Handicap",
    "distance_f": "1m2f",
    "going": "Good",
    "race_class": "3",
    "field_size": "3",
    "runners": [
        {
            "horse": "Harp Melody", "trainer": "W P Mullins", "jockey": "P Townend",
            "draw": "4", "lbs": "132", "ofr": "95", "age": "5",
            "odds": [
                {"bookmaker": "Bet365", "decimal": "4.5"},
                {"bookmaker": "PaddyPower", "decimal": "4.33"},
            ],
        },
        {
            "horse": "Liffey Runner", "trainer": "A P O'Brien", "jockey": "R Moore",
            "draw": "1", "lbs": "128", "ofr": "88", "age": "4",
            "odds": [{"bookmaker": "Bet365", "decimal": "2.1"}],
        },
        {"horse": "Shannon Mist", "trainer": "J Harrington", "jockey": "S Foley",
         "draw": "2", "lbs": "126", "ofr": "84", "age": "6", "odds": []},
    ],
}


def test_parse_distance_m():
    assert parse_distance_m("1m2f") == pytest.approx(1609.34 + 2 * 201.168, rel=1e-4)
    assert parse_distance_m("6f") == pytest.approx(6 * 201.168, rel=1e-4)
    assert parse_distance_m("2m110y") == pytest.approx(2 * 1609.34 + 110 * 0.9144, rel=1e-4)
    assert parse_distance_m(1600) == 1600.0
    assert parse_distance_m("nonsense") is None


def test_store_racecard_maps_fixture(settings):
    conn = init_db(settings.database_path)
    race_id = store_racecard(conn, RACECARD_FIXTURE, ts_utc="2026-06-10T08:00:00+00:00")
    assert race_id is not None

    race = conn.execute("SELECT * FROM races WHERE id=?", (race_id,)).fetchone()
    assert race["source_id"] == "RAPI-rac_123456"
    assert race["date"] == "2026-06-10"
    assert race["race_type"] == "flat"
    assert race["status"] == "scheduled"

    runners = conn.execute(
        "SELECT COUNT(*) n FROM runners WHERE race_id=?", (race_id,)
    ).fetchone()
    assert runners["n"] == 3

    odds = conn.execute(
        """SELECT COUNT(*) n FROM odds_snapshots o
           JOIN runners r ON r.id=o.runner_id WHERE r.race_id=?""", (race_id,)
    ).fetchone()
    assert odds["n"] == 3
    conn.close()


def test_store_racecard_skips_non_ukire(settings):
    conn = init_db(settings.database_path)
    card = dict(RACECARD_FIXTURE, region="USA", race_id="rac_999")
    assert store_racecard(conn, card) is None
    conn.close()


def test_store_result_updates_positions(settings):
    conn = init_db(settings.database_path)
    store_racecard(conn, RACECARD_FIXTURE)
    result = json.loads(json.dumps(RACECARD_FIXTURE))
    result["runners"][0]["position"] = "2"
    result["runners"][1]["position"] = "1"
    # third runner has no position -> non-runner
    race_id = store_result(conn, result)
    rows = conn.execute(
        """SELECT h.name, r.status, r.finish_pos, r.win_flag FROM runners r
           JOIN horses h ON h.id=r.horse_id WHERE r.race_id=? ORDER BY h.name""",
        (race_id,),
    ).fetchall()
    by_name = {r["name"]: r for r in rows}
    assert by_name["Liffey Runner"]["win_flag"] == 1
    assert by_name["Harp Melody"]["finish_pos"] == 2
    assert by_name["Shannon Mist"]["status"] == "nonrunner"
    race = conn.execute("SELECT status FROM races WHERE id=?", (race_id,)).fetchone()
    assert race["status"] == "result"
    conn.close()


def test_client_requires_credentials():
    with pytest.raises(ConfigError):
        RacingApiClient(Settings())


def test_client_throttles_requests():
    settings = Settings(racing_api_username="u", racing_api_password="p")

    fake_time = {"now": 0.0}
    sleeps: list[float] = []

    def clock() -> float:
        return fake_time["now"]

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        fake_time["now"] += seconds

    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"racecards": []})

    client = RacingApiClient(
        settings, transport=httpx.MockTransport(handler),
        clock=clock, sleep=sleep, min_interval=0.5,
    )
    client.racecards("2026-06-10")   # first request: no wait
    client.racecards("2026-06-10")   # immediate second request: throttled
    assert sleeps and sleeps[0] == pytest.approx(0.5, abs=1e-6)
