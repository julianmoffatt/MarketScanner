import numpy as np

def compute(timeframes):
    panels = []
    timeframe = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    for i, df in enumerate(timeframes):
        df = df.reset_index(names="date")
        df["deviation"] = np.where(
            df["type"] == "Green",
            (((df["Open"] - df["Low"]) / df["Open"]) * 100)*-1,
            ((df["High"] - df["Open"]) / df["Open"]) * 100,
        )
        df_green = df[df["type"] == "Green"].copy()
        df_red = df[df["type"] == "Red"].copy()

        for candle_type, group in [("Green", df_green), ("Red", df_red)]:
            subset = group[["date", "deviation"]].copy()
            subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")

            if candle_type == "Green":
                # la desviacion de las velas verdes se grafica en negativo
                # (por debajo), igual que Absorption en deviation_ema_trend --
                # "p95" debe seguir mostrando el caso mas extremo, que aqui es
                # el valor mas negativo (quantile(0.05)).
                p95 = subset["deviation"].quantile(0.05)
                p05 = subset["deviation"].quantile(0.95)
            else:
                # las rojas se mantienen en positivo, sin invertir: p95 ya es
                # el caso mas extremo de forma natural.
                p05 = subset["deviation"].quantile(0.05)
                p95 = subset["deviation"].quantile(0.95)

            current_value = subset["deviation"].iloc[-1]
            panels.append({
                "timeframe": timeframe[i],
                "type": candle_type,
                "current_value": current_value,
                "percentile": (subset["deviation"] <= current_value).mean() * 100,
                "p05": p05,
                "p95": p95,
                "rows": subset.to_dict(orient="records"),
            })
    return panels
