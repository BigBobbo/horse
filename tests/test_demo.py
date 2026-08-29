"""The fresh-checkout guarantee: `furlong demo` must work with no keys."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from furlong.cli import build_parser, main
from furlong.config import Settings
from furlong.pipeline.demo import run_demo
from furlong.web.app import create_app


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    settings = Settings(data_dir=tmp_path_factory.mktemp("demo") / "data")
    summary = run_demo(settings, seed=42, seasons=2)
    return settings, summary


def test_demo_reports_the_headline_numbers(demo):
    _, summary = demo
    assert {"delta_r2", "backtest_roi", "backtest_bets", "date",
            "n_suggestions", "mean_clv"} <= set(summary)
    assert summary["backtest_bets"] > 0
    assert summary["n_suggestions"] >= 0


def test_demo_finds_the_planted_edge(demo):
    """The demo must demonstrate a working system, not just run."""
    _, summary = demo
    assert summary["delta_r2"] > 0, "model added no information over the market"
    assert summary["backtest_roi"] > 0, "value strategy did not beat the market"


def test_demo_writes_its_artifacts(demo):
    settings, summary = demo
    data_dir = Path(settings.data_dir)
    assert (data_dir / "furlong.sqlite").exists()
    assert (data_dir / "reports" / "backtest.json").exists()
    assert (data_dir / "reports" / "backtest.html").exists()
    assert (data_dir / "reports" / "performance.json").exists()
    assert (data_dir / "models" / "gbm.txt").exists()

    payload = json.loads((data_dir / "reports" / "backtest.json").read_text())
    assert payload["n_bets"] == summary["backtest_bets"]


def test_web_serves_the_demo_database(demo):
    """After the demo, the app must be browsable and populated."""
    settings, summary = demo
    client = TestClient(create_app(settings))

    today = client.get("/")
    assert today.status_code == 200
    assert summary["date"] in today.text

    performance = client.get("/performance")
    assert performance.status_code == 200
    assert "Mean CLV" in performance.text

    api = client.get("/api/performance").json()
    assert api["n_settled"] == summary["n_suggestions"]


# -- the CLI contract -------------------------------------------------------

def test_cli_lists_every_documented_command():
    parser = build_parser()
    subparsers = [
        action for action in parser._actions
        if hasattr(action, "choices") and isinstance(action.choices, dict)
    ][0]
    expected = {
        "init-db", "generate", "ingest-bsp", "import-csv", "train", "backtest",
        "daily", "rescore", "settle", "report", "web", "demo",
    }
    assert expected <= set(subparsers.choices)


def test_cli_help_exits_cleanly(capsys):
    assert main([]) == 0
    assert "value engine" in capsys.readouterr().out


def test_cli_init_db_and_generate(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FURLONG_DATA_DIR", str(tmp_path / "data"))
    assert main(["init-db"]) == 0
    assert "Initialised database" in capsys.readouterr().out

    assert main(["generate", "--seed", "5", "--horses", "120", "--seasons", "1"]) == 0
    out = capsys.readouterr().out
    assert "Synthetic world" in out


def test_cli_ingest_bsp_without_input_fails_clearly(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FURLONG_DATA_DIR", str(tmp_path / "data"))
    assert main(["ingest-bsp"]) == 1
    assert "Nothing to ingest" in capsys.readouterr().err
