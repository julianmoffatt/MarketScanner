import numpy as np
import random
import pandas as pd
from backend.src.market_platform.data.data import *
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
from backend.src.market_platform.data.ingestion import Assets
from backend.src.market_platform.data.storage import *
import plotly.graph_objects as go
from plotly.subplots import make_subplots  


def append_values_row(row, df, num):
    total = sum(df.values())
    for i in range(num):
        if total > 0:
            row.append(round((df[i]/total)*100,1))
        else:
            row.append(0)
    return row


def cycle_dynamics_calculation(symbol, df, open, timeframe, df_vol, vol_p20, vol_p80, TIMEFRAME_WEIGHT):
    try:
        threshold = 0
        vol_k = 1
        weight = TIMEFRAME_WEIGHT.get(timeframe.upper(), 1.0)
        flips, lastFlip, side = 0, 1, 0
        sides = {1: 0, 0: 1}
        side = 1 if df.iloc[0]["Close"] >= open else 0

        for k in range(1, len(df)):
            vol_now = df_vol.iloc[k] if k < len(df_vol) and not np.isnan(df_vol.iloc[k]) else vol_p20
            threshold = np.clip(vol_now * vol_k * weight, vol_p20 * vol_k * weight, vol_p80 * vol_k * weight)
            upper_threshold = open * (1 + threshold / 100)
            lower_threshold = open * (1 - threshold / 100)

            if ((df.iloc[k]["Close"] > upper_threshold) and (side == 0)) or \
               ((df.iloc[k]["Close"] < lower_threshold) and (side == 1)):
                side = sides[side]
                flips += 1
                lastFlip = k + 1
                print(symbol, "|| FLIP ||", df.index[k], "||", df.iloc[k]["Close"],
                      "|| threshold:", round(threshold, 2), "%", timeframe)
        return flips, lastFlip, round(threshold, 2)
    except Exception as e:
        print(e) 




def calculation_cycle_flips_all_symbols(lower_timeframe, symbols):
    try:
        assets = Assets()
        TIMEFRAME_WEIGHT = {"WEEKLY": 0.50, "MONTHLY": 1, "QUARTERLY": 1.25, "YEARLY": 2}
        timeframes_name = ["weekly", "monthly", "quarterly"]
        if lower_timeframe == "daily":
            timeframes_name = ["weekly", "monthly", "quarterly"]
        elif lower_timeframe == "weekly":
            timeframes_name = ["monthly", "quarterly", "yearly"]
        elif lower_timeframe == "monthly":
            timeframes_name = ["quarterly", "yearly"]
        columns = []
        columns.append("Stock")
        columns.append("Ocurrences "+str(timeframes_name[0][0]).upper())
        for i in range (0,3):
            columns.append(str(i) + " " + timeframes_name[0] + "_F")
        columns.append("Ocurrences "+str(timeframes_name[1][0]).upper())
        for i in range (0,5):
            columns.append(str(i) + " " + timeframes_name[1] + "_F")
        columns.append("LF" + timeframes_name[1] + "_p50") 

        if len(timeframes_name) > 2:
            columns.append("Ocurrences "+str(timeframes_name[2][0]).upper())
            for i in range (0,5):
                columns.append(str(i) + " " + timeframes_name[2] + "_F")
            columns.append("5+ " + timeframes_name[2] + "_F")
            columns.append("LF" + timeframes_name[2] + "_p50") 
        df = pd.DataFrame(columns=columns)
        df_detail = pd.DataFrame(columns=columns)

        for symbol in symbols:
            print(symbol)
            timeframes = assets.loadTimeframes(symbol)
            dfs = cycle_dynamics(symbol, timeframes, TIMEFRAME_WEIGHT)

            # 1. Define la configuración para cada DataFrame en dfs # [rango_reindex, indices_a_guardar_en_df_final, usar_quantile]
            config = [
                [[0, 1, 2],    False], # DataFrame 0
                [[0, 1, 2, 3, 4], True], # DataFrame 1 
                [[0, 1, 2, 3, 4, 5], True]  # DataFrame 2
            ]
            new_row = [assets.name_sustitution(symbol)]

            for i, df_item in enumerate(dfs):
                flips_to_show, use_quantile = config[i]

                counts = df_item["Flips"].value_counts().reindex(range(10), fill_value=0)
                total = counts.sum()
                print("TOTAL", total)
                print(new_row)
                new_row.append(round(total, 0))
                # Añadimos los porcentajes específicos definidos en 'targets'
                for f in flips_to_show:
                    percentage = round((counts[f] / total) * 100, 1) if total > 0 else 0
                    new_row.append(percentage)

                # Añadimos el cuantil si la configuración lo pide
                if use_quantile:
                    q_val = round(df_item["LastFlip"].quantile(0.50), 1)
                    new_row.append(q_val)

            # Insertar en el dataframe final
            df.loc[len(df)] = new_row
            print(df.head)
            dfs_green, dfs_red = dataframe_candle_split(dfs)

            if lower_timeframe == "daily":
                n = "excels/analysis/monthly_" + symbol + ".csv"
                dfs[1].to_csv(n)
            elif lower_timeframe == "weekly":
                n = "excels/analysis/quarterly_" + symbol + ".csv"
                dfs[1].to_csv(n)

            names = [" (Green)", " (Red)"]
            x = 0
            for df_aux in [dfs_green, dfs_red]: #dfs si quiero la neutra antes que detalle verde y rojo
                counts_A = df_aux[0]["Flips"].value_counts().reindex(range(10), fill_value=0).to_dict()
                counts_B = df_aux[1]["Flips"].value_counts().reindex(range(10), fill_value=0).to_dict()
                p_01 = round(df_aux[1]["LastFlip"].quantile(0.50), 1)
                symbol_name = assets.name_sustitution(symbol)+names[x]
                row_details = [symbol_name]
                print(counts_A)
                print(counts_A.values())
                print(sum(counts_A.values()))
                row_details.append(sum(counts_A.values()))
                row_details = append_values_row(row_details, counts_A, 3)
                row_details.append(sum(counts_B.values()))
                row_details = append_values_row(row_details, counts_B, 5)
                row_details.append(p_01)

                if len(timeframes_name) > 2:
                    counts_C = df_aux[2]["Flips"].value_counts().reindex(range(10), fill_value=0).to_dict()
                    row_details.append(sum(counts_C.values()))
                    row_details = append_values_row(row_details, counts_C, 6)
                    p_02 = round(df_aux[2]["LastFlip"].quantile(0.50), 1)   
                    row_details.append(p_02)

                df_detail.loc[len(df_detail)] = row_details
                x = x+1  

            for a in range (0,len(dfs)):
                name = "excels/LastFlipOpen/" + lower_timeframe +"_flip_on_"+timeframes_name[a] + "_" + symbol + ".csv"
                dfs[a]["LastFlip"].to_csv(name)

        name_csv = "excels/flips" + lower_timeframe + ".csv"
        df.to_csv(name_csv)
        name_csv = "excels/flips_detail_" + lower_timeframe + ".csv"
        df_detail.to_csv(name_csv)
        print(df.head)
        return df
    except Exception as e:
        print(e)
        
 
def clean_timestamp_rsi(timeframes):
    fechas, valores = [], []
    
    for d in timeframes:          # cada elemento es un dict con 1 clave
        for k, v in d.items():
            # Convertir Timestamp → datetime Python
            if isinstance(k, pd.Timestamp):
                fechas.append(k.to_pydatetime())
            else:
                fechas.append(k)
            
            # Convertir np.float64 → float
            if isinstance(v, np.generic):
                valores.append(float(v))
            else:
                valores.append(v)

    return fechas, valores


def rsi_tradingview(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi
   
# hacer return estilo XO y J.Donato (portugues)

#def calculation_cycle_returns():
#    symbols = getSymbols()
#    rows = []
#    for symbol in symbols:
#        print(symbol)
#        aux_timeframes = getDataStock(symbol) # get data of ticker  
#        timeframes = preparingData([aux_timeframes[0]])
#        daily_data = last_year(timeframes)
#        daily_data['weekday'] = daily_data.index.dayofweek
#        daily_data['day_of_month'] = daily_data.index.day
#        mean_by_weekday = daily_data.groupby('weekday')['Return'].mean()
#        mean_by_monthday = daily_data.groupby('day_of_month')['Return'].mean()
#        weekday_mean = mean_by_weekday.reindex(range(5), fill_value=0)   # 0–4
#        monthday_mean = mean_by_monthday.reindex(range(1, 32), fill_value=0)       # 1–31
#        row = {'symbol': symbol}
#        row.update({f'S{i+1}': round((weekday_mean[i]-1)*100,1) for i in range(5)})
#        row.update({f'M{i}': round((monthday_mean[i]-1)*100,1) for i in range(1, 32)})
#        rows.append(row)   # row es dict
#    df = pd.DataFrame(rows)
#    df.to_csv("excels/returns.csv")
#    return df
    



        

