"""Betfair SP (BSP) file ingestion.

Betfair publishes free daily CSVs of Betfair Starting Prices for GB and
Irish racing back to 28 May 2008 at
https://promo.betfair.com/betfairsp/prices — files named
``dwbfprices{ire|uk}{win|place}DDMMYYYY.csv`` with columns::

    EVENT_ID, MENU_HINT, EVENT_NAME, EVENT_DT, SELECTION_ID, SELECTION_NAME,
    WIN_LOSE, BSP, PPWAP, MORNINGWAP, PPMAX, PPMIN, IPMAX, IPMIN,
    MORNINGTRADEDVOL, PPTRADEDVOL, IPTRADEDVOL

Rows are matched to already-ingested runners by (race date, normalised
horse name); unmatched rows are counted and reported, never fatal.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from furlong.config import Settings
from furlong.db import init_db
from furlong import repo

BASE_URL = "https://promo.betfair.com/betfairsp/prices"

_COUNTRY_SUFFIX = re.compile(r"\s*\((IRE|GB|USA|FR|GER|UAE|AUS|NZ|SAF|JPN|ITY|CAN)\)\s*$",
                             re.IGNORECASE)
_NON_ALNUM = re.compile(r"[^A-Z0-9]")


def normalise_horse_name(name: str) -> str:
    """Uppercase, strip country suffixes and punctuation: ``Sea The Stars (IRE)`` -> ``SEATHESTARS``."""
    cleaned = _COUNTRY_SUFFIX.sub("", name.strip())
    return _NON_ALNUM.sub("", cleaned.upper())


def market_from_filename(path: str | Path) -> str:
    stem = Path(path).name.lower()
    if "place" in stem:
        return "place"
    return "win"


def parse_event_dt(raw: str) -> str | None:
    """``01-07-2024 14:30`` -> ``2024-07-01`` (race-day ISO date)."""
    raw = raw.strip()
    for fmt in ("%d-%m-%Y %H:%M", "%d-%m-%Y", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _to_float(raw: str) -> float | None:
    raw = (raw or "").strip()
    if not raw or raw.upper() in {"NULL", "NA", "N/A", "INF"}:
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value > 0 else None


@dataclass
class IngestResult:
    files: int = 0
    rows_ingested: int = 0
    rows_unmatched: int = 0
    rows_skipped: int = 0


def ingest_files(settings: Settings, paths: list[str | Path]) -> IngestResult:
    conn = init_db(settings.database_path)
    result = IngestResult()

    # Build the (date, normalised horse name) -> runner_id lookup once.
    rows = conn.execute(
        """SELECT r.id AS runner_id, ra.date AS date, h.name AS horse
           FROM runners r JOIN races ra ON ra.id = r.race_id
           JOIN horses h ON h.id = r.horse_id"""
    ).fetchall()
    lookup: dict[tuple[str, str], int] = {}
    ambiguous: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["date"], normalise_horse_name(row["horse"]))
        if key in lookup and lookup[key] != row["runner_id"]:
            ambiguous.add(key)
        lookup[key] = row["runner_id"]

    for path in paths:
        market = market_from_filename(path)
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                result.rows_skipped += 1
                continue
            fieldmap = {name.strip().upper(): name for name in reader.fieldnames}

            def col(row: dict, name: str) -> str:
                actual = fieldmap.get(name)
                return row.get(actual, "") if actual else ""

            for row in reader:
                event_dt = parse_event_dt(col(row, "EVENT_DT"))
                selection = col(row, "SELECTION_NAME")
                if not event_dt or not selection:
                    result.rows_skipped += 1
                    continue
                key = (event_dt, normalise_horse_name(selection))
                if key in ambiguous or key not in lookup:
                    result.rows_unmatched += 1
                    continue
                repo.upsert_bsp(
                    conn,
                    lookup[key],
                    market,
                    bsp=_to_float(col(row, "BSP")),
                    ppwap=_to_float(col(row, "PPWAP")),
                    morning_wap=_to_float(col(row, "MORNINGWAP")),
                    pp_max=_to_float(col(row, "PPMAX")),
                    pp_min=_to_float(col(row, "PPMIN")),
                )
                result.rows_ingested += 1
        result.files += 1

    conn.commit()
    conn.close()
    return result


def download_for_date(settings: Settings, iso_date: str,
                      countries: tuple[str, ...] = ("ire", "uk"),
                      markets: tuple[str, ...] = ("win", "place")) -> list[str]:
    """Download the four daily files for a date. Returns local paths of successes.

    Network failures are reported and skipped — Betfair geo-blocks some
    regions, so this must never crash a pipeline run.
    """
    import httpx

    day = datetime.fromisoformat(iso_date).date()
    stamp = day.strftime("%d%m%Y")
    out_dir = Path(settings.data_dir) / "bsp"
    out_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[str] = []
    for country in countries:
        for market in markets:
            filename = f"dwbfprices{country}{market}{stamp}.csv"
            url = f"{BASE_URL}/{filename}"
            target = out_dir / filename
            try:
                response = httpx.get(url, timeout=30.0, follow_redirects=True)
                if response.status_code == 200 and response.text.upper().startswith("EVENT_ID"):
                    target.write_text(response.text)
                    downloaded.append(str(target))
                else:
                    print(f"  skip {filename}: HTTP {response.status_code} "
                          f"(Betfair may geo-block this region; download manually from "
                          f"{BASE_URL})")
            except Exception as exc:  # noqa: BLE001 — resilience by design
                print(f"  skip {filename}: {exc}")
    return downloaded
