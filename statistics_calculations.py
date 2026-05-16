import numpy as np
from functions import * 
import pandas as pd
from data import *
from scipy import stats

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
        probability = next_candle_probability(data[cont].iloc[i]["type"], probability_green, probability_red, num+1)
        probability_list.append(probability)
        color_list.append("blue")
        probability = next_candle_probability(data[cont].iloc[i]["type"], probability_green, probability_red, num+2)
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

   
def cycle_dynamics_calculation(symbol, df, open, marginK, timeframe):  
    try:
        timeframe = timeframe.upper()
        print(timeframe)
        if timeframe == "WEEKLY":
            m = 0.8
        elif timeframe == "MONTHLY":
            m = 0.02
        elif timeframe == "QUARTERLY":
            m = 0.025
        elif timeframe == "YEARLY": 
            m = 0.03
        flips, lastFlip, side = 0, 1, 0
        sides = {1:0, 0:1}
        if df.iloc[0]["Close"] >= open:
            side = 1
        else:
            side = 0
        for k in range (1, len(df)):
            vol_ema = df.iloc[k]["Vol_EMA"]
            aux_margin = np.exp(vol_ema * marginK / 100)
            if aux_margin > 1.03:
                upper_threshold = open * 1.025
                lower_threshold = open * 0.975
            elif aux_margin < m:
                upper_threshold = open * (1 + m)
                lower_threshold = open * (1 - m)
            else:
                upper_threshold = open * np.exp(vol_ema * marginK / 100)
                lower_threshold = open * np.exp(-vol_ema * marginK / 100)

            if ((df.iloc[k]["Close"] > upper_threshold) and (side == 0)) or ((df.iloc[k]["Close"] < lower_threshold) and (side == 1)):
                side = sides[side]
                flips = flips + 1
                lastFlip = k + 1                
                print(symbol, "|| FLIP", " || ", df.index[k], " || ", df.iloc[k]["Close"], "|| Margin to count the flip", round(((upper_threshold - open)/open)*100, 2), " || ", round(vol_ema,1), "(", round(aux_margin,1), ")")
        return flips, lastFlip
    except Exception as e:
        print(e) 


def cycle_dynamics(symbol, data, lower_timeframe):
    timeframe = ["WEEKLY", "MONTHLY", "QUARTERLY"]
    parameters = []
    if lower_timeframe == "daily":
        timeframe = ["WEEKLY", "MONTHLY", "QUARTERLY"]
        margin = 0.125
        t = 0
        parameters = [pd.Timedelta(days=7), pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3)]
    elif lower_timeframe == "weekly":
        timeframe = ["MONTHLY", "QUARTERLY", "YEARLY"]
        margin = 0.075
        t = 1
        parameters = [pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3), pd.offsets.MonthBegin(12)]
    elif lower_timeframe == "monthly":
        timeframe = ["QUARTERLY", "YEARLY"]
        margin = 0.05
        t = 2
        parameters = [pd.offsets.MonthBegin(3), pd.offsets.MonthBegin(12)]
    
    LT = data[t][14:].copy()
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
        
        cycle = pd.DataFrame(columns=["Date", "Open", "Flips", "LastFlip", "Direction", "Return"])

        for x in range(0, len(HT)-1):
            df = LT[(LT.index >= HT.index[x]) & (LT.index < HT.index[x+1])]
            if df.empty:
                continue
            if lower_timeframe == "weekly":
                df_partialweek = MT[(MT.index >= HT.index[x]) & (MT.index < df.index[0])]
                if not df_partialweek.empty and len(df_partialweek) == 4:
                    df = merge_partialweek(df, df_partialweek)
            print(timeframe[i-1-t], "| OPEN:", HT.iloc[x]["Open"], "| CLOSE:", HT.iloc[x]["Close"], "| DATE:", HT.index[x])
            if lower_timeframe == "weekly":
                print(df)
            params = cycle_dynamics_calculation(symbol, df, HT.iloc[x]["Open"], margin, timeframe[p])
            cycle.loc[len(cycle)] = [HT.index[x], round(HT.iloc[x]["Open"], 1), params[0], params[1], HT.iloc[x]["type"], HT.iloc[x]["Return"]]

        df = LT[(LT.index >= HT.index[-1])]
        if not df.empty:
            if lower_timeframe == "weekly":
                df_partialweek = MT[(MT.index >= HT.index[x]) & (MT.index < df.index[0])]
                if not df_partialweek.empty and len(df_partialweek) == 4:
                    df = merge_partialweek(df, df_partialweek)
            params = cycle_dynamics_calculation(symbol, df, HT.iloc[-1]["Open"], margin, timeframe[p])
            cycle.loc[len(cycle)] = [HT.index[-1], round(HT.iloc[-1]["Open"],1), params[0], params[1], HT.iloc[x]["type"], HT.iloc[x]["Return"]]
        cycle.set_index("Date", inplace=True)
        timeframes_cycles.append(cycle)
        p += 1
    return timeframes_cycles


def dataframe_candle_split(data):
    data_green = []
    data_red = []
    for df in data:
        data_green.append(df[df["Direction"] == "Green"].copy())
        data_red.append(df[df["Direction"] == "Red"].copy())
    return data_green, data_red


def calculation_cycle_flips_all_symbols(lower_timeframe, symbols):
    try:
        timeframes_name = ["weekly", "monthly", "quarterly"]
        if lower_timeframe == "daily":
            timeframes_name = ["weekly", "monthly", "quarterly"]
        elif lower_timeframe == "weekly":
            timeframes_name = ["monthly", "quarterly", "yearly"]
        elif lower_timeframe == "monthly":
            timeframes_name = ["quarterly", "yearly"]
        columns = []
        columns.append("Stock")
        for i in range (0,3):
            columns.append(str(i) + " " + timeframes_name[0] + "_F")
        for i in range (0,5):
            columns.append(str(i) + " " + timeframes_name[1] + "_F")
        columns.append("LF" + timeframes_name[1] + "_p50") 
        if len(timeframes_name) > 2:
            for i in range (0,5):
                columns.append(str(i) + " " + timeframes_name[2] + "_F")
            columns.append("5+ " + timeframes_name[2] + "_F")
            columns.append("LF" + timeframes_name[2] + "_p50") 
        df = pd.DataFrame(columns=columns)
        df_detail = pd.DataFrame(columns=columns)

        for symbol in symbols:
            print(symbol)
            aux_timeframes = getDataStock(symbol)    
            aux_timeframes_2= last_X_years(aux_timeframes, 30)
            timeframes = create_hightimeframes(aux_timeframes_2, lower_timeframe)
            data_candles = preparingData(timeframes) 
            dfs = cycle_dynamics(symbol, data_candles, lower_timeframe)

            # 1. Define la configuración para cada DataFrame en dfs # [rango_reindex, indices_a_guardar_en_df_final, usar_quantile]
            config = [
                [[0, 1, 2],    False], # DataFrame 0
                [[0, 1, 2, 3, 4], True], # DataFrame 1 
                [[0, 1, 2, 3, 4, 5], True]  # DataFrame 2
            ]
            new_row = [symbol]

            for i, df_item in enumerate(dfs):
                flips_to_show, use_quantile = config[i]

                counts = df_item["Flips"].value_counts().reindex(range(10), fill_value=0)
                total = counts.sum()

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
                symbol_name = symbol+names[x]
                row_details = [symbol_name]
                row_details = append_values_row(row_details, counts_A, 3)
                row_details = append_values_row(row_details, counts_B, 5)
                row_details.append(p_01)

                if len(timeframes_name) > 2:
                    counts_C = df_aux[2]["Flips"].value_counts().reindex(range(10), fill_value=0).to_dict()
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
        return df
    except Exception as e:
        print(e)


def current_cycle_flips_all_symbols(lower_timeframe):
    try:
        timeframes_name = ["weekly", "monthly", "quarterly"]
        if lower_timeframe == "daily":
            t = 0
            margin = 0.125
            timeframes_name = ["weekly", "monthly", "quarterly"]
        elif lower_timeframe == "weekly":
            t = 1
            margin = 0.1
            timeframes_name = ["monthly", "quarterly", "yearly"]
        elif lower_timeframe == "monthly":
            t = 2
            margin = 0.01
            timeframes_name = ["quarterly", "yearly"]

        symbols = getSymbols()
        rows = []
        for symbol in symbols:
            row = {}
            print("i process", symbol)
            timeframes = getDataStock(symbol) # get data of ticker         
            timeframes = create_hightimeframes(timeframes, lower_timeframe)  
            data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values   
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
                flips, lastFlip = cycle_dynamics_calculation(symbol, lowerTimeframeCandles, open_price, margin, timeframes_name[p])
                if flips > 5:
                    flips = 5 #represent a 5+ or a cell with the actual number
                symbol_flips.append([flips, lastFlip])
                p += 1
            row = {"symbol": symbol}
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
    fechas = []
    valores = []
    
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


def screener_ema_extensions():
    try:
        symbols = getSymbols()
        col_name_ema = ["extension_ema10", "extension_ema20"]
        timeframes_name = ["D"]
        emas_name = ["EMA 10", "EMA 20"]
        rows = []
        num = 1
        for symbol in symbols:
            print("SCREENER PROCESSING", symbol, num)
            num = num + 1
            timeframes = getDataStock(symbol) 
            data = preparingData(timeframes) 
            timeframes = calculation_ema_extension(data)
            timeframes = timeframes[0]
            row = {"Stock": symbol, "Price": round(timeframes["Close"].iloc[-1],1)}
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
        longs_df = df[(df['P_D_EMA 10'] <= 30) & (df['P_D_EMA 20'] <= 30)].sort_values(by='TimeAway', ascending=False)
        shorts_df = df[(df['P_D_EMA 10'] >= 70) & (df['P_D_EMA 20'] >= 70)].sort_values(by='TimeAway', ascending=False)
        return longs_df, shorts_df
    df = pd.DataFrame(rows)
    longs_df = df[(df['P_D_EMA 10'] <= 30) & (df['P_D_EMA 20'] <= 30)].sort_values(by='TimeAway', ascending=False)
    shorts_df = df[(df['P_D_EMA 10'] >= 70) & (df['P_D_EMA 20'] >= 70)].sort_values(by='TimeAway', ascending=False)
    return longs_df, shorts_df


def calculation_average_deviation(data):
    timeframes = []
    for df in data:
        df = df.copy()
        df['Deviation'] = np.where(df['type'] == 'Green', ((df['Open'] - df['Low']) / df['Open'])*100, ((df['High'] - df['Open']) / df['Open'])*100)
        df = df[df['Deviation']>=0]
        timeframes.append(df)
    return timeframes 


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
        aux_timeframes = getDataStock(symbol) # get data of ticker  
        timeframes = preparingData(aux_timeframes)
        data = last_X_years(timeframes, 15)
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
            gaps_study.loc[len(gaps_study)] = [symbol, totalGaps, round(len(closedGaps)/totalGaps, 2), percentil_10, percentil_50, percentil_90] 
            print("END GAPS", symbol)
    gaps_study.to_csv("excels/gapsallsymbols.csv")
    return gaps_study


def calculation_cycle_peak_expansion(data, stock):
    dataframes = []
    dataframes_absolute = []
    try:
        timeframe = ["weekly", "monthly"]
        df_daily = data[0]
        for x in range(2, len(data)):
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
        symbols = getSymbols()
        timeframes = ["Weekly", "Monthly"]
        columns = ["Symbol", "Type", "Occurrences"]

        for p in [10,20,50,80,90]:
            name_column = timeframes[1] + " " + "p" + str(p)
            columns.append(name_column)

        peak_study = pd.DataFrame(columns=columns)
    
        for symbol in symbols:
            print(symbol)
            aux_timeframes = getDataStock(symbol) # get data of ticker  
            timeframes = preparingData(aux_timeframes)
            data = last_X_years(timeframes, 25)
            dataframes_symbol, dataframes_symbol_absolute = calculation_cycle_peak_expansion(data, symbol)
            df = dataframes_symbol[0].copy()
            df_absolute = dataframes_symbol_absolute[0].copy()
            df_green = df[df["Return"]>=0]
            df_red = df[df["Return"]<0]
            colour = ["Absolute", "Green", "Red"]
            k = 0
            for dataframe in (df_absolute, df_green, df_red):
                info = [symbol, colour[k], len(dataframe)]        
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
    rows = []
    symbols = get_hyperliquid_symbols()
    for symbol in symbols:
        print("CASH SESSION", symbol)
        try:
            aux_timeframes = getDataStock(symbol) # get data of ticker  
            timeframes = preparingData(aux_timeframes)
            print("preparingDataCompleted")
            data = last_X_years(timeframes, 3)
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
                    row["symbol"] = symbol
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

def calculation_open_momentum(timeframes):
    try:
        daily = timeframes[0].copy()
        daily['month_period'] = daily.index.tz_localize(None).to_period('M')
        monthly = timeframes[2].copy()
        monthly['month_period'] = monthly.index.tz_localize(None).to_period('M')
        start_period = monthly['month_period'].iloc[0]
        end_period = monthly['month_period'].iloc[-1]
        daily = daily[(daily['month_period'] >= start_period) & (daily['month_period'] <= end_period)]
        firstdays_df = daily.groupby('month_period').head(3)
        sum_retornos = firstdays_df.groupby('month_period')['Return'].sum()
        monthly['Added_Return_2D'] = monthly['month_period'].map(sum_retornos)
        return monthly 
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
    



        

