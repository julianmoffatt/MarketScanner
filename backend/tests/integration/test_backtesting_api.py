import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.src.market_platform import pipeline
from backend.src.market_platform.api.main import app

pytestmark = pytest.mark.integration

DATES = pd.bdate_range("2021-01-04", periods=800)


def synthetic_daily(seed):
    returns = np.random.default_rng(seed).normal(0.0004, 0.01, len(DATES))
    extension = np.random.default_rng(seed + 100).normal(size=len(DATES))
    return pd.DataFrame({"Close": 100 * np.exp(np.cumsum(returns)), "extension_ema20": extension}, index=DATES)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(pipeline, "processedTimeframes", lambda ticker, i: (synthetic_daily(sum(map(ord, ticker))), None))
    return TestClient(app)


def payload(**overrides):
    body = {"tickers": ["AAA", "BBB"], "strategy": "buy_and_hold", "config": {"window_years": 1}}
    body.update(overrides)
    return body


def test_run_returns_the_full_response_shape(client):
    response = client.post("/backtesting/run", json=payload())

    assert response.status_code == 200
    body = response.json()
    assert body["tickers"] == ["AAA", "BBB"]
    assert body["strategy"] == "buy_and_hold"
    assert len(body["equity"]) == len(body["benchmark_equity"]) == len(body["exposure"])
    assert set(body["average_exposure"]) == {"AAA", "BBB"}
    assert "total_return" in body["metrics"]
    assert "total_return" in body["benchmark_metrics"]


def test_buy_and_hold_with_full_initial_exposure_matches_its_benchmark(client):
    config = {"window_years": 1, "initial_exposure": 1.0}

    body = client.post("/backtesting/run", json=payload(config=config)).json()

    assert [p["value"] for p in body["equity"]] == pytest.approx([p["value"] for p in body["benchmark_equity"]])


def test_mean_reversion_strategy_runs(client):
    response = client.post("/backtesting/run", json=payload(strategy="mean_reversion_distance"))

    assert response.status_code == 200


def test_unknown_strategy_returns_422(client):
    response = client.post("/backtesting/run", json=payload(strategy="nope"))

    assert response.status_code == 422
    assert "no registrada" in response.json()["detail"]


def test_invalid_config_returns_422(client):
    response = client.post("/backtesting/run", json=payload(config={"starting_capital": -5}))

    assert response.status_code == 422


def test_missing_tickers_returns_422(client):
    assert client.post("/backtesting/run", json={"strategy": "buy_and_hold", "config": {}}).status_code == 422


def test_get_is_not_allowed(client):
    assert client.get("/backtesting/run").status_code == 405
