"""Importer for the rpscrape-schema SQLite database (raceform.db).

Source: https://www.kaggle.com/datasets/deltaromeo/horse-racing-results-ukireland-2015-2025
Covers UK and Irish racing from 2015 to 2026 in a single SQLite file with one
row per runner, using rpscrape's column set.

Provenance is a scrape of Racing Post. That is workable for a personal model
you never redistribute, and is *not* a licence: the uploader cannot grant
rights they do not hold, whatever label the dataset carries. Anything you
intend to sell must be re-platformed onto a licensed feed first -- see
docs/GO-LIVE-CHECKLIST.md.

Two of its columns need real parsing rather than a cast:

* ``sp`` is a fractional starting price -- "5/1", "7/2", "Evens", "4/5".
* ``wgt`` is stones and pounds -- "11-2" meaning 11st 2lb, i.e. 156 lb.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import date as date_cls
from pathlib import Path

from furlong.config import Settings
from furlong.db import init_db
from furlong import repo
from furlong.repo import RaceRecord, RunnerRecord
from furlong.sources.csv_import import _norm_going
from furlong.sources.kaggle_import import _course_and_country
from furlong.sources.racing_api import parse_distance_m

# Only UK and Irish racing is in scope; the dataset also carries French and
# other foreign cards, which have different conventions and no market here.
IN_SCOPE_COUNTRIES = ("GB", "IRE")

EVENS = {"evens", "evs", "even", "1/1"}

# rpscrape records a non-finisher as a code in the position column.
NON_FINISH_CODES = {"PU", "F", "UR", "BD", "RO", "SU", "REF", "DSQ", "VOI", "RR", "LFT"}


@dataclass
class RaceformImportResult:
    races: int = 0
    runners: int = 0
    skipped_foreign: int = 0
    skipped: int = 0
    errors: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"raceform.db import: {self.races:,} races, {self.runners:,} runners"
            f" ({self.skipped_foreign:,} foreign races skipped,"
            f" {self.skipped:,} rows skipped)"
        ]
        if self.errors:
            lines.append("  first errors: " + "; ".join(self.errors[:3]))
        return "\n".join(lines)


def parse_fractional_sp(raw) -> float | None:
    """Fractional starting price to decimal odds. "5/1" -> 6.0, "4/5" -> 1.8."""
    if raw is None:
        return None
    text = str(raw).strip().lower().replace(" ", "")
    if not text:
        return None
    if text in EVENS:
        return 2.0
    # already decimal
    if "/" not in text:
        try:
            value = float(text)
        except ValueError:
            return None
        return value if value > 1.0 else None
    numerator, _, denominator = text.partition("/")
    try:
        num, den = float(numerator), float(denominator)
    except ValueError:
        return None
    if den <= 0:
        return None
    return num / den + 1.0


def parse_weight_lbs(raw) -> float | None:
    """Stones-and-pounds to pounds. "11-2" -> 156.0."""
    if raw is None:
        return None
    text = str(raw).strip()
    match = re.match(r"^(\d+)\s*-\s*(\d+)$", text)
    if match:
        return float(match.group(1)) * 14 + float(match.group(2))
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0 else None


def parse_position(raw) -> int | None:
    """Finishing position, or None for a non-finisher or disqualification."""
    if raw is None:
        return None
    text = str(raw).strip().upper()
    if not text or text in NON_FINISH_CODES:
        return None
    # rpscrape sometimes suffixes a dead heat, e.g. "1D"
    match = re.match(r"^(\d+)", text)
    return int(match.group(1)) if match else None


def _iso_date(raw) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()[:10]
    try:
        return date_cls.fromisoformat(text).isoformat()
    except ValueError:
        return None


def _num(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value) -> int | None:
    number = _num(value)
    return int(number) if number is not None else None


def _race_type(raw_type: str | None, race_name: str | None) -> str:
    text = f"{raw_type or ''} {race_name or ''}".lower()
    if any(word in text for word in ("hurdle", "chase", "nh flat", "bumper", "n.h.")):
        return "nh"
    return "flat"


def inspect(db_path: str | Path) -> dict:
    """Report the shape of the database without importing."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    columns = [r["name"] for r in conn.execute("PRAGMA table_info(data)")]
    report: dict = {"columns": columns}
    if columns:
        stats = conn.execute(
            "SELECT COUNT(*) rows, COUNT(DISTINCT race_id) races, "
            "MIN(date) first, MAX(date) last FROM data"
        ).fetchone()
        report.update(dict(stats))
        report["countries"] = [
            dict(r) for r in conn.execute(
                "SELECT course, COUNT(DISTINCT race_id) races FROM data "
                "GROUP BY course ORDER BY races DESC LIMIT 12"
            )
        ]
    conn.close()
    return report


def import_raceform_db(settings: Settings, db_path: str | Path,
                       since: str | None = None,
                       until: str | None = None) -> RaceformImportResult:
    """Import UK and Irish races from an rpscrape-schema SQLite database."""
    result = RaceformImportResult()
    source = Path(db_path)
    if not source.exists():
        result.errors.append(f"database not found: {source}")
        return result

    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    src.row_factory = sqlite3.Row
    conn = init_db(settings.database_path)

    where, params = [], []
    if since:
        where.append("date >= ?")
        params.append(since)
    if until:
        where.append("date <= ?")
        params.append(until)
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    rows = src.execute(
        f"SELECT * FROM data{clause} ORDER BY date, race_id, num", params
    )

    current_race: str | None = None
    race_db_id: int | None = None
    race_runner_count = 0
    written = 0

    for row in rows:
        race_key = str(row["race_id"])
        if race_key != current_race:
            if race_db_id is not None and race_runner_count:
                conn.execute("UPDATE races SET field_size=? WHERE id=?",
                             (race_runner_count, race_db_id))
            current_race = race_key
            race_db_id = None
            race_runner_count = 0

            date = _iso_date(row["date"])
            course, code = _course_and_country(row["course"])
            # No bracket (or an all-weather marker) means a British course in
            # this dataset's convention; any other code is a foreign meeting.
            country = "GB" if code is None else code
            if country not in IN_SCOPE_COUNTRIES:
                result.skipped_foreign += 1
                continue
            if not date or not course:
                result.skipped += 1
                continue

            off = str(row["off"] or "12:00").strip()
            if len(off) == 4:            # "2:35" -> "02:35"
                off = "0" + off
            race_db_id = repo.upsert_race(conn, RaceRecord(
                source_id=f"RFDB-{race_key}",
                course=course,
                country=country,
                date=date,
                start_time_utc=f"{date}T{off if len(off) == 5 else '12:00'}:00+00:00",
                race_type=_race_type(row["type"], row["race_name"]),
                distance_m=parse_distance_m(row["dist"]) or 0.0,
                going=_norm_going(row["going"]),
                race_class=_int(re.sub(r"\D", "", str(row["class"] or "")) or None),
                field_size=_int(row["ran"]),
                status="result",
            ))
            result.races += 1

        if race_db_id is None:
            continue  # this race was skipped as foreign or malformed

        horse = str(row["horse"] or "").strip()
        if not horse:
            result.skipped += 1
            continue

        position = parse_position(row["pos"])
        runner_id = repo.upsert_runner(conn, race_db_id, RunnerRecord(
            horse=horse,
            trainer=(str(row["trainer"]) or "").strip() or None,
            jockey=(str(row["jockey"]) or "").strip() or None,
            draw=_int(row["draw"]),
            weight_lbs=parse_weight_lbs(row["wgt"]),
            official_rating=_num(row["or"]),
            age=_int(row["age"]),
            status="ran" if position is not None else "nonrunner",
            finish_pos=position,
            # ovr_btn is lengths behind the winner, which is the quantity the
            # feature builder wants; btn is behind the horse in front.
            beaten_lengths=_num(row["ovr_btn"]),
            win_flag=int(position == 1) if position is not None else None,
        ))
        result.runners += 1
        race_runner_count += 1

        price = parse_fractional_sp(row["sp"])
        if price and price > 1.0:
            date = _iso_date(row["date"])
            repo.add_odds_snapshot(conn, runner_id, "book",
                                   f"{date}T12:00:00+00:00", price, bookmaker="SP")

        written += 1
        if written % 20000 == 0:
            conn.commit()

    if race_db_id is not None and race_runner_count:
        conn.execute("UPDATE races SET field_size=? WHERE id=?",
                     (race_runner_count, race_db_id))
    conn.commit()
    conn.close()
    src.close()
    return result
