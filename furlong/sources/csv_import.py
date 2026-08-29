"""Historic results CSV importer.

Imports user-provided historical results (e.g. an rpscrape-style export or
a Kaggle UK+IRE results file) into the local database. Column names are
configurable via a JSON mapping file; the defaults match common rpscrape
output. Bad rows are counted and reported, never fatal; re-import is
idempotent (races are keyed on date+course+off time).

Default expected columns (override with --mapping):
    date, course, off, name, trainer, jockey, pos, draw, or, age, dist_m,
    going, type, class, country, sp_dec
"""

from __future__ import annotations

import csv
import json
from datetime import date as date_cls
from dataclasses import dataclass, field
from pathlib import Path

from furlong.config import Settings
from furlong.db import init_db
from furlong import repo
from furlong.repo import RaceRecord, RunnerRecord

DEFAULT_MAPPING = {
    "date": "date",
    "course": "course",
    "off": "off",
    "horse": "name",
    "trainer": "trainer",
    "jockey": "jockey",
    "position": "pos",
    "draw": "draw",
    "official_rating": "or",
    "age": "age",
    "distance_m": "dist_m",
    "going": "going",
    "race_type": "type",
    "race_class": "class",
    "country": "country",
    "sp_decimal": "sp_dec",
}

GOING_NORMALISE = {
    "hvy": "heavy", "heavy": "heavy",
    "sft": "soft", "soft": "soft", "yielding": "soft", "yld": "soft",
    "gd": "good", "good": "good", "std": "good", "standard": "good",
    "gf": "good_to_firm", "good to firm": "good_to_firm", "gd-fm": "good_to_firm",
    "fm": "firm", "firm": "firm", "fast": "firm",
}


@dataclass
class ImportResult:
    races: int = 0
    runners: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)


def _to_float(value) -> float | None:
    if value in (None, "", "-", "–"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def _to_int(value) -> int | None:
    f = _to_float(value)
    return int(f) if f is not None else None


def _iso_date(raw: str) -> str | None:
    """Accept only unambiguous ISO dates."""
    try:
        return date_cls.fromisoformat(raw).isoformat()
    except (ValueError, TypeError):
        return None


def _norm_country(raw: str | None) -> str | None:
    text = (raw or "").strip().upper()
    if text in ("IRE", "IRELAND", "IE"):
        return "IRE"
    if text in ("GB", "UK", "ENGLAND", "SCOTLAND", "WALES"):
        return "GB"
    return None


def _norm_going(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    # match the most specific pattern first ("good to firm" before "good")
    for key in sorted(GOING_NORMALISE, key=len, reverse=True):
        if key in text:
            return GOING_NORMALISE[key]
    return "good"


def _norm_race_type(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if any(word in text for word in ("hurdle", "chase", "nh", "bumper", "jump")):
        return "nh"
    return "flat"


def import_results_csv(settings: Settings, path: str | Path,
                       mapping_path: str | Path | None = None) -> ImportResult:
    mapping = dict(DEFAULT_MAPPING)
    if mapping_path:
        mapping.update(json.loads(Path(mapping_path).read_text()))

    conn = init_db(settings.database_path)
    result = ImportResult()
    seen_races: dict[str, int] = {}

    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for line_no, row in enumerate(reader, start=2):
            def col(name: str) -> str | None:
                column = mapping.get(name)
                return row.get(column) if column else None

            raw_date = (col("date") or "").strip()[:10]
            date = _iso_date(raw_date)
            course = (col("course") or "").strip()
            horse = (col("horse") or "").strip()
            if raw_date and date is None:
                # An unparseable or ambiguous date is worse than a missing one:
                # "01/03/2024" would be read as 3 January and silently corrupt
                # the chronology every split and purge gap depends on.
                result.skipped += 1
                if len(result.errors) < 20:
                    result.errors.append(
                        f"line {line_no}: date {raw_date!r} is not ISO format "
                        "(YYYY-MM-DD)"
                    )
                continue
            country = _norm_country(col("country")) or ("IRE" if course in IRISH_COURSES else "GB")
            if not date or not course or not horse:
                result.skipped += 1
                if len(result.errors) < 20:
                    result.errors.append(f"line {line_no}: missing date/course/horse")
                continue

            off = (col("off") or "12:00").strip()
            race_key = f"CSV-{date}-{course}-{off}"
            if race_key not in seen_races:
                race_id = repo.upsert_race(conn, RaceRecord(
                    source_id=race_key,
                    course=course,
                    country=country,
                    date=date,
                    start_time_utc=f"{date}T{off if len(off) == 5 else '12:00'}:00+00:00",
                    race_type=_norm_race_type(col("race_type")),
                    distance_m=_to_float(col("distance_m")) or 0.0,
                    going=_norm_going(col("going")),
                    race_class=_to_int(col("race_class")),
                    status="result",
                ))
                seen_races[race_key] = race_id
                result.races += 1
            race_id = seen_races[race_key]

            position = _to_int(col("position"))
            repo.upsert_runner(conn, race_id, RunnerRecord(
                horse=horse,
                trainer=(col("trainer") or "").strip() or None,
                jockey=(col("jockey") or "").strip() or None,
                draw=_to_int(col("draw")),
                official_rating=_to_float(col("official_rating")),
                age=_to_int(col("age")),
                status="ran" if position is not None else "nonrunner",
                finish_pos=position,
                win_flag=int(position == 1) if position is not None else None,
            ))
            result.runners += 1

    # keep field_size in sync with imported runners
    for race_id in set(seen_races.values()):
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM runners WHERE race_id=?", (race_id,)
        ).fetchone()["n"]
        conn.execute("UPDATE races SET field_size=? WHERE id=?", (count, race_id))

    conn.commit()
    conn.close()
    return result


IRISH_COURSES = {
    "Ballinrobe", "Bellewstown", "Clonmel", "Cork", "Curragh", "Down Royal",
    "Downpatrick", "Dundalk", "Fairyhouse", "Galway", "Gowran Park", "Kilbeggan",
    "Killarney", "Laytown", "Leopardstown", "Limerick", "Listowel", "Naas",
    "Navan", "Punchestown", "Roscommon", "Sligo", "Thurles", "Tipperary",
    "Tramore", "Wexford",
}
