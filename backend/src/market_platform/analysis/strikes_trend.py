import pandas as pd
from ..features.build_features import calculate_volatility


def _ema_trend_streaks(df, ema_period=10, weight=0.3):
    """Racha de dias que el Close se mantiene por encima o por debajo de la
    EMA, con una banda de tolerancia (segun volatilidad) para no contar como
    cambio de tendencia el ruido que apenas cruza la EMA.
    """
    vol, vol_p20, vol_p80 = calculate_volatility(df["Close"])
    vol = vol.shift(1)  # tolerancia calculada solo con info hasta t-1, sin look-ahead
    tolerance = (vol.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight

    df = df.iloc[ema_period:].copy()  # warm-up de la ema
    tolerance = tolerance.reindex(df.index)

    ema_col = f"ema{ema_period}"
    ema_vals = df[ema_col]
    close_vals = df["Close"]
    dates = df.index

    above_rows, below_rows = [], []

    tol0 = tolerance.iloc[0]
    side = "Above" if close_vals.iloc[0] >= ema_vals.iloc[0] * (1 + tol0) else "Below"
    streak_start = 0

    for i in range(1, len(df)):
        close = close_vals.iloc[i]
        ema = ema_vals.iloc[i]
        tol = tolerance.iloc[i]
        upper = ema * (1 + tol)
        lower = ema * (1 - tol)

        is_opposite_day = (close < lower) if side == "Above" else (close > upper)

        if is_opposite_day:
            row = {"date": str(dates[i - 1].date()), "num_days": i - streak_start}
            (above_rows if side == "Above" else below_rows).append(row)
            side = "Below" if side == "Above" else "Above"
            streak_start = i

    # la racha en curso (todavia sin cerrar) se incluye como dato historico
    # mas, igual que el resto de pantallas de la app (ej. Time Away).
    current_length = len(df) - streak_start
    (above_rows if side == "Above" else below_rows).append(
        {"date": str(dates[-1].date()), "num_days": current_length}
    )

    return above_rows, below_rows, side, current_length


def compute(timeframes):
    timeframe_labels = ["daily", "weekly"]
    panels = []

    for i, df in enumerate(timeframes[:2]):
        above_rows, below_rows, current_side, current_length = _ema_trend_streaks(df)

        for side, rows in (("Above", above_rows), ("Below", below_rows)):
            if not rows:
                continue

            lengths = pd.Series([r["num_days"] for r in rows])
            is_current_side = side == current_side
            # solo el lado que esta realmente en curso tiene un valor
            # "actual" -- el otro lado no tiene ninguna racha abierta ahora
            # mismo, asi que su current queda en 0 (no resaltado).
            current_value = current_length if is_current_side else 0

            panels.append({
                "timeframe": timeframe_labels[i],
                "type": side,
                "is_current": is_current_side,
                "current_value": current_value,
                "p25": lengths.quantile(0.25),
                "median": lengths.median(),
                "p75": lengths.quantile(0.75),
                "p95": lengths.quantile(0.95),
                "percentile": (lengths <= current_value).mean() * 100,
                "rows": rows,
            })

    return panels
