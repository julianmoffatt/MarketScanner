import pandas as pd
from ...features.stats import create_mean_reversion_statistics

def _last(df, column):
    value = df[column].iloc[-1]
    if isinstance(value, str):
        return value
    return None if pd.isna(value) else float(value)

def compute(ticker, timeframes):
    daily, weekly, monthly = [create_mean_reversion_statistics(df.copy()) for df in timeframes] # copy to avoid problems with the cached version
    row = {"ticker": ticker}
    # STRIKES
    for name, df in (("daily", daily), ("weekly", weekly), ("monthly", monthly)):
        row[f"{name}_type"] = _last(df, "type")
        row[f"{name}_strike"] = _last(df, "strike")
        row[f"{name}_strike_percentile"] = _last(df, "percentile_strike")
    # TIME AWAY MEAN
    for ema in ("ema10", "ema20", "ema50"):
        row[f"daily_time_away_{ema}"] = _last(daily, f"time_away_{ema}")
        row[f"daily_time_away_{ema}_percentile"] = _last(daily, f"percentile_time_away_{ema}")
    row["weekly_time_away_ema10"] = _last(weekly, "time_away_ema10")
    row["weekly_time_away_ema10_percentile"] = _last(weekly, "percentile_time_away_ema10")
    # EXTENSION TO MEAN
    for name, df in (("daily", daily), ("weekly", weekly)):
        for ema in ("ema10", "ema20"):
            row[f"{name}_extension_{ema}_percentile"] = _last(df, f"percentile_extension_{ema}")
    # DURATION TREND
    for ema in ("ema10", "ema20"):
        row[f"trend_{ema}_side"] = _last(daily, f"trend_side_{ema}")
        row[f"trend_{ema}_duration"] = _last(daily, f"duration_trend_{ema}")
        row[f"trend_{ema}_percentile"] = _last(daily, f"percentile_duration_trend_{ema}")
    return row
