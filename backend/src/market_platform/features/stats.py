import numpy as np
import pandas as pd
from ..features.build_features import calculate_volatility

emas = ["ema10", "ema20", "ema50"]

def create_mean_reversion_statistics(df):
    df = create_percentile_scores(df, ["extension_ema10", "extension_ema20"])
    df = create_candle_strikes_and_percentile_score(df)
    df = create_time_away_mean_and_percentile_score(df)
    df = create_duration_trend_and_percentile_score(df)
    return df


def create_percentile_scores(df, col_names, min_periods=252, ignore_zeros=False): # receives a list of columns and creates the percentile score columns
    for col in col_names:
        values = df[col].where(df[col] > 0) if ignore_zeros else df[col]
        percentile = values.expanding(min_periods=min_periods).rank(method="max", pct=True) * 100
        df["percentile_" + col] = percentile.where(df[col] > 0, 0) if ignore_zeros else percentile
    return df


def create_candle_strikes_and_percentile_score(df, min_periods=30):
    run = (df["type"] != df["type"].shift()).cumsum()
    df["strike"] = df.groupby(run).cumcount() + 1
    df["percentile_strike"] = df.groupby("type")["strike"].transform(
        lambda s: s.expanding(min_periods=min_periods).rank(method="max", pct=True) * 100
    )
    return df

def create_time_away_mean_and_percentile_score(df, min_periods=100, weight=0.30):
    vol, vol_p20, vol_p80 = calculate_volatility(df["Close"])
    tolerance = (vol.fillna(vol_p20).clip(vol_p20, min(vol_p80, 3)) / 100) * weight
    for ema in emas:
        above = df["Low"] > df[ema] * (1 + tolerance)
        below = df["High"] < df[ema] * (1 - tolerance)
        away = above | below
        run = (away != away.shift()).cumsum()
        df["time_away_" + ema] = (df.groupby(run).cumcount() + 1).where(away, 0)
    create_percentile_scores(df, ["time_away_" + ema for ema in emas], min_periods=min_periods, ignore_zeros=True)
    return df

def create_duration_trend_and_percentile_score(df, min_periods=30, weight=0.30):   
    vol, vol_p20, vol_p80 = calculate_volatility(df["Close"])
    tolerance = (vol.shift(1).fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight
    for ema in emas:
        warmup = int(ema.removeprefix("ema"))
        if len(df) <= warmup:
            for column in ("trend_side_", "duration_trend_", "percentile_duration_trend_"):
                df[column + ema] = np.nan
            continue
        close, ema_values = df["Close"].iloc[warmup:], df[ema].iloc[warmup:]
        upper = ema_values * (1 + tolerance.loc[close.index])
        lower = ema_values * (1 - tolerance.loc[close.index])
        side = pd.Series(np.nan, index=close.index)
        side[close > upper] = 1
        side[close < lower] = -1
        side = side.ffill().fillna(1 if close.iloc[0] >= upper.iloc[0] else -1)
        run = (side != side.shift()).cumsum()
        df["trend_side_" + ema] = side
        df["duration_trend_" + ema] = side.groupby(run).cumcount() + 1
        df["percentile_duration_trend_" + ema] = df.groupby("trend_side_" + ema)["duration_trend_" + ema].transform(
            lambda s: s.expanding(min_periods=min_periods).rank(method="max", pct=True) * 100
        )
    return df
