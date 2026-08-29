"""Shared fixtures: temporary settings and a small deterministic world."""

from __future__ import annotations

import sqlite3

import pytest

from furlong.config import Settings
from furlong.db import init_db
from furlong.sources.synthetic import generate_world


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path / "data")


@pytest.fixture
def conn(settings) -> sqlite3.Connection:
    connection = init_db(settings.database_path)
    yield connection
    connection.close()


# A deterministic world shared by the analytical tests. 420 days (~1.15
# seasons) generates in ~2 seconds and leaves ~490 races in the test split,
# enough for the blend's Delta R-squared assertion to be stable.
WORLD_SEED = 11
WORLD_DAYS = 420
WORLD_HORSES = 400


@pytest.fixture(scope="session")
def world_settings(tmp_path_factory) -> Settings:
    data_dir = tmp_path_factory.mktemp("world") / "data"
    settings = Settings(data_dir=data_dir)
    generate_world(settings, seed=WORLD_SEED, n_horses=WORLD_HORSES, days=WORLD_DAYS)
    return settings


@pytest.fixture
def world_conn(world_settings) -> sqlite3.Connection:
    connection = init_db(world_settings.database_path)
    yield connection
    connection.close()
