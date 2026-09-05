import pandas as pd
from data.assets import Assets

def calculation_retest_bands(data, weight = 0.3):
    timeframes = []
    for df in data:
        rows = []
        k = 0
        df = df[10:]
        if df.empty:
            empty_df = pd.DataFrame(columns=["TimeAway"])
            empty_df.index.name = "Date"
            timeframes.append(empty_df)
            continue
        vol, vol_p20, vol_p80 = Assets.calculate_volatility(df["Close"])
        tolerance = (vol.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight
        print("tolerance avg%:", round(tolerance.mean() * 100, 3))

        for i in range(len(df)):
            is_away = ((df['Low'].iloc[i] * (1 - tolerance.iloc[i])) > df['ema10'].iloc[i]) or ((df['High'].iloc[i] * (1 + tolerance.iloc[i])) < df['ema10'].iloc[i])
            if is_away:
                k += 1
            else:
                if k > 0:
                    rows.append({"Date": df.index[i], "TimeAway": k})
                k = 0

        rows.append({"Date": df.index[-1], "TimeAway": k})
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
        timeframes.append(df)
    return timeframes
