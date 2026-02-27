import numpy as np
from functions import * 
import pandas as pd
from data import *

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
    lenght_cycle = (df.index[-1]-df.index[0]).days
    print(lenght_cycle)
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
    print("--------------------------------------------------------------------------------------------------------")
    print("Margin to count the flip", margin)
    return flips, lastFlip


def cycle_dynamics(data, lower_timeframe):
    print(len(data), "---------")
    print(1111)
    parameters = []
    if lower_timeframe == "daily":
        parameters = [pd.Timedelta(days=7), pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3)]
    elif lower_timeframe == "weekly":
        parameters = [pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3), pd.offsets.MonthBegin(12)]
    print(1111)
    timeframes_cycles = []
    LT = data[0][14:].copy()
    end = []
    print(1)
    end.append(pd.to_datetime((data[1].index[-1] + parameters[0]), utc=True))
    print(2)
    end.append(pd.to_datetime((data[2].index[-1] + parameters[1]), utc=True))
    print(2)
    end.append(pd.to_datetime((data[3].index[-1] + parameters[2]), utc=True))
    timeframe = ["WEEKLY", "MONTHLY", "QUARTERLY"]
    print(1111)

    print("start dynamics for")
    for i in range (1, len(data)):
        HT = data[i].copy()
        LT = LT[LT.index < end[i-1]]
        cycle = pd.DataFrame(columns=["Date", "Open", "Flips", "LastFlip"])
        print("start dynamics for 2")
        for x in range(0, len(HT)-1):
            df = LT[(LT.index >= HT.index[x]) & (LT.index < HT.index[x+1])]
            if df.empty:
                continue
            print("--------------------------------------------------------------------------------------------------------")
            print(timeframe[i-1], HT.iloc[x]["Open"], HT.iloc[x]["Close"], HT.index[x])
            params = cycle_dynamics_calculation(df, HT.iloc[x]["Open"])
            cycle.loc[len(cycle)] = [HT.index[x], round(HT.iloc[x]["Open"],1), params[0], params[1]]

        df = LT[(LT.index >= HT.index[-1])]

        if not df.empty:
            params = cycle_dynamics_calculation(df, HT.iloc[-1]["Open"])
            cycle.loc[len(cycle)] = [HT.index[-1], round(HT.iloc[-1]["Open"],1), params[0], params[1]]

        cycle.set_index("Date", inplace=True)
        timeframes_cycles.append(cycle)

    return timeframes_cycles


def calculation_cycle_flips_all_symbols(lower_timeframe):
    symbols = getSymbols()
    timeframes_name = ["weekly", "monthly", "quarterly"]
    if lower_timeframe == "daily":
        timeframes_name = ["weekly", "monthly", "quarterly"]
    elif lower_timeframe == "weekly":
        timeframes_name = ["monthly", "quarterly", "yearly"]
    columns = []
    columns.append("Stock")
    for i in range (0,4):
        columns.append(str(i) + " " + timeframes_name[0] + "_F")
    for i in range (0,5):
        columns.append(str(i) + " " + timeframes_name[1] + "_F")
    for i in range (0,5):
        columns.append(str(i) + " " + timeframes_name[2] + "_F")
    
    df = pd.DataFrame(columns=columns)
    for symbol in symbols:
        print(symbol)
        aux_timeframes = getDataStock(symbol) # get data of ticker        
        timeframes = last_X_years(aux_timeframes, 15)
        timeframes = create_hightimeframes(timeframes, lower_timeframe)
        data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
        print("to cycle dynamics")
        dfs = cycle_dynamics(data_candles, lower_timeframe)
        print("i got back from cycle dynamics")
        counts_A = dfs[0]["Flips"].value_counts().reindex(range(4), fill_value=0).to_dict()
        counts_B = dfs[1]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
        counts_C = dfs[2]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
        total_A = sum(counts_A.values())
        total_B = sum(counts_B.values())
        total_C = sum(counts_C.values())
        df.loc[len(df)] = [symbol, round((counts_A[0]/total_A)*100,1), round((counts_A[1]/total_A)*100,1), round((counts_A[2]/total_A)*100,1), round((counts_A[3]/total_A)*100,1), round((counts_B[0]/total_B)*100,1), round((counts_B[1]/total_B)*100,1), round((counts_B[2]/total_B)*100,1), round((counts_B[3]/total_B)*100,1), round((counts_B[4]/total_B)*100,1), round((counts_C[0]/total_C)*100,1), round((counts_C[1]/total_C)*100,1), round((counts_C[2]/total_C)*100,1), round((counts_C[3]/total_C)*100,1), round((counts_C[4]/total_C)*100,1)]
    name_csv = "flips_" + lower_timeframe + ".csv"
    df.to_csv(name_csv)
    return df


def current_cycle_flips_all_symbols(lower_timeframe):
    timeframes_name = ["weekly", "monthly", "quarterly"]
    if lower_timeframe == "daily":
        timeframes_name = ["weekly", "monthly", "quarterly"]
    elif lower_timeframe == "weekly":
        timeframes_name = ["monthly", "quarterly", "yearly"]
    
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
        print("start for loop")
        for i in range (1,len(data_candles)):
            lowerTimeframeCandles = data_candles[0][data_candles[0].index >= data_candles[i].index[-1]]
            open_price = data_candles[i].iloc[-1]["Open"]
            flips, lastFlip = cycle_dynamics_calculation(lowerTimeframeCandles, open_price)
            if flips > 4:
                flips = 4 #represent a 5+ or a cell with the actual number
            symbol_flips.append([flips, lastFlip])
        print("gets to make the row")
        row = {"symbol": symbol}
        print(1)
        for i, tf in enumerate(timeframes_name):
            print(2)
            row[f"{tf}Flip"] = symbol_flips[i][0]
            print(3)
            row[f"{tf}LastFlip"] = symbol_flips[i][1]
            print(4)
        print("ends the row")
        rows.append(row)   
    df = pd.DataFrame(rows)
    name_csv = "currentflips_" + lower_timeframe + ".csv"
    df.to_csv(name_csv)    
    print("i return the csv")
    return df 


def calculation_cycle_returns():
    symbols = getSymbols()
    rows = []
    for symbol in symbols:
        print(symbol)
        aux_timeframes = getDataStock(symbol) # get data of ticker  
        timeframes = preparingData([aux_timeframes[0]])
        daily_data = last_year(timeframes)
        daily_data['weekday'] = daily_data.index.dayofweek
        daily_data['day_of_month'] = daily_data.index.day
        mean_by_weekday = daily_data.groupby('weekday')['Return'].mean()
        mean_by_monthday = daily_data.groupby('day_of_month')['Return'].mean()
        weekday_mean = mean_by_weekday.reindex(range(5), fill_value=0)   # 0–4
        monthday_mean = mean_by_monthday.reindex(range(1, 32), fill_value=0)       # 1–31
        row = {'symbol': symbol}
        row.update({f'S{i+1}': round((weekday_mean[i]-1)*100,1) for i in range(5)})
        row.update({f'M{i}': round((monthday_mean[i]-1)*100,1) for i in range(1, 32)})
        rows.append(row)   # row es dict
    df = pd.DataFrame(rows)
    df.to_csv("returns.csv")
    return df
    

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
def calculation_ema_extension (stock): 
    data_aux = getDataStock(stock)
    data = preparingData(data_aux)

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
    return ema_extensions    


from scipy import stats
def screener_ema_extensions():
    #symbols_sp500 = get_sp500_symbols()
    #symbols_crypto = get_crypto_symbols()
    symbols = get_hyperliquid_symbols()
    
    col_name_ema = ["extension_ema10", "extension_ema20", "extension_ema50"] 
    timeframes_name = ["DAILY", "WEEKLY", "MONTHLY"] #, "extension_ema50", "extension_ema200"]
    emas_name = ["EMA 10", "EMA 20", "EMA 50", "EMA 200"]
    rows = []
    num = 1
    for symbol in symbols:
        print("SCREENER PROCESSING", symbol, num)
        num = num + 1
        timeframes = calculation_ema_extension(symbol)
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
    # Lado Izquierdo: Buscamos el "Pánico" (Longs)
    # Priorizamos los que están por debajo de 50 en Semanal Y bajísimos en Diario
    longs_df = df[(df['P WEEKLY EMA 10'] < 70) & (df['P WEEKLY EMA 20'] < 70) & (df['P DAILY EMA 10'] < 40)].sort_values(by='P DAILY EMA 10', ascending=True)
    # Lado Derecho: Buscamos la "Euforia" (Shorts)
    # Priorizamos los que están por encima de 50 en Semanal Y altísimos en Diario
    shorts_df = df[(df['P WEEKLY EMA 10'] > 35) & (df['P WEEKLY EMA 20'] > 35) & (df['P DAILY EMA 10'] > 60)].sort_values(by='P DAILY EMA 10', ascending=False)
    #guardar datos after hours
    return longs_df, shorts_df


def calculation_average_deviation(data):
    timeframes = []
    for df in data:
        df = df.copy()
        df['Deviation'] = np.where(df['type'] == 'Green', ((df['Open'] - df['Low']) / df['Open'])*100, ((df['High'] - df['Open']) / df['Open'])*100)
        timeframes.append(df)
    return timeframes 


def symbols_probability_list():
    symbols = getSymbols()
    for symbol in symbols:
        timeframes = getDataStock(symbol) # get data of ticker 
        data_candles = preparingData(timeframes)
        probabilities, colours  = calculation_StrikesProbabilities(data_candles)









## Calculo de los reversal points del rsi para las graficas
#def calculation_RsiReversals(data): 
#    localExtremes = []
#    currentRsi = []
#    parameters = [0, 0, 0] #daily, weekly, montly (umbral highs, mid confirmation, umbral low)
#    cont = 0
#    for df in data:
#        lag = [70, 500, 1800]
#        df = df[df.index > df.index[0]+pd.Timedelta(days=lag[cont])]
#        percentil_25 = np.percentile(df["rsi"], 25)
#        percentil_50 = np.percentile(df["rsi"], 50)
#        percentil_75 = np.percentile(df["rsi"], 75)
#        parameters[0] = percentil_75
#        parameters[1] = percentil_50
#        parameters[2] = percentil_25
#        print("-------------------------------------------------------------------------------------------------------------")
#        state, value = 0, 50
#        highs, lows = [], []
#        lecture = False
#        date = df.index[0]
#        for i in range (0, len(df)):
#            if df.iloc[i]["rsi"] >= parameters[0]:
#                if not lecture:
#                   state = 1
#                   lecture = True
#                   value = df.iloc[i]["rsi"]
#                   date = df.index[i]
#                else:
#                    if df.iloc[i]["rsi"] > value:
#                        value = df.iloc[i]["rsi"]
#                        date = df.index[i]
#            elif df.iloc[i]["rsi"] <= parameters[2]:
#                if not lecture:
#                   state = 2
#                   lecture = True
#                   value = df.iloc[i]["rsi"]
#                   date = df.index[i]
#                else:
#                    if df.iloc[i]["rsi"] < value:
#                        value = df.iloc[i]["rsi"]
#                        date = df.index[i]
#
#            elif df.iloc[i]["rsi"] > parameters[2] and df.iloc[i]["rsi"] < parameters[0] and lecture and state > 0:
#                if state == 1 and df.iloc[i]["rsi"] <= parameters[1]:
#                    if value >= parameters[0]:
#                        highs.append({date: value})
#                    state = 0
#                    lecture = False
#                    value = parameters[1]
#                elif state == 2 and df.iloc[i]["rsi"] >= parameters[1]:
#                    if value <= parameters[2]:
#                        lows.append({date: value})
#                    state = 0
#                    lecture = False
#                    value = parameters[1]
#        currentRsi.append({ df.index[-1] : df.iloc[-1]["rsi"]})
#        aux_data = highs + lows
#        data = [d for d in aux_data if not (isinstance(list(d.keys())[0], float) and np.isnan(list(d.keys())[0]))]
#        localExtremes.append(data)
#        cont = cont + 1    
#    return localExtremes, currentRsi











                
                
                
               
                
      
   
               
 