"""Importer for the Kaggle UK+Ireland historical racing dataset.

Source: https://www.kaggle.com/datasets/hwaitt/horse-racing
Licence: CC BY-NC 4.0 -- non-commercial use is granted, so this is a clean
route to real form history for a personal model. It cannot be the basis of
anything you sell; see docs/GO-LIVE-CHECKLIST.md.

Shape: one pair of files per year, joined on the race id --

    races_YYYY.csv   one row per race:   rid, course, date, distance, going,
                                         class, country, winning time, prizes
    horses_YYYY.csv  one row per runner: rid, horse, age, draw, decimal odds,
                                         trainer, jockey, position, weight,
                                         RPR, TR (Topspeed), OR, pedigree

Column names vary between the dataset's own vintages, so every field is read
through a list of candidates rather than one hard-coded name. Run
``furlong import-kaggle <dir> --inspect`` to see exactly what was detected in
your copy before importing.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date as date_cls
from pathlib import Path

from furlong.config import Settings
from furlong.db import init_db
from furlong import repo
from furlong.repo import RaceRecord, RunnerRecord
from furlong.sources.csv_import import IRISH_COURSES, _norm_going, _norm_race_type

# Candidate column names, most specific first. The dataset has shipped under
# several header conventions; these cover the ones documented and observed.
RACE_COLUMNS = {
    "race_id": ["rid", "raceId", "race_id", "id"],
    "course": ["course", "courseName", "track", "venue"],
    "date": ["date", "raceDate", "meetingDate"],
    "time": ["time", "off", "offTime", "raceTime"],
    "distance": ["metric", "distance", "distanceYards", "dist"],
    "going": ["condition", "going", "ground"],
    "race_class": ["rclass", "class", "raceClass"],
    "country": ["countryCode", "country", "region"],
    "title": ["title", "raceName", "name"],
    "hurdles": ["hurdles", "obstacle"],
    "runners": ["runners", "numberOfRunners", "field_size"],
}

RUNNER_COLUMNS = {
    "race_id": ["rid", "raceId", "race_id"],
    "horse": ["horseName", "horse", "name"],
    "position": ["position", "pos", "finishPosition"],
    "age": ["age"],
    "draw": ["saddle", "draw", "stall"],
    "decimal_odds": ["decimalPrice", "decimal_odds", "odds", "sp_dec"],
    "trainer": ["trainerName", "trainer"],
    "jockey": ["jockeyName", "jockey"],
    "official_rating": ["OR", "or", "officialRating"],
    "rpr": ["RPR", "rpr"],
    "topspeed": ["TR", "tr", "topspeed"],
    # weightLb is pounds; the bare "weight" column in this dataset is
    # kilograms, so it must never be the first choice.
    "weight_lbs": ["weightLb", "lbs", "weight_lbs"],
    "weight_kg": ["weight"],
    # "dist" is lengths behind the winner; "positionL" is lengths behind the
    # horse in front, which is a different quantity.
    "beaten": ["dist", "btn", "beaten", "positionL"],
    "res_win": ["res_win", "resWin"],
}

# The dataset's decimalPrice column is a fractional *probability* in some
# vintages (0.25 meaning 4.0) and a decimal price in others. Values below 1.0
# can only be the former.
PROB_LIKE_THRESHOLD = 1.0

# The dataset encodes a non-finisher as position 40, not as a blank. Treating
# that as a real finishing position would hand every faller and pulled-up
# horse a normalised performance score and feed it into form and Elo.
DNF_POSITION = 40

# Course names carry the country in brackets -- "Curragh (IRE)", "Ascot" for
# Britain, and the "(AW)" suffix for all-weather tracks. Left in place, the
# same course would fragment into several identities.
COURSE_SUFFIX = re.compile(r"\s*\((IRE|GB|UK|AW|FR|GER|USA|SAF|UAE|AUS)\)\s*",
                           re.IGNORECASE)


@dataclass
class KaggleImportResult:
    files: int = 0
    races: int = 0
    runners: int = 0
    skipped: int = 0
    detected: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Kaggle import: {self.races:,} races, {self.runners:,} runners "
            f"from {self.files} file pair(s), {self.skipped:,} rows skipped"
        ]
        if self.errors:
            lines.append(f"  first errors: {'; '.join(self.errors[:3])}")
        return "\n".join(lines)


def _resolve(header: list[str], candidates: dict[str, list[str]]) -> dict[str, str]:
    """Map our field names onto whichever column names this file actually uses."""
    lookup = {name.strip().lower(): name for name in header}
    resolved: dict[str, str] = {}
    for field_name, options in candidates.items():
        for option in options:
            actual = lookup.get(option.lower())
            if actual is not None:
                resolved[field_name] = actual
                break
    return resolved


def _num(value) -> float | None:
    if value in (None, "", "-", "NA", "NaN"):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def _int(value) -> int | None:
    number = _num(value)
    return int(number) if number is not None else None


def _iso_date(raw: str | None) -> str | None:
    if not raw:
        return None
    text = str(raw).strip()[:10]
    try:
        return date_cls.fromisoformat(text).isoformat()
    except ValueError:
        return None


def _position(raw) -> int | None:
    """Finishing position, or None for a non-finisher.

    Non-finishers appear either as a letter code (PU pulled up, F fell, UR
    unseated, BD brought down, RO ran out) or, in this dataset specifically,
    as the sentinel position 40.
    """
    if raw is None:
        return None
    text = str(raw).strip().upper()
    if not text or not text.isdigit():
        return None
    position = int(text)
    if position >= DNF_POSITION:
        return None
    return position


def _course_and_country(raw: str | None) -> tuple[str, str | None]:
    """Split "Curragh (IRE)" into a clean course name and its country."""
    text = (raw or "").strip()
    country = None
    for match in COURSE_SUFFIX.finditer(text):
        code = match.group(1).upper()
        if code in ("IRE",):
            country = "IRE"
        elif code in ("GB", "UK"):
            country = "GB"
    cleaned = COURSE_SUFFIX.sub(" ", text).strip()
    return cleaned, country


def _odds(raw) -> float | None:
    """Decimal odds, accepting the probability-style column some vintages use."""
    value = _num(raw)
    if value is None or value <= 0:
        return None
    if value < PROB_LIKE_THRESHOLD:
        return 1.0 / value
    return value


def _country(raw: str | None, course: str) -> str:
    text = (raw or "").strip().upper()
    if text in ("IRE", "IE", "IRELAND"):
        return "IRE"
    if text in ("GB", "UK", "ENG", "SCO", "WAL"):
        return "GB"
    return "IRE" if course in IRISH_COURSES else "GB"


def find_pairs(directory: str | Path) -> list[tuple[Path, Path]]:
    """Locate matching races_YYYY / horses_YYYY files, oldest year first."""
    root = Path(directory)
    races = {}
    horses = {}
    for path in root.rglob("*.csv"):
        match = re.search(r"(\d{4})", path.stem)
        if not match:
            continue
        year = match.group(1)
        stem = path.stem.lower()
        if stem.startswith("races"):
            races[year] = path
        elif stem.startswith("horses"):
            horses[year] = path
    return [(races[y], horses[y]) for y in sorted(races) if y in horses]


def inspect(directory: str | Path) -> dict:
    """Report the files found and the columns detected, without importing."""
    pairs = find_pairs(directory)
    report: dict = {"pairs": len(pairs), "years": [], "races": {}, "runners": {}}
    if not pairs:
        return report
    races_path, horses_path = pairs[0]
    report["years"] = [p[0].stem for p in pairs]
    with open(races_path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        header = next(csv.reader(fh))
    report["races"] = {"file": races_path.name, "columns": header,
                       "mapped": _resolve(header, RACE_COLUMNS)}
    with open(horses_path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        header = next(csv.reader(fh))
    report["runners"] = {"file": horses_path.name, "columns": header,
                         "mapped": _resolve(header, RUNNER_COLUMNS)}
    return report


def import_kaggle_dataset(settings: Settings, directory: str | Path,
                          years: tuple[str, ...] | None = None
                          ) -> KaggleImportResult:
    """Import every races/horses pair found under ``directory``."""
    pairs = find_pairs(directory)
    if years:
        pairs = [p for p in pairs if any(y in p[0].stem for y in years)]
    result = KaggleImportResult()
    if not pairs:
        result.errors.append(
            f"no races_YYYY.csv / horses_YYYY.csv pairs found under {directory}"
        )
        return result

    conn = init_db(settings.database_path)
    for races_path, horses_path in pairs:
        _import_pair(conn, races_path, horses_path, result)
        result.files += 1
        conn.commit()
    conn.close()
    return result


def _import_pair(conn, races_path: Path, horses_path: Path,
                 result: KaggleImportResult) -> None:
    # Runners first, grouped by race, so field size is known before the race
    # row is written.
    with open(horses_path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh)
        runner_map = _resolve(reader.fieldnames or [], RUNNER_COLUMNS)
        result.detected.setdefault("runners", runner_map)
        by_race: dict[str, list[dict]] = defaultdict(list)
        for row in reader:
            race_id = (row.get(runner_map.get("race_id", ""), "") or "").strip()
            if race_id:
                by_race[race_id].append(row)

    with open(races_path, newline="", encoding="utf-8-sig", errors="replace") as fh:
        reader = csv.DictReader(fh)
        race_map = _resolve(reader.fieldnames or [], RACE_COLUMNS)
        result.detected.setdefault("races", race_map)

        for row in reader:
            def race_col(name: str):
                column = race_map.get(name)
                return row.get(column) if column else None

            race_id = (race_col("race_id") or "").strip()
            date = _iso_date(race_col("date"))
            course, course_country = _course_and_country(race_col("course"))
            runners = by_race.get(race_id, [])

            if not race_id or not date or not course or len(runners) < 2:
                result.skipped += len(runners) or 1
                if len(result.errors) < 20 and race_id:
                    result.errors.append(
                        f"race {race_id}: missing date/course or fewer than 2 runners"
                    )
                continue

            off = (race_col("time") or "12:00").strip()[:5]
            country = course_country or _country(race_col("country"), course)
            distance = _num(race_col("distance")) or 0.0
            race_type = _norm_race_type(
                f"{race_col('title') or ''} {race_col('hurdles') or ''}"
            )

            db_race_id = repo.upsert_race(conn, RaceRecord(
                source_id=f"KAG-{race_id}",
                course=course,
                country=country,
                date=date,
                start_time_utc=f"{date}T{off if len(off) == 5 else '12:00'}:00+00:00",
                race_type=race_type,
                distance_m=distance,
                going=_norm_going(race_col("going")),
                race_class=_int(race_col("race_class")),
                field_size=len(runners),
                status="result",
            ))
            result.races += 1

            for runner in runners:
                def col(name: str):
                    column = runner_map.get(name)
                    return runner.get(column) if column else None

                horse = (col("horse") or "").strip()
                if not horse:
                    result.skipped += 1
                    continue
                position = _position(col("position"))
                explicit_win = _num(col("res_win"))
                won = (
                    int(explicit_win == 1) if explicit_win is not None
                    else (int(position == 1) if position is not None else None)
                )
                weight_lbs = _num(col("weight_lbs"))
                if weight_lbs is None:
                    kilos = _num(col("weight_kg"))
                    weight_lbs = kilos * 2.20462 if kilos else None
                runner_db_id = repo.upsert_runner(conn, db_race_id, RunnerRecord(
                    horse=horse,
                    trainer=(col("trainer") or "").strip() or None,
                    jockey=(col("jockey") or "").strip() or None,
                    draw=_int(col("draw")),
                    weight_lbs=weight_lbs,
                    official_rating=_num(col("official_rating")),
                    age=_int(col("age")),
                    status="ran" if position is not None else "nonrunner",
                    finish_pos=position,
                    beaten_lengths=_num(col("beaten")),
                    win_flag=won if position is not None else None,
                ))
                result.runners += 1

                # The recorded price is the starting price: the closing line,
                # and the benchmark the value engine is measured against.
                price = _odds(col("decimal_odds"))
                if price and price > 1.0:
                    repo.add_odds_snapshot(
                        conn, runner_db_id, "book", f"{date}T12:00:00+00:00",
                        price, bookmaker="SP",
                    )
