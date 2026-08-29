from pathlib import Path

import pytest

from furlong.config import ConfigError, Settings


def test_defaults():
    s = Settings.load(env={}, env_file=None)
    assert s.source == "synthetic"
    assert s.exchange_commission == 0.02
    assert s.min_edge == 0.05
    assert s.kelly_fraction == 0.25
    assert s.database_path == Path("data") / "furlong.sqlite"


def test_env_overrides():
    s = Settings.load(env={
        "FURLONG_SOURCE": "racing_api",
        "FURLONG_MIN_EDGE": "0.08",
        "FURLONG_DATA_DIR": "/tmp/x",
        "IGNORED": "yes",
    }, env_file=None)
    assert s.source == "racing_api"
    assert s.min_edge == 0.08
    assert s.data_dir == Path("/tmp/x")


def test_env_file_and_precedence(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FURLONG_MIN_EDGE=0.10\nFURLONG_SOURCE=racing_api\n# comment\n")
    s = Settings.load(env={"FURLONG_MIN_EDGE": "0.20"}, env_file=env_file)
    assert s.min_edge == 0.20  # environment beats .env file
    assert s.source == "racing_api"  # .env applies when env doesn't override


def test_bad_float_raises():
    with pytest.raises(ConfigError, match="FURLONG_MIN_EDGE"):
        Settings.load(env={"FURLONG_MIN_EDGE": "not-a-number"}, env_file=None)


def test_racing_api_credentials_only_required_on_use():
    s = Settings.load(env={}, env_file=None)  # loads fine without credentials
    with pytest.raises(ConfigError, match="RACING_API_USERNAME"):
        s.require_racing_api()
    s2 = Settings.load(env={
        "FURLONG_RACING_API_USERNAME": "user",
        "FURLONG_RACING_API_PASSWORD": "pass",
    }, env_file=None)
    assert s2.require_racing_api() == ("user", "pass")
