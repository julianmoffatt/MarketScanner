import numpy as np
import pytest

from backend.src.market_platform.backtesting.portfolio import Portfolio


@pytest.fixture
def portfolio():
    p = Portfolio(assets=["A", "B"], initial_exposure=0.5, starting_capital=1000)
    p.update_shares_initial_purchase(np.array([2.5, 2.5]))
    p.setLastSharePrice(np.array([100.0, 100.0]))
    return p


def test_cash_initial_purchase():
    portfolio = Portfolio(assets=["sp500", "gold"], starting_capital=1000, initial_exposure=0.5)
    assert portfolio.cash_initial_purchase() == [250, 250]


@pytest.mark.parametrize(
    "exposure, n_assets, expected_purchase",
    [
        (0.25, 1, [250]),
        (1.0, 2, [500, 500]),
        (0.0, 2, [0, 0]),
        (0.4, 3, [400 / 3] * 3),
    ],
)
def test_cash_initial_purchase_splits_the_invested_part_between_assets(exposure, n_assets, expected_purchase):
    p = Portfolio(assets=list("ABC")[:n_assets], initial_exposure=exposure, starting_capital=1000)

    assert p.cash_initial_purchase() == pytest.approx(expected_purchase)


@pytest.mark.parametrize("exposure, n_assets", [(0.25, 1), (0.5, 2), (0.4, 3), (0.0, 2), (1.0, 2)])
def test_cash_and_initial_purchase_add_up_to_the_capital(exposure, n_assets):
    p = Portfolio(assets=list("ABC")[:n_assets], initial_exposure=exposure, starting_capital=1000)

    assert sum(p.cash) + sum(p.cash_initial_purchase()) == pytest.approx(1000)


@pytest.mark.parametrize(
    "exposure, n_assets, expected_cash",
    [
        (0.5, 2, [250, 250]),
        (0.25, 1, [750]),
        (1.0, 2, [0, 0]),
        (0.0, 2, [500, 500]),
        (0.4, 3, [200, 200, 200]),
    ],
)
def test_init_splits_the_uninvested_cash_between_assets(exposure, n_assets, expected_cash):
    p = Portfolio(assets=list("ABC")[:n_assets], initial_exposure=exposure, starting_capital=1000)

    assert p.cash == pytest.approx(expected_cash)


def test_init_starts_without_shares_or_prices():
    p = Portfolio(assets=["A", "B"], initial_exposure=0.5, starting_capital=1000)

    assert list(p.shares) == [0, 0]
    assert list(p.last_share_price) == [0, 0]


def test_init_histories_start_with_the_initial_state():
    p = Portfolio(assets=["A", "B"], initial_exposure=0.25, starting_capital=1000)

    assert p.equity_value_history == [1000]
    assert len(p.coefficients_exposure_history) == 1
    assert list(p.coefficients_exposure_history[0]) == [0.25, 0.25]


def test_two_portfolios_do_not_share_state():
    a = Portfolio(assets=["A"], initial_exposure=0.5, starting_capital=1000)
    b = Portfolio(assets=["A"], initial_exposure=0.5, starting_capital=1000)

    a.update_metrics()

    assert len(a.equity_value_history) == 2
    assert len(b.equity_value_history) == 1
    assert len(b.coefficients_exposure_history) == 1


def test_set_last_share_price_stores_the_prices(portfolio):
    portfolio.setLastSharePrice(np.array([120.0, 80.0]))

    assert list(portfolio.last_share_price) == [120, 80]


def test_zero_price_keeps_the_previous_price(portfolio):
    portfolio.setLastSharePrice(np.array([0.0, 80.0]))

    assert list(portfolio.last_share_price) == [100, 80]


@pytest.mark.parametrize(
    "new_coefficient, expected_order",
    [
        (0.25, -1.25),
        (0.0, -2.5),
        (0.75, 125),
        (1.0, 250),
        (0.5, 0),
    ],
)
def test_balancing_orders_for_each_coefficient_change(portfolio, new_coefficient, expected_order):
    orders = portfolio.balancing_portfolio(np.array([new_coefficient, new_coefficient]))

    assert orders == pytest.approx([expected_order, expected_order])


def test_balancing_gives_each_asset_its_own_order(portfolio):
    orders = portfolio.balancing_portfolio(np.array([0.25, 1.0]))

    assert orders == pytest.approx([-1.25, 250])


def test_balancing_from_zero_exposure_buys_the_requested_share_of_cash():
    p = Portfolio(assets=["A", "B"], initial_exposure=0.0, starting_capital=1000)
    p.setLastSharePrice(np.array([100.0, 100.0]))

    orders = p.balancing_portfolio(np.array([0.4, 0.4]))

    assert orders == pytest.approx([200, 200])


def test_price_moves_alone_do_not_generate_orders(portfolio):
    portfolio.setLastSharePrice(np.array([150.0, 50.0]))

    orders = portfolio.balancing_portfolio(np.array([0.5, 0.5]))

    assert orders == [0, 0]


def test_balancing_remembers_the_latest_coefficients(portfolio):
    portfolio.balancing_portfolio(np.array([0.25, 0.75]))

    assert list(portfolio.coefficients_exposure) == [0.25, 0.75]
    assert portfolio.balancing_portfolio(np.array([0.25, 0.75])) == [0, 0]


def test_balancing_accepts_a_plain_list(portfolio):
    assert portfolio.balancing_portfolio([0.25, 0.25]) == pytest.approx([-1.25, -1.25])


def test_buy_fill_adds_shares_and_removes_cash(portfolio):
    portfolio.update_shares_and_cash(np.array([1.0, 0.0]), np.array([-100.0, 0.0]))

    assert list(portfolio.shares) == [3.5, 2.5]
    assert list(portfolio.cash) == [150, 250]


def test_sale_fill_removes_shares_and_adds_cash(portfolio):
    portfolio.update_shares_and_cash(np.array([-1.25, 0.0]), np.array([125.0, 0.0]))

    assert list(portfolio.shares) == [1.25, 2.5]
    assert list(portfolio.cash) == [375, 250]


def test_update_metrics_values_the_portfolio_at_last_prices(portfolio):
    portfolio.setLastSharePrice(np.array([120.0, 100.0]))

    portfolio.update_metrics()

    assert portfolio.equity_value_history[-1] == pytest.approx(1050)


def test_update_metrics_adds_one_entry_per_call(portfolio):
    for _ in range(3):
        portfolio.update_metrics()

    assert len(portfolio.equity_value_history) == 4
    assert len(portfolio.coefficients_exposure_history) == 4


def test_exposure_history_keeps_each_days_coefficients(portfolio):
    portfolio.update_metrics()
    portfolio.balancing_portfolio(np.array([0.25, 0.75]))
    portfolio.update_metrics()

    history = [list(row) for row in portfolio.coefficients_exposure_history]
    assert history == [[0.5, 0.5], [0.5, 0.5], [0.25, 0.75]]


def test_rebalancing_without_costs_keeps_the_portfolio_value(portfolio):
    portfolio.update_metrics()

    orders = portfolio.balancing_portfolio(np.array([0.25, 1.0]))
    portfolio.update_shares_and_cash(np.array([orders[0], 250 / 100]), np.array([-orders[0] * 100, -250.0]))
    portfolio.update_metrics()

    assert portfolio.equity_value_history[-1] == pytest.approx(portfolio.equity_value_history[0])
