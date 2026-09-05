import pandas as pd
from analytics.retest_bands import calculation_retest_bands

def calculation_retest_bands_screener(df):
    result = calculation_retest_bands([df])[0].copy()
    result["EMA10_now"] = 0.0
    result["EMA10_tmw"] = 0.0
    if not result.empty:
        ema10_now = df["ema10"].iloc[-1]
        ema10_tomorrow = ema10_now / (df["ema10"].iloc[-2] / ema10_now)
        result.iloc[-1, result.columns.get_loc("EMA10_now")] = ema10_now
        result.iloc[-1, result.columns.get_loc("EMA10_tmw")] = ema10_tomorrow
    return result
