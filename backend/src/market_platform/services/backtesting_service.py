from dataclasses import replace

from ..backtesting import backtesting
from ..backtesting.backtest_config import BacktestConfig
from ..backtesting.backtest_result import BacktestResult
from ..backtesting.strategies.registry import get_strategy
from .. import pipeline

BENCHMARK_STRATEGY = "buy_and_hold"

def _curve(equity) -> list:
    return [
        {"date": date.strftime("%Y-%m-%d"), "value": float(value)}
        for date, value in equity.items()
    ]

def _to_response(result: BacktestResult, benchmark: BacktestResult, strategy_name: str) -> dict:
    return {
        "tickers": list(result.assets),
        "strategy": strategy_name,
        "equity": _curve(result.equity),
        "exposure": [
            {"date": date.strftime("%Y-%m-%d"), "values": {asset: float(x) for asset, x in row.items()}}
            for date, row in result.exposure.iterrows()
        ],
        "average_exposure": {asset: float(x) for asset, x in result.exposure.mean().items()},
        "metrics": result.metrics,
        "benchmark_equity": _curve(benchmark.equity),
        "benchmark_metrics": benchmark.metrics,
    }

def run_backtesting(tickers: list, strategy_name: str, config: BacktestConfig) -> dict:
    data = []
    for ticker in tickers:
        df = pipeline.processedTimeframes(ticker, 0)[0] #daily
        data.append(df)
    strategy = get_strategy(strategy_name)
    result = backtesting.backtesting(strategy, tickers, data, config)
    benchmark = backtesting.backtesting(
        get_strategy(BENCHMARK_STRATEGY), tickers, data, replace(config, initial_exposure=1.0)
    )
    return _to_response(result, benchmark, strategy_name)
