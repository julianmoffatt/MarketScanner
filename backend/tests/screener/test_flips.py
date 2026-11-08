import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.src.market_platform.api.main import app
from backend.src.market_platform import pipeline
from backend.src.market_platform.analysis.screeners import flips
from backend.src.market_platform.services import screener_service


def make_timeframes(days=1500, seed=0):
    """[daily, weekly, monthly, quarterly, yearly] sinteticos con las columnas que usa el screener."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=days, freq="B", tz="UTC")
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.015, days))), index=idx)
    daily = pd.DataFrame({"Open": close.shift(1).fillna(close.iloc[0]), "Close": close})

    def resample(df, rule):
        return df.resample(rule, label="left", closed="left").agg({"Open": "first", "Close": "last"}).dropna()

    weekly = resample(daily, "W-MON")
    monthly = resample(daily, "MS")
    quarterly = resample(monthly, "QS")
    yearly = resample(quarterly, "YS")
    return [daily, weekly, monthly, quarterly, yearly]


# ---- count_flips: casos calculados a mano ----

def test_a_flip_needs_a_close_beyond_the_volatility_band():
    # open 100, banda de 1 % (vol 1 x peso 1). Empieza encima (101 >= 100).
    closes = np.array([101.0, 99.5, 98.9, 100.5, 101.2])
    vols = np.ones(5)

    result = flips.count_flips(closes, vols, 100.0, 1.0, 1.0, 1.0)

    # 99.5 no baja de 99 (sin flip); 98.9 si (flip 1, vela 3); 100.5 no sube de 101; 101.2 si (flip 2, vela 5).
    assert result == (2, 5)


def test_no_flips_returns_last_flip_one():
    assert flips.count_flips(np.array([101.0, 102.0, 101.5]), np.ones(3), 100.0, 1.0, 1.0, 1.0) == (0, 1)


def test_starts_below_when_the_first_close_is_under_the_open():
    # Empieza debajo (99 < 100): para flipear tiene que cerrar por encima de 101.
    assert flips.count_flips(np.array([99.0, 100.9, 101.1]), np.ones(3), 100.0, 1.0, 1.0, 1.0) == (1, 3)


def test_band_scales_with_the_weight_and_is_clamped_between_the_low_and_high_volatility():
    closes = np.array([101.0, 98.0])
    # La vol actual es 10 % pero el tope (vol_high) es 1 %: la banda queda en 1 x peso 2 = 2 %,
    # y 98 no baja de 98 (sin flip). Con peso 1.5 la banda es 1.5 % y 98 < 98.5 si flipea.
    assert flips.count_flips(closes, np.array([1.0, 10.0]), 100.0, 1.5, 1.0, 1.0) == (1, 2)


def test_nan_volatility_falls_back_to_the_low_volatility_band():
    closes = np.array([101.0, 98.9])
    assert flips.count_flips(closes, np.array([np.nan, np.nan]), 100.0, 1.0, 1.0, 5.0) == (1, 2)


# ---- compute ----

def test_distribution_sums_to_100_and_the_current_candle_is_excluded():
    timeframes = make_timeframes()

    row = flips.compute("AAA", "daily", timeframes)

    assert [b["timeframe"] for b in row["blocks"]] == ["weekly", "monthly", "quarterly", "yearly"]
    for block, timeframe in zip(row["blocks"], ["weekly", "monthly", "quarterly", "yearly"]):
        assert sum(block["distribution"]) == pytest.approx(100, abs=0.3)
        assert len(block["distribution"]) == flips.BUCKETS["daily"][timeframe]
        # una vela alta menos que las que hay: la ultima (en curso) no entra en la distribucion
        assert block["occurrences"] == len(timeframes[flips.TIMEFRAMES.index(timeframe)]) - 1


def test_current_bucket_is_the_current_flip_count_capped_at_the_last_bucket():
    row = flips.compute("AAA", "daily", make_timeframes())

    for block in row["blocks"]:
        last = len(block["distribution"]) - 1
        assert block["current_bucket"] == min(block["current_flips"], last)


def test_monthly_lower_timeframe_only_has_quarterly_and_yearly():
    row = flips.compute("AAA", "monthly", make_timeframes(days=2500))

    assert [b["timeframe"] for b in row["blocks"]] == ["quarterly", "yearly"]
    assert len(row["blocks"][0]["distribution"]) == 3  # un trimestre tiene 3 meses: 0, 1 o 2+ flips


def test_too_little_history_returns_none():
    assert flips.compute("AAA", "daily", make_timeframes(days=15)) is None


def test_bucket_labels_group_the_tail():
    assert flips.bucket_labels(3) == ["0", "1", "2+"]


# ---- API ----

@pytest.fixture
def client(monkeypatch):
    frames = {"AAA": make_timeframes(seed=1), "BBB": make_timeframes(seed=2), "SHORT": make_timeframes(days=15)}

    def processed(ticker, kind):
        if ticker not in frames:
            raise FileNotFoundError(ticker)
        return [df.copy() for df in frames[ticker]]

    monkeypatch.setattr(pipeline, "processedTimeframes", processed)
    monkeypatch.setattr(
        screener_service, "load_config",
        lambda: {"universes": {"mine": ["AAA", "BBB", "AAA", "SHORT", "NOPE"]}},
    )
    return TestClient(app)


def test_endpoint_returns_rows_buckets_and_missing_assets(client):
    response = client.get("/screeners/flips/mine")

    assert response.status_code == 200
    body = response.json()
    assert body["lower"] == "daily"
    assert [row["ticker"] for row in body["rows"]] == ["AAA", "BBB"]
    assert body["missing"] == ["SHORT", "NOPE"]  # sin historia o sin datos: se informan y no rompen la tabla
    assert body["buckets"]["weekly"] == ["0", "1", "2+"]
    assert len(body["rows"][0]["blocks"]) == 4


def test_endpoint_accepts_the_monthly_lower_timeframe(client):
    body = client.get("/screeners/flips/mine?lower=monthly").json()

    assert body["lower"] == "monthly"
    assert list(body["buckets"]) == ["quarterly", "yearly"]


def test_endpoint_rejects_an_unsupported_lower_timeframe(client):
    assert client.get("/screeners/flips/mine?lower=weekly").status_code == 422
