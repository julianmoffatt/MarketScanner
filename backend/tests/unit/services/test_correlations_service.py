import numpy as np
import pandas as pd
import pytest

from backend.src.market_platform import pipeline
from backend.src.market_platform.services import correlations_service


def daily_frame(seed, tz="UTC", periods=800):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=periods, freq="D", tz=tz)
    return pd.DataFrame({"Close": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, periods)))}, index=idx)


@pytest.fixture
def fake_pipeline(monkeypatch):
    frames = {s: daily_frame(i) for i, s in enumerate(["GOOGL", "AAPL", "SP500", "BTC"])}
    requested = []

    def processed(symbol, kind):
        requested.append(symbol)
        if symbol not in frames:
            raise FileNotFoundError(symbol)  # activos sin datos
        return [frames[symbol]]

    monkeypatch.setattr(pipeline, "processedTimeframes", processed)
    monkeypatch.setattr(correlations_service, "peer_list",
                        lambda: [("AAPL", "Equity"), ("MSFT", "Equity"), ("SP500", "Index"), ("BTC", "Crypto")])
    return requested


def test_peer_list_contains_indices_commodities_and_bitcoin():
    peers = correlations_service.peer_list()

    assert [s for s, _ in peers] == ["SP500", "NASDAQ", "GOLD", "SILVER", "OIL", "BTC"]
    assert {g for _, g in peers} == {"Index", "Commodity", "Crypto"}


def test_result_has_table_curves_and_missing_assets(fake_pipeline):
    result = correlations_service.get_correlations("googl")  # minusculas, como llega de la URL

    assert [p["symbol"] for p in result["peers"]] == ["AAPL", "SP500", "BTC"]
    assert result["missing"] == ["MSFT"]  # sin datos: se informa y no rompe la pantalla
    assert [c["symbol"] for c in result["curves"]][0] == "GOOGL"


def test_missing_selected_asset_raises(fake_pipeline):
    with pytest.raises(FileNotFoundError):
        correlations_service.get_correlations("UNKNOWN")


def test_timezone_aware_and_naive_series_can_be_compared(monkeypatch):
    frames = {"AAA": daily_frame(1, tz="UTC"), "BBB": daily_frame(2, tz=None)}
    monkeypatch.setattr(pipeline, "processedTimeframes", lambda symbol, kind: [frames[symbol]])
    monkeypatch.setattr(correlations_service, "peer_list", lambda: [("BBB", "Index")])

    result = correlations_service.get_correlations("AAA")

    assert result["peers"][0]["windows"]["1Y"]["observations"] > 300
