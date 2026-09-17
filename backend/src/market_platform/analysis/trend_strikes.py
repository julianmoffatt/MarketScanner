import numpy as np
import pandas as pd
from backend.src.market_platform.data.ingestion import *

MAX_STREAK = 25
N_YEARS = 5

def calculation_ema_trends(ema_period=10, weight=0.3, symbols_universe="mysymbols"):
    assets = Assets()
    symbols = assets.getAssets(symbols_universe)
    symbols = list(dict.fromkeys(symbols))
    current_year = pd.Timestamp.now().year
    years = list(range(current_year - N_YEARS + 1, current_year + 1))
    columns = (["Asset"] + [f"D{d}" for d in range(1, MAX_STREAK + 1)]
               + [f"Top{n}" for n in range(N_YEARS, 0, -1)]
               + [str(y) for y in years])
    rows = []

    for symbol in symbols:
        print("EMA TREND:", symbol)
        try:
            data = assets.loadStatistics(assets.loadTimeframes(symbol))
            symbol_rows = calculation_ema_trends_symbol(data[0], symbol, ema_period, years, weight)
            if symbol_rows is not None:
                rows.extend(symbol_rows)
        except Exception as e:
            print(symbol, e)

    df = pd.DataFrame(rows, columns=columns)
    return df


def calculation_ema_trends_symbol(daily, symbol, ema_period, years, weight):
    assets = Assets()
    df = daily.copy()
    ema_col = f"ema{ema_period}"
    if ema_col not in df.columns:
        df[ema_col] = df["Close"].ewm(span=ema_period, adjust=False).mean()

    vol, vol_p20, vol_p80 = Assets.calculate_volatility(df["Close"])
    vol = vol.shift(1) # tolerancia calculada solo con informacion hasta t-1
    tolerance = (vol.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight

    df = df.iloc[ema_period:].copy()
    tolerance = tolerance.reindex(df.index)

    if len(df) < 2:
        return None

    close_vals = df["Close"]
    ema_vals = df[ema_col]

    above_counts = [0] * (MAX_STREAK + 1) # indice 0 sin uso, streaks van de 1 a MAX_STREAK
    below_counts = [0] * (MAX_STREAK + 1)
    above_streaks = [] # (length, start_date) sin clippear, para top5 y maximos por año
    below_streaks = []

    def record_streak(side, length, start_date):
        clipped = min(length, MAX_STREAK)
        if side == "above":
            above_counts[clipped] += 1
            above_streaks.append((length, start_date))
        else:
            below_counts[clipped] += 1
            below_streaks.append((length, start_date))

    side = "above" if close_vals.iloc[0] >= ema_vals.iloc[0] else "below"
    streak_start = 0

    for i in range(1, len(df)):
        close = close_vals.iloc[i]
        ema = ema_vals.iloc[i]
        tol = tolerance.iloc[i]
        upper = ema * (1 + tol)
        lower = ema * (1 - tol)

        is_opposite_day = (close < lower) if side == "above" else (close > upper)

        if is_opposite_day:
            record_streak(side, i - streak_start, df.index[streak_start])
            side = "below" if side == "above" else "above"
            streak_start = i

    record_streak(side, len(df) - streak_start, df.index[streak_start])

    name = assets.name_sustitution(symbol)
    above_row = ([f"{name} (Ov)"] + format_counts_with_cumulative(above_counts)
                 + top_n(above_streaks) + max_by_year(above_streaks, years))
    below_row = ([f"{name} (Un)"] + format_counts_with_cumulative(below_counts)
                 + top_n(below_streaks) + max_by_year(below_streaks, years))
    return [above_row, below_row]


def format_counts_with_cumulative(counts):
    total = sum(counts[1:])
    cum = 0
    cells = []
    for d in range(1, MAX_STREAK + 1):
        count = counts[d]
        if total > 0:
            cum += count / total * 100
        cells.append(f"{count} ({int(round(cum))}%)")
    return cells


def top_n(streaks, n=N_YEARS):
    lengths = sorted((length for length, _ in streaks), reverse=True)
    lengths = lengths[:n] + [0] * max(0, n - len(lengths)) # rellena con 0 si hay menos de n rachas
    return list(reversed(lengths)) # ascendente: TopN (mas chico) ... Top1 (el mas largo)


def max_by_year(streaks, years):
    result = []
    for year in years:
        year_lengths = [length for length, start_date in streaks if start_date.year == year]
        result.append(max(year_lengths) if year_lengths else 0)
    return result
