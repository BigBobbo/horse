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


# A moderately sized deterministic world shared by analytical tests.
# ~180 days keeps generation around a second while giving enough history
# for feature/model tests.
WORLD_SEED = 11
WORLD_DAYS = 180
WORLD_HORSES = 300


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
