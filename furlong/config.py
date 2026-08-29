"""Configuration for Furlong.

Settings load from (in precedence order): explicit overrides, environment
variables prefixed ``FURLONG_``, a ``.env`` file in the working directory,
then built-in defaults. Credentials for real data sources are only required
at the moment the relevant source is used.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, fields
from pathlib import Path

ENV_PREFIX = "FURLONG_"


class ConfigError(RuntimeError):
    """Raised when configuration required for the requested operation is missing."""


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal KEY=VALUE .env file (no quoting rules, # comments)."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


@dataclass
class Settings:
    # Storage
    data_dir: Path = Path("data")
    db_path: Path | None = None  # defaults to data_dir / "furlong.sqlite"

    # Data source for the daily pipeline: synthetic | racing_api
    source: str = "synthetic"

    # The Racing API credentials (HTTP basic auth)
    racing_api_username: str | None = None
    racing_api_password: str | None = None
    racing_api_base_url: str = "https://api.theracingapi.com/v1"

    # Value engine
    exchange_commission: float = 0.02  # Betfair My Rewards Basic plan
    min_edge: float = 0.05            # minimum EV per unit staked to suggest
    min_prob: float = 0.05            # Bolton-Chapman longshot exclusion
    max_odds: float = 21.0            # never advise above this decimal price

    # Staking
    kelly_fraction: float = 0.25
    bankroll_units: float = 200.0
    max_stake_pct: float = 0.02       # per-bet cap as fraction of bankroll
    max_daily_stake_pct: float = 0.10  # per-day cap as fraction of bankroll

    # Display / scheduling
    timezone: str = "Europe/Dublin"

    # Populated for provenance
    env_file: Path | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # Accept plain strings for path settings: constructing Settings
        # directly is common in scripts and tests.
        if not isinstance(self.data_dir, Path):
            self.data_dir = Path(self.data_dir)
        if self.db_path is not None and not isinstance(self.db_path, Path):
            self.db_path = Path(self.db_path)

    @property
    def database_path(self) -> Path:
        return self.db_path if self.db_path is not None else self.data_dir / "furlong.sqlite"

    # -- loading -----------------------------------------------------------

    _FLOAT_FIELDS = {
        "exchange_commission",
        "min_edge",
        "min_prob",
        "max_odds",
        "kelly_fraction",
        "bankroll_units",
        "max_stake_pct",
        "max_daily_stake_pct",
    }
    _PATH_FIELDS = {"data_dir", "db_path"}

    @classmethod
    def load(cls, env: dict[str, str] | None = None, env_file: str | Path | None = ".env",
             **overrides) -> "Settings":
        """Build settings from defaults <- .env file <- environment <- overrides."""
        environ = dict(os.environ if env is None else env)
        file_path = Path(env_file) if env_file else None
        file_values = _parse_env_file(file_path) if file_path else {}

        merged: dict[str, str] = {}
        merged.update(file_values)
        merged.update({k: v for k, v in environ.items() if k.startswith(ENV_PREFIX)})

        kwargs: dict[str, object] = {}
        valid_names = {f.name for f in fields(cls) if f.name != "env_file"}
        for key, raw in merged.items():
            if not key.startswith(ENV_PREFIX):
                continue
            name = key[len(ENV_PREFIX):].lower()
            if name not in valid_names:
                continue
            if name in cls._FLOAT_FIELDS:
                try:
                    kwargs[name] = float(raw)
                except ValueError as exc:
                    raise ConfigError(f"{key} must be a number, got {raw!r}") from exc
            elif name in cls._PATH_FIELDS:
                kwargs[name] = Path(raw)
            else:
                kwargs[name] = raw

        kwargs.update(overrides)
        settings = cls(**kwargs)  # type: ignore[arg-type]
        settings.env_file = file_path if file_values else None
        return settings

    # -- guarded accessors -------------------------------------------------

    def require_racing_api(self) -> tuple[str, str]:
        """Return (username, password) or raise a clear error."""
        if not self.racing_api_username or not self.racing_api_password:
            raise ConfigError(
                "The Racing API credentials are not configured. Set "
                "FURLONG_RACING_API_USERNAME and FURLONG_RACING_API_PASSWORD "
                "(see docs/OPERATIONS.md for how to obtain a key)."
            )
        return self.racing_api_username, self.racing_api_password
