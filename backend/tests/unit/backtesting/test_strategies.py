import pandas as pd
import pytest

from backend.src.market_platform.backtesting.strategies import registry
from backend.src.market_platform.backtesting.strategies.buy_and_hold import BuyAndHold
from backend.src.market_platform.backtesting.strategies.mean_reversion import MeanReversion
from backend.src.market_platform.backtesting.strategies.strategy import Strategy


def row(percentile):
    return pd.DataFrame({"percentile_extension_ema20": [percentile]})


def test_registered_strategies_are_available():
    assert {"buy_and_hold", "mean_reversion_distance"} <= set(registry.available_strategys())


def test_available_strategies_are_sorted():
    names = registry.available_strategys()

    assert names == sorted(names)


@pytest.mark.parametrize("name, cls", [("buy_and_hold", BuyAndHold), ("mean_reversion_distance", MeanReversion)])
def test_get_strategy_returns_an_instance_of_the_registered_class(name, cls):
    assert type(registry.get_strategy(name)) is cls


def test_get_strategy_returns_a_new_instance_each_time():
    assert registry.get_strategy("buy_and_hold") is not registry.get_strategy("buy_and_hold")


def test_unknown_strategy_raises_and_lists_the_available_ones():
    with pytest.raises(ValueError, match="no registrada.*buy_and_hold"):
        registry.get_strategy("does_not_exist")


def test_registering_a_different_class_under_a_taken_name_raises():
    with pytest.raises(ValueError, match="Ya existe"):
        registry.register_model("buy_and_hold")(type("Other", (), {}))


def test_registering_the_same_class_twice_is_allowed():
    assert registry.register_model("buy_and_hold")(BuyAndHold) is BuyAndHold


@pytest.fixture
def clean_registry(monkeypatch):
    monkeypatch.setattr(registry, "_REGISTRY", dict(registry._REGISTRY))


def test_register_model_adds_the_class_under_its_name(clean_registry):
    @registry.register_model("temporary")
    class Temporary(Strategy):
        def compute(self, df, coef):
            return coef

    assert isinstance(registry.get_strategy("temporary"), Temporary)


def test_strategy_cannot_be_instantiated_without_compute():
    class Incomplete(Strategy):
        pass

    with pytest.raises(TypeError):
        Incomplete()


def test_prepare_features_defaults_to_returning_the_same_frame():
    df = row(10)

    assert BuyAndHold().prepare_features(df) is df


@pytest.mark.parametrize("coef", [0.0, 0.3, 1.0])
def test_buy_and_hold_always_returns_one(coef):
    assert BuyAndHold().compute(row(50), coef) == 1.0


@pytest.mark.parametrize("percentile, coef, expected", [
    (99, 1, 0),
    (100, 1, 0),
    (99.5, 0.5, 0),
    (50, 0, 1),
    (10, 0, 1),
    (0.5, 0.5, 1),
])
def test_mean_reversion_switches_at_the_extremes(percentile, coef, expected):
    assert MeanReversion().compute(row(percentile), coef) == expected


@pytest.mark.parametrize("percentile, coef", [(98.9, 1), (98.9, 0), (50.1, 1), (50.1, 0), (75, 0.4)])
def test_mean_reversion_keeps_the_current_coefficient_between_thresholds(percentile, coef):
    assert MeanReversion().compute(row(percentile), coef) == coef


def test_mean_reversion_uses_only_the_last_row():
    df = pd.DataFrame({"percentile_extension_ema20": [100, 100, 10]})

    assert MeanReversion().compute(df, 0) == 1


def test_mean_reversion_prepare_features_adds_the_percentile_column():
    idx = pd.bdate_range("2022-01-03", periods=300)
    df = pd.DataFrame({"extension_ema20": range(300)}, index=idx)

    out = MeanReversion().prepare_features(df)

    assert "percentile_extension_ema20" in out.columns
    assert out["percentile_extension_ema20"].iloc[:251].isna().all()
    assert out["percentile_extension_ema20"].iloc[251:].notna().all()
