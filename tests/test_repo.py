from furlong import repo
from furlong.repo import RaceRecord, RunnerRecord


def make_race(source_id="R1", **kw):
    defaults = dict(
        source_id=source_id, course="Curragh", country="IRE", date="2026-05-01",
        start_time_utc="2026-05-01T14:00:00+00:00", race_type="flat",
        distance_m=1600.0, going="good", race_class=3, field_size=8,
    )
    defaults.update(kw)
    return RaceRecord(**defaults)


def test_race_runner_round_trip(conn):
    race_id = repo.upsert_race(conn, make_race())
    runner_id = repo.upsert_runner(conn, race_id, RunnerRecord(
        horse="Sea The Stars", trainer="J Oxx", jockey="M Kinane",
        draw=4, official_rating=140, status="ran", finish_pos=1, win_flag=1,
    ))
    runs = repo.load_runs(conn)
    assert len(runs) == 1
    row = runs.iloc[0]
    assert row["horse"] == "Sea The Stars"
    assert row["course"] == "Curragh"
    assert row["country"] == "IRE"
    assert row["finish_pos"] == 1
    assert row["runner_id"] == runner_id


def test_upserts_are_idempotent(conn):
    race_id = repo.upsert_race(conn, make_race())
    race_id2 = repo.upsert_race(conn, make_race(going="soft"))
    assert race_id == race_id2
    assert conn.execute("SELECT COUNT(*) n FROM races").fetchone()["n"] == 1
    assert conn.execute("SELECT going FROM races").fetchone()["going"] == "soft"

    for _ in range(2):
        repo.upsert_runner(conn, race_id, RunnerRecord(horse="Hurricane Fly"))
    assert conn.execute("SELECT COUNT(*) n FROM runners").fetchone()["n"] == 1


def test_odds_snapshot_idempotent_and_latest(conn):
    race_id = repo.upsert_race(conn, make_race())
    runner_id = repo.upsert_runner(conn, race_id, RunnerRecord(horse="Faugheen"))
    repo.add_odds_snapshot(conn, runner_id, "book", "2026-05-01T09:00:00", 5.0, "GreenBook")
    repo.add_odds_snapshot(conn, runner_id, "book", "2026-05-01T09:00:00", 5.5, "GreenBook")
    repo.add_odds_snapshot(conn, runner_id, "book", "2026-05-01T11:00:00", 4.5, "GreenBook")
    repo.add_odds_snapshot(conn, runner_id, "exchange", "2026-05-01T09:00:00", 5.8)
    n = conn.execute("SELECT COUNT(*) n FROM odds_snapshots").fetchone()["n"]
    assert n == 3  # duplicate ts+book updated in place

    latest = repo.load_latest_odds(conn, [race_id])
    book = latest[latest.venue == "book"]
    assert len(book) == 1
    assert book.iloc[0]["odds_decimal"] == 4.5


def test_bsp_upsert(conn):
    race_id = repo.upsert_race(conn, make_race())
    runner_id = repo.upsert_runner(conn, race_id, RunnerRecord(horse="Galileo"))
    repo.upsert_bsp(conn, runner_id, "win", bsp=4.2, ppwap=4.4)
    repo.upsert_bsp(conn, runner_id, "win", bsp=4.0, ppwap=4.1)
    bsp = repo.load_bsp(conn)
    assert len(bsp) == 1
    assert bsp.iloc[0]["bsp"] == 4.0
