import pandas as pd

def _clean(value, decimals=1):
    return None if pd.isna(value) else round(float(value), decimals)

def _trailing_return(close, years):
    past_price = close.asof(close.index[-1] - pd.DateOffset(years=years))
    return _clean((close.iloc[-1] / past_price - 1) * 100)

def compute(timeframes):
    daily_close = timeframes[0]["Close"]

    return {
        "current_price": float(daily_close.iloc[-1]),
        "previous_close": float(daily_close.iloc[-2]),
        "current_week_return": _clean(timeframes[1]["return"].iloc[-1]),
        "current_month_return": _clean(timeframes[2]["return"].iloc[-1]),
        "current_quarter_return": _clean(timeframes[3]["return"].iloc[-1]),
        "current_year_return": _clean(timeframes[4]["return"].iloc[-1]),
        "trailing_1y_return": _trailing_return(daily_close, 1),
        "trailing_3y_return": _trailing_return(daily_close, 3),
        "trailing_5y_return": _trailing_return(daily_close, 5),
    }
