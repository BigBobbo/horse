import pytest
from fastapi.testclient import TestClient

from furlong.config import Settings
from furlong.db import init_db
from furlong.pipeline.daily import run_daily
from furlong.sources.synthetic import generate_world, resolve_open_card
from furlong.value.settlement import settle_suggestions
from furlong.web.app import create_app

PAGES = ["/", "/performance", "/method"]


@pytest.fixture(scope="module")
def web_settings(tmp_path_factory) -> Settings:
    settings = Settings(data_dir=tmp_path_factory.mktemp("web") / "data")
    generate_world(settings, seed=17, n_horses=400, days=420, open_last_day=True)
    outcome = run_daily(settings)
    resolve_open_card(settings, seed=99)
    settle_suggestions(settings, date=outcome.date)
    settings._demo_date = outcome.date  # type: ignore[attr-defined]
    return settings


@pytest.fixture(scope="module")
def client(web_settings) -> TestClient:
    return TestClient(create_app(web_settings))


# -- pages ------------------------------------------------------------------

@pytest.mark.parametrize("path", PAGES)
def test_pages_render(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert "Furlong" in response.text


@pytest.mark.parametrize("path", PAGES)
def test_every_page_carries_responsible_gambling_information(client, path):
    """Non-negotiable: age gate, helpline and support links on every page."""
    text = client.get(path).text
    assert "18+" in text
    assert "1800 936 725" in text
    assert "gamblingcare.ie" in text.lower()
    assert "does not take bets" in text


def test_today_page_lists_suggestions(client, web_settings):
    text = client.get("/").text
    assert "Suggestions" in text
    # the price-floor warning must be present whenever bets are shown
    assert "Floor" in text or "No qualifying value bets" in text
    if "No qualifying value bets" not in text:
        assert "Do not take a price below the floor" in text


def test_today_page_accepts_a_date(client, web_settings):
    date = web_settings._demo_date
    response = client.get("/", params={"date": date})
    assert response.status_code == 200
    assert date in response.text


def test_today_page_handles_a_day_with_nothing(client):
    response = client.get("/", params={"date": "2019-01-01"})
    assert response.status_code == 200
    assert "No qualifying value bets" in response.text


def test_race_page_renders(client, web_settings):
    conn = init_db(web_settings.database_path)
    race_id = conn.execute(
        "SELECT race_id FROM suggestions LIMIT 1"
    ).fetchone()["race_id"]
    conn.close()
    response = client.get(f"/races/{race_id}")
    assert response.status_code == 200
    assert "Model" in response.text
    assert "BSP" in response.text


def test_missing_race_is_404(client):
    assert client.get("/races/999999").status_code == 404


def test_performance_page_leads_with_clv(client):
    text = client.get("/performance").text
    assert "Mean CLV" in text
    assert "closing line value" in text.lower()


def test_method_page_states_the_hard_numbers(client):
    """The expectations page must not be marketing."""
    text = client.get("/method").text
    assert "losing run" in text.lower()
    assert "4–7% ROI" in text or "4-7% ROI" in text
    assert "Benter" in text
    assert "restrict" in text.lower()


# -- JSON API ---------------------------------------------------------------

def test_api_suggestions_schema(client, web_settings):
    payload = client.get("/api/suggestions").json()
    assert {"date", "count", "suggestions"} <= set(payload)
    assert payload["count"] == len(payload["suggestions"])
    if payload["suggestions"]:
        entry = payload["suggestions"][0]
        assert {"runner_id", "race_id", "advised_odds", "price_floor", "ev",
                "stake_units", "blend_prob", "horse", "course", "status"} <= set(entry)
        assert entry["price_floor"] > 1.0


def test_api_suggestions_validates_the_date(client):
    assert client.get("/api/suggestions", params={"date": "not-a-date"}).status_code == 400
    assert client.get("/api/suggestions", params={"date": "2019-01-01"}).status_code == 200


def test_api_race_schema(client, web_settings):
    conn = init_db(web_settings.database_path)
    race_id = conn.execute("SELECT race_id FROM suggestions LIMIT 1").fetchone()["race_id"]
    conn.close()
    payload = client.get(f"/api/races/{race_id}").json()
    assert {"race", "runners"} <= set(payload)
    assert payload["runners"]
    assert {"horse", "runner_id"} <= set(payload["runners"][0])


def test_api_race_404(client):
    assert client.get("/api/races/999999").status_code == 404


def test_api_performance_schema(client):
    payload = client.get("/api/performance").json()
    assert "n_settled" in payload
    if payload["n_settled"]:
        assert {"mean_clv", "roi", "monthly", "roi_is_significant"} <= set(payload)


def test_empty_database_still_serves(tmp_path):
    settings = Settings(data_dir=tmp_path / "data")
    init_db(settings.database_path).close()
    empty_client = TestClient(create_app(settings))
    for path in PAGES:
        assert empty_client.get(path).status_code == 200
    assert empty_client.get("/api/suggestions").json()["count"] == 0
