"""Source interface for the daily pipeline.

Sources populate the local database; the analytical layers only ever read
from the database. A source's ``sync_daily`` is called before the daily run
to bring racecards and odds for the target date up to date.
"""

from __future__ import annotations

import sqlite3
from typing import Protocol

from furlong.config import Settings


class Source(Protocol):
    name: str

    def sync_daily(self, settings: Settings, conn: sqlite3.Connection, date: str) -> None:
        """Fetch/refresh racecards and odds for ``date`` into the database."""
        ...


def get_source(settings: Settings) -> "Source":
    if settings.source == "synthetic":
        from furlong.sources.synthetic import SyntheticSource

        return SyntheticSource()
    if settings.source == "racing_api":
        from furlong.sources.racing_api import RacingApiSource

        return RacingApiSource()
    raise ValueError(
        f"Unknown FURLONG_SOURCE {settings.source!r}: expected 'synthetic' or 'racing_api'"
    )
