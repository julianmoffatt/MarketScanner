import pandas as pd
from backend.src.market_platform.data.data_validation import clean_ohlcv

def last_X_years(df, num_years):
    df.index = pd.to_datetime(df.index)
    last_date = df.index.max()
    cutoff_date = last_date - pd.DateOffset(years=num_years)
    return df.loc[df.index >= cutoff_date].copy()


def preprocessing(df_base, t, symbol=None):
    if isinstance(df_base.columns, pd.MultiIndex):
        df_base.columns = df_base.columns.get_level_values(0)
        df_base.index = pd.to_datetime(df_base.index, utc=True)

    if t == 0:
        df_base.index = df_base.index.normalize()
        df_base = df_base.sort_index()
    else:
        if df_base.index.tz is None:
            df_base.index = df_base.index.tz_localize('UTC')
        else:
            df_base.index = df_base.index.tz_convert('UTC')
    timeframe_preprocessing = {0: lambda: preprocessing_highertimeframe(df_base, symbol), 1: lambda: preprocessing_lowertimeframe(df_base), 2: lambda: preprocessing_microtimeframe(df_base)}
    return timeframe_preprocessing[t]()

# Excepciones puntuales al corte generico de 40 años
RELIABLE_HISTORY_YEARS_OVERRIDES = {
    "SP500": 64,
}

def preprocessing_highertimeframe(df_base, symbol=None):
    reliable_years = RELIABLE_HISTORY_YEARS_OVERRIDES.get(symbol, 40)
    df_base = last_X_years(df_base, reliable_years)
    timeframes = []
    df_base = clean_ohlcv(df_base)
    weekly = df_base.resample('W-MON', label='left', closed='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    monthly = df_base.resample('MS', label='left', closed='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    quarterly = monthly.resample('QS', label='left', closed='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    yearly = quarterly.resample('YS').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    for t in [df_base, weekly, monthly, quarterly, yearly]:
        timeframes.append(t)
    return timeframes


def preprocessing_lowertimeframe(df_base):
    timeframes = []
    df_base = clean_ohlcv(df_base)
    data4H = df_base.resample('4h', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data4H.dropna(inplace=True)
    for t in [df_base, data4H]:
        timeframes.append(t)
    return timeframes


def preprocessing_microtimeframe(df_base):
    timeframes = []
    df_base = clean_ohlcv(df_base)
    data5min = df_base.resample('5min', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data5min.dropna(inplace=True)
    data15min = df_base.resample('15min', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data15min.dropna(inplace=True)
    data30min = df_base.resample('30min', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data30min.dropna(inplace=True)
    for t in [df_base, data5min, data15min, data30min]:
        timeframes.append(t)
    return timeframes
