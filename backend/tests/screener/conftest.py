import numpy as np
import pandas as pd
import pytest


def _timeframe(seed, periods, freq):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=periods, freq=freq)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0005, 0.02, periods))), index=idx)
    df = pd.DataFrame({"Close": close, "Low": close * 0.99, "High": close * 1.01})
    df["type"] = np.where(close > close.shift(1), "Green", "Red")
    for period in (10, 20, 50):
        df[f"ema{period}"] = close.ewm(span=period, adjust=False).mean()
        df[f"extension_ema{period}"] = (close - df[f"ema{period}"]) / df[f"ema{period}"] * 100
    return df


@pytest.fixture
def screener_timeframes() -> list[pd.DataFrame]:
    """Diario, semanal y mensual sinteticos con las columnas que necesita el screener."""
    return [_timeframe(1, 400, "B"), _timeframe(2, 120, "W"), _timeframe(3, 40, "MS")]
