import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    """OHLCV diario sintetico y determinista (300 dias habiles), valido por construccion."""
    rng = np.random.default_rng(42)
    idx = pd.bdate_range("2022-01-03", periods=300)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, len(idx))))
    open_ = close * (1 + rng.normal(0, 0.002, len(idx)))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.003, len(idx))))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.003, len(idx))))
    volume = rng.integers(1_000, 10_000, len(idx)).astype(float)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=idx,
    )
