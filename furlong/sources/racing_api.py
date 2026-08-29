"""The Racing API connector (theracingapi.com).

Covers UK & Irish racecards, results and (Standard plan and up) bookmaker
odds via a REST API with HTTP basic auth. Free tier: basic daily racecards.
Docs: https://www.theracingapi.com/documentation

The client is deliberately defensive about response shapes: field names are
read with fallbacks, and the mapper is exercised against recorded JSON
fixtures in tests. Verify the mapping against your plan's live responses
when you first connect (see docs/OPERATIONS.md).

Rate limit: the API allows a small number of requests per second; the
client enforces a configurable minimum interval between requests
(injectable clock/sleep for tests).
"""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime, timezone
from typing import Any, Callable

from furlong.config import Settings
from furlong import repo
from furlong.repo import RaceRecord, RunnerRecord

DEFAULT_MIN_INTERVAL = 0.5  # seconds between requests (2 req/s)


def _first(d: dict, *keys, default=None):
    for key in keys:
        if key in d and d[key] not in (None, "", "null"):
            return d[key]
    return default


def _to_float(value) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    f = _to_float(value)
    return int(f) if f is not None else None


def parse_distance_m(raw) -> float | None:
    """Parse distances like ``1m2f``, ``6f``, ``2m110y`` or metres to metres."""
    if raw in (None, ""):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip().lower()
    try:
        return float(text)
    except ValueError:
        pass
    metres = 0.0
    import re

    m = re.match(r"^(?:(\d+)m)?(?:(\d+)f)?(?:(\d+)y)?$", text.replace(" ", ""))
    if not m or not any(m.groups()):
        return None
    miles, furlongs, yards = (int(g) if g else 0 for g in m.groups())
    metres += miles * 1609.34 + furlongs * 201.168 + yards * 0.9144
    return metres or None


def infer_race_type(raw: dict) -> str:
    text = " ".join(
        str(_first(raw, key, default="")) for key in ("race_type", "type", "race_name")
    ).lower()
    if any(word in text for word in ("hurdle", "chase", "nh flat", "bumper", "n.h.")):
        return "nh"
    return "flat"


def map_country(raw: dict) -> str | None:
    region = str(_first(raw, "region", "country", default="")).upper()
    if region in ("IRE", "IRELAND"):
        return "IRE"
    if region in ("GB", "UK", "GREAT BRITAIN"):
        return "GB"
    return None


class RacingApiClient:
    """Thin authenticated HTTP client with request throttling."""

    def __init__(self, settings: Settings,
                 transport=None,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep,
                 min_interval: float = DEFAULT_MIN_INTERVAL) -> None:
        username, password = settings.require_racing_api()
        import httpx

        self._client = httpx.Client(
            base_url=settings.racing_api_base_url,
            auth=(username, password),
            timeout=30.0,
            transport=transport,
        )
        self._clock = clock
        self._sleep = sleep
        self._min_interval = min_interval
        self._last_request: float | None = None

    def _throttle(self) -> None:
        now = self._clock()
        if self._last_request is not None:
            wait = self._min_interval - (now - self._last_request)
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()

    def get(self, path: str, params: dict | None = None) -> Any:
        self._throttle()
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def racecards(self, date: str) -> list[dict]:
        data = self.get("/racecards/free", params={"day": date})
        return data.get("racecards", data if isinstance(data, list) else [])

    def results(self, start_date: str, end_date: str) -> list[dict]:
        data = self.get("/results", params={"start_date": start_date, "end_date": end_date})
        return data.get("results", data if isinstance(data, list) else [])


# -- mapping into the local database ---------------------------------------

def store_racecard(conn: sqlite3.Connection, card: dict,
                   ts_utc: str | None = None) -> int | None:
    """Map one racecard dict into races/runners/odds. Returns race_id or None."""
    country = map_country(card)
    if country is None:
        return None  # only UK+IRE racing is in scope
    course = str(_first(card, "course", "course_name", default="")).strip()
    date = str(_first(card, "date", "race_date", default="")).strip()[:10]
    off_time = str(_first(card, "off_time", "time", "off_dt", default="12:00")).strip()
    source_id = str(_first(card, "race_id", "id", default=f"{date}-{course}-{off_time}"))
    if not course or not date:
        return None

    if "T" in off_time:
        start_iso = off_time
    else:
        start_iso = f"{date}T{off_time}:00+00:00" if len(off_time) == 5 else f"{date}T12:00:00+00:00"

    race_id = repo.upsert_race(conn, RaceRecord(
        source_id=f"RAPI-{source_id}",
        course=course,
        country=country,
        date=date,
        start_time_utc=start_iso,
        race_type=infer_race_type(card),
        distance_m=parse_distance_m(_first(card, "distance_f", "distance", "dist")) or 0.0,
        going=str(_first(card, "going", default="good")).lower().replace(" ", "_"),
        race_class=_to_int(_first(card, "race_class", "class")),
        field_size=_to_int(_first(card, "field_size")) or len(card.get("runners", [])),
        status="scheduled",
    ))

    ts = ts_utc or datetime.now(timezone.utc).isoformat()
    for runner in card.get("runners", []):
        horse = str(_first(runner, "horse", "horse_name", "name", default="")).strip()
        if not horse:
            continue
        runner_id = repo.upsert_runner(conn, race_id, RunnerRecord(
            horse=horse,
            trainer=_first(runner, "trainer", "trainer_name"),
            jockey=_first(runner, "jockey", "jockey_name"),
            draw=_to_int(_first(runner, "draw", "stall")),
            weight_lbs=_to_float(_first(runner, "lbs", "weight_lbs", "weight")),
            official_rating=_to_float(_first(runner, "ofr", "or", "official_rating")),
            age=_to_int(_first(runner, "age")),
            status="declared",
        ))
        for quote in runner.get("odds", []) or []:
            price = _to_float(_first(quote, "decimal", "price", "odds_decimal"))
            bookmaker = _first(quote, "bookmaker", "book", default=None)
            if price and price > 1.0:
                repo.add_odds_snapshot(conn, runner_id, "book", ts, price, bookmaker=bookmaker)
    return race_id


def store_result(conn: sqlite3.Connection, result: dict) -> int | None:
    """Map one result dict onto an existing (or new) race."""
    race_id = store_racecard(conn, result, ts_utc=None)
    if race_id is None:
        return None
    conn.execute("UPDATE races SET status='result' WHERE id=?", (race_id,))
    for runner in result.get("runners", []):
        horse = str(_first(runner, "horse", "horse_name", "name", default="")).strip()
        if not horse:
            continue
        position = _to_int(_first(runner, "position", "pos", "finish_pos"))
        row = conn.execute(
            """SELECT r.id FROM runners r JOIN horses h ON h.id=r.horse_id
               WHERE r.race_id=? AND h.name=?""",
            (race_id, horse),
        ).fetchone()
        if not row:
            continue
        if position is None:
            conn.execute("UPDATE runners SET status='nonrunner' WHERE id=?", (row["id"],))
        else:
            conn.execute(
                """UPDATE runners SET status='ran', finish_pos=?, win_flag=?,
                   beaten_lengths=? WHERE id=?""",
                (position, int(position == 1),
                 _to_float(_first(runner, "btn", "beaten_lengths", "ovr_btn")), row["id"]),
            )
    return race_id


class RacingApiSource:
    """Daily-pipeline source backed by The Racing API."""

    name = "racing_api"

    def sync_daily(self, settings: Settings, conn: sqlite3.Connection, date: str) -> None:
        client = RacingApiClient(settings)
        for card in client.racecards(date):
            store_racecard(conn, card)
        conn.commit()
