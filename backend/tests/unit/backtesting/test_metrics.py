import numpy as np
import pandas as pd
import pytest

from backend.src.market_platform.backtesting import metrics


def curve(values):
    return pd.Series(values, index=pd.bdate_range("2024-01-01", periods=len(values)), dtype=float)


def exposure(rows):
    return pd.DataFrame(rows, columns=["A", "B"][: len(rows[0])])


RETURNS = np.array([0.02, -0.01, 0.03, -0.02, 0.01])
RETURNS_CURVE = curve(np.r_[100, 100 * np.cumprod(1 + RETURNS)])
FLAT_GROWTH = curve(100 * 1.01 ** np.arange(10))


def test_total_return():
    assert metrics.total_return(curve([100, 120, 90, 110])) == pytest.approx(0.10)


def test_total_return_negative():
    assert metrics.total_return(curve([100, 80])) == pytest.approx(-0.20)


@pytest.mark.parametrize("values", [[], [100]])
def test_total_return_without_enough_points_is_none(values):
    assert metrics.total_return(curve(values)) is None


def test_cagr_one_period_per_year():
    assert metrics.cagr(curve([100, 110, 121]), periods_per_year=1) == pytest.approx(0.10)


def test_cagr_doubling_in_one_year():
    assert metrics.cagr(curve(np.linspace(100, 200, 253)), periods_per_year=252) == pytest.approx(1.0)


def test_cagr_depends_on_periods_per_year():
    values = curve([100, 110, 121])

    assert metrics.cagr(values, periods_per_year=1) != pytest.approx(metrics.cagr(values, periods_per_year=252))


@pytest.mark.parametrize("values", [[100], [100, 0], [0, 100]])
def test_cagr_not_computable_is_none(values):
    assert metrics.cagr(curve(values)) is None


def test_annualized_volatility():
    expected = RETURNS.std(ddof=1) * np.sqrt(252)

    assert metrics.annualized_volatility(RETURNS_CURVE) == pytest.approx(expected)


def test_annualized_volatility_uses_periods_per_year():
    expected = RETURNS.std(ddof=1) * np.sqrt(365)

    assert metrics.annualized_volatility(RETURNS_CURVE, periods_per_year=365) == pytest.approx(expected)


def test_annualized_volatility_needs_two_returns():
    assert metrics.annualized_volatility(curve([100, 101])) is None


def test_sharpe_ratio():
    expected = RETURNS.mean() / RETURNS.std(ddof=1) * np.sqrt(252)

    assert metrics.sharpe_ratio(RETURNS_CURVE) == pytest.approx(expected)


def test_sharpe_ratio_with_risk_free_rate():
    excess = RETURNS - 0.02 / 252
    expected = excess.mean() / excess.std(ddof=1) * np.sqrt(252)

    assert metrics.sharpe_ratio(RETURNS_CURVE, risk_free_rate=0.02) == pytest.approx(expected)


def test_sharpe_ratio_is_lower_with_higher_risk_free_rate():
    assert metrics.sharpe_ratio(RETURNS_CURVE, risk_free_rate=0.05) < metrics.sharpe_ratio(RETURNS_CURVE)


def test_sharpe_ratio_with_zero_volatility_is_none():
    assert metrics.sharpe_ratio(FLAT_GROWTH) is None


def test_sharpe_ratio_needs_two_returns():
    assert metrics.sharpe_ratio(curve([100, 101])) is None


def test_sortino_ratio():
    downside = np.sqrt(np.mean(np.minimum(RETURNS, 0) ** 2))
    expected = RETURNS.mean() / downside * np.sqrt(252)

    assert metrics.sortino_ratio(RETURNS_CURVE) == pytest.approx(expected)


def test_sortino_ratio_without_negative_returns_is_none():
    assert metrics.sortino_ratio(FLAT_GROWTH) is None


def test_sortino_ratio_is_higher_than_sharpe_when_losses_are_small():
    assert metrics.sortino_ratio(RETURNS_CURVE) > metrics.sharpe_ratio(RETURNS_CURVE)


def test_max_drawdown():
    assert metrics.max_drawdown(curve([100, 120, 90, 110])) == pytest.approx(-0.25)


def test_max_drawdown_takes_the_deepest_one():
    assert metrics.max_drawdown(curve([100, 90, 100, 120, 60, 130])) == pytest.approx(-0.50)


def test_max_drawdown_of_rising_curve_is_zero():
    assert metrics.max_drawdown(curve([1, 2, 3])) == 0


def test_max_drawdown_of_empty_curve_is_none():
    assert metrics.max_drawdown(curve([])) is None


def test_max_drawdown_duration():
    assert metrics.max_drawdown_duration(curve([100, 120, 90, 110])) == 2


def test_max_drawdown_duration_counts_the_longest_run():
    assert metrics.max_drawdown_duration(curve([100, 90, 80, 100, 95])) == 2


def test_max_drawdown_duration_counts_a_run_that_never_recovers():
    assert metrics.max_drawdown_duration(curve([100, 90, 80, 85, 82])) == 4


def test_max_drawdown_duration_of_rising_curve_is_zero():
    assert metrics.max_drawdown_duration(curve([1, 2, 3])) == 0


def test_max_drawdown_duration_of_empty_curve_is_none():
    assert metrics.max_drawdown_duration(curve([])) is None


def test_average_exposure():
    assert metrics.average_exposure(exposure([[0.5, 0.5], [1, 1], [1, 0.5]])) == pytest.approx(0.75)


def test_average_exposure_single_asset():
    assert metrics.average_exposure(exposure([[0.2], [0.4]])) == pytest.approx(0.3)


def test_average_exposure_of_empty_frame_is_none():
    assert metrics.average_exposure(pd.DataFrame()) is None


def test_exposure_changes_counts_days_with_any_change():
    assert metrics.exposure_changes(exposure([[0.5, 0.5], [1, 1], [1, 0.5]])) == 2


def test_exposure_changes_with_constant_exposure_is_zero():
    assert metrics.exposure_changes(exposure([[0.5], [0.5], [0.5]])) == 0


def test_exposure_changes_counts_a_day_once_even_if_two_assets_change():
    assert metrics.exposure_changes(exposure([[0.5, 0.5], [1, 1]])) == 1


def test_compute_metrics_returns_all_keys():
    result = metrics.compute_metrics(RETURNS_CURVE, exposure([[0.5]] * len(RETURNS_CURVE)))

    assert set(result) == {
        "total_return",
        "cagr",
        "volatility",
        "sharpe",
        "sortino",
        "max_drawdown",
        "max_drawdown_duration",
        "average_exposure",
        "exposure_changes",
    }


def test_compute_metrics_matches_individual_functions():
    expo = exposure([[0.5]] * len(RETURNS_CURVE))

    result = metrics.compute_metrics(RETURNS_CURVE, expo, periods_per_year=365, risk_free_rate=0.02)

    assert result["total_return"] == pytest.approx(metrics.total_return(RETURNS_CURVE))
    assert result["cagr"] == pytest.approx(metrics.cagr(RETURNS_CURVE, 365))
    assert result["sharpe"] == pytest.approx(metrics.sharpe_ratio(RETURNS_CURVE, 365, 0.02))
    assert result["max_drawdown"] == pytest.approx(metrics.max_drawdown(RETURNS_CURVE))
    assert result["average_exposure"] == pytest.approx(0.5)


def test_compute_metrics_values_are_plain_numbers_or_none():
    result = metrics.compute_metrics(RETURNS_CURVE, exposure([[0.5, 1.0]] * len(RETURNS_CURVE)))

    for value in result.values():
        assert value is None or type(value) in (float, int)


def test_compute_metrics_on_too_short_curve_gives_none_not_errors():
    result = metrics.compute_metrics(curve([100]), exposure([[0.5]]))

    assert result["total_return"] is None
    assert result["sharpe"] is None
    assert result["cagr"] is None
