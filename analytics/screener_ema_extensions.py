import pandas as pd
import numpy as np
from data.assets import Assets
from analytics.screener_retest_bands import *
from scipy import stats

def screener_ema_extensions():
    try:
        assets = Assets()
        symbols = assets.getAssets("mysymbols")
        col_name_ema = ["extension_ema10", "extension_ema20"]
        timeframes_name = ["D"]
        emas_name = ["EMA 10", "EMA 20"]
        rows = []
        num = 1
        for symbol in symbols:
            print("SCREENER PROCESSING", symbol, num)
            num = num + 1
            timeframes = assets.loadStatistics(assets.loadTimeframes(symbol))
            timeframes = timeframes[0]
            row = {"Stock": assets.name_sustitution(symbol), "Price": round(timeframes["Close"].iloc[-1],1)}
            e = 0
            for col_name in col_name_ema:
                current_value = timeframes[col_name].iloc[-1]
                p = stats.percentileofscore(timeframes[col_name].dropna(), current_value, kind='rank')
                column = "P_" + timeframes_name[0] + "_" + emas_name[e]
                row[column] = round(p, 1)
                e = e + 1
            retest_bands = calculation_retest_bands_screener(timeframes) 
            row["P 80"] = round(retest_bands["TimeAway"].quantile(0.8),1)
            row["P 95"] = round(retest_bands["TimeAway"].quantile(0.95),1)
            row["P 99"] = round(retest_bands["TimeAway"].quantile(0.99),1)
            row["TimeAway"] = retest_bands["TimeAway"].iloc[-1]
            row["EMA10_now"] = round(retest_bands["EMA10_now"].iloc[-1],1)
            row["EMA10_tmw"] = round(retest_bands["EMA10_tmw"].iloc[-1],1)
            rows.append(row) 
    except Exception as e:
        print(e)
        df = pd.DataFrame(rows)
        longs_df = df[(df['P_D_EMA 10'] < 50)].sort_values(by='TimeAway', ascending=False)
        shorts_df = df[(df['P_D_EMA 10'] >= 50)].sort_values(by='TimeAway', ascending=False)
        return longs_df, shorts_df
    df = pd.DataFrame(rows)
    longs_df = df[(df['P_D_EMA 10'] < 50)].sort_values(by='TimeAway', ascending=False)
    shorts_df = df[(df['P_D_EMA 10'] >= 50)].sort_values(by='TimeAway', ascending=False)
    return longs_df, shorts_df