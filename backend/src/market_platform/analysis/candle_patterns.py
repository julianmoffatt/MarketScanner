import pandas as pd
import numpy as np

def candle_pattern(timeframes):
    try:
        timeframe = ["daily", "weekly", "monthly", "quarterly"]
        timeframes = timeframes[0:4].copy()
        columns = ["timeframe", "type", "degree", "N", "p05", "p25", "p50", "p75", "p95"]
        rows = []
        for i, df in enumerate(timeframes):
            df = df[df["Volatility"]>=np.quantile(df["Volatility"], 0.25)].copy()
            for wick in ["Upper_wick", "Lower_wick"]:
                df1 = df[(df[wick]>=0.2) & (df[wick]<=0.4)].copy()
                df2 = df[(df[wick]>=0.45) & (df[wick]<=0.65)].copy()
                df3 = df[(df[wick]>=0.7) & (df[wick]<=0.9)].copy()
                degree = 0
                degree_levels = ["soft_absortion", "medium_absortion", "strong_absortion"]
                for df_aux in [df1, df2, df3]:
                    new_row = [timeframe[i]]
                    new_row.append(wick)
                    new_row.append(degree_levels[degree])
                    new_row.append(len(df_aux))
                    copy_row = new_row
                    try:
                        for n in [0.05, 0.25, 0.5, 0.75, 0.95]:
                            new_row.append(round(np.quantile(df_aux["Return_NextDay"], n),2))
                    except Exception as e:
                        new_row = copy_row
                        for n in [0.05, 0.25, 0.5, 0.75, 0.95]:
                            new_row.append(0)
                    rows.append(new_row)
                    degree += 1
        df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(e)