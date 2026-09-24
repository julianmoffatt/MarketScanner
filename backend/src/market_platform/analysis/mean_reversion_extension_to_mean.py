def compute_lowertimeframe(timeframes):
    panels = []
    timeframes = timeframes[0:2].copy()
    timeframe = ["1h", "4h"]
    ema_periods = [10, 20]

    for i, df in enumerate(timeframes):
        df = df.reset_index(names="date")
        for ema_period in ema_periods:
            extension_name = f"extension_ema{ema_period}"
            subset = df[["date", extension_name]].copy()
            subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")
            subset = subset.rename(columns={extension_name: "extension_to_mean"})
            current_value = subset["extension_to_mean"].iloc[-1]
            panels.append({
                "timeframe": timeframe[i],
                "ema_period": ema_period,
                "current_value": current_value,
                "percentile": (subset["extension_to_mean"] <= current_value).mean() * 100,
                "p05": subset["extension_to_mean"].quantile(0.05),
                "p95": subset["extension_to_mean"].quantile(0.95),
                "rows": subset.to_dict(orient="records"),
            })
    return panels


def compute_highertimeframe(timeframes):
    panels = []
    timeframes = timeframes[0:2].copy()
    timeframe = ["daily", "weekly"]
    ema_periods = [10, 20]

    for i, df in enumerate(timeframes):
        df = df.reset_index(names="date")
        for ema_period in ema_periods:
            extension_name = f"extension_ema{ema_period}"
            subset = df[["date", extension_name]].copy()
            subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")
            subset = subset.rename(columns={extension_name: "extension_to_mean"})
            current_value = subset["extension_to_mean"].iloc[-1]
            panels.append({
                "timeframe": timeframe[i],
                "ema_period": ema_period,
                "current_value": current_value,
                "percentile": (subset["extension_to_mean"] <= current_value).mean() * 100,
                "p05": subset["extension_to_mean"].quantile(0.05),
                "p95": subset["extension_to_mean"].quantile(0.95),
                "rows": subset.to_dict(orient="records"),
            })
    return panels


def compute_macrotimeframe(timeframes):
    panels = []
    timeframes = timeframes[0:2].copy()
    timeframe = ["daily", "weekly"]
    ema_periods = [50, 200]

    for i, df in enumerate(timeframes):
        df = df.reset_index(names="date")
        for ema_period in ema_periods:
            extension_name = f"extension_ema{ema_period}"
            subset = df[["date", extension_name]].copy()
            subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")
            subset = subset.rename(columns={extension_name: "extension_to_mean"})
            current_value = subset["extension_to_mean"].iloc[-1]
            panels.append({
                "timeframe": timeframe[i],
                "ema_period": ema_period,
                "current_value": current_value,
                "percentile": (subset["extension_to_mean"] <= current_value).mean() * 100,
                "p05": subset["extension_to_mean"].quantile(0.05),
                "p95": subset["extension_to_mean"].quantile(0.95),
                "rows": subset.to_dict(orient="records"),
            })
    return panels
