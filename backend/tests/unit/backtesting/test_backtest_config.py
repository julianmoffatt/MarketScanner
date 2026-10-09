import dataclasses
import pytest
from backend.src.market_platform.backtesting.backtest_config import BacktestConfig


def test_defaults():
    config = BacktestConfig()

    assert config.starting_capital == 5000.0
    assert config.initial_exposure == 0.5
    assert config.window_years == 5
    assert config.fee == 0.25
    assert config.spread == 0.001
    assert config.periods_per_year == 252
    assert config.risk_free_rate == 0.0


@pytest.mark.parametrize(
    "field, value",
    [
        ("starting_capital", 0),
        ("starting_capital", -1),
        ("initial_exposure", -0.1),
        ("initial_exposure", 1.1),
        ("window_years", 0),
        ("window_years", -3),
        ("fee", -0.01),
        ("spread", -0.001),
        ("periods_per_year", 0),
    ],
)
def test_invalid_value_raises_value_error_naming_the_field(field, value):
    with pytest.raises(ValueError, match=field):
        BacktestConfig(**{field: value})


@pytest.mark.parametrize(
    "field, value",
    [
        ("initial_exposure", 0),
        ("initial_exposure", 1),
        ("fee", 0),
        ("spread", 0),
        ("risk_free_rate", 0.03),
        ("risk_free_rate", -0.01),
    ],
)
def test_boundary_values_are_valid(field, value):
    config = BacktestConfig(**{field: value})

    assert getattr(config, field) == value


def test_config_is_immutable():
    config = BacktestConfig()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.fee = 1.0


def test_replace_changes_only_the_given_field():
    config = BacktestConfig(starting_capital=1000, fee=0.5)

    replaced = dataclasses.replace(config, initial_exposure=1.0)

    assert replaced.initial_exposure == 1.0
    assert replaced.starting_capital == 1000
    assert replaced.fee == 0.5
    assert config.initial_exposure == 0.5


def test_replace_validates_the_new_value():
    with pytest.raises(ValueError, match="initial_exposure"):
        dataclasses.replace(BacktestConfig(), initial_exposure=2.0)


def test_configs_with_same_values_are_equal():
    assert BacktestConfig(fee=0.1) == BacktestConfig(fee=0.1)
    assert BacktestConfig(fee=0.1) != BacktestConfig(fee=0.2)
