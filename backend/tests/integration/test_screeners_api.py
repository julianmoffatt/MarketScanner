import pytest
from fastapi.testclient import TestClient

from backend.src.market_platform import pipeline
from backend.src.market_platform.api.main import app
from backend.src.market_platform.api.schemas import MeanReversionScreener_Row
from backend.src.market_platform.services import screener_service

pytestmark = pytest.mark.integration


@pytest.fixture
def client(monkeypatch, screener_timeframes):
    monkeypatch.setattr(pipeline, "processedTimeframes", lambda ticker, i: [df.copy() for df in screener_timeframes])
    monkeypatch.setattr(screener_service, "load_config", lambda: {"universes": {"mine": ["AAA", "BBB", "AAA"], "empty": []}})
    return TestClient(app)


def test_returns_one_row_per_ticker_in_the_universe(client):
    response = client.get("/screeners/mean_reversion/mine")

    assert response.status_code == 200
    body = response.json()
    assert body["universe"] == "mine"
    assert [row["ticker"] for row in body["rows"]] == ["AAA", "BBB"]


def test_every_row_has_all_the_schema_fields(client):
    rows = client.get("/screeners/mean_reversion/mine").json()["rows"]

    assert all(set(row) == set(MeanReversionScreener_Row.model_fields) for row in rows)


def test_missing_values_are_sent_as_null(client):
    row = client.get("/screeners/mean_reversion/mine").json()["rows"][0]

    assert row["monthly_strike_percentile"] is None


def test_empty_universe_returns_no_rows(client):
    response = client.get("/screeners/mean_reversion/empty")

    assert response.status_code == 200
    assert response.json()["rows"] == []


def test_unknown_universe_returns_404_listing_the_available_ones(client):
    response = client.get("/screeners/mean_reversion/nope")

    assert response.status_code == 404
    assert "empty" in response.json()["detail"] and "mine" in response.json()["detail"]


def test_post_is_not_allowed(client):
    assert client.post("/screeners/mean_reversion/mine").status_code == 405
