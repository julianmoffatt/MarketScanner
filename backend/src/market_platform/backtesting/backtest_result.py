from dataclasses import dataclass

import pandas as pd

from backend.src.market_platform.backtesting.backtest_config import BacktestConfig


@dataclass(frozen=True, eq=False)
class BacktestResult:
    config: BacktestConfig
    assets: tuple
    equity: pd.Series          # portfolio value per date, named "equity"
    exposure: pd.DataFrame     # exposure coefficient per date (rows) and asset (columns)
    metrics: dict              # output of metrics.compute_metrics for this run
