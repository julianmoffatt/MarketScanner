import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.src.market_platform import pipeline
from backend.src.market_platform.api.main import app

pytestmark = pytest.mark.integration


def with_types(*types):
    return pd.DataFrame({"type": list(types)})


@pytest.fixture
def client(monkeypatch):
    # pipeline.processedTimeframes(ticker, 0) -> timeframes altos; (ticker, 1) -> 1h y 4h
    timeframes = {
        0: [with_types("Green", "Red", "Red")] * 5,
        1: [with_types("Green", "Green", "Red"), with_types("Red", "Green")],
    }
    monkeypatch.setattr(pipeline, "processedTimeframes", lambda ticker, kind: timeframes[kind])
    return TestClient(app)


def test_lower_timeframe_endpoint_returns_1h_and_4h_panels(client):
    response = client.get("/analytics/btc/strikes_candles_lt")

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "btc"
    assert [(p["timeframe"], p["type"]) for p in body["panels"]] == [
        ("1h", "Green"), ("1h", "Red"), ("4h", "Green"), ("4h", "Red"),
    ]


def test_lower_timeframe_rows_follow_the_response_schema(client):
    panels = client.get("/analytics/btc/strikes_candles_lt").json()["panels"]

    green_1h = next(p for p in panels if p["timeframe"] == "1h" and p["type"] == "Green")
    assert green_1h["rows"] == [{"length": 2, "count": 1, "pct": 100.0}]
    assert green_1h["current_length"] == 1
    assert green_1h["is_current"] is False


def test_higher_timeframe_endpoint_is_unchanged(client):
    panels = client.get("/analytics/sp500/strikes_candles").json()["panels"]

    assert {p["timeframe"] for p in panels} == {"daily", "weekly", "monthly"}


def test_fundamentals_endpoint_returns_sections(client, monkeypatch):
    from backend.src.market_platform.services import fundamentals_service

    monkeypatch.setattr(fundamentals_service, "fetch_info", lambda s: {"quoteType": "EQUITY", "trailingPE": 25.0})
    fundamentals_service.clear_cache()

    body = client.get("/analytics/aapl/fundamentals").json()

    fundamentals_service.clear_cache()
    assert body["ticker"] == "aapl"
    assert body["available"] is True
    assert body["valuation"]["trailing_pe"] == 25.0
    assert set(body) >= {"profitability", "growth", "balance_dividend", "analysts"}


def test_correlations_endpoint_returns_table_and_curves(client, monkeypatch):
    from backend.src.market_platform.services import correlations_service

    fake = {
        "windows": ["1M"],
        "peers": [{"symbol": "AAPL", "group": "Mag 7",
                   "windows": {"1M": {"correlation": 0.5, "beta_up": 1.2, "beta_down": 0.8, "observations": 21,
                                      "observations_up": 11, "observations_down": 10}}}],
        "curves": [{"symbol": "GOOGL", "selected": True, "dates": ["2026-01-01"], "values": [1.5]}],
        "missing": [],
    }
    monkeypatch.setattr(correlations_service, "get_correlations", lambda ticker: fake)

    response = client.get("/analytics/googl/correlations")

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "googl"
    assert body["peers"][0]["windows"]["1M"]["correlation"] == 0.5
    assert body["peers"][0]["windows"]["1M"]["beta_up"] == 1.2
    assert body["peers"][0]["windows"]["1M"]["beta_down"] == 0.8
    assert body["curves"][0]["selected"] is True
