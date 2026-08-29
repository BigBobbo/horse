import sqlite3

import pytest

from furlong.db import init_db, table_names

EXPECTED_TABLES = {
    "courses", "horses", "trainers", "jockeys", "races", "runners",
    "odds_snapshots", "bsp_prices", "synthetic_truth", "model_runs",
    "suggestions", "settlements",
}


def test_init_creates_all_tables(settings):
    conn = init_db(settings.database_path)
    assert EXPECTED_TABLES <= table_names(conn)
    conn.close()


def test_init_is_idempotent(settings, conn):
    conn.execute("INSERT INTO horses (name) VALUES ('Kicking King')")
    conn.commit()
    conn2 = init_db(settings.database_path)  # second init must not wipe data
    row = conn2.execute("SELECT COUNT(*) AS n FROM horses").fetchone()
    assert row["n"] == 1
    conn2.close()


def test_foreign_keys_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO runners (race_id, horse_id) VALUES (999, 999)"
        )


def test_odds_check_constraint(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """INSERT INTO odds_snapshots (runner_id, venue, ts_utc, odds_decimal)
               VALUES (1, 'book', '2026-01-01T09:00:00', 0.99)"""
        )
