def compute(timeframes):
    panels = []
    timeframe_labels = ["daily", "weekly"]
    ema_periods = [10, 20]

    for i, timeframe_label in enumerate(timeframe_labels):
        df = timeframes[i].reset_index(names="date")

        for ema_period in ema_periods:
            name = f"ema{ema_period}"
            ema = df[name]

            # Absorption: la vela se mantiene por encima de la ema (open/close con
            # margen) pero el Low la toca/perfora -- soporte que "absorbe" el precio.
            absorption = (df["Open"] * 0.998 > ema) & (df["Close"] * 0.998 > ema) & (df["Low"] * 1.002 < ema)
            # Rejection: la vela se mantiene por debajo de la ema pero el High la
            # toca/perfora -- resistencia que "rechaza" el precio.
            rejection = (df["Open"] * 1.002 < ema) & (df["Close"] * 1.002 < ema) & (df["High"] * 0.998 > ema)

            patterns = [
                ("Absorption", absorption, df["extension_low_" + name]),
                ("Rejection", rejection, df["extension_high_" + name]),
            ]

            for pattern_type, mask, deviation in patterns:
                subset = df.loc[mask, ["date"]].copy()
                if subset.empty:
                    continue

                subset["deviation"] = deviation[mask].values
                subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")

                if pattern_type == "Absorption":
                    # invertido a proposito: la etiqueta "p95" lleva el valor
                    # quantile(0.05) (la caida mas profunda), y "p05" lleva
                    # quantile(0.95) (la menos profunda) -- asi "p95" siempre
                    # representa el caso mas extremo, igual que en Rejection.
                    p95 = subset["deviation"].quantile(0.05)
                    p05 = subset["deviation"].quantile(0.95)
                else:
                    p95 = subset["deviation"].quantile(0.95)
                    p05 = subset["deviation"].quantile(0.05)

                current_value = subset["deviation"].iloc[-1]
                panels.append({
                    "timeframe": timeframe_label,
                    "ema_period": ema_period,
                    "type": pattern_type,
                    "current_value": current_value,
                    "percentile": (subset["deviation"] <= current_value).mean() * 100,
                    "p05": p05,
                    "p95": p95,
                    "rows": subset.to_dict(orient="records"),
                })
    return panels
