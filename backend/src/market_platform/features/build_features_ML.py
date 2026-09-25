from scipy.stats import percentileofscore
import numpy as np
import pandas as pd


def _time_away_running(df, ema_col, weight=0.3, vol_window=20):
    log_returns = np.log(df["Close"] / df["Close"].shift(1))
    vol = log_returns.rolling(vol_window).std() * 100

    vol_p20 = vol.expanding().quantile(0.20)
    vol_p80 = vol.expanding().quantile(0.80)
    tolerance = (vol.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight

    ema = df[ema_col]
    is_away = ((df["Low"] * (1 - tolerance)) > ema) | ((df["High"] * (1 + tolerance)) < ema)

    groups = (is_away != is_away.shift()).cumsum()
    streak = is_away.groupby(groups).cumcount() + 1
    return streak.where(is_away, 0)


def _streak_running(df):
    is_green = df["type"] == "Green"
    groups = (is_green != is_green.shift()).cumsum()
    return is_green.groupby(groups).cumcount() + 1


def _position_vs_period_open(df, freq):
    period = df["date"].dt.to_period(freq)
    period_open = df.groupby(period)["Open"].transform("first")
    return (df["Close"] - period_open) / period_open * 100


def build_features_ML(df):
    # Handling look ahead bias features
    df = df.drop('next_close', axis=1) 
    df = df.drop('return_next_day', axis=1)
    # Creating calendar info features
    df["day_of_week"] = df["date"].dt.day_name()
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter  
    df["week_of_year"] = df["date"].dt.isocalendar().week 
    # Creating advanced features
    # - rsi
    df["rsi_percentile"] = [percentileofscore(df["rsi"].iloc[:i].dropna(), df["rsi"].iloc[i], kind="rank") for i in range(len(df))]
    df = df.drop('rsi', axis=1) 
    # - distance to mean
    ema_extensions = ["extension_ema10", "extension_ema20", "extension_ema50", "extension_ema200"] 
    SHORT_WINDOW = 1000
    for ema_extension in ema_extensions:
        df["percentile_"+ema_extension] = [percentileofscore(df[ema_extension].iloc[:i], df[ema_extension].iloc[i], kind="rank") for i in range(len(df))]
        # corto / régimen reciente (rolling ventana fija)
        col = df[ema_extension]
        df["percentile_short_" + ema_extension] = [
            percentileofscore(col.iloc[i - SHORT_WINDOW:i], col.iloc[i], kind="rank")
            if i >= SHORT_WINDOW else np.nan
            for i in range(len(df))
        ]
    # - time away from mean
    ema_periods = [10, 20, 50, 200]
    for ema_period in ema_periods:
        col_name = "time_away_ema" + str(ema_period)
        df[col_name] = _time_away_running(df, "ema" + str(ema_period))
        col = df[col_name]
        df["percentile_" + col_name] = [
            percentileofscore(col.iloc[:i], col.iloc[i], kind="rank") for i in range(len(df))
        ]
    # - position respect open
    period_freqs = {"week": "W", "month": "M", "quarter": "Q", "year": "Y"}
    for label, freq in period_freqs.items():
        df["position_vs_" + label + "_open"] = _position_vs_period_open(df, freq)

    # - strikes (racha de velas seguidas del mismo color)
    df["streak"] = _streak_running(df)
    df["percentile_streak"] = [
        percentileofscore(df["streak"].iloc[:i], df["streak"].iloc[i], kind="rank") for i in range(len(df))
    ]

    # Deleting features no estacionarios
    raw_price_cols = ["date", "Adj Close", "Open", "High", "Low", "Close", "Volume",
                       "last_close", "ema10", "ema20", "ema50", "ema200"]
    df = df.drop(columns=raw_price_cols)

    # Deleting some time that can confuse the model with percentiles without warming up
    df = df.iloc[SHORT_WINDOW:].copy()

    # creating target variable y
    df["y_type"] = df["type"].shift(-1)

    # La ultima fila es "hoy": no tiene y_type (no sabemos aun el tipo de
    # manana), por eso el dropna() de abajo la descarta del set de
    # entrenamiento -- pero es justo la fila que hace falta para predecir en
    # vivo, asi que la guardamos aparte antes de perderla.
    X_latest = df.drop(columns=["y_type"]).iloc[[-1]]

    df = df.dropna()
    X = df.drop('y_type', axis=1)
    y = df['y_type']
    return X, y, X_latest