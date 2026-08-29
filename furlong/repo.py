"""Persistence helpers: upsert-style writes keyed on natural/source ids.

All writers are idempotent: re-ingesting the same data does not duplicate
rows. Reads return pandas DataFrames for the analytical layers.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pandas as pd


# -- reference entities ----------------------------------------------------

def get_or_create(conn: sqlite3.Connection, table: str, name: str, **extra) -> int:
    """Return the id for a named row in courses/horses/trainers/jockeys."""
    row = conn.execute(f"SELECT id FROM {table} WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    cols = ["name", *extra.keys()]
    placeholders = ", ".join("?" for _ in cols)
    cur = conn.execute(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})",
        (name, *extra.values()),
    )
    return int(cur.lastrowid)


# -- races and runners -----------------------------------------------------

@dataclass
class RaceRecord:
    source_id: str
    course: str
    country: str  # 'IRE' | 'GB'
    date: str
    start_time_utc: str
    race_type: str  # 'flat' | 'nh'
    distance_m: float
    going: str
    race_class: int | None = None
    field_size: int | None = None
    status: str = "scheduled"
    # As for RunnerRecord: a racecard re-fetch must not downgrade a race
    # that has already been run back to 'scheduled'.
    preserve_result: bool = False


@dataclass
class RunnerRecord:
    horse: str
    trainer: str | None = None
    jockey: str | None = None
    draw: int | None = None
    weight_lbs: float | None = None
    official_rating: float | None = None
    age: int | None = None
    status: str = "declared"
    finish_pos: int | None = None
    beaten_lengths: float | None = None
    win_flag: int | None = None
    # When True, an update leaves the result columns (status, finish_pos,
    # beaten_lengths, win_flag) as they already stand. Racecard feeds carry
    # no result, so re-fetching today's card after racing would otherwise
    # wipe the finishing positions and strand the bets unsettleable.
    preserve_result: bool = False


def upsert_race(conn: sqlite3.Connection, race: RaceRecord) -> int:
    course_id = get_or_create(conn, "courses", race.course, country=race.country)
    existing = conn.execute(
        "SELECT id FROM races WHERE source_id = ?", (race.source_id,)
    ).fetchone()
    if existing:
        race_id = int(existing["id"])
        status = race.status
        if race.preserve_result:
            current = conn.execute(
                "SELECT status FROM races WHERE id=?", (race_id,)
            ).fetchone()["status"]
            if current == "result":
                status = "result"
        conn.execute(
            """UPDATE races SET course_id=?, date=?, start_time_utc=?, race_type=?,
               distance_m=?, going=?, race_class=?, field_size=?, status=? WHERE id=?""",
            (course_id, race.date, race.start_time_utc, race.race_type, race.distance_m,
             race.going, race.race_class, race.field_size, status, race_id),
        )
        return race_id
    cur = conn.execute(
        """INSERT INTO races (source_id, course_id, date, start_time_utc, race_type,
           distance_m, going, race_class, field_size, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (race.source_id, course_id, race.date, race.start_time_utc, race.race_type,
         race.distance_m, race.going, race.race_class, race.field_size, race.status),
    )
    return int(cur.lastrowid)


def upsert_runner(conn: sqlite3.Connection, race_id: int, runner: RunnerRecord) -> int:
    horse_id = get_or_create(conn, "horses", runner.horse)
    trainer_id = get_or_create(conn, "trainers", runner.trainer) if runner.trainer else None
    jockey_id = get_or_create(conn, "jockeys", runner.jockey) if runner.jockey else None
    existing = conn.execute(
        "SELECT id FROM runners WHERE race_id = ? AND horse_id = ?", (race_id, horse_id)
    ).fetchone()
    values = (
        trainer_id, jockey_id, runner.draw, runner.weight_lbs, runner.official_rating,
        runner.age, runner.status, runner.finish_pos, runner.beaten_lengths, runner.win_flag,
    )
    if existing:
        runner_id = int(existing["id"])
        if runner.preserve_result:
            conn.execute(
                """UPDATE runners SET trainer_id=?, jockey_id=?, draw=?, weight_lbs=?,
                   official_rating=?, age=? WHERE id=?""",
                (trainer_id, jockey_id, runner.draw, runner.weight_lbs,
                 runner.official_rating, runner.age, runner_id),
            )
        else:
            conn.execute(
                """UPDATE runners SET trainer_id=?, jockey_id=?, draw=?, weight_lbs=?,
                   official_rating=?, age=?, status=?, finish_pos=?, beaten_lengths=?,
                   win_flag=? WHERE id=?""",
                (*values, runner_id),
            )
        return runner_id
    cur = conn.execute(
        """INSERT INTO runners (race_id, horse_id, trainer_id, jockey_id, draw, weight_lbs,
           official_rating, age, status, finish_pos, beaten_lengths, win_flag)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (race_id, horse_id, *values),
    )
    return int(cur.lastrowid)


def add_odds_snapshot(conn: sqlite3.Connection, runner_id: int, venue: str,
                      ts_utc: str, odds_decimal: float, bookmaker: str | None = None) -> None:
    # Idempotent on (runner, venue, bookmaker, ts): re-ingesting a snapshot is a no-op.
    existing = conn.execute(
        """SELECT id FROM odds_snapshots WHERE runner_id=? AND venue=?
           AND ts_utc=? AND COALESCE(bookmaker,'') = COALESCE(?, '')""",
        (runner_id, venue, ts_utc, bookmaker),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE odds_snapshots SET odds_decimal=? WHERE id=?",
            (odds_decimal, existing["id"]),
        )
        return
    conn.execute(
        """INSERT INTO odds_snapshots (runner_id, venue, bookmaker, ts_utc, odds_decimal)
           VALUES (?, ?, ?, ?, ?)""",
        (runner_id, venue, bookmaker, ts_utc, odds_decimal),
    )


def upsert_bsp(conn: sqlite3.Connection, runner_id: int, market: str, bsp: float | None,
               ppwap: float | None = None, morning_wap: float | None = None,
               pp_max: float | None = None, pp_min: float | None = None) -> None:
    conn.execute(
        """INSERT INTO bsp_prices (runner_id, market, bsp, ppwap, morning_wap, pp_max, pp_min)
           VALUES (?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(runner_id, market) DO UPDATE SET
             bsp=excluded.bsp, ppwap=excluded.ppwap, morning_wap=excluded.morning_wap,
             pp_max=excluded.pp_max, pp_min=excluded.pp_min""",
        (runner_id, market, bsp, ppwap, morning_wap, pp_max, pp_min),
    )


def set_synthetic_truth(conn: sqlite3.Connection, runner_id: int, true_prob: float) -> None:
    conn.execute(
        """INSERT INTO synthetic_truth (runner_id, true_prob) VALUES (?, ?)
           ON CONFLICT(runner_id) DO UPDATE SET true_prob=excluded.true_prob""",
        (runner_id, true_prob),
    )


# -- analytical reads ------------------------------------------------------

RUNS_QUERY = """
SELECT
    r.id            AS runner_id,
    r.race_id       AS race_id,
    ra.source_id    AS race_source_id,
    ra.date         AS date,
    ra.start_time_utc AS start_time_utc,
    ra.race_type    AS race_type,
    ra.distance_m   AS distance_m,
    ra.going        AS going,
    ra.race_class   AS race_class,
    ra.field_size   AS field_size,
    ra.status       AS race_status,
    c.name          AS course,
    c.country       AS country,
    h.id            AS horse_id,
    h.name          AS horse,
    t.id            AS trainer_id,
    t.name          AS trainer,
    j.id            AS jockey_id,
    j.name          AS jockey,
    r.draw          AS draw,
    r.weight_lbs    AS weight_lbs,
    r.official_rating AS official_rating,
    r.age           AS age,
    r.status        AS status,
    r.finish_pos    AS finish_pos,
    r.beaten_lengths AS beaten_lengths,
    r.win_flag      AS win_flag
FROM runners r
JOIN races ra   ON ra.id = r.race_id
JOIN courses c  ON c.id = ra.course_id
JOIN horses h   ON h.id = r.horse_id
LEFT JOIN trainers t ON t.id = r.trainer_id
LEFT JOIN jockeys j  ON j.id = r.jockey_id
"""


def load_runs(conn: sqlite3.Connection, where: str = "", params: tuple = ()) -> pd.DataFrame:
    query = RUNS_QUERY + (f" WHERE {where}" if where else "") + " ORDER BY ra.start_time_utc, ra.id, r.id"
    return pd.read_sql_query(query, conn, params=params)


def load_latest_odds(conn: sqlite3.Connection, race_ids: list[int]) -> pd.DataFrame:
    """Latest odds per (runner, venue, bookmaker) for the given races."""
    if not race_ids:
        return pd.DataFrame(
            columns=["runner_id", "venue", "bookmaker", "ts_utc", "odds_decimal"]
        )
    placeholders = ", ".join("?" for _ in race_ids)
    query = f"""
        SELECT o.runner_id, o.venue, o.bookmaker, o.ts_utc, o.odds_decimal
        FROM odds_snapshots o
        JOIN runners r ON r.id = o.runner_id
        WHERE r.race_id IN ({placeholders})
          AND o.ts_utc = (
            SELECT MAX(o2.ts_utc) FROM odds_snapshots o2
            WHERE o2.runner_id = o.runner_id AND o2.venue = o.venue
              AND COALESCE(o2.bookmaker,'') = COALESCE(o.bookmaker,'')
          )
    """
    return pd.read_sql_query(query, conn, params=race_ids)


def load_bsp(conn: sqlite3.Connection, market: str = "win") -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT runner_id, market, bsp, ppwap, morning_wap FROM bsp_prices WHERE market = ?",
        conn,
        params=(market,),
    )


def load_truth(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT runner_id, true_prob FROM synthetic_truth", conn)
