import pandas as pd
from ..features.build_features import calculate_volatility


def _compute_panel(df, timeframe_label, ema_period, weight):
    df = df[10:]
    if df.empty:
        return None

    ema_col = f"ema{ema_period}"
    vol, vol_p20, vol_p80 = calculate_volatility(df["Close"])
    tolerance = (vol.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight

    rows = []
    k = 0
    for j in range(len(df)):
        is_away = ((df["Low"].iloc[j] * (1 - tolerance.iloc[j])) > df[ema_col].iloc[j]) or (
            (df["High"].iloc[j] * (1 + tolerance.iloc[j])) < df[ema_col].iloc[j]
        )
        if is_away:
            k += 1
        else:
            if k > 0:
                rows.append({"date": df.index[j], "time_away": k})
            k = 0
    rows.append({"date": df.index[-1], "time_away": k})

    subset = pd.DataFrame(rows)
    subset["date"] = pd.to_datetime(subset["date"]).astype(str)

    current_value = subset["time_away"].iloc[-1]

    return {
        "timeframe": timeframe_label,
        "ema_period": ema_period,
        "current_value": current_value,
        "median": subset["time_away"].median(),
        "percentile": (subset["time_away"] <= current_value).mean() * 100,
        "p05": subset["time_away"].quantile(0.05),
        "p25": subset["time_away"].quantile(0.25),
        "p95": subset["time_away"].quantile(0.95),
        "max": subset["time_away"].max(),
        "rows": subset.to_dict(orient="records"),
    }


def compute_highertimeframe(timeframes, weight=0.3):
    daily = timeframes[0]
    panels = []
    for ema_period in [10, 20, 50, 200]:
        panel = _compute_panel(daily, "daily", ema_period, weight)
        if panel is not None:
            panels.append(panel)
    return panels


def compute_macro(timeframes, weight=0.3):
    weekly, monthly = timeframes[1], timeframes[2]
    panels = []
    groups = [("weekly", weekly, [10, 20, 200]), ("monthly", monthly, [10, 20])]
    for timeframe_label, df, ema_periods in groups:
        for ema_period in ema_periods:
            panel = _compute_panel(df, timeframe_label, ema_period, weight)
            if panel is not None:
                panels.append(panel)
    return panels
