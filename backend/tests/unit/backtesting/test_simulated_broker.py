import pytest

from backend.src.market_platform.backtesting.simulated_broker import SimulatedBroker


@pytest.fixture
def broker():
    return SimulatedBroker(fee=0.5, spread=0.001)


def test_buy_gives_shares_and_spends_cash(broker):
    shares, cash = broker.execute([1000], [100.0])

    assert shares[0] == pytest.approx(9.985015)
    assert cash[0] == -1000


def test_sale_removes_shares_and_gives_cash(broker):
    shares, cash = broker.execute([-10], [100.0])

    assert shares[0] == -10
    assert cash[0] == pytest.approx(998.5)


def test_zero_order_does_nothing(broker):
    shares, cash = broker.execute([0], [100.0])

    assert shares == [0]
    assert cash == [0]


def test_nan_order_does_nothing(broker):
    shares, cash = broker.execute([float("nan")], [100.0])

    assert shares == [0]
    assert cash == [0]


@pytest.mark.parametrize("order", [1000, -10])
@pytest.mark.parametrize("price", [float("nan"), 0, -5])
def test_invalid_price_does_nothing(broker, order, price):
    shares, cash = broker.execute([order], [price])

    assert shares == [0]
    assert cash == [0]


def test_zero_costs_buy_is_exact():
    shares, cash = SimulatedBroker(fee=0, spread=0).execute([1000], [100.0])

    assert shares[0] == pytest.approx(10)
    assert cash[0] == -1000


def test_zero_costs_sale_returns_the_full_value():
    shares, cash = SimulatedBroker(fee=0, spread=0).execute([-10], [100.0])

    assert shares[0] == -10
    assert cash[0] == pytest.approx(1000)


def test_spread_makes_buys_dearer_and_sales_cheaper():
    spread_broker = SimulatedBroker(fee=0, spread=0.01)

    bought_shares, _ = spread_broker.execute([1000], [100.0])
    _, sale_cash = spread_broker.execute([-10], [100.0])

    assert bought_shares[0] == pytest.approx(1000 / 101)
    assert sale_cash[0] == pytest.approx(990)


def test_each_asset_is_handled_independently(broker):
    shares, cash = broker.execute([1000, -10], [100.0, 50.0])

    assert shares == [pytest.approx(9.985015), -10]
    assert cash == [-1000, pytest.approx(499.0)]


@pytest.mark.parametrize("order", [0.3, 0.5])
def test_buy_that_does_not_cover_the_fee_does_nothing(broker, order):
    shares, cash = broker.execute([order], [100.0])

    assert shares == [0]
    assert cash == [0]


def test_sale_worth_less_than_the_fee_does_nothing(broker):
    shares, cash = broker.execute([-0.001], [100.0])

    assert shares == [0]
    assert cash == [0]


def test_round_trip_loses_money_to_fee_and_spread(broker):
    bought_shares, bought_cash = broker.execute([1000], [100.0])
    sold_shares, sold_cash = broker.execute([-bought_shares[0]], [100.0])

    assert bought_shares[0] + sold_shares[0] == pytest.approx(0)
    assert bought_cash[0] + sold_cash[0] == pytest.approx(-2.997, abs=1e-3)


def test_result_has_one_entry_per_order(broker):
    shares, cash = broker.execute([1000, 0, -10], [100.0, 50.0, 20.0])

    assert len(shares) == len(cash) == 3
