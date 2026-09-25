import pandas as pd

FORWARD_HORIZONS = [1, 3, 5]

def compute(timeframes):
    panels = []
    timeframe_labels = ["daily", "weekly"]
    ema_periods = [10]

    for i, timeframe_label in enumerate(timeframe_labels):
        df = timeframes[i].reset_index(names="date")
        # Retorno a 1/3/5 velas vista de CADA fila -- se calcula una sola vez
        # sobre la serie completa (no solo sobre los eventos) para que cada
        # evento mire su propio futuro real, no el de otro evento. Esto es
        # analitica retrospectiva ("que paso historicamente despues de esto"),
        # no una feature de ML, asi que mirar hacia adelante aqui es
        # exactamente el punto, no look-ahead bias.
        forward_returns = {
            h: (df["Close"].shift(-h) / df["Close"] - 1) * 100
            for h in FORWARD_HORIZONS
        }

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
                # Eventos muy recientes (dentro de los ultimos N dias/semanas)
                # todavia no tienen "futuro" conocido -- se manda None en vez
                # de NaN (JSON no tiene NaN valido) y el frontend los excluye
                # del ranking, pero sin afectar current_value/percentile de
                # abajo, que se calculan sobre el subset completo.
                for h in FORWARD_HORIZONS:
                    subset[f"forward_return_{h}"] = forward_returns[h][mask].values
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
                rows = subset.to_dict(orient="records")
                for row in rows:
                    for h in FORWARD_HORIZONS:
                        key = f"forward_return_{h}"
                        if pd.isna(row[key]):
                            row[key] = None

                panels.append({
                    "timeframe": timeframe_label,
                    "ema_period": ema_period,
                    "type": pattern_type,
                    "current_value": current_value,
                    "percentile": (subset["deviation"] <= current_value).mean() * 100,
                    "p05": p05,
                    "p95": p95,
                    "rows": rows,
                })
    return panels
