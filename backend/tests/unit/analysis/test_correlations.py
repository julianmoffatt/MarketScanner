import numpy as np
import pandas as pd
import pytest

from backend.src.market_platform.analysis import correlations


def prices(returns, start="2020-01-01", freq="D", base=100.0):
    idx = pd.date_range(start, periods=len(returns) + 1, freq=freq)
    return pd.Series(base * np.exp(np.concatenate([[0.0], np.cumsum(returns)])), index=idx)


@pytest.fixture
def rng_returns():
    return np.random.default_rng(7).normal(0.0005, 0.01, 1500)


def test_identical_series_have_correlation_one_and_both_betas_one(rng_returns):
    asset = prices(rng_returns)

    stats = correlations.pair_stats(asset, asset)

    one_year = stats["1Y"]
    assert one_year["correlation"] == pytest.approx(1.0)
    assert one_year["beta_up"] == pytest.approx(1.0)
    assert one_year["beta_down"] == pytest.approx(1.0)


def test_opposite_series_have_correlation_minus_one(rng_returns):
    stats = correlations.pair_stats(prices(rng_returns), prices(-rng_returns))

    assert stats["3M"]["correlation"] == pytest.approx(-1.0)
    assert stats["3M"]["beta_up"] == pytest.approx(-1.0)
    assert stats["3M"]["beta_down"] == pytest.approx(-1.0)


def test_window_without_enough_history_is_none():
    short = prices(np.random.default_rng(1).normal(0, 0.01, 200))  # ~200 dias: no cubre 3Y ni 5Y

    stats = correlations.pair_stats(short, short)

    assert stats["3M"]["correlation"] is not None
    assert stats["1Y"]["correlation"] is None  # 200 dias no cubren un ano
    assert stats["3Y"]["correlation"] is None
    assert stats["3Y"]["beta_up"] is None and stats["3Y"]["beta_down"] is None
    assert stats["5Y"]["correlation"] is None


def test_window_with_too_few_observations_is_none():
    # Dos series con solo 10 dias en comun: la ventana de 1 mes no llega al minimo.
    rng = np.random.default_rng(2)
    asset = prices(rng.normal(0, 0.01, 400))
    peer = prices(rng.normal(0, 0.01, 400))
    peer = peer.iloc[-11:]  # 10 retornos comunes

    stats = correlations.pair_stats(asset, peer)

    assert stats["1M"]["observations"] == 10
    assert stats["1M"]["correlation"] is None


def test_returns_are_computed_after_aligning_calendars(rng_returns):
    # El peer opera solo en dias laborables y el activo todos los dias (como BTC): los retornos
    # del activo en los huecos se acumulan en el siguiente dia comun, no se pierden ni se mezclan.
    asset = prices(rng_returns)
    weekdays = asset[asset.index.dayofweek < 5]
    peer = weekdays * 2  # misma serie de retornos que el activo en dias comunes

    stats = correlations.pair_stats(asset, peer)

    assert stats["1Y"]["correlation"] == pytest.approx(1.0)
    assert stats["1Y"]["observations"] < 300  # solo dias laborables, no 365


def test_cumulative_curves_start_near_zero_and_highlight_the_selected_asset(rng_returns):
    closes = {"AAA": prices(rng_returns), "BBB": prices(rng_returns[::-1].copy())}

    curves = correlations.cumulative_return_curves(closes, "BBB")

    assert [c["symbol"] for c in curves] == ["BBB", "AAA"]  # el seleccionado primero
    assert curves[0]["selected"] is True and curves[1]["selected"] is False
    last_year = closes["AAA"].iloc[-1] / closes["AAA"].iloc[-366] - 1
    assert curves[1]["values"][-1] == pytest.approx(last_year * 100, abs=0.01)
    assert abs(curves[1]["values"][0]) < 5  # arranca cerca de 0 %
    assert len(curves[1]["dates"]) == len(curves[1]["values"])


def test_series_without_history_in_the_last_year_is_omitted(rng_returns):
    old = prices(rng_returns[:100], start="2010-01-01")
    closes = {"NEW": prices(rng_returns), "OLD": old}

    curves = correlations.cumulative_return_curves(closes, "NEW")

    assert [c["symbol"] for c in curves] == ["NEW"]


def test_compute_leaves_the_selected_asset_out_of_the_table_but_keeps_its_curve(rng_returns):
    closes = {"AAA": prices(rng_returns), "BBB": prices(rng_returns * 0.5), "CCC": prices(-rng_returns)}
    peers = [("AAA", "Mag 7"), ("BBB", "Index"), ("CCC", "Crypto"), ("ZZZ", "Index")]  # ZZZ sin datos

    result = correlations.compute("AAA", closes, peers)

    assert result["windows"] == ["1M", "3M", "1Y", "3Y", "5Y"]
    assert [p["symbol"] for p in result["peers"]] == ["BBB", "CCC"]
    assert result["peers"][0]["group"] == "Index"
    assert result["peers"][0]["windows"]["1Y"]["correlation"] == pytest.approx(1.0)
    assert result["peers"][1]["windows"]["1Y"]["correlation"] == pytest.approx(-1.0)
    assert any(c["symbol"] == "AAA" and c["selected"] for c in result["curves"])


def test_up_and_down_betas_capture_an_asymmetric_relationship():
    # El activo reacciona el doble que la referencia cuando esta sube y la mitad cuando baja.
    peer_returns = np.random.default_rng(11).normal(0, 0.01, 1500)
    asset_returns = np.where(peer_returns > 0, 2.0 * peer_returns, 0.5 * peer_returns)

    stats = correlations.pair_stats(prices(asset_returns), prices(peer_returns))

    for window in ("3M", "1Y", "3Y"):  # 1.500 dias (~4 anos): 5Y no esta cubierta
        assert stats[window]["beta_up"] == pytest.approx(2.0)
        assert stats[window]["beta_down"] == pytest.approx(0.5)
        counts = stats[window]
        assert counts["observations_up"] + counts["observations_down"] <= counts["observations"]
        assert counts["observations_up"] > 0 and counts["observations_down"] > 0


def test_beta_is_none_when_one_side_has_too_few_days():
    # En la ultima ventana de 1 mes la referencia solo sube un dia (por debajo del minimo por lado).
    n = 400
    peer_returns = np.random.default_rng(5).normal(0, 0.01, n)
    peer_returns[-30:] = -np.abs(peer_returns[-30:])
    peer_returns[-1] = 0.01
    asset_returns = np.random.default_rng(6).normal(0, 0.01, n)

    stats = correlations.pair_stats(prices(asset_returns), prices(peer_returns))

    assert stats["1M"]["observations_up"] < correlations.MIN_SIDE_OBSERVATIONS
    assert stats["1M"]["beta_up"] is None
    assert stats["1M"]["beta_down"] is not None


def test_days_when_the_reference_does_not_move_are_in_neither_side():
    peer_returns = np.random.default_rng(3).normal(0, 0.01, 300)
    peer_returns[-25:-20] = 0.0  # cinco dias planos dentro de la ventana de 1 mes
    asset_returns = np.random.default_rng(4).normal(0, 0.01, 300)

    stats = correlations.pair_stats(prices(asset_returns), prices(peer_returns))["1M"]

    assert stats["observations_up"] + stats["observations_down"] == stats["observations"] - 5
