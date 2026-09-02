"""Importer for Betfair's published UK & Irish thoroughbred racing files.

Source: https://betfair-datascientists.github.io/data/dataListing/
(``UK_IE_Thoroughbred_Racing_Model_YYYY.csv``, one file per year to 2025 and
one per month thereafter.)

This is the honest free alternative to the Kaggle archive, and on the axis
that matters most it is better:

* **Betfair Starting Price for every runner that ran.** BSP is the
  margin-free closing price -- the benchmark this whole system is built to
  be measured against, and the one the backtest settles at. The Kaggle
  archive carries industry SP, which is margin-laden and an easier bar.
* **It is current.** 2024 through last month, against Kaggle's stop in 2020.
* **It downloads without a login,** from a host Betfair's own data-science
  team publishes to, under an explicit "you may download this" disclaimer.

What it does *not* carry is form. There is no going, no trainer, no jockey,
no draw, no official rating, no weight, and no finishing position beyond
win/placed/unplaced. **Fourteen of the feature builder's twenty-nine
features are therefore constant** on this data -- every trainer and jockey
statistic, every going feature, the draw and the official rating -- so the
model built from it is substantially weaker than one built on a full form
archive. That is a real limitation, not a rounding error; see
docs/OPERATIONS.md and docs/REAL-DATA-FINDINGS.md.

Three columns need real parsing rather than a cast:

* ``LOCAL_RACE_DATE`` is ISO in the 2026 monthly files and **day-first**
  ``D/M/YYYY`` in the 2024 and 2025 yearly ones. Day-first is not a guess:
  across both yearly files the first component ranges 1-31 and the second
  never exceeds 12.
* ``RACETIME`` is in **Australia/Sydney** time -- the files are published by
  Betfair Australia. Converting it to Europe/Dublin reproduces
  ``LOCAL_RACE_DATE`` on all 143,131 rows that carry one, and yields a
  racing-hours distribution peaking at 14:00-17:00. Reading it as local time
  would put a third of British racing after 22:00.
* ``WIN_MARKET_NAME`` is the only source of distance and code: ``1m4f Hcap``,
  ``2m4f Hcap Hrd``, ``6f Nov Stks``.

``WIN_MARKET_ID`` is **not** a unique race key: an abandoned meeting can
reappear under the same id on the rescheduled day. Races are keyed on
(market id, local date).
"""

from __future__ import annotations

import csv
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from furlong.config import Settings
from furlong.db import init_db
from furlong import repo
from furlong.repo import RaceRecord, RunnerRecord
from furlong.sources.racing_api import parse_distance_m

# The files are produced by Betfair Australia; RACETIME is their local time.
PUBLISHER_TZ = ZoneInfo("Australia/Sydney")
UTC = ZoneInfo("UTC")

REQUIRED_COLUMNS = (
    "LOCAL_RACE_DATE", "TRACK", "WIN_MARKET_ID", "SELECTION_ID",
    "RUNNER_NAME", "WIN_BSP", "WIN_RESULT",
)

# Betfair's numeric country ids. Anything else is out of scope.
COUNTRY_IDS = {1: "GB", 35: "IRE"}

# Suffixes of WIN_MARKET_NAME that mark a National Hunt race.
NH_TOKENS = ("hrd", "chs", "nhf", "inhf", "hunt")

# Betfair grades the card A (best) to H; the feature builder wants the
# British convention where 1 is the best class.
CLASS_LETTERS = {c: i + 1 for i, c in enumerate("ABCDEFGH")}

# WIN_RESULT sentinels.
RESULT_LOST, RESULT_WON, RESULT_NON_RUNNER = 0, 1, -1

MIN_PRICED_RUNNERS = 2

# Where the files live, and the default place to put them.
BASE_URL = "https://betfair-datascientists.github.io/data/assets"
FILE_STEM = "UK_IE_Thoroughbred_Racing_Model"
DEFAULT_DIR_NAME = "betfair-hub"

# Name recorded against RATED_PRICE in benchmark_ratings.
BENCHMARK_SOURCE = "betfair_hub_model"

# The publisher switched from one file per year to one per month during 2026.
FIRST_YEARLY, LAST_YEARLY = 2024, 2025
FIRST_MONTHLY_YEAR = 2026


@dataclass
class BetfairHubImportResult:
    files: int = 0
    races: int = 0
    runners: int = 0
    priced_runners: int = 0
    non_runners: int = 0
    skipped_unsettled: int = 0
    skipped_no_winner: int = 0
    skipped_thin: int = 0
    skipped_foreign: int = 0
    duplicate_rows: int = 0
    errors: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Betfair hub import: {self.races:,} races, {self.runners:,} runners "
            f"({self.priced_runners:,} with BSP, {self.non_runners:,} non-runners) "
            f"from {self.files} file(s)",
            f"  skipped: {self.skipped_unsettled:,} races with no result, "
            f"{self.skipped_no_winner:,} without exactly one winner, "
            f"{self.skipped_thin:,} with fewer than {MIN_PRICED_RUNNERS} priced runners, "
            f"{self.skipped_foreign:,} outside GB/IRE",
        ]
        if self.duplicate_rows:
            lines.append(f"  {self.duplicate_rows:,} duplicate runner row(s) collapsed")
        if self.errors:
            lines.append("  first errors: " + "; ".join(self.errors[:3]))
        return "\n".join(lines)


# -- field parsers ---------------------------------------------------------

def parse_local_date(raw) -> str | None:
    """ISO or day-first ``D/M/YYYY`` to an ISO date string."""
    text = str(raw or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_racetime_utc(raw, date: str, race_number: int | None = None) -> str:
    """RACETIME (Australia/Sydney) to an ISO UTC timestamp.

    Falls back to a placeholder ordered by race number when the column is
    blank, which it is for most of the 2025 file. The fallback preserves
    within-day ordering -- which is all the feature builder needs -- and
    never claims a precision the row does not have.
    """
    text = str(raw or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            naive = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return (naive.replace(tzinfo=PUBLISHER_TZ)
                     .astimezone(UTC).isoformat().replace("+00:00", "+00:00"))
    hour = 12 + min(max(int(race_number or 1) - 1, 0), 9)
    return f"{date}T{hour:02d}:00:00+00:00"


def parse_market_name(raw) -> tuple[float | None, str]:
    """``1m4f Hcap Hrd`` -> (2414.0 metres, 'nh')."""
    text = str(raw or "").strip()
    if not text:
        return None, "flat"
    match = re.match(r"^\s*((?:\d+m)?\s*(?:\d+f)?\s*(?:\d+y)?)", text)
    distance = parse_distance_m(match.group(1).replace(" ", "")) if match else None
    tail = text[match.end():].lower() if match else text.lower()
    race_type = "nh" if any(token in tail.split() for token in NH_TOKENS) else "flat"
    return distance, race_type


def parse_class(race_name) -> int | None:
    """``(Class B)`` -> 2. Betfair letters A-H map to British classes 1-8."""
    match = re.search(r"\(class\s*([a-h0-9])\)", str(race_name or ""), re.IGNORECASE)
    if not match:
        return None
    token = match.group(1).upper()
    if token.isdigit():
        return int(token)
    return CLASS_LETTERS.get(token)


def parse_country(raw) -> str | None:
    """``'1'`` or ``'1.0'`` -> ``'GB'``. Unknown ids are out of scope."""
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        return COUNTRY_IDS.get(int(float(text)))
    except ValueError:
        return None


def _num(raw) -> float | None:
    text = str(raw or "").strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value


def _result(raw) -> int | None:
    value = _num(raw)
    return None if value is None else int(value)


def finish_band(won: bool, placed: bool | None, ran: int, places: int) -> int:
    """A banded finishing position, because the source has no finishing order.

    The file records only whether a runner won, and whether it was placed in
    Betfair's place market. That is a genuine three-way ordering, so it is
    imported as one:

    * winner -> 1
    * placed, not the winner -> 2
    * ran, unplaced -> the midpoint of the band it must lie in

    The midpoint is the minimum-assumption estimate for a runner known only
    to have finished behind the places. It keeps ``recent_form`` monotone in
    the information actually present without inventing an exact position for
    a horse whose finishing place is genuinely unknown. Elo and the career
    strike rate use ``win_flag`` and are unaffected; the career place rate
    becomes a Betfair-place-market strike rate, whose number of places varies
    with field size -- which is a real quantity, not a fixed top three.
    """
    if won:
        return 1
    if placed:
        return 2
    lower = max(places + 1, 2)
    return max(2, int(round((lower + max(ran, lower)) / 2)))


def _place_terms(ran: int) -> int:
    """Betfair's standard place-market terms, used only to band the field."""
    if ran < 5:
        return 0
    if ran < 8:
        return 2
    return 3


# -- fetching --------------------------------------------------------------

def published_names(today: datetime | None = None) -> list[str]:
    """Names of the files Betfair has published, oldest first.

    Yearly files to 2025, then one per month. The current month is included:
    the publisher updates it in place as racing happens, so a re-download
    picks up the days since the last run.
    """
    now = today or datetime.now()
    names = [f"{FILE_STEM}_{year}.csv" for year in range(FIRST_YEARLY, LAST_YEARLY + 1)]
    for year in range(FIRST_MONTHLY_YEAR, now.year + 1):
        last_month = now.month if year == now.year else 12
        names += [f"{FILE_STEM}_{year}-{month:02d}.csv" for month in range(1, last_month + 1)]
    return names


def download_files(target: str | Path, today: datetime | None = None,
                   timeout: int = 120) -> tuple[list[Path], list[tuple[str, str]]]:
    """Download the published files into ``target``.

    Returns the paths written and a list of (name, reason) for those that
    could not be fetched. A month that does not exist yet 404s, which is a
    normal state and not an error worth stopping for.
    """
    directory = Path(target)
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    failures: list[tuple[str, str]] = []
    for name in published_names(today):
        destination = directory / name
        try:
            with urllib.request.urlopen(f"{BASE_URL}/{name}", timeout=timeout) as response:
                payload = response.read()
        except (urllib.error.URLError, OSError) as exc:
            failures.append((name, str(exc)))
            continue
        destination.write_bytes(payload)
        written.append(destination)
    return written, failures


# -- reading ---------------------------------------------------------------

def _csv_paths(target: str | Path) -> list[Path]:
    path = Path(target)
    if path.is_dir():
        return sorted(path.glob("*.csv"))
    return [path] if path.exists() else []


def _read_rows(paths: list[Path], result: BetfairHubImportResult) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        try:
            with open(path, newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames or ())
                if missing:
                    result.errors.append(
                        f"{path.name}: missing column(s) {', '.join(sorted(missing))}")
                    continue
                rows.extend(reader)
            result.files += 1
        except OSError as exc:                       # pragma: no cover - I/O
            result.errors.append(f"{path.name}: {exc}")
    return rows


def inspect(target: str | Path) -> dict:
    """Report the shape of the files without importing anything."""
    result = BetfairHubImportResult()
    paths = _csv_paths(target)
    rows = _read_rows(paths, result)
    dates = sorted(d for d in (parse_local_date(r["LOCAL_RACE_DATE"]) for r in rows) if d)
    tracks: dict[str, int] = {}
    countries: dict[str, int] = {}
    races: set[tuple[str, str]] = set()
    for row in rows:
        date = parse_local_date(row["LOCAL_RACE_DATE"])
        if not date:
            continue
        races.add((str(row["WIN_MARKET_ID"]), date))
        tracks[row["TRACK"]] = tracks.get(row["TRACK"], 0) + 1
        country = parse_country(row.get("COUNTRY_ID")) or "unknown"
        countries[country] = countries.get(country, 0) + 1
    return {
        "files": result.files,
        "paths": [p.name for p in paths],
        "rows": len(rows),
        "races": len(races),
        "first": dates[0] if dates else None,
        "last": dates[-1] if dates else None,
        "countries": sorted(countries.items(), key=lambda kv: -kv[1]),
        "tracks": sorted(tracks.items(), key=lambda kv: -kv[1])[:12],
        "errors": result.errors,
    }


# -- import ----------------------------------------------------------------

def import_betfair_hub(settings: Settings, target: str | Path,
                       since: str | None = None,
                       until: str | None = None,
                       with_benchmark: bool = False) -> BetfairHubImportResult:
    """Import Betfair's UK/IRE model files into the Furlong database.

    ``with_benchmark`` also stores the file's own ``RATED_PRICE`` in
    ``benchmark_ratings``. That column is *another model's opinion*, so it is
    never a feature and the market layer cannot reach it: it is not in
    ``odds_snapshots`` at all, and ``MARKET_SOURCES`` lists only
    bsp/exchange/book. It is imported solely so Furlong's edge can be
    compared against a published one on identical races.
    """
    result = BetfairHubImportResult()
    paths = _csv_paths(target)
    if not paths:
        result.errors.append(f"no CSV files found at {target}")
        return result

    rows = _read_rows(paths, result)
    if not rows:
        return result

    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        market_id = str(row.get("WIN_MARKET_ID") or "").strip()
        date = parse_local_date(row.get("LOCAL_RACE_DATE"))
        if not market_id or not date:
            continue
        if since and date < since:
            continue
        if until and date > until:
            continue
        grouped.setdefault((market_id, date), []).append(row)

    conn = init_db(settings.database_path)
    written = 0

    for (market_id, date), group in sorted(grouped.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        seen: set[str] = set()
        runners = []
        for row in group:
            selection = str(row.get("SELECTION_ID") or "").strip()
            if selection and selection in seen:
                result.duplicate_rows += 1
                continue
            seen.add(selection)
            runners.append(row)

        outcomes = [_result(r.get("WIN_RESULT")) for r in runners]
        if all(o is None for o in outcomes):
            result.skipped_unsettled += 1
            continue
        if sum(1 for o in outcomes if o == RESULT_WON) != 1:
            result.skipped_no_winner += 1
            continue

        head = runners[0]
        country = parse_country(head.get("COUNTRY_ID"))
        if country is None:
            country = next(
                (c for c in (parse_country(r.get("COUNTRY_ID")) for r in runners) if c),
                None,
            )
        if country is None:
            result.skipped_foreign += 1
            continue

        ran_rows = [
            (row, outcome) for row, outcome in zip(runners, outcomes)
            if outcome in (RESULT_LOST, RESULT_WON)
        ]
        priced = [(row, o) for row, o in ran_rows if (_num(row.get("WIN_BSP")) or 0) > 1.0]
        if len(priced) < MIN_PRICED_RUNNERS:
            result.skipped_thin += 1
            continue

        market_name = next((r.get("WIN_MARKET_NAME") for r in runners
                            if str(r.get("WIN_MARKET_NAME") or "").strip()), "")
        distance_m, race_type = parse_market_name(market_name)
        race_number = None
        for row in runners:
            race_number = _num(row.get("RACE_NUMBER"))
            if race_number:
                break
        racetime = next((r.get("RACETIME") for r in runners
                         if str(r.get("RACETIME") or "").strip()), "")

        race_db_id = repo.upsert_race(conn, RaceRecord(
            source_id=f"BFHUB-{market_id}-{date}",
            course=str(head.get("TRACK") or "").strip() or "Unknown",
            country=country,
            date=date,
            start_time_utc=parse_racetime_utc(racetime, date,
                                              int(race_number) if race_number else None),
            race_type=race_type,
            distance_m=distance_m or 0.0,
            # The files carry no going. Recording "good" -- the normaliser's
            # default -- would silently invent a ground condition for every
            # race in the archive, so the absence is recorded as an absence.
            going="unknown",
            race_class=parse_class(head.get("RACE_NAME")),
            field_size=len(ran_rows),
            status="result",
        ))
        result.races += 1

        n_ran = len(ran_rows)
        places = _place_terms(n_ran)
        for row, outcome in zip(runners, outcomes):
            horse = str(row.get("RUNNER_NAME") or "").strip()
            if not horse:
                continue
            if outcome == RESULT_WON or outcome == RESULT_LOST:
                place_result = _result(row.get("PLACE_RESULT"))
                runner_id = repo.upsert_runner(conn, race_db_id, RunnerRecord(
                    horse=horse,
                    status="ran",
                    finish_pos=finish_band(outcome == RESULT_WON,
                                           place_result == 1, n_ran, places),
                    win_flag=int(outcome == RESULT_WON),
                ))
                result.runners += 1
                bsp = _num(row.get("WIN_BSP"))
                if bsp and bsp > 1.0:
                    repo.upsert_bsp(conn, runner_id, "win", bsp)
                    result.priced_runners += 1
                place_bsp = _num(row.get("PLACE_BSP"))
                if place_bsp and place_bsp > 1.0:
                    repo.upsert_bsp(conn, runner_id, "place", place_bsp)
            else:
                runner_id = repo.upsert_runner(conn, race_db_id, RunnerRecord(
                    horse=horse, status="nonrunner",
                ))
                result.non_runners += 1

            if with_benchmark:
                rated = _num(row.get("RATED_PRICE"))
                if rated and rated > 1.0:
                    repo.upsert_benchmark_rating(conn, runner_id,
                                                 BENCHMARK_SOURCE, rated)

            written += 1
            if written % 20000 == 0:
                conn.commit()

    conn.commit()
    conn.close()
    return result
