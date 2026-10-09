import numpy as np
import pandas as pd
import pytest

from backend.src.market_platform.backtesting.backtest_config import BacktestConfig
from backend.src.market_platform.backtesting.backtest_result import BacktestResult
from backend.src.market_platform.backtesting.backtesting import backtesting
from backend.src.market_platform.backtesting.strategies.strategy import Strategy

pytestmark = pytest.mark.integration

DATES = pd.bdate_range("2023-01-02", periods=300)
ZERO_COSTS = BacktestConfig(starting_capital=5000, window_years=1, fee=0, spread=0)


def prices_frame(seed):
    returns = np.random.default_rng(seed).normal(0.0004, 0.01, len(DATES))
    return pd.DataFrame({"Close": 100 * np.exp(np.cumsum(returns))}, index=DATES)


class Constant(Strategy):
    def __init__(self, value):
        self.value = value

    def compute(self, df, coef):
        return self.value


class Recorder(Strategy):
    def __init__(self):
        self.calls = []
        self.prepared_lengths = []

    def prepare_features(self, df):
        self.prepared_lengths.append(len(df))
        return df

    def compute(self, df, coef):
        self.calls.append((df, coef))
        return 1.0


class AddsColumn(Strategy):
    def prepare_features(self, df):
        df["extra"] = 1
        return df

    def compute(self, df, coef):
        return 1.0


class Step(Strategy):
    def compute(self, df, coef):
        return 1.0 if df.index[-1] < pd.Timestamp("2023-09-01") else 0.25


@pytest.fixture
def data():
    return [prices_frame(1), prices_frame(2)]


def test_always_invested_without_costs_matches_the_closed_form(data):
    result = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert result.equity.iloc[-1] == pytest.approx(4391.9475, abs=1e-3)


def test_half_invested_without_costs_matches_the_closed_form(data):
    result = backtesting(Constant(0.5), ["A", "B"], data, ZERO_COSTS)

    assert result.equity.iloc[-1] == pytest.approx(4694.4848, abs=1e-3)


def test_final_value_scales_with_the_starting_capital(data):
    config = BacktestConfig(starting_capital=1000, window_years=1, fee=0, spread=0)

    result = backtesting(Constant(1.0), ["A", "B"], data, config)

    assert result.equity.iloc[-1] == pytest.approx(878.3895, abs=1e-3)


def test_fully_invested_without_costs_equals_buy_and_hold(data):
    config = BacktestConfig(starting_capital=5000, initial_exposure=1.0, window_years=1, fee=0, spread=0)

    result = backtesting(Constant(1.0), ["A", "B"], data, config)

    first, last = result.equity.index[0], result.equity.index[-1]
    expected = sum(2500 * df.Close.loc[last] / df.Close.loc[first] for df in data)
    assert result.equity.iloc[-1] == pytest.approx(expected)


def test_default_costs_reduce_the_final_value(data):
    with_costs = backtesting(Constant(1.0), ["A", "B"], data, BacktestConfig(starting_capital=5000, window_years=1))
    without_costs = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert with_costs.equity.iloc[-1] == pytest.approx(4386.6824, abs=1e-3)
    assert with_costs.equity.iloc[-1] < without_costs.equity.iloc[-1]


def test_result_carries_the_inputs(data):
    result = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert isinstance(result, BacktestResult)
    assert result.assets == ("A", "B")
    assert result.config is ZERO_COSTS


def test_equity_curve_covers_the_window(data):
    result = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert result.equity.name == "equity"
    assert len(result.equity) == 262
    assert result.equity.iloc[0] == 5000
    assert result.equity.index[0] == pd.Timestamp("2023-02-23")
    assert result.equity.index[-1] == pd.Timestamp("2024-02-23")
    assert result.equity.index.is_monotonic_increasing


def test_window_longer_than_the_data_uses_all_dates(data):
    config = BacktestConfig(starting_capital=5000, window_years=2, fee=0, spread=0)

    result = backtesting(Constant(1.0), ["A", "B"], data, config)

    assert len(result.equity) == 300
    assert result.equity.index[0] == DATES[0]


def test_exposure_starts_at_the_initial_exposure_then_follows_the_strategy(data):
    result = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert result.exposure.shape == (262, 2)
    assert list(result.exposure.columns) == ["A", "B"]
    assert list(result.exposure.iloc[0]) == [0.5, 0.5]
    assert (result.exposure.iloc[1:] == 1.0).all().all()
    assert result.exposure.index.equals(result.equity.index)


def test_constant_half_exposure_never_changes(data):
    result = backtesting(Constant(0.5), ["A", "B"], data, ZERO_COSTS)

    assert (result.exposure == 0.5).all().all()
    assert result.metrics["exposure_changes"] == 0


def test_metrics_are_computed_from_the_curve(data):
    result = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert result.metrics["total_return"] == pytest.approx(result.equity.iloc[-1] / result.equity.iloc[0] - 1)
    assert result.metrics["average_exposure"] == pytest.approx(result.exposure.mean(axis=1).mean())
    assert result.metrics["exposure_changes"] == 1


def test_changing_exposure_without_price_moves_conserves_the_value():
    flat = pd.DataFrame({"Close": 100.0}, index=DATES)

    result = backtesting(Step(), ["A"], [flat], ZERO_COSTS)

    assert sorted(result.exposure["A"].unique()) == [0.25, 0.5, 1.0]
    assert result.equity.to_numpy() == pytest.approx(5000)


def test_changing_exposure_costs_money_when_there_are_fees():
    flat = pd.DataFrame({"Close": 100.0}, index=DATES)

    result = backtesting(Step(), ["A"], [flat], BacktestConfig(starting_capital=5000, window_years=1))

    assert result.equity.iloc[-1] < 5000


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -0.1, 1.3, None, "0.5"])
def test_invalid_coefficient_from_the_strategy_raises(data, bad_value):
    with pytest.raises(ValueError, match=r"Constant.compute returned .* for A on 2023-02-24"):
        backtesting(Constant(bad_value), ["A", "B"], data, ZERO_COSTS)


@pytest.mark.parametrize("edge_value", [0, 1, 0.0, 1.0])
def test_coefficient_limits_are_accepted(data, edge_value):
    result = backtesting(Constant(edge_value), ["A", "B"], data, ZERO_COSTS)

    assert len(result.equity) == 262


def test_input_data_is_not_modified(data):
    before = [df.copy() for df in data]

    backtesting(AddsColumn(), ["A", "B"], data, ZERO_COSTS)

    for original, current in zip(before, data):
        pd.testing.assert_frame_equal(original, current)


def test_prepare_features_sees_the_full_history_once_per_asset(data):
    strategy = Recorder()

    backtesting(strategy, ["A", "B"], data, ZERO_COSTS)

    assert strategy.prepared_lengths == [300, 300]


def test_compute_receives_one_row_and_the_current_coefficient(data):
    strategy = Recorder()

    backtesting(strategy, ["A", "B"], data, ZERO_COSTS)

    first_df, first_coef = strategy.calls[0]
    second_df, second_coef = strategy.calls[2]
    assert len(first_df) == 1
    assert first_df.index[0] == pd.Timestamp("2023-02-24")
    assert first_coef == 0.5
    assert second_df.index[0] == pd.Timestamp("2023-02-27")
    assert second_coef == 1.0
    assert len(strategy.calls) == 2 * 261


def test_asset_with_a_missing_price_does_not_break_the_run(data):
    data[1].loc[pd.Timestamp("2023-06-15"), "Close"] = np.nan

    result = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert len(result.equity) == 262
    assert result.equity.notna().all()


def test_two_runs_give_the_same_result(data):
    first = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)
    second = backtesting(Constant(1.0), ["A", "B"], data, ZERO_COSTS)

    assert first.equity.equals(second.equity)
    assert len(second.equity) == 262
