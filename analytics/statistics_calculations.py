import numpy as np
import random
import pandas as pd
from data.data import *
from scipy import stats
from concurrent.futures import ProcessPoolExecutor
from data.assets import Assets

# Calculation of strikes probabilities
def calculation_StrikesProbabilities(data):
    strikes = []
    for df in data:
        strike = {"Green": {}, "Red": {}}
        num = 1
        for i in range (1, len(df)):
            if (df.iloc[i]["type"] == df.iloc[i-1]["type"]) and i != (len(df)-1):
                num = num + 1
            else:
                x = i-1
                if i == (len(df)-1):
                    x = i
                if num in strike[df.iloc[x]["type"]]:
                  strike[df.iloc[x]["type"]][num] = strike[df.iloc[x]["type"]][num] + 1
                else:
                  strike[df.iloc[x]["type"]][num] = 1 
                num = 1
        print("---------------------------------------------------------------")
        sorted_by_key_green = dict(sorted(strike["Green"].items()))
        print(sorted_by_key_green)
        sorted_by_key_red = dict(sorted(strike["Red"].items()))
        print(sorted_by_key_red)
        print("---------------------------------------------------------------")
        strikes.append({"Green": dict(sorted(strike["Green"].items())),"Red":   dict(sorted(strike["Red"].items()))})
    #ocurrences = []
    probabilities, colours = [], [], 
    for cont in range(len(strikes)):
        number_points = 12
        probability_green = strikes[cont]["Green"]
        probability_red = strikes[cont]["Red"]
        probability_list = []
        #ocurrences_list = []
        x0 = (len(data[cont]) - 1) - number_points 
        num = 1
        candle = data[cont].iloc[x0]["type"]
        x = x0 - 1
        while x >= 0 and data[cont].iloc[x]["type"] == candle:
            num += 1
            x -= 1
        probability = round(next_candle_probability(candle, probability_green, probability_red, num) * 100, 0)
        probability_list.append(probability)
        for i in range(len(data[cont]) - number_points, len(data[cont])):
            if data[cont].iloc[i]["type"] == data[cont].iloc[i-1]["type"]:
                num = num + 1
            else:
                num = 1
            probability = next_candle_probability(data[cont].iloc[i]["type"], probability_green, probability_red, num) # returns red prob, get green with 1 - red prob
            probability_list.append(probability)

        color_list = []
        for i in range((len(data[cont]) - 1) - number_points, len(data[cont])):
            color_list.append(data[cont].iloc[i]["type"])
        # proyected continuation of 2 candle with proyected probabilities
        for k in range (1,4):
            probability = next_candle_probability(data[cont].iloc[i]["type"], probability_green, probability_red, num+k)
            probability_list.append(probability)
            color_list.append("blue")
        probabilities.append(probability_list)
        colours.append(color_list)
    return probabilities, colours  


# Gives the probabilities of the next candle depending on colour and current strike
def next_candle_probability(candle, probability_green, probability_red, num):
    probBeyond = 0
    streaks = pd.DataFrame()
    if candle == "Green":
        streaks = pd.DataFrame(list(probability_green.items()), columns=["days", "frequency"])
    else:
        streaks = pd.DataFrame(list(probability_red.items()), columns=["days", "frequency"])
    beyond = streaks[streaks["days"]>num]["frequency"].sum()
    equal = streaks[streaks["days"]==num]["frequency"].sum()
    if (equal + beyond) > 0:
        probBeyond = round((beyond / (equal + beyond)), 2) #probabilidad de racha continuando

    if candle == "Green":
        return 1-probBeyond#, beyond, equal        # i want to return red probability so, for a green strike the red prob is inverse of beyond (beyond is continuation of green)
    else:
        return probBeyond#, equal, beyond
    

# Calculo de los reversal points del rsi para las graficas
def calculation_Rsi(data): 
    lag = [250, 750, 1500]
    timeframes = []
    cont = 0
    for df in data:
        df_filtered = df[df.index > df.index[0]+pd.Timedelta(days=lag[cont])]
        timeframes.append(df_filtered)
        cont = cont + 1
    return timeframes


def append_values_row(row, df, num):
    total = sum(df.values())
    for i in range(num):
        if total > 0:
            row.append(round((df[i]/total)*100,1))
        else:
            row.append(0)
    return row


def cycle_dynamics_calculation(symbol, df, open, timeframe, df_vol, vol_p10, vol_p90, TIMEFRAME_WEIGHT):
    try:
        threshold = 0
        vol_k = 1
        weight = TIMEFRAME_WEIGHT.get(timeframe.upper(), 1.0)
        flips, lastFlip, side = 0, 1, 0
        sides = {1: 0, 0: 1}
        side = 1 if df.iloc[0]["Close"] >= open else 0

        for k in range(1, len(df)):
            vol_now = df_vol.iloc[k] if k < len(df_vol) and not np.isnan(df_vol.iloc[k]) else vol_p10
            threshold = np.clip(vol_now * vol_k * weight, vol_p10 * vol_k * weight, vol_p90 * vol_k * weight)
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


def cycle_dynamics(symbol, data, lower_timeframe, TIMEFRAME_WEIGHT):
    timeframe = ["WEEKLY", "MONTHLY", "QUARTERLY"]
    parameters = []
    if lower_timeframe == "daily":
        timeframe = ["WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"]
        t = 0
        parameters = [pd.Timedelta(days=7), pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3)]
    elif lower_timeframe == "weekly":
        timeframe = ["MONTHLY", "QUARTERLY", "YEARLY"]
        t = 1
        parameters = [pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3), pd.offsets.MonthBegin(12)]
    elif lower_timeframe == "monthly":
        timeframe = ["QUARTERLY", "YEARLY"]
        t = 2
        parameters = [pd.offsets.MonthBegin(3), pd.offsets.MonthBegin(12)]
    
    LT = data[t][14:].copy()

    # volatilidad histórica del LT completo — log-returns rolling 20, percentiles para clamps
    LT_vol = np.log(LT["Close"] / LT["Close"].shift(1)).rolling(20).std() * 100
    vol_p10 = LT_vol.quantile(0.10)
    vol_p90 = LT_vol.quantile(0.90)

    timeframes_cycles = []
    end = []
    for k in range(len(parameters)):
        end.append(pd.to_datetime((data[k+1+t].index[-1] + parameters[k]), utc=True))

    p = 0
    for i in range (1+t, len(data)):
        HT = data[i].copy()
        LT = LT[LT.index < end[i-1-t]]
        MT = pd.DataFrame()
        if lower_timeframe == "weekly":
            MT = data[0][14:].copy()

        cycle = pd.DataFrame(columns=["Date", "Open", "Flips", "LastFlip", "Threshold", "Direction", "Return"])

        for x in range(0, len(HT)-1):
            df = LT[(LT.index >= HT.index[x]) & (LT.index < HT.index[x+1])]
            if df.empty:
                continue
            df_vol = LT_vol.reindex(df.index)
            print(timeframe[i-1-t], "| OPEN:", HT.iloc[x]["Open"], "| CLOSE:", HT.iloc[x]["Close"], "| DATE:", HT.index[x])
            params = cycle_dynamics_calculation(symbol, df, HT.iloc[x]["Open"], timeframe[p], df_vol, vol_p10, vol_p90, TIMEFRAME_WEIGHT)
            cycle.loc[len(cycle)] = [HT.index[x], round(HT.iloc[x]["Open"], 1), params[0], params[1], params[2], HT.iloc[x]["type"], HT.iloc[x]["Return"]]

        df = LT[(LT.index >= HT.index[-1])]
        if not df.empty:
            df_vol = LT_vol.reindex(df.index)
            params = cycle_dynamics_calculation(symbol, df, HT.iloc[-1]["Open"], timeframe[p], df_vol, vol_p10, vol_p90, TIMEFRAME_WEIGHT)
            cycle.loc[len(cycle)] = [HT.index[-1], round(HT.iloc[-1]["Open"],1), params[0], params[1], params[2], HT.iloc[x]["type"], HT.iloc[x]["Return"]]
        cycle.set_index("Date", inplace=True)
        timeframes_cycles.append(cycle)
        p += 1
    return timeframes_cycles


def dataframe_candle_split(data):
    data_green, data_red  = [], []
    for df in data:
        data_green.append(df[df["Direction"] == "Green"].copy())
        data_red.append(df[df["Direction"] == "Red"].copy())
    return data_green, data_red


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
            data_candles = preparing_timeframes(symbol, lower_timeframe)
            dfs = cycle_dynamics(symbol, data_candles, lower_timeframe, TIMEFRAME_WEIGHT)

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


def current_cycle_flips_all_symbols(lower_timeframe):
    try:
        assets = Assets()
        timeframes_name = ["weekly", "monthly", "quarterly"]
        if lower_timeframe == "daily":
            t = 0
            timeframes_name = ["weekly", "monthly", "quarterly"]
        elif lower_timeframe == "weekly":
            t = 1
            timeframes_name = ["monthly", "quarterly", "yearly"]
        elif lower_timeframe == "monthly":
            t = 2
            timeframes_name = ["quarterly", "yearly"]

        symbols = getSymbols()
        rows = []
        for symbol in symbols:
            row = {}
            print("i process", symbol)
            data_candles = preparing_timeframes(symbol, lower_timeframe)
            LT_full = data_candles[0+t]
            LT_vol = np.log(LT_full["Close"] / LT_full["Close"].shift(1)).rolling(20).std() * 100
            vol_p10 = LT_vol.quantile(0.10)
            vol_p90 = LT_vol.quantile(0.90)
            symbol_flips = []
            row = {}
            p = 0
            for i in range (1+t,len(data_candles)):
                lowerTimeframeCandles = data_candles[0+t][data_candles[0+t].index >= data_candles[i].index[-1]]
                if lower_timeframe == "weekly":
                    MT = data_candles[0][data_candles[0].index >= data_candles[i].index[-1]]
                    df_partialweek = MT[MT.index >= data_candles[i].index[-1]]
                    if not df_partialweek.empty and len(df_partialweek) == 4:
                        lowerTimeframeCandles = merge_partialweek(lowerTimeframeCandles, df_partialweek)
                open_price = data_candles[i].iloc[-1]["Open"]
                df_vol = LT_vol.reindex(lowerTimeframeCandles.index)
                flips, lastFlip = cycle_dynamics_calculation(symbol, lowerTimeframeCandles, open_price, timeframes_name[p], df_vol, vol_p10, vol_p90)
                if flips > 5:
                    flips = 5 #represent a 4+ or a cell with the actual number
                symbol_flips.append([flips, lastFlip])
                p += 1
            row = {"symbol": assets.name_sustitution(symbol)}
            for i, tf in enumerate(timeframes_name):
                row[f"{tf}Flip"] = symbol_flips[i][0]
                row[f"{tf}LastFlip"] = symbol_flips[i][1]
            rows.append(row)   
        df = pd.DataFrame(rows)
        name_csv = "excels/currentflips" + lower_timeframe + ".csv"
        df.to_csv(name_csv)    
        print("i return the csv of current flips")
        return df 
    except Exception as e:
        print(e)
        
 
def clean_timestamp_rsi(data):
    fechas, valores = [], []
    
    for d in data:          # cada elemento es un dict con 1 clave
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


def calculation_ema_extension(data): 
    try:
        ema_extensions = []
        for df in data:
            df = df.copy()
            ema_number = [10,20,50,200]
            ema_name = ["ema10", "ema20", "ema50", "ema200"]        
            i = 0
            for ema in ["EMA10", "EMA20", "EMA50", "EMA200"]:
                df[ema] = df["Close"].ewm(span=ema_number[i], adjust=False).mean()
                df["extension_"+ema_name[i]] = ((df["Close"] - df[ema]) / df[ema])*100
                df["extension_low_"+ema_name[i]] = ((df["Low"] - df[ema]) / df[ema])*100
                df["extension_high_"+ema_name[i]] = ((df["High"] - df[ema]) / df[ema])*100
                i += 1
            ema_extensions.append(df)
        return ema_extensions 
    except Exception as e:
        print(e)   


def screener_ema_extensions():
    try:
        assets = Assets()
        symbols = getSymbols()
        col_name_ema = ["extension_ema10", "extension_ema20"]
        timeframes_name = ["D"]
        emas_name = ["EMA 10", "EMA 20"]
        rows = []
        num = 1
        for symbol in symbols:
            print("SCREENER PROCESSING", symbol, num)
            num = num + 1
            data = preparing_timeframes(symbol, "")
            timeframes = calculation_ema_extension(data)
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


def calculation_average_deviation(data):
    try:
        data = create_hightimeframes(data, "daily")
        data = preparingData(data)
        timeframes = []
        for df in data:
            df = df.copy()
            df['Deviation'] = np.where(df['type'] == 'Green', ((df['Open'] - df['Low']) / df['Open'])*100, ((df['High'] - df['Open']) / df['Open'])*100)
            df = df[df['Deviation']>=0]
            timeframes.append(df)
        return timeframes 
    except Exception as e:
        print(e)


def calculation_retest_bands_screener(df): 
    df = df.copy()
    rows = []
    k = 0

    df["EMA_10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["EMA_25"] = df["Close"].ewm(span=25, adjust=False).mean()
    df = df.iloc[25:].copy() # Cortamos para tener datos limpios
    
    tolerance = 0.01 
    ema_top = df[['EMA_10', 'EMA_25']].max(axis=1) * (1 + tolerance)
    ema_bot = df[['EMA_10', 'EMA_25']].min(axis=1) * (1 - tolerance)

    for i in range(len(df)):
        is_away = (df['Low'].iloc[i] > ema_top.iloc[i]) or (df['High'].iloc[i] < ema_bot.iloc[i])

        if is_away:
            k += 1
        else:
            if k > 0:
                rows.append({"Date": df.index[i], "TimeAway": k, "EMA10_now": 0, "EMA10_tmw": 0})
            k = 0
    ema10Tomorrow = df['EMA_10'].iloc[-1] / (df['EMA_10'].iloc[-2]/df['EMA_10'].iloc[-1])
    rows.append({"Date": df.index[-1], "TimeAway": k, "EMA10_now": df['EMA_10'].iloc[-1], "EMA10_tmw": ema10Tomorrow})    
    return pd.DataFrame(rows)


def calculation_retest_bands(data, timeframe):
    timeframes = []
    cont = 0
    for df in data:
        cont = cont + 1
        rows = []
        k = 0
        df["EMA_10"] = df["Close"].ewm(span=10, adjust=False).mean()
        df = df[10:]
        tolerance = 0.01
        if timeframe  == "LT":
            tolerance = 0.0025

        for i in range(len(df)):
            is_away = ((df['Low'].iloc[i] * (1 - tolerance)) > df['EMA_10'].iloc[i]) or ((df['High'].iloc[i] * (1 + tolerance)) < df['EMA_10'].iloc[i])
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


def calculation_closing_gaps(symbol):
    try:
        data = preparing_timeframes(symbol, "")
        df = data[0]
        gaps = []
        for i in range (1, len(df)):
            # LOGICA QUE DETECTA CIERRE DE GAPS
            for gap in gaps:
                if gap["Status"] == "Open":
                    if (df["Low"].iloc[i] <= gap["GapLow"]) and (df["High"].iloc[i] >= gap["GapHigh"]): #AÑADIR MARGEN DE ERROR (NO ES PERFECTO UN CIERRE DE GAP)
                        gap["GapFilled"] = True
                        gap["Status"] = "Closed"
                        gap["DaysOpen"] = (df.index[i] - gap["Date"]).days
                    elif (df["Low"].iloc[i] >= gap["GapLow"]) and (df["High"].iloc[i] <= gap["GapHigh"]):
                        gap["GapFilled"] = True
                        gap["GapHigh"] = round(df["High"].iloc[i], 2)
                        gap["GapLow"] = round(df["Low"].iloc[i], 2)
                        if gap["FirstRetest"] == False: 
                            gap["FirstRetest"] == True 
                            gap["DaysOpen"] = (df.index[i] - gap["Date"]).days
                    elif (df["Low"].iloc[i] <= gap["GapLow"]) and (df["High"].iloc[i] > gap["GapLow"]) and (df["High"].iloc[i] > gap["GapHigh"]):
                        gap["GapHigh"] = round(df["High"].iloc[i], 2)
                        gap["GapFilled"] = True
                        if gap["FirstRetest"] == False: 
                            gap["FirstRetest"] == True 
                            gap["DaysOpen"] = (df.index[i] - gap["Date"]).days
                    elif (df["High"].iloc[i] >= gap["GapHigh"]) and (df["Low"].iloc[i] > gap["GapLow"]) and (df["Low"].iloc[i] < gap["GapHigh"]):
                        gap["GapLow"] = round(df["Low"].iloc[i], 2)
                        gap["GapFilled"] = True
                        if gap["FirstRetest"] == False: 
                            gap["FirstRetest"] == True 
                            gap["DaysOpen"] = (df.index[i] - gap["Date"]).days

            # LOGICA QUE DETECTA Y GUARDA UN GAP
            gap_high, gap_low = 0, 0
            if (df["Low"].iloc[i] > df["Close"].iloc[i-1]) or (df["High"].iloc[i] < df["Close"].iloc[i-1]):
                gapSize = 0
                if (df["Low"].iloc[i] > df["Close"].iloc[i-1]):
                    gapSize = round((round(df["Low"].iloc[i] / df["Close"].iloc[i-1], 3)-1) * 100, 1)
                    gap_high = round(df["Low"].iloc[i], 2)
                    gap_low = round(df["Close"].iloc[i-1], 2)
                else:
                    gapSize = round(abs(round(df["High"].iloc[i] / df["Close"].iloc[i-1], 3) - 1) * 100, 1)
                    gap_high = round(df["Close"].iloc[i-1], 2)
                    gap_low = round(df["High"].iloc[i], 2)
                if (gap_high/gap_low) >= 1.0075:
                    gaps.append({"Date": df.index[i], "Status": "Open", "DaysOpen": -1, "GapSize": round(gapSize,1), "GapHigh": gap_high, "GapLow": gap_low, "GapFilled": False, "FirstRetest": False})
        for gap in gaps:
            if gap["Status"] == "Open":
                gap["DaysOpen"] = (df.index[-1] - gap["Date"]).days
        df_gaps = pd.DataFrame(gaps) 
        name = "excels/gaps/" + symbol + ".csv"
        df_gaps.to_csv(name)
        return df_gaps 
    except Exception as e:
        print("The exception was:", e)


def calculation_closing_gaps_all_symbols():
    assets = Assets()
    symbols = getSymbols()
    gaps_study = pd.DataFrame(columns=["Symbol", "Total Gaps", "Closed Ratio", "Days Open p20", "Days Open p50", "Days Open p80"])

    for symbol in symbols:
        if symbol != "BTC-USD" and symbol != "ETH-USD":
            print("Processing gaps", symbol)
            df = calculation_closing_gaps(symbol)
            df = df[df["GapSize"] >= 0.5] # filtrar por una fraccion de la volatilidad de los ultimos 10 años por ejemplo (dinamico al activo)
            totalGaps = len(df)
            closedGaps = df[df["Status"] == "Closed"]
            percentil_10 = round(closedGaps["DaysOpen"].quantile(0.20), 2)
            percentil_50 = round(closedGaps["DaysOpen"].quantile(0.50), 2)
            percentil_90 = round(closedGaps["DaysOpen"].quantile(0.80), 2)
            gaps_study.loc[len(gaps_study)] = [assets.name_sustitution(symbol), totalGaps, round(len(closedGaps)/totalGaps, 2), percentil_10, percentil_50, percentil_90] 
            print("END GAPS", symbol)
    gaps_study.to_csv("excels/gapsallsymbols.csv")
    return gaps_study


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
            name = "excels/peaks/" + stock + "_" + timeframe[x-1] + ".csv"
            df.to_csv(name)
            dataframes.append(df)
            dataframes_absolute.append(df1)
        return dataframes, dataframes_absolute
    except Exception as e:
        print(e)
        return dataframes
    

def calculation_cycle_peak_expansion_all_symbols():
    try:
        assets = Assets()
        symbols = getSymbols()
        timeframes = ["Weekly", "Monthly"]
        columns = ["Symbol", "Type", "Occurrences"]

        for p in [10,20,50,80,90]:
            name_column = timeframes[1] + " " + "p" + str(p)
            columns.append(name_column)

        peak_study = pd.DataFrame(columns=columns)
    
        for symbol in symbols:
            print(symbol)
            try:
                data = preparing_timeframes(symbol, "")
            except Exception as e:
                print(e)
            print("llega aca")
            dataframes_symbol, dataframes_symbol_absolute = calculation_cycle_peak_expansion(data, symbol)
            df = dataframes_symbol[0].copy()
            df_absolute = dataframes_symbol_absolute[0].copy()
            df_green = df[df["Return"]>=0]
            df_red = df[df["Return"]<0]
            colour = ["Absolute", "Green", "Red"]
            k = 0
            for dataframe in (df_absolute, df_green, df_red):
                info = [assets.name_sustitution(symbol), colour[k], len(dataframe)]        
                for p in [0.10,0.20,0.50,0.80,0.90]:
                    percentil = dataframe["PeakExpansion"].quantile(p)
                    info.append(round(percentil,0))
                peak_study.loc[len(peak_study)] = info
                k += 1

        peak_study.to_csv("excels/peaksoverview.csv")
        return peak_study
    except Exception as e:
        print("Error" + e)


def calculation_cashsession_dynamics():
    assets = Assets()
    rows = []
    symbols = get_hyperliquid_symbols()
    for symbol in symbols:
        print("CASH SESSION", symbol)
        try:
            data = preparing_timeframes(symbol, "")
            data_HT = data[0].copy()
            data = getDataStock_LT(symbol, False)
            data_LT = data[0].copy()
            data_MicroT = getDataStock_MT(symbol)

            if not data_HT.empty and not data_LT.empty and not data_MicroT.empty:
                nameField = ["Return1H", "type1H", "Return15m", "type15m"]
                timeframes = ["1h","15m"]
                x = 0
                row = {}
                for df in [data_LT, data_MicroT]:
                    data_HT = data_HT[data_HT.index >= df.index[0]]  
                    df = df[df.index >= data_HT.index[0]]           
                    data_HT = data_HT[1:].copy()
                    data_HT[nameField[0+x]] = data_HT["Return"]
                    data_HT[nameField[1+x]] = data_HT["type"]    
                    for i in range(0, len(data_HT)):
                        aux = data_LT[data_LT.index.date == data_HT.index[i].date()]
                        idx = data_HT.index[i]
                        if not aux.empty:
                            data_HT.loc[idx, nameField[0+x]] = ((aux["Close"].iloc[0]/aux["Open"].iloc[0])-1) * 100
                            if data_HT.loc[idx, nameField[0+x]] >= 0:
                                data_HT.loc[idx, nameField[1+x]] = "Green"
                            else:
                                data_HT.loc[idx, nameField[1+x]] = "Red"
                    print("pre-filtro", len(data_HT))
                    data_HT = data_HT[abs((data_HT["Close"]/data_HT["Open"])-1) >= 0.0025]
                    print("filtro completado", len(data_HT))
                    Green = data_HT[(data_HT[nameField[1+x]]) == "Green"]
                    Green_Green = Green[Green["type"] == "Green"]
                    Green_Green_Beyond = Green_Green[Green_Green["Return"] > Green_Green[nameField[0+x]]]
                    Green_Red= Green[Green["type"] == "Red"]
                    Red = data_HT[data_HT[nameField[1+x]] == "Red"] 
                    Red_Green = Red[Red["type"] == "Green"]
                    Red_Red = Red[Red["type"] == "Red"]
                    Red_Red_Beyond = Red_Red[Red_Red["Return"] < Red_Red[nameField[0+x]]]
                    row["symbol"] = assets.name_sustitution(symbol)
                    name = "NumGreen" + timeframes[x]
                    row[name] = len(Green)
                    name = "Green " + timeframes[x] + " (GreenDay)"
                    row[name] = round(len(Green_Green)/len(Green),2)
                    name = "Green " + timeframes[x] + " (RedDay)"
                    row[name] = round(len(Green_Red)/len(Green),2)
                    name = "Day higher vs" + timeframes[x] + " (Green)"
                    row[name] = round(len(Green_Green_Beyond)/len(Green_Green),2)
                    name = "NumRed" + timeframes[x]
                    row[name] = len(Red)
                    name = "Red " + timeframes[x] + " (RedDay)"
                    row[name] = round(len(Red_Red)/len(Red),2)
                    name = "Red " + timeframes[x] + " (GreenDay)"
                    row[name] = round(len(Red_Green)/len(Red),2)
                    name = "Day lower vs " + timeframes[x]
                    row[name] = round(len(Red_Red_Beyond)/len(Red_Red),2)
                    x += 1
                print(row)
                rows.append(row)
        except Exception as e:
            print(e)
            break    
        #pillar distintos timeframes y filtrar quedandome a partir del primer dia de data
        # montar las probabilidades segun el primer close de 15min, 30min, 1h, 2h (opcional)
    df = pd.DataFrame(rows)
    return df


import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd


def calculation_open_momentum(timeframes):
    try:
        daily = timeframes[0].copy()
        daily['month_period'] = daily.index.tz_localize(None).to_period('M')        
        monthly = timeframes[2].copy()
        monthly['month_period'] = monthly.index.tz_localize(None).to_period('M')        
        start_period = monthly['month_period'].iloc[0]
        end_period = monthly['month_period'].iloc[-1]
        daily = daily[(daily['month_period'] >= start_period) & (daily['month_period'] <= end_period)]
        daily['Return_Decimal'] = daily['Return'] / 100 if daily['Return'].max() > 1 else daily['Return']

        for k in (1, 3, 5):
            firstdays_df = daily.groupby('month_period').head(k)
            prod_retornos = firstdays_df.groupby('month_period')['Return_Decimal'].apply(lambda x: (1 + x).prod() - 1)
            prod_retornos_pct = prod_retornos * 100            
            name = 'Added_Return_' + str(k)
            monthly[name] = monthly['month_period'].map(prod_retornos_pct)            
        return monthly 
    except Exception as e:
        print(e)


def calculation_open_momentum_all_symbols():
    symbols = get_hyperliquid_symbols()
    target_days = [1, 3, 5]
    sigmas = [1.0, 1.5, 2]
    columns = ["Asset"]
    rows = []
    for d in target_days:
        for s in sigmas:
            columns.append("ADDED DAY"+str(d)+"-std("+str(s)+")")
            columns.append("Ocurr (day "+str(d)+"-"+str(s)+")")
    
    columns.append("Avg-Corr")

    for symbol in symbols:
        average = []
        print(symbol)
        try:
            row = [symbol]
            data = preparing_timeframes(symbol, "")
            df = calculation_open_momentum(data)
            for row_idx, day in enumerate(target_days, start=1):
                current_col = f"Added_Return_{day}"            
                df_clean = df[["Return", current_col]].dropna()
                for col_idx, sigma in enumerate(sigmas, start=1):
                    if len(df_clean) >= 2:
                        mean_k = df_clean[current_col].mean()
                        std_k = df_clean[current_col].std()
                        df_filtered = df_clean[(df_clean[current_col] - mean_k).abs() >= (sigma * std_k)]
                        r_value = 0.0
                        if len(df_filtered) > 1:
                            r_value = df_filtered["Return"].corr(df_filtered[current_col])
                            row.append(round(r_value, 2))
                            average.append(r_value)
                            row.append(len(df_filtered))
                        else:
                            r_value = "-"
                    else:
                        r_value = "-"
                    if r_value == "-":
                        row.append(np.nan)
                        row.append(np.nan)
            aux_df = pd.DataFrame(average)
            row.append(round(float(aux_df.mean().item()), 2))
            rows.append(row)
        except Exception as e:
            print(e)
    try:
        df_ordered = pd.DataFrame(rows, columns=columns)
        df_ordered = df_ordered.sort_values(by="Avg-Corr", ascending=False)
        return df_ordered
    except Exception as e:
        print(e)


def golden_cross(df):
    if df["EMA_12"].iloc[-1] < df["EMA_25"].iloc[-1]:
        incr1 = df["EMA_12"].iloc[-1]/df["EMA_12"].iloc[-2]
        incr2 = df["EMA_25"].iloc[-1]/df["EMA_25"].iloc[-2]
        if (df["EMA_12"].iloc[-1] * incr1 * 1.001) > (df["EMA_25"].iloc[-1] * incr2):
            return True      
    return False


def relative_return(entry, value):
    num = float(value)  
    return round(((num / entry) - 1) * 100, 1)

def golden_cross_performance(entry, df):
    row = []
    for i in range(len(df)):
        for k in ["Open", "Close", "High", "Low"]:
            row.append(relative_return(entry, df[k].iloc[i]))
    return row


def calculation_golden_crosses_history(symbol, timeframes, t):
    if t == "weekly":
        df = timeframes[1].copy()
        df = df[-200:]
        p = 200
    elif t == "daily":
        df = timeframes[0].copy()
        df = df[-1300:]
        p = 1300
    golden_crosses = []
    row = []
    columns = ["D" + str(i) + k for i in range(1, 6) for k in ["Open", "Close", "High", "Low"]]
    columns = ["Symbol", "Date", "Day", "Month(Q)", "D1%Month", "D1%Quarter", "D1%Year", "D0volume", "D1volume", "D0_xEma12", "D1_xEma12", "D0.EXT.10D", "D0.EXT.20D", "D0.EXT.10W", "D0.DAILY.RSI", "%D1vsEXT.10D.P95", "%D1vsEXT.10D.P99"] + columns
    if len(df) >= p: # +- 2 años
        for i in range(1, len(df)-1):
            if golden_cross(df[i-1:i+1]) and ((df["EMA_12"].iloc[i+1] * 1.001) >= df["EMA_25"].iloc[i+1]):
                daily_aux = timeframes[0].copy()
                if t == 'weekly':
                    today = daily_aux[(daily_aux.index > df.index[i]) & (daily_aux.index < df.index[i+1])]
                    today = today.iloc[-1:]
                elif t == 'daily':
                    today = df.iloc[i:i+1]                    
                
                daily_aux = daily_aux[daily_aux.index >= df.index[i+1]].copy()
                D0incr12, D1incr12 = 0, 0
                
                if len(daily_aux) >= 5: 
                    daily = daily_aux[0:5].copy()
                    D0incr12 = round(((df["EMA_12"].iloc[i]/df["EMA_12"].iloc[i-1])-1)*100, 2)
                    D1incr12 = round(((daily["EMA_12"].iloc[0]/df["EMA_12"].iloc[i])-1)*100, 2)
                    daily_extensions = timeframes[0][timeframes[0].index < df.index[i+1]]
                    weekly_extensions = timeframes[1][timeframes[1].index < df.index[i+1]]
                    d10 = stats.percentileofscore(daily_extensions["extension_ema10"].dropna(), df["extension_ema10"].iloc[i], kind='rank')
                    d20 = stats.percentileofscore(daily_extensions["extension_ema20"].dropna(), df["extension_ema20"].iloc[i], kind='rank')
                    w10 = stats.percentileofscore(weekly_extensions["extension_ema10"].dropna(), df["extension_ema10"].iloc[i], kind='rank')
                    rsi = stats.percentileofscore(daily_extensions["rsi"].dropna(), df["rsi"].iloc[i], kind='rank')
                    upsideP95ext10 = round(daily_extensions["extension_ema10"].quantile(0.95) - daily["extension_ema10"].iloc[0], 1)
                    upsideP99ext10 = round(daily_extensions["extension_ema10"].quantile(0.99) - daily["extension_ema10"].iloc[0], 1)
                    monthly = timeframes[2][(timeframes[2].index.year == daily.index[0].year) & (timeframes[2].index.month == daily.index[0].month)]
                    D1vsMO = round(((daily["Close"].iloc[0] / monthly["Open"].iloc[0]) - 1) * 100, 1)
                    q = (daily.index[0].month - 1) // 3 + 1
                    quarter = timeframes[2][(timeframes[2].index.year == daily.index[0].year) & (timeframes[2].index.month == (3*(q-1))+1)]
                    D1vsQO = round(((daily["Close"].iloc[0] / quarter["Open"].iloc[0]) - 1) * 100, 1)
                    yearly = timeframes[2][(timeframes[2].index.year == daily.index[0].year) & (timeframes[2].index.month == 1)]
                    D1vsYO = round(((daily["Close"].iloc[0] / yearly["Open"].iloc[0]) - 1) * 100, 1)
                    D0volume_percentil = stats.percentileofscore(daily_extensions["Volume"].dropna(), df["Volume"].iloc[i], kind='rank')
                    D1volume_percentil = stats.percentileofscore(daily_extensions["Volume"].dropna(), daily["Volume"].iloc[0], kind='rank')
                    row = [symbol, df.index[i], df.index[i].day, ((df.index[i].month - 1) % 3) + 1, D1vsMO, D1vsQO, D1vsYO, round(D0volume_percentil,0), round(D1volume_percentil,0), D0incr12, D1incr12, round(d10,0), round(d20,0), round(w10,0), round(rsi,0), upsideP95ext10,  upsideP99ext10] + golden_cross_performance(df["Close"].iloc[i], daily)
                    golden_crosses.append(row)
        df_stats = pd.DataFrame(golden_crosses, columns=columns)
        if not df_stats.empty:
            return df_stats
    return pd.DataFrame() # calcular la volatilidad del activo general y actual?    
    

def golden_cross_screener(t):
    try:
        symbols_aux = get_sp500_symbols() + get_nasdaq_non_sp500() + get_commodities_symbols() + get_crypto_symbols() + get_china_symbols() + get_japan_adrs_symbols() + get_european_symbols()
        symbols = list(dict.fromkeys(symbols_aux))
        golden_crosses = pd.DataFrame()
        for symbol in symbols:            
            print(symbol)
            data_aux = preparing_timeframes(symbol, "")
            data = calculation_ema_extension(data_aux)
            if len(data[0]) >= 2000:
                try:
                    df_symbol = calculation_golden_crosses_history(symbol, data, t)
                    if not df_symbol.empty:
                        golden_crosses = pd.concat([golden_crosses, df_symbol], ignore_index=True)
                except:
                    pass
        print(golden_crosses)
        golden_crosses["mx1wk"] = golden_crosses[["D2High", "D3High", "D4High", "D5High"]].max(axis=1)
        golden_crosses["min1wk"] = golden_crosses[["D2Low", "D3Low", "D4Low", "D5Low"]].min(axis=1)
        golden_crosses["MoveToCatch"] = round(golden_crosses["mx1wk"] - golden_crosses["D1Close"],2)
        golden_crosses["SL"] = round(golden_crosses["min1wk"] - golden_crosses["D1Close"],2)
        golden_crosses["R:R"] = round(golden_crosses["MoveToCatch"] / golden_crosses["SL"], 2)
        df_ordered = golden_crosses.sort_values(by="mx1wk", ascending=False)
        print("SET-UPS TOTALES", len(df_ordered), round(df_ordered["mx1wk"].mean(), 2), round(df_ordered["min1wk"].mean(), 2))
        df_ordered.to_csv("excels/golden_crosses.csv")
        return df_ordered 
    except Exception as e:
        print(e)   


def relative_strenght_screener():
    pass


def row_stats(data):
    try:
        df = data[0].copy()
        d10 = stats.percentileofscore(df["extension_ema10"].dropna(), df["extension_ema10"].iloc[-1], kind='rank')
        d20 = stats.percentileofscore(df["extension_ema20"].dropna(), df["extension_ema20"].iloc[-1], kind='rank')
        w10 = stats.percentileofscore(data[1]["extension_ema10"].dropna(), data[0]["extension_ema10"].iloc[-1], kind='rank')
        upsideP95ext10 = round(df["extension_ema10"].quantile(0.95) - df["extension_ema10"].iloc[-1], 1)
        upsideP99ext10 = round(df["extension_ema10"].quantile(0.99) - df["extension_ema10"].iloc[-1], 1)
        monthly = data[2][(data[2].index.year == df.index[-1].year) & (data[2].index.month == df.index[-1].month)]
        returnMO = round(((df["Close"].iloc[-1] / monthly["Open"].iloc[0]) - 1) * 100, 1)
        returnMOLast = round(((df["Close"].iloc[-2] / monthly["Open"].iloc[0]) - 1) * 100, 1)
        q = (df.index[-1].month - 1) // 3 + 1
        quarter = data[2][(data[2].index.year == df.index[-1].year) & (data[2].index.month == q)]
        returnQO = round(((df["Close"].iloc[-1] / quarter["Open"].iloc[0]) - 1) * 100, 1)
        returnQOLast = round(((df["Close"].iloc[-2] / quarter["Open"].iloc[0]) - 1) * 100, 1)
        yearly = data[2][(data[2].index.year == df.index[-1].year) & (data[2].index.month == 1)]
        returnYO = round(((df["Close"].iloc[-1] / yearly["Open"].iloc[0]) - 1) * 100, 1)
        returnYOLast = round(((df["Close"].iloc[-2] / yearly["Open"].iloc[0]) - 1) * 100, 1)
        volume_percentil = round(stats.percentileofscore(df["Volume"].dropna(), df["Volume"].iloc[-1], kind='rank'), 1)
        xEMA12 = round(((df["EMA_12"].iloc[-1]/df["EMA_12"].iloc[-2])-1)*100, 2)
        DAY = df.index[-1].day
        MonthQ = ((df.index[-1].month - 1) % 3) + 1
        D1Close = round(((df["Close"].iloc[-1] / df["Close"].iloc[-2]) - 1) * 100, 1)
        row = [returnMO, returnQO, returnYO, returnMOLast, returnQOLast, returnYOLast, round(d10,0), round(d20,0), round(w10,0), upsideP95ext10, upsideP99ext10, xEMA12, volume_percentil, D1Close, DAY, MonthQ]
        return row
    except Exception as e:
        print(e)
        return False


def calculation_12_25_cross():
    columns = ["Symbol", "%MonthLast", "%QuarterLast", "%YearLast", "%Month", "%Quarter", "%Year", "Ext10d", "Ext20d", "Ext10w", "Ext10dp95", "Ext10dp99", "xEma12", "Vol", "D1Close", "Day", "Month(Q)"]
    planning = pd.DataFrame(columns=columns)
    execution = pd.DataFrame(columns=columns)
    symbols_aux = get_sp500_symbols() + get_nasdaq_non_sp500() + get_commodities_symbols() + get_crypto_symbols() + get_china_symbols() + get_japan_adrs_symbols() + get_european_symbols()
    symbols = list(dict.fromkeys(symbols_aux))

    for symbol in symbols:
        print(symbol)
        try:
            data_aux = preparing_timeframes(symbol, "")
            data = calculation_ema_extension(data_aux)
            parameters = row_stats(data)
            if parameters:
                display = [symbol] + parameters
                if golden_cross(data[0][-2:].copy()):
                    planning.loc[len(planning)] = display
                elif golden_cross(data[0][-3:-1].copy()):
                    execution.loc[len(execution)] = display
        except Exception as e:
            print(e)    
    planning = planning[(planning["xEma12"]>=0.1) & (planning["%Quarter"]>=-3) & (planning["Ext10dp99"]>=2)] # & (((planning["DAY"]>=1) & (planning["DAY"]<=10)) | ((planning["DAY"]>=25) & (planning["DAY"]<=31)))]  
    execution = execution[(execution["xEma12"]>=0.1) & (execution["%Quarter"]>=0) & (execution["Ext10dp99"]>=2)] # & (((execution["DAY"]>=1) & (execution["DAY"]<=10)) | ((execution["DAY"]>=25) & (execution["DAY"]<=31)))]  
    # & (planning["D1Close"]>=1) , & (planning["MONTH(Q)"] < 3)
    return planning, execution



def test_strategy(symbol):
    try:
        test = []
        aux_timeframes = getDataStock(symbol)  
        aux_timeframes2 = preparingData(aux_timeframes)
        timeframes = calculation_ema_extension(aux_timeframes2)

        for a in range(0, 1):
            #h1 = round(random.uniform(0.85, 0.96),2) #h2 = round(random.uniform(0.97, 0.995),2)
            #phigh = timeframes[0][:-365]["extension_low_ema10"].quantile(h1) #0.93 #phigh_stop = timeframes[0][:-365]["extension_high_ema10"].quantile(h2) #0.96
            l1 = round(random.uniform(0.2, 0.02),2)
            l2 = round(random.uniform(l1, 0.01),2)
            plow = timeframes[0][:-730]["extension_low_ema10"].quantile(l1)
            plow_stop = timeframes[0][:-730]["extension_low_ema10"].quantile(l2) 
            #mean = timeframes[0][:-730]["extension_low_ema10"].mean()
            std = timeframes[0][:-730]["extension_low_ema10"].std()
            #plow = round(mean - std - std, 4)
            #plow = timeframes[0][:-730]["extension_low_ema10"].quantile(0.07)
            #plow_stop = round(mean - std - std - (std/2), 4)
            data = last_X_years(timeframes, 2) 
            df = data[0]
            entry, take_profit, stop_loss = 0, 0, 0
            long, short = False, False
            cash = 1000
            rows = []

            for i in range(1, len(df)):
                if long or short:
                    if long:
                        if df["High"].iloc[i] > take_profit and df["Low"].iloc[i] > stop_loss:
                            profit = cash * ((take_profit/entry)-1)
                            cash = cash + profit - 0.1
                            rows.append({"side": "long", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": profit, "portfolio": cash})
                            print("CLOSED LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "PROFIT:", profit)
                            long = False
                        elif df["High"].iloc[i] < take_profit and df["Low"].iloc[i] < stop_loss:
                            loss = cash * ((stop_loss / entry) - 1)
                            cash = cash + loss - 0.1
                            rows.append({"side": "long", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": loss, "portfolio": cash})
                            print("STOPPED LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "LOSS:", loss)
                            long = False
                        elif df["High"].iloc[i] > take_profit and df["Low"].iloc[i] < stop_loss:
                            rows.append({"side": "cancelled", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": 0, "portfolio": cash})
                            long = False
                        else:
                            correction = round((1-(0.001*abs(std))), 3)
                            take_profit = ((df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]) * correction
                            stop_loss = df["EMA_10"].iloc[i] * (1+(plow_stop/100))  

                    #elif short:
                    #    if df["Low"].iloc[i] < take_profit and df["High"].iloc[i] < stop_loss:
                    #        profit = (cash * (1 - (take_profit / entry)))
                    #        cash = cash + profit - 1
                    #        rows.append({"side": "short", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": profit, "portfolio": cash})
                    #        print("CLOSED SHORT", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "PROFIT:", profit)
                    #        short = False
                    #    elif df["Low"].iloc[i] > take_profit and df["High"].iloc[i] > stop_loss:
                    #        loss = cash * (1 - (stop_loss / entry))
                    #        cash = cash + loss - 1
                    #        rows.append({"side": "short", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": loss, "portfolio": cash})
                    #        print("STOPPED SHORT", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "LOSS:", loss)
                    #        short = False
                    #        stopped = True
                    #    elif df["High"].iloc[i] < take_profit and df["Low"].iloc[i] > stop_loss:
                    #        rows.append({"side": "cancelled", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": 0, "portfolio": cash})
                    #        short = False
                    #    else:
                    #        take_profit = ((df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]) * 1.0025
                    #        #stop_loss = df["EMA_10"].iloc[i] * (1+(phigh_stop/100)) 
                else:                
                    if df["extension_low_ema10"].iloc[i] <= plow:
                        long = True
                        entry = df["EMA_10"].iloc[i] * (1+(plow/100)) #(df["Close"].iloc[i] + df["Low"].iloc[i]) / 2
                        take_profit = ((df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]) * 0.995
                        stop_loss = df["EMA_10"].iloc[i] * (1+(plow_stop/100)) 
                        print("LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss)
                        if df["extension_low_ema10"].iloc[i] <= plow_stop:  
                            loss = cash * ((stop_loss / entry) - 1)
                            cash = cash + loss - 0.1
                            rows.append({"side": "long", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": loss, "portfolio": cash})
                            print("STOPPED LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "LOSS:", loss)
                            long = False

                        #elif df["extension_high_ema10"].iloc[i] >= phigh:
                        #    short = True
                        #    entry = df["EMA_10"].iloc[i] * (1+(phigh/100)) #(df["Close"].iloc[i] + df["High"].iloc[i]) / 2
                        #    take_profit = (df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]
                        #    stop_loss = df["EMA_10"].iloc[i] * (1+(phigh_stop/100)) 
                        #    print("SHORT", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss)
            df_strategy = pd.DataFrame(rows)
            if not df_strategy.empty:
                df_win = df_strategy[df_strategy["outcome"] > 0].copy()
                if not df_win.empty:
                    df_win["Return"] = round((df_win["outcome"] / (df_win["portfolio"] - df_win ["outcome"])) * 100,1)
                    returnPerWin = df_win["Return"].mean()
                else:
                    returnPerWin = 0
                df_loss = df_strategy[df_strategy["outcome"] < 0].copy()
                df_cancelled = df_strategy[df_strategy["outcome"] == 0].copy() #que pasa si entro cuando viene rebotando de abajo, por si la primera caida es muy violenta
                if len(df_win) == 0:
                    hitrate = 0
                elif len(df_loss) == 0:
                    hitrate = 1
                else:
                    hitrate = round(len(df_win)/(len(df_loss)+len(df_win)),1)
                test.append({"symbol": symbol, "portfolio": round(cash,1), "trades": len(df_strategy), "hitrate": hitrate, "%ReturnWins": round(returnPerWin,1), "cancelled": len(df_cancelled), "plow": plow, "plow_stop": plow_stop, "correction": correction})    
        print("processing dataframe to show")
        if len(test) > 0:
            df = pd.DataFrame(test)   
            df = df.sort_values(by='portfolio', ascending=False)
            return df.iloc[0].to_dict()
        else:
            return False
    except Exception as e:
        print(e)
        return False


def test_strategy_all_symbols():
    symbols = get_hyperliquid_symbols() + get_forex_symbols()
    with ProcessPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(test_strategy, symbols))    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df = df.sort_values(by='portfolio', ascending=False)
    print("plow", df["plow"].mean(), "plow_stop", df["plow_stop"].mean()) #, "phigh", df["phigh"].mean(), "phigh_stop", df["phigh_stop"].mean())
    df.to_csv("test_strategy_symbols.csv") 
    return df


def calculation_patterns():
    try:
        all_patterns = ['GGG','GGR','GRG','GRR','RRR','RRG','RGR','RGG']
        green_patterns = ['GGG', 'GGR', 'GRG', 'GRR']
        red_patterns   = ['RRR', 'RRG', 'RGR', 'RGG']
        gg_patterns = ['GGG', 'GGR']
        gr_patterns = ['GRG', 'GRR']
        rr_patterns = ['RRR', 'RRG']
        rg_patterns = ['RGR', 'RGG']
        symbols = getSymbols()
        data = []
        for symbol in symbols:
            data_aux = preparing_timeframes(symbol, "monthly")
            monthly = data_aux[2].copy()
            monthly['year']       = monthly.index.year
            monthly['quarter']    = monthly.index.quarter
            monthly['month_of_q'] = monthly.index.month - (monthly['quarter'] - 1) * 3
            results = []
            for (year, quarter), group in monthly.groupby(['year', 'quarter']):
                group = group.sort_values('month_of_q')
                if len(group) != 3:
                    continue
                pattern = ''.join(group['type'].map({'Green': 'G', 'Red': 'R'}).tolist())
                results.append({
                    'symbol':  symbol,
                    'year':    year,
                    'quarter': quarter,
                    'pattern': pattern,
                })
            df_patterns = pd.DataFrame(results)
            if not df_patterns.empty:
                pattern_counts = (df_patterns.groupby('pattern').size().reindex(all_patterns, fill_value=0))
                total = pattern_counts.sum()
                pattern_formatted = pattern_counts.apply(lambda x: f"{round(x/total*100)}% ({x})" if total > 0 else "0% (0)")
                row = {'symbol': symbol} | pattern_formatted.to_dict()
                data.append(row)
                total_green = pattern_counts[green_patterns].sum()
                total_red   = pattern_counts[red_patterns].sum()
                pattern_green = pattern_counts[green_patterns].apply(lambda x: f"{round(x/total_green*100)}% ({x})" if total_green > 0 else "0% (0)")
                pattern_red   = pattern_counts[red_patterns].apply(lambda x: f"{round(x/total_red*100)}% ({x})"   if total_red   > 0 else "0% (0)")
                row = {'symbol': symbol} | pattern_green.to_dict() | pattern_red.to_dict()
                data.append(row)
                total_gg = pattern_counts[gg_patterns].sum()
                total_gr = pattern_counts[gr_patterns].sum()
                total_rr = pattern_counts[rr_patterns].sum()
                total_rg = pattern_counts[rg_patterns].sum()                
                pattern_gg = pattern_counts[gg_patterns].apply(lambda x: f"{round(x/total_gg*100)}% ({x})" if total_gg > 0 else "0% (0)")
                pattern_gr = pattern_counts[gr_patterns].apply(lambda x: f"{round(x/total_gr*100)}% ({x})" if total_gr > 0 else "0% (0)")
                pattern_rr = pattern_counts[rr_patterns].apply(lambda x: f"{round(x/total_rr*100)}% ({x})" if total_rr > 0 else "0% (0)")
                pattern_rg = pattern_counts[rg_patterns].apply(lambda x: f"{round(x/total_rg*100)}% ({x})" if total_rg > 0 else "0% (0)")
                row = {'symbol': symbol} | pattern_gg.to_dict() | pattern_gr.to_dict() | pattern_rr.to_dict() | pattern_rg.to_dict()
                data.append(row)
        return pd.DataFrame(data)
    except Exception as e:
        print(e)


def calculation_drawdowns_ema_10_20(N=5, min_days_above=5, vol_k=0.2, min_occurrences=100, neutral_threshold = 0.01):
    assets = Assets()
    symbols = get_sp500_symbols() + get_nasdaq_non_sp500() + get_china_symbols() + get_european_symbols() + get_commodities_symbols() + get_crypto_symbols()
    symbols = list(dict.fromkeys(symbols))
    rows = []

    for symbol in symbols:
        print("EMA DRAWDOWN:", symbol)
        try:
            data_aux = preparing_timeframes(symbol, "")
            daily = data_aux[0].copy()
            # volatilidad rolling: std de returns diarios en ventana 20 dias
            daily["vol"] = daily["Close"].pct_change().rolling(20).std()
            daily = daily.iloc[20:].reset_index(drop=False)

            row = {"Symbol": assets.name_sustitution(symbol)}
            row["Vol Avg%"] = round(daily["vol"].mean() * 100, 3)

            variants = [("EMA_10", "EMA10C", False), ("EMA_10", "EMA10L", True)]
            for ema_col, label, use_low in variants:
                buckets = [[] for _ in range(N + 1)]  # D0 + D1..DN
                tol_i = daily["vol"].iloc[0] * vol_k
                above = daily["Close"].iloc[0] >= daily[ema_col].iloc[0] * (1 - tol_i)
                days_above = 1 if above else 0
                tols_used = []

                for i in range(1, len(daily) - N):
                    tol_i = daily["vol"].iloc[i] * vol_k
                    now_above = daily["Close"].iloc[i] >= daily[ema_col].iloc[i] * (1 - tol_i)
                    if days_above >= min_days_above and not now_above:
                        ref = daily[ema_col].iloc[i] * (1 - (tol_i*1.1))
                        tols_used.append(tol_i * 100)
                        price_d0 = daily["Low"].iloc[i] if use_low else daily["Close"].iloc[i]
                        buckets[0].append(((price_d0 - ref) / ref) * 100)
                        for d in range(N):
                            price_d = daily["Low"].iloc[i + 1 + d] if use_low else daily["Close"].iloc[i + 1 + d]
                            buckets[d + 1].append(((price_d - ref) / ref) * 100)
                    days_above = days_above + 1 if now_above else 0
                    above = now_above

                row[f"{label} Occurrences"] = f"{len(buckets[0])}n"
                row[f"{label} Avg Tol%"] = round(np.mean(tols_used), 3) if tols_used else 0
                row[f"{label} D0 Avg"] = round(np.mean(buckets[0]), 2) if buckets[0] else 0
                row[f"{label} D0 Med"] = round(np.median(buckets[0]), 2) if buckets[0] else 0
                for d in range(N):
                    row[f"{label} D{d+1} Avg"] = round(np.mean(buckets[d+1]), 2) if buckets[d+1] else 0
                    row[f"{label} D{d+1} Med"] = round(np.median(buckets[d+1]), 2) if buckets[d+1] else 0

            # EMA10T: low toca 1x tolerancia, referencia en ese nivel, D0 = close del día
            buckets_t = [[] for _ in range(N + 1)]
            tols_used_t = []
            tol_i = daily["vol"].iloc[0] * vol_k
            days_above_t = 1 if daily["Close"].iloc[0] >= daily["EMA_10"].iloc[0] * (1 - tol_i) else 0
            for i in range(1, len(daily) - N):
                tol_i = daily["vol"].iloc[i] * vol_k
                ema_thresh = daily["EMA_10"].iloc[i] * (1 - tol_i)
                ref_t = daily["EMA_10"].iloc[i] * (1 - tol_i)
                low_touches = daily["Low"].iloc[i] < ref_t
                now_above = daily["Close"].iloc[i] >= ema_thresh
                if days_above_t >= min_days_above and low_touches:
                    tols_used_t.append(tol_i * 100)
                    buckets_t[0].append(((daily["Close"].iloc[i] - ref_t) / ref_t) * 100)
                    for d in range(N):
                        buckets_t[d + 1].append(((daily["Close"].iloc[i + 1 + d] - ref_t) / ref_t) * 100)
                days_above_t = days_above_t + 1 if now_above else 0

            row["EMA10T Occurrences"] = f"{len(buckets_t[0])}n"
            row["EMA10T Avg Tol%"] = round(np.mean(tols_used_t), 3) if tols_used_t else 0
            row["EMA10T D0 Avg"] = round(np.mean(buckets_t[0]), 2) if buckets_t[0] else 0
            row["EMA10T D0 Med"] = round(np.median(buckets_t[0]), 2) if buckets_t[0] else 0
            for d in range(N):
                row[f"EMA10T D{d+1} Avg"] = round(np.mean(buckets_t[d+1]), 2) if buckets_t[d+1] else 0
                row[f"EMA10T D{d+1} Med"] = round(np.median(buckets_t[d+1]), 2) if buckets_t[d+1] else 0
            rows.append(row)
        except Exception as e:
            print(f"Error {symbol}: {e}")

    df = pd.DataFrame(rows)

    def parse_count(val):
        try:
            return int(str(val).replace("n", ""))
        except:
            return 0

    neutral_threshold = 0.1

    def build_summary_rows(group_df, prefix, N, neutral_threshold):
        r_g = {"Symbol": f"{prefix} G"}
        r_r = {"Symbol": f"{prefix} R"}
        for label in ["EMA10C", "EMA10L", "EMA10T"]:
            occ_col = f"{label} Occurrences"
            eligible = group_df
            counts = []
            for day_label in ["D0"] + [f"D{d+1}" for d in range(N)]:
                col_avg = f"{label} {day_label} Avg"
                col_med = f"{label} {day_label} Med"
                for r in [r_g, r_r]:
                    r.setdefault(col_avg, "")
                    r.setdefault(col_med, "")

                vals_avg = eligible[col_avg]
                nn_avg = vals_avg[abs(vals_avg) > neutral_threshold]
                g_a = (nn_avg > neutral_threshold).sum(); r_a = (nn_avg < -neutral_threshold).sum()
                d_a = g_a + r_a; counts.append(int(d_a))
                r_g[col_avg] = f"{round((g_a/d_a)*100,1)}%" if d_a > 0 else "0%"
                r_r[col_avg] = f"{round((r_a/d_a)*100,1)}%" if d_a > 0 else "0%"

                vals_med = eligible[col_med]
                nn_med = vals_med[abs(vals_med) > neutral_threshold]
                g_m = (nn_med > neutral_threshold).sum(); r_m = (nn_med < -neutral_threshold).sum()
                d_m = g_m + r_m
                r_g[col_med] = f"{round((g_m/d_m)*100,1)}%" if d_m > 0 else "0%"
                r_r[col_med] = f"{round((r_m/d_m)*100,1)}%" if d_m > 0 else "0%"

            for r in [r_g, r_r]:
                r[occ_col] = f"{len(eligible)}n"
                r[f"{label} Avg Tol%"] = ""
        return [r_g, r_r]

    # filtrar por min_occurrences primero, luego dividir por beta
    df_assets = df[df["Vol Avg%"].notna() & (df["Vol Avg%"] > 0)].copy()
    df_assets = df_assets[df_assets["EMA10C Occurrences"].apply(parse_count) >= min_occurrences]
    t25 = df_assets["Vol Avg%"].quantile(0.2)
    t75 = df_assets["Vol Avg%"].quantile(0.8)
    low_vol  = df_assets[df_assets["Vol Avg%"] <= t25]
    mid_vol  = df_assets[(df_assets["Vol Avg%"] > t25) & (df_assets["Vol Avg%"] <= t75)]
    high_vol = df_assets[df_assets["Vol Avg%"] > t75]

    summary_rows = (
        build_summary_rows(df_assets, "ALL", N, neutral_threshold) +
        build_summary_rows(high_vol,  "HIGH", N, neutral_threshold) +
        build_summary_rows(mid_vol,   "MID",  N, neutral_threshold) +
        build_summary_rows(low_vol,   "LOW",  N, neutral_threshold)
    )

    df_summary = pd.DataFrame(summary_rows)
    df = pd.concat([df_summary, df], ignore_index=True)

    df.to_csv("excels/drawdowns_ema_10_20.csv")
    print(df)
    return df


def calculation_ema_trends():
    symbols = get_sp500_symbols() + get_nasdaq_non_sp500()# + get_china_symbols() + get_european_symbols() + get_commodities_symbols() + get_crypto_symbols()
    symbols = list(dict.fromkeys(symbols))
    rows = []
    
    for symbol in symbols:
        print("EMA DRAWDOWN:", symbol)
        try:
            data_aux = preparing_timeframes(symbol, "")
        except Exception as e:
            print(e)


def calculation_trend_deviation(timeframes):
    #timeframes = preparing_timeframes(symbol, "")
    df = timeframes[0].copy()
    df["EMA10_Absortion"] = np.where(((df["Open"]*0.998) > df["EMA_10"]) & ((df["Close"]*0.998) > df["EMA_10"]) & ((df["Low"]*1.002) < df["EMA_10"]), True, False)
    df["EMA10_Rejection"] = np.where(((df["Open"]*1.002) < df["EMA_10"]) & ((df["Close"]*1.002) < df["EMA_10"]) & ((df["High"]*0.998) > df["EMA_10"]), True, False)
    df["EMA20_Absortion"] = np.where(((df["Open"]*0.998) > df["EMA_20"]) & ((df["Close"]*0.998) > df["EMA_20"]) & ((df["Low"]*1.002) < df["EMA_20"]), True, False)
    df["EMA20_Rejection"] = np.where(((df["Open"]*1.002) < df["EMA_20"]) & ((df["Close"]*1.002) < df["EMA_20"]) & ((df["High"]*0.998) > df["EMA_20"]), True, False)
    df["MinClose1"] = pd.concat([df["Close"].shift(-1)], axis=1).min(axis=1)
    df["MinClose2"] = pd.concat([df["Close"].shift(-1), df["Close"].shift(-2)], axis=1).min(axis=1)
    df["MinClose3"] = pd.concat([df["Close"].shift(-1), df["Close"].shift(-2), df["Close"].shift(-3)], axis=1).min(axis=1)
    df["MaxClose"] = pd.concat([df["Close"].shift(-1),df["Close"].shift(-2),df["Close"].shift(-3)], axis=1).max(axis=1)
    df["Low3Days"] = (pd.concat([df["Low"].shift(-1),df["Low"].shift(-2),df["Low"].shift(-3)], axis=1).min(axis=1) / df["EMA_10"] - 1) * 100
    df["Max3Days"] = (pd.concat([df["High"].shift(-1),df["High"].shift(-2),df["High"].shift(-3)], axis=1).max(axis=1) / df["EMA_10"] - 1) * 100
    df["LowGrab"] = (pd.concat([df["Low"].shift(-1),df["Low"].shift(-2),df["Low"].shift(-3)], axis=1).min(axis=1) / df["Low"] - 1) * 100
    df["DeviationEMA"] = round(((df["Low"] / df["EMA_10"])-1)*100,1)
    return df


def candle_pattern(timeframes):
    try:
        timeframe = ["daily", "weekly", "monthly"]
        columns = ["timeframe", "type", "p05", "p25", "p50", "p75", "p95"]
        rows = []
        for i, df in enumerate(timeframes):
            df = df[df["Volatility"]>=np.quantile(df["Volatility"], 0.25)].copy()
            for wick in ["Upper_wick", "Lower_wick"]:
                df1 = df[df[wick]>=0.6].copy()
                df2 = df[df[wick]>=0.8].copy()
                for df_aux in [df1, df2]:
                    new_row = [timeframe[i]]
                    new_row.append(wick)
                    for n in [0.05, 0.25, 0.5, 0.75, 0.95]:
                        new_row.append(round(np.quantile(df_aux["Return_NextDay"], n),2))
                    rows.append(new_row)
        df = pd.DataFrame(rows, columns=columns)
        return df
    except Exception as e:
        print(e)


    



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
    



        

