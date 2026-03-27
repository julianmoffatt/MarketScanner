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

   
# calculations of flips of a dataframe data around a given open
def cycle_dynamics_calculation(df, open):  
    flips, lastFlip, side = 0, 1, 0
    sides = {1:0, 0:1}
    margin = 0
    if df.iloc[0]["Close"] >= open:
        side = 1
    else:
        side = 0
    for k in range (1, len(df)):
        margin = (open * (df.iloc[k]["Volatility_Rolling"] * 0.075))
        close_fixed_bull = df.iloc[k]["Close"] - margin
        close_fixed_bear = df.iloc[k]["Close"] + margin
        if ((close_fixed_bull > open) and (side == 0)) or ((close_fixed_bear < open) and (side == 1)):
            side = sides[side]
            flips = flips + 1
            lastFlip = k + 1
            print("FLIP", df.index[k], df.iloc[k]["Close"])
    print("Margin to count the flip", margin)
    return flips, lastFlip


def cycle_dynamics(data, lower_timeframe):
    parameters = []
    if lower_timeframe == "daily":
        parameters = [pd.Timedelta(days=7), pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3)]
    elif lower_timeframe == "weekly":
        parameters = [pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3), pd.offsets.MonthBegin(12)]
    timeframes_cycles = []
    LT = data[0][14:].copy()
    end = []
    end.append(pd.to_datetime((data[1].index[-1] + parameters[0]), utc=True))
    end.append(pd.to_datetime((data[2].index[-1] + parameters[1]), utc=True))
    end.append(pd.to_datetime((data[3].index[-1] + parameters[2]), utc=True))
    timeframe = ["WEEKLY", "MONTHLY", "QUARTERLY"]

    for i in range (1, len(data)):
        HT = data[i].copy()
        LT = LT[LT.index < end[i-1]]
        cycle = pd.DataFrame(columns=["Date", "Open", "Flips", "LastFlip", "Direction", "Return"])
        for x in range(0, len(HT)-1):
            df = LT[(LT.index >= HT.index[x]) & (LT.index < HT.index[x+1])]
            if df.empty:
                continue
            print(timeframe[i-1], HT.iloc[x]["Open"], HT.iloc[x]["Close"], HT.index[x])
            params = cycle_dynamics_calculation(df, HT.iloc[x]["Open"])
            print("save cycle")
            cycle.loc[len(cycle)] = [HT.index[x], round(HT.iloc[x]["Open"], 1), params[0], params[1], HT.iloc[x]["type"], HT.iloc[x]["Return"]]
            print("saved")

        df = LT[(LT.index >= HT.index[-1])]
        if not df.empty:
            params = cycle_dynamics_calculation(df, HT.iloc[-1]["Open"])
            print("save last cycle")
            cycle.loc[len(cycle)] = [HT.index[-1], round(HT.iloc[-1]["Open"],1), params[0], params[1], HT.iloc[x]["type"], HT.iloc[x]["Return"]]
            print("saved")
        cycle.set_index("Date", inplace=True)
        timeframes_cycles.append(cycle)
    return timeframes_cycles


def dataframe_candle_split(data):
    data_green = []
    data_red = []
    for df in data:
        data_green.append(df[df["Direction"] == "Green"].copy())
        data_red.append(df[df["Direction"] == "Red"].copy())
    return data_green, data_red


def calculation_cycle_flips_all_symbols(lower_timeframe, symbols):
    timeframes_name = ["weekly", "monthly", "quarterly"]
    if lower_timeframe == "daily":
        timeframes_name = ["weekly", "monthly", "quarterly"]
    elif lower_timeframe == "weekly":
        timeframes_name = ["monthly", "quarterly", "yearly"]
    columns = []
    columns.append("Stock")
    for i in range (0,3):
        columns.append(str(i) + " " + timeframes_name[0] + "_F")
    for i in range (0,5):
        columns.append(str(i) + " " + timeframes_name[1] + "_F")
    columns.append("LF" + timeframes_name[1] + "_p50") 
    for i in range (0,5):
        columns.append(str(i) + " " + timeframes_name[2] + "_F")
    columns.append("LF" + timeframes_name[2] + "_p50") 
    df = pd.DataFrame(columns=columns)
    df_detail = pd.DataFrame(columns=columns)

    for symbol in symbols:
        print(symbol)
        aux_timeframes = getDataStock(symbol)    
        aux_timeframes_2= last_X_years(aux_timeframes, 25)
        print("Crear Hightimeframe")
        timeframes = create_hightimeframes(aux_timeframes_2, lower_timeframe)
        print("Vuelve de crear el Hightimeframe")
        data_candles = preparingData(timeframes) 
        print("VuelVe de preparar la data")
        dfs = cycle_dynamics(data_candles, lower_timeframe)
        print("comeback from cycle dynamics")
        counts_A = dfs[0]["Flips"].value_counts().reindex(range(4), fill_value=0).to_dict()
        counts_B = dfs[1]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
        counts_C = dfs[2]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
        total_A = sum(counts_A.values())
        total_B = sum(counts_B.values())
        total_C = sum(counts_C.values())
        #-----------------------------------------------
        print("ANTES DEL DESGLOSE")
        dfs_green, dfs_red = dataframe_candle_split(dfs)

        if lower_timeframe == "daily":
            n = "excels/analysis/monthly_" + symbol + ".csv"
            dfs[1].to_csv(n)
        else:
            n = "excels/analysis/quarterly_" + symbol + ".csv"
            dfs[1].to_csv(n)

        print("VUELVE")
        names = ["", "_green", "_red"]
        x = 0
        for df_aux in [dfs, dfs_green, dfs_red]:
            counts_A = df_aux[0]["Flips"].value_counts().reindex(range(4), fill_value=0).to_dict()
            counts_B = df_aux[1]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
            counts_C = df_aux[2]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
            total_A = sum(counts_A.values())
            total_B = sum(counts_B.values())
            total_C = sum(counts_C.values())
            p_01 = round(df_aux[1]["LastFlip"].quantile(0.50), 1)
            p_02 = round(df_aux[2]["LastFlip"].quantile(0.50), 1)   
            symbol_name = symbol+names[x]
            df_detail.loc[len(df_detail)] = [symbol_name, round((counts_A[0]/total_A)*100,1), round((counts_A[1]/total_A)*100,1), round((counts_A[2]/total_A)*100,1), round((counts_B[0]/total_B)*100,1), round((counts_B[1]/total_B)*100,1), round((counts_B[2]/total_B)*100,1), round((counts_B[3]/total_B)*100,1), round((counts_B[4]/total_B)*100,1), p_01, round((counts_C[0]/total_C)*100,1), round((counts_C[1]/total_C)*100,1), round((counts_C[2]/total_C)*100,1), round((counts_C[3]/total_C)*100,1), round((counts_C[4]/total_C)*100,1), p_02]
            x = x+1  
        print("DESPUES DEL DESGLOSE")
        
        for a in range (0,3):
            name = "excels/LastFlipOpen/" + lower_timeframe +"_flip_on_"+timeframes_name[a] + "_" + symbol + ".csv"
            dfs[a]["LastFlip"].to_csv(name)
        
        p_01 = round(dfs[1]["LastFlip"].quantile(0.50), 1)
        p_02 = round(dfs[2]["LastFlip"].quantile(0.50), 1)    
        print("LOC", symbol)
        df.loc[len(df)] = [symbol, round((counts_A[0]/total_A)*100,1), round((counts_A[1]/total_A)*100,1), round((counts_A[2]/total_A)*100,1), round((counts_B[0]/total_B)*100,1), round((counts_B[1]/total_B)*100,1), round((counts_B[2]/total_B)*100,1), round((counts_B[3]/total_B)*100,1), round((counts_B[4]/total_B)*100,1), p_01, round((counts_C[0]/total_C)*100,1), round((counts_C[1]/total_C)*100,1), round((counts_C[2]/total_C)*100,1), round((counts_C[3]/total_C)*100,1), round((counts_C[4]/total_C)*100,1), p_02]
        print("AFTER LOC", symbol)
    
    name_csv = "excels/flips" + lower_timeframe + ".csv"
    df.to_csv(name_csv)
    name_csv = "excels/flips_detail_" + lower_timeframe + ".csv"
    df_detail.to_csv(name_csv)
    return df


def current_cycle_flips_all_symbols(lower_timeframe):
    try:
        timeframes_name = ["weekly", "monthly", "quarterly"]
        if lower_timeframe == "daily":
            timeframes_name = ["weekly", "monthly", "quarterly"]
        elif lower_timeframe == "weekly":
            timeframes_name = ["monthly", "quarterly", "yearly"]
        symbols = getSymbols()
        rows = []
        for symbol in symbols:
            row = {}
            print("--------------------------------------------------------------------------------------------------------")
            print("i process", symbol)
            timeframes = getDataStock(symbol) # get data of ticker         
            timeframes = create_hightimeframes(timeframes, lower_timeframe)  
            data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values   
            symbol_flips = []
            row = {}
            for i in range (1,len(data_candles)):
                lowerTimeframeCandles = data_candles[0][data_candles[0].index >= data_candles[i].index[-1]]
                open_price = data_candles[i].iloc[-1]["Open"]
                flips, lastFlip = cycle_dynamics_calculation(lowerTimeframeCandles, open_price)
                if flips > 4:
                    flips = 4 #represent a 5+ or a cell with the actual number
                symbol_flips.append([flips, lastFlip])
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


# Calculo de EMA EXTENSION
def calculation_ema_extension(data): 
    print("Entra")
    ema_extensions = []
    for df in data:
        df = df.copy()
        df["EMA10"] = df["Close"].ewm(span=10, adjust=False).mean()
        df["extension_ema10"] = ((df["Close"] - df["EMA10"]) / df["EMA10"])*100
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["extension_ema20"] = ((df["Close"] - df["EMA20"]) / df["EMA20"])*100
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["extension_ema50"] = ((df["Close"] - df["EMA50"]) / df["EMA50"])*100
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
        df["extension_ema200"] = ((df["Close"] - df["EMA200"]) / df["EMA200"])*100   
        ema_extensions.append(df)
    print("Salgo")
    return ema_extensions    


def screener_ema_extensions():
    #symbols_sp500 = get_sp500_symbols()
    #symbols_crypto = get_crypto_symbols()
    #symbols = get_hyperliquid_symbols()
    try:
        symbols = getSymbols()

        col_name_ema = ["extension_ema10", "extension_ema20", "extension_ema50"] 
        timeframes_name = ["DAILY", "WEEKLY", "MONTHLY"] #, "extension_ema50", "extension_ema200"]
        emas_name = ["EMA 10", "EMA 20", "EMA 50", "EMA 200"]
        rows = []
        num = 1
        for symbol in symbols:
            print("SCREENER PROCESSING", symbol, num)
            num = num + 1
            timeframes = getDataStock(symbol) 
            data = preparingData(timeframes) 
            timeframes = calculation_ema_extension(data)
            timeframes = timeframes[:2]
            row = {"Stock": symbol, "Price": round(timeframes[0]["Close"].iloc[-1],1)}
            t, e = 0, 0
            for tf in timeframes:
                e = 0
                for col_name in col_name_ema:
                    current_value = tf[col_name].iloc[-1]
                    p = stats.percentileofscore(tf[col_name].dropna(), current_value, kind='rank')
                    column = "P " + timeframes_name[t] + " " + emas_name[e]
                    row[column] = round(p, 1)
                    if t == 1 and e == 1:
                        break
                    e = e + 1
                t = t + 1                
            rows.append(row) 
            if num == 100:
                break
        df = pd.DataFrame(rows)
        longs_df = df[(df['P DAILY EMA 10'] <= 70) & (df['P DAILY EMA 20'] <= 70)].sort_values(by='P DAILY EMA 10', ascending=True)
        shorts_df = df[(df['P DAILY EMA 10'] >= 30) & (df['P DAILY EMA 20'] >= 30)].sort_values(by='P DAILY EMA 10', ascending=False)
        return longs_df, shorts_df
    except Exception as e:
        print(e)
        return pd.DataFrame()


def calculation_average_deviation(data):
    timeframes = []
    for df in data:
        df = df.copy()
        df['Deviation'] = np.where(df['type'] == 'Green', ((df['Open'] - df['Low']) / df['Open'])*100, ((df['High'] - df['Open']) / df['Open'])*100)
        timeframes.append(df)
    return timeframes 


def calculation_retest_bands(data):
    timeframes = []
    cont = 0
    for df in data:
        cont = cont + 1
        rows = []
        k = 0
        df["EMA_12"] = df["Close"].ewm(span=12, adjust=False).mean()
        df["EMA_21"] = df["Close"].ewm(span=21, adjust=False).mean()
        df = df[12:]
        tolerance = 0.0025 * cont
        ema_top = df[['EMA_12', 'EMA_21']].max(axis=1) * (1 + tolerance)
        ema_bot = df[['EMA_21', 'EMA_12']].min(axis=1) * (1 - tolerance)

        for i in range(len(df)):
            top_val = ema_top.iloc[i] * (1 + tolerance)
            bot_val = ema_bot.iloc[i] * (1 - tolerance)
            try:
                is_away = (df['Low'].iloc[i] > top_val) or (df['High'].iloc[i] < bot_val)
            except Exception as e:
                print(e)

            if is_away:
                k += 1
            else:
                if k > 0:
                    rows.append({"Date": df.index[i], "TimeAway": k})
                k = 0
        # Para capturar la racha actual si todavía sigue lejos
        rows.append({"Date": df.index[-1], "TimeAway": k})  
        timeframes.append(pd.DataFrame(rows))
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
    try:
        timeframe = ["weekly", "monthly"]
        df_daily = data[0]
        for x in range(1, len(data)): # High timeframe
            HT = data[x]
            rows = []
            for i in range(0, len(HT)-1): # High timeframe candles 
                max_dev = 0
                #if (HT["High"].iloc[i]-HT["Open"].iloc[i]) >= abs(HT["Open"].iloc[i]-HT["Low"].iloc[i]):
                #    max_dev = HT["High"].iloc[i]
                #else:
                #    max_dev = HT["Low"].iloc[i]

                if (HT["type"].iloc[i] == "Green"):
                    max_dev = HT["High"].iloc[i]
                else:
                    max_dev = HT["Low"].iloc[i]

                LT = df_daily.loc[HT.index[i] : HT.index[i+1]].iloc[:-1]
                for k in range(0, len(LT)):
                    if (max_dev == LT["High"].iloc[k]) or (max_dev == LT["Low"].iloc[k]):
                        rows.append({"Date": HT.index[i], "PeakExpansion": k + 1})
                        break
            df = pd.DataFrame(rows)
            #name = "/excels/peak/" + stock + timeframe[x-1]
            #df.to_csv(name)
            dataframes.append(df)
        return dataframes
    except Exception as e:
        print(e)
        return dataframes
    

def calculation_cycle_peak_expansion_all_symbols():
    try:
        symbols = getSymbols()
        timeframes = ["Weekly", "Monthly"]
        columns = ["Symbol"]

        for p in [10,20,50,80,90]:
            name_column = timeframes[1] + " " + "p" + str(p)
            columns.append(name_column)

        peak_study = pd.DataFrame(columns=columns)
    
        for symbol in symbols:
            print(symbol)
            aux_timeframes = getDataStock(symbol) # get data of ticker  
            timeframes = preparingData(aux_timeframes)
            data = last_X_years(timeframes, 25)
            print("before function", symbol)
            dataframes_symbol = calculation_cycle_peak_expansion(data, symbol)
            print("after function", symbol)
            info = [symbol]
            print(1)
            for t in range(1,2):
                for p in [0.10,0.20,0.50,0.80,0.90]:
                    percentil = dataframes_symbol[t]["PeakExpansion"].quantile(p)
                    info.append(round(percentil,0))
            print(3)
            peak_study.loc[len(peak_study)] = info
            print(4)

        peak_study.to_csv("excels/peaksoverview.csv")
        return peak_study
    except Exception as e:
        print("Error" + e)


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
    



        

