import pandas as pd
import numpy as np
from data.assets import Assets
from data.database import *

def calculation_cycle_peak_expansion(data, stock):
    dataframes = []
    dataframes_absolute = []
    try:
        timeframe = ["weekly", "monthly"]
        df_daily = data[0]
        for x in range(2, 3):
            HT = data[x]
            rows = []
            rows_absolute = []
            for i in range(0, len(HT)-1):
                max_dev = 0 # peak after last flip
                if (HT["type"].iloc[i] == "Green"):
                    max_dev = HT["High"].iloc[i]
                else:
                    max_dev = HT["Low"].iloc[i]

                max_dev_absolute = 0 # absolute peak of cycle
                if (HT["High"].iloc[i]-HT["Open"].iloc[i]) >= abs(HT["Open"].iloc[i]-HT["Low"].iloc[i]):
                    max_dev_absolute = HT["High"].iloc[i]
                else:
                    max_dev_absolute = HT["Low"].iloc[i]

                max, max_absolute = False, False

                LT = df_daily.loc[HT.index[i] : HT.index[i+1]].iloc[:-1]
                for k in range(0, len(LT)):
                    if not max and (max_dev == LT["High"].iloc[k]) or (max_dev == LT["Low"].iloc[k]):
                        rows.append({"Date": HT.index[i], "PeakExpansion": k + 1, "Return": HT["Return"].iloc[i]})
                        max = True
                    if not max_absolute and (max_dev_absolute == LT["High"].iloc[k]) or (max_dev_absolute == LT["Low"].iloc[k]):
                        rows_absolute.append({"Date": HT.index[i], "PeakExpansion": k + 1, "Return": HT["Return"].iloc[i]})
                        max_absolute = True

            df = pd.DataFrame(rows)
            df1 = pd.DataFrame(rows_absolute)
            database = Database()
            database.save_csv(df, "peaks_" + stock + "_" + timeframe[x-1])
            dataframes.append(df)
            dataframes_absolute.append(df1)
        return dataframes, dataframes_absolute
    except Exception as e:
        print(e)
        return dataframes


def calculation_cycle_peak_expansion_all_symbols():
    try:
        assets = Assets()
        symbols = assets.getAssets("mysymbols")
        timeframes = ["Weekly", "Monthly"]
        columns = ["Symbol", "Type", "Occurrences"]

        for p in [10,25,50,75,90]:
            name_column = timeframes[1] + " " + "p" + str(p)
            columns.append(name_column)

        peak_study = pd.DataFrame(columns=columns)
    
        for symbol in symbols:
            print(symbol)
            try:
                data = assets.loadStatistics(assets.loadTimeframes(symbol))
            except Exception as e:
                print(e)
            dataframes_symbol, dataframes_symbol_absolute = calculation_cycle_peak_expansion(data, symbol)
            df = dataframes_symbol[0].copy()
            df_absolute = dataframes_symbol_absolute[0].copy()
            df_green = df[df["Return"]>=0]
            df_red = df[df["Return"]<0]
            colour = ["Absolute", "Green", "Red"]
            k = 0
            for dataframe in (df_absolute, df_green, df_red):
                info = [assets.name_sustitution(symbol), colour[k], len(dataframe)]        
                for p in [0.10,0.25,0.50,0.75,0.90]:
                    percentil = dataframe["PeakExpansion"].quantile(p)
                    info.append(round(percentil,0))
                peak_study.loc[len(peak_study)] = info
                k += 1

        database = Database()
        database.save_csv(peak_study, "peaks_overview")
        return peak_study
    except Exception as e:
        print(e)
