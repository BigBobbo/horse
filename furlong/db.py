"""SQLite storage layer: schema, connection helpers, idempotent init."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    country TEXT NOT NULL CHECK (country IN ('IRE', 'GB'))
);

CREATE TABLE IF NOT EXISTS horses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS trainers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS jockeys (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS races (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,      -- stable id from the data source
    course_id INTEGER NOT NULL REFERENCES courses(id),
    date TEXT NOT NULL,                  -- ISO date, local race day
    start_time_utc TEXT NOT NULL,        -- ISO datetime UTC
    race_type TEXT NOT NULL CHECK (race_type IN ('flat', 'nh')),
    distance_m REAL NOT NULL,
    going TEXT NOT NULL,
    race_class INTEGER,
    field_size INTEGER,
    status TEXT NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'result', 'abandoned'))
);
CREATE INDEX IF NOT EXISTS idx_races_date ON races(date);

CREATE TABLE IF NOT EXISTS runners (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL REFERENCES races(id),
    horse_id INTEGER NOT NULL REFERENCES horses(id),
    trainer_id INTEGER REFERENCES trainers(id),
    jockey_id INTEGER REFERENCES jockeys(id),
    draw INTEGER,
    weight_lbs REAL,
    official_rating REAL,
    age INTEGER,
    status TEXT NOT NULL DEFAULT 'declared'
        CHECK (status IN ('declared', 'nonrunner', 'ran')),
    finish_pos INTEGER,
    beaten_lengths REAL,
    win_flag INTEGER,
    UNIQUE (race_id, horse_id)
);
CREATE INDEX IF NOT EXISTS idx_runners_race ON runners(race_id);
CREATE INDEX IF NOT EXISTS idx_runners_horse ON runners(horse_id);

CREATE TABLE IF NOT EXISTS odds_snapshots (
    id INTEGER PRIMARY KEY,
    runner_id INTEGER NOT NULL REFERENCES runners(id),
    venue TEXT NOT NULL CHECK (venue IN ('book', 'exchange')),
    bookmaker TEXT,                      -- NULL for exchange
    ts_utc TEXT NOT NULL,
    odds_decimal REAL NOT NULL CHECK (odds_decimal > 1.0)
);
CREATE INDEX IF NOT EXISTS idx_odds_runner ON odds_snapshots(runner_id);

-- A published rating from someone else's model, kept deliberately out of
-- odds_snapshots. It is not a market quote and must never be mistaken for
-- one: the CHECK on odds_snapshots.venue is what stops that happening, and
-- a separate table is what stops anyone being tempted to relax it. Used only
-- to compare Furlong's edge against a published benchmark on the same races.
CREATE TABLE IF NOT EXISTS benchmark_ratings (
    runner_id INTEGER NOT NULL REFERENCES runners(id),
    source TEXT NOT NULL,
    rated_price REAL NOT NULL CHECK (rated_price > 1.0),
    PRIMARY KEY (runner_id, source)
);

CREATE TABLE IF NOT EXISTS bsp_prices (
    runner_id INTEGER NOT NULL REFERENCES runners(id),
    market TEXT NOT NULL CHECK (market IN ('win', 'place')),
    bsp REAL,
    ppwap REAL,
    morning_wap REAL,
    pp_max REAL,
    pp_min REAL,
    PRIMARY KEY (runner_id, market)
);

-- Ground truth for the synthetic world only. Never read by features/models.
CREATE TABLE IF NOT EXISTS synthetic_truth (
    runner_id INTEGER PRIMARY KEY REFERENCES runners(id),
    true_prob REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS model_runs (
    id INTEGER PRIMARY KEY,
    ts_utc TEXT NOT NULL,
    model_kind TEXT NOT NULL,
    params_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    artifact_path TEXT
);

-- Every runner scored on a race day, not only the ones worth backing.
-- The 10:15 rescore needs the whole race to renormalise probabilities when a
-- horse comes out, and most withdrawals are of horses we never backed.
CREATE TABLE IF NOT EXISTS race_scores (
    date TEXT NOT NULL,
    race_id INTEGER NOT NULL REFERENCES races(id),
    runner_id INTEGER NOT NULL REFERENCES runners(id),
    model_prob REAL NOT NULL,
    blend_prob REAL NOT NULL,
    market_prob REAL,
    PRIMARY KEY (date, runner_id)
);
CREATE INDEX IF NOT EXISTS idx_race_scores_race ON race_scores(race_id);

CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    race_id INTEGER NOT NULL REFERENCES races(id),
    runner_id INTEGER NOT NULL REFERENCES runners(id),
    model_prob REAL NOT NULL,
    blend_prob REAL NOT NULL,
    market_prob REAL,
    fair_odds REAL NOT NULL,
    advised_odds REAL NOT NULL,
    price_floor REAL NOT NULL,
    venue TEXT NOT NULL CHECK (venue IN ('book', 'exchange')),
    bookmaker TEXT,
    ev REAL NOT NULL,
    stake_units REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'withdrawn', 'settled')),
    reason TEXT,
    created_ts TEXT NOT NULL,
    UNIQUE (date, runner_id)
);
CREATE INDEX IF NOT EXISTS idx_suggestions_date ON suggestions(date);

CREATE TABLE IF NOT EXISTS settlements (
    suggestion_id INTEGER PRIMARY KEY REFERENCES suggestions(id),
    result TEXT NOT NULL CHECK (result IN ('won', 'lost', 'void', 'deadheat')),
    pl_units REAL NOT NULL,
    bsp_at_off REAL,
    clv REAL,
    rule4_deduction REAL NOT NULL DEFAULT 0,
    settled_ts TEXT NOT NULL
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection with FK enforcement and dict-like rows."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Columns added after the initial schema, applied to existing databases.
MIGRATIONS: list[tuple[str, str, str]] = [
    ("suggestions", "market_prob", "ALTER TABLE suggestions ADD COLUMN market_prob REAL"),
]


def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Create the schema (idempotent), apply migrations, return a connection."""
    conn = connect(db_path)
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns missing from databases created by an earlier version."""
    for table, column, statement in MIGRATIONS:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        if existing and column not in existing:
            conn.execute(statement)


def table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {r["name"] for r in rows}
