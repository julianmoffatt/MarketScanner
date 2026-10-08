import pandas as pd
import numpy as np
from backend.src.market_platform.backtesting.portfolio import Portfolio
from backend.src.market_platform.backtesting.simulated_broker import SimulatedBroker
from backend.src.market_platform.backtesting.backtest_config import BacktestConfig
from backend.src.market_platform.backtesting.backtest_result import BacktestResult
from backend.src.market_platform.backtesting.metrics import compute_metrics

def _validated_coefficient(strategy, asset, date, value):
    try:
        valid = bool(np.isfinite(value)) and 0 <= value <= 1
    except TypeError:
        valid = False
    if not valid:
        raise ValueError(
            f"{type(strategy).__name__}.compute returned {value!r} for {asset} on {date.date()}; "
            "expected a finite number between 0 and 1"
        )
    return float(value)

def backtesting(strategy, assets, data, config):
    portfolio = Portfolio(assets, config.initial_exposure, config.starting_capital)
    simulatedBroker = SimulatedBroker(config.fee, config.spread)

    #creates the stategys features
    data_assets = [strategy.prepare_features(df.copy()) for df in data]

    index = sorted(set().union(*[df.index for df in data_assets]))
    index = pd.DatetimeIndex(index)
    start = index[-1] - pd.DateOffset(years = config.window_years)
    index = index[index >= start]
    data_assets = [df.reindex(index) for df in data_assets]

    # buying initial shares before backtesting #############################
    initial_purchase_candle = [df.loc[index[0], "Close"] for df in data_assets]
    orders = portfolio.cash_initial_purchase()
    shares, cash = simulatedBroker.execute(orders, initial_purchase_candle)
    portfolio.update_shares_initial_purchase(shares)

    # BACKTESTING
    for t in index[1:]:
        coefficients = np.zeros(len(assets))
        prices = np.zeros(len(assets))
        for k, df in enumerate(data_assets):
            df_now = df.loc[[t]] 
            close = df_now["Close"].iloc[-1]
            prices[k] = False if np.isnan(close) else close
            coefficient = strategy.compute(df_now, portfolio.coefficients_exposure[k])
            coefficients[k] = _validated_coefficient(strategy, assets[k], t, coefficient)
        portfolio.setLastSharePrice(prices)
        orders = portfolio.balancing_portfolio(coefficients)
        shares, cash = simulatedBroker.execute(orders, prices)
        portfolio.update_shares_and_cash(np.array(shares), np.array(cash))
        portfolio.update_metrics()
    
    equity = pd.Series(portfolio.equity_value_history, index=index, name="equity")
    exposure = pd.DataFrame(portfolio.coefficients_exposure_history, index=index, columns=assets)
    metrics = compute_metrics(equity, exposure, config.periods_per_year, config.risk_free_rate)
    return BacktestResult(config=config, assets=tuple(assets), equity=equity, exposure=exposure, metrics=metrics)




