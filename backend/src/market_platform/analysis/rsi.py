import pandas as pd

def compute(timeframes):
    timeframe_labels = ["daily", "weekly"]
    lag_days = [140, 700]  # se salta el warm-up inicial de cada timeframe
    panels = []

    for i, df in enumerate(timeframes[:2]):
        df_filtered = df[df.index > df.index[0] + pd.Timedelta(days=lag_days[i])]

        subset = df_filtered[["rsi"]].reset_index(names="date")
        subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")
        subset = subset.rename(columns={"rsi": "rsi_value"})

        current_value = subset["rsi_value"].iloc[-1]

        panels.append({
            "timeframe": timeframe_labels[i],
            "current_value": current_value,
            "p05": subset["rsi_value"].quantile(0.05),
            "p95": subset["rsi_value"].quantile(0.95),
            "percentile": (subset["rsi_value"] <= current_value).mean() * 100,
            "rows": subset.to_dict(orient="records"),
        })

    return panels
