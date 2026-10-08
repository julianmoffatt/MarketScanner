import numpy as np
import pandas as pd


def _returns(equity: pd.Series) -> pd.Series:
    return equity.pct_change().dropna()


def _finite_or_none(value):
    if value is None or not np.isfinite(value):
        return None
    return float(value)


def total_return(equity: pd.Series):
    if len(equity) < 2 or equity.iloc[0] <= 0:
        return None
    return _finite_or_none(equity.iloc[-1] / equity.iloc[0] - 1)


def cagr(equity: pd.Series, periods_per_year: int = 252):
    if len(equity) < 2 or equity.iloc[0] <= 0 or equity.iloc[-1] <= 0:
        return None
    years = (len(equity) - 1) / periods_per_year
    return _finite_or_none((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)


def annualized_volatility(equity: pd.Series, periods_per_year: int = 252):
    returns = _returns(equity)
    if len(returns) < 2:
        return None
    return _finite_or_none(returns.std(ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(equity: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0):
    excess = _returns(equity) - risk_free_rate / periods_per_year
    if len(excess) < 2:
        return None
    std = excess.std(ddof=1)
    if not np.isfinite(std) or std < 1e-12:
        return None
    return _finite_or_none(excess.mean() / std * np.sqrt(periods_per_year))


def sortino_ratio(equity: pd.Series, periods_per_year: int = 252, risk_free_rate: float = 0.0):
    excess = _returns(equity) - risk_free_rate / periods_per_year
    if len(excess) < 2:
        return None
    downside = np.sqrt(np.mean(np.minimum(excess, 0) ** 2))
    if not np.isfinite(downside) or downside < 1e-12:
        return None
    return _finite_or_none(excess.mean() / downside * np.sqrt(periods_per_year))


def max_drawdown(equity: pd.Series):
    if equity.empty:
        return None
    drawdown = equity / equity.cummax() - 1
    return _finite_or_none(drawdown.min())


def max_drawdown_duration(equity: pd.Series):
    if equity.empty:
        return None
    underwater = equity < equity.cummax()
    groups = (underwater != underwater.shift()).cumsum()
    return int(underwater.groupby(groups).sum().max())


def average_exposure(exposure: pd.DataFrame):
    if exposure.empty:
        return None
    return _finite_or_none(exposure.mean(axis=1).mean())


def exposure_changes(exposure: pd.DataFrame) -> int:
    return int((exposure.diff().abs() > 1e-9).any(axis=1).sum())


def compute_metrics(
    equity: pd.Series,
    exposure: pd.DataFrame,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> dict:
    return {
        "total_return": total_return(equity),
        "cagr": cagr(equity, periods_per_year),
        "volatility": annualized_volatility(equity, periods_per_year),
        "sharpe": sharpe_ratio(equity, periods_per_year, risk_free_rate),
        "sortino": sortino_ratio(equity, periods_per_year, risk_free_rate),
        "max_drawdown": max_drawdown(equity),
        "max_drawdown_duration": max_drawdown_duration(equity),
        "average_exposure": average_exposure(exposure),
        "exposure_changes": exposure_changes(exposure),
    }
