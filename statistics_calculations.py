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
        color_list.append("black")
        probability = next_candle_probability(data[cont].iloc[i]["type"], probability_green, probability_red, num+2)
        probability_list.append(probability)
        color_list.append("black")
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
def calculation_RsiReversals(data): 
    localExtremes = []
    currentRsi = []
    parameters = [0, 0, 0] #daily, weekly, montly (umbral highs, mid confirmation, umbral low)
    cont = 0
    for df in data:
        lag = [70, 500, 1800]
        df = df[df.index > df.index[0]+pd.Timedelta(days=lag[cont])]
        percentil_25 = np.percentile(df["rsi"], 25)
        percentil_50 = np.percentile(df["rsi"], 50)
        percentil_75 = np.percentile(df["rsi"], 75)
        parameters[0] = percentil_75
        parameters[1] = percentil_50
        parameters[2] = percentil_25
        print("-------------------------------------------------------------------------------------------------------------")
        state, value = 0, 50
        highs, lows = [], []
        lecture = False
        date = df.index[0]
        for i in range (0, len(df)):
            if df.iloc[i]["rsi"] >= parameters[0]:
                if not lecture:
                   state = 1
                   lecture = True
                   value = df.iloc[i]["rsi"]
                   date = df.index[i]
                else:
                    if df.iloc[i]["rsi"] > value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]
            elif df.iloc[i]["rsi"] <= parameters[2]:
                if not lecture:
                   state = 2
                   lecture = True
                   value = df.iloc[i]["rsi"]
                   date = df.index[i]
                else:
                    if df.iloc[i]["rsi"] < value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]

            elif df.iloc[i]["rsi"] > parameters[2] and df.iloc[i]["rsi"] < parameters[0] and lecture and state > 0:
                if state == 1 and df.iloc[i]["rsi"] <= parameters[1]:
                    if value >= parameters[0]:
                        highs.append({date: value})
                    state = 0
                    lecture = False
                    value = parameters[1]
                elif state == 2 and df.iloc[i]["rsi"] >= parameters[1]:
                    if value <= parameters[2]:
                        lows.append({date: value})
                    state = 0
                    lecture = False
                    value = parameters[1]
        currentRsi.append({ df.index[-1] : df.iloc[-1]["rsi"]})
        aux_data = highs + lows
        data = [d for d in aux_data if not (isinstance(list(d.keys())[0], float) and np.isnan(list(d.keys())[0]))]
        localExtremes.append(data)
        cont = cont + 1    
    return localExtremes, currentRsi


def cycle_dynamics_calculation(df, open):
    flips, last, side = 0, 1, 0
    sides = {1:0, 0:1}

    if df.iloc[0]["Close"] >= open:
        side = 1
    else:
        side = 0

    for k in range (1, len(df)):
        if ((df.iloc[k]["Close"] > open) and (side == 0)) or ((df.iloc[k]["Close"] < open) and (side == 1)):
            #print(k, open, df.index[k], df.iloc[k]["Close"], "side:", side)
            side = sides[side]
            flips = flips + 1
            last = k + 1

    return flips, last


def cycle_dynamics(data):
    timeframes_cycles = []
    LT = data[0].copy()
    end = []
    end.append(pd.to_datetime((data[1].index[-1] + pd.Timedelta(days=7)), utc=True))
    end.append(pd.to_datetime((data[2].index[-1] + pd.offsets.MonthBegin(1)), utc=True))
    
    for i in range (1, len(data)):
        HT = data[i].copy()
        LT = LT[LT.index < end[i-1]]
        cycle = pd.DataFrame()
        cycle = pd.DataFrame(columns=["Date", "Open", "Flips", "LastFlip"])
        for x in range(0, len(HT)-1):
            df = LT[(LT.index >= HT.index[x]) & (LT.index < HT.index[x+1])]
            if df.empty:
                continue
            params = cycle_dynamics_calculation(df, HT.iloc[x]["Open"])
            cycle.loc[len(cycle)] = [HT.index[x], round(HT.iloc[x]["Open"],1), params[0], params[1]]
        df = LT[(LT.index >= HT.index[-1])]
        if not df.empty:
            params = cycle_dynamics_calculation(df, HT.iloc[-1]["Open"])
            cycle.loc[len(cycle)] = [HT.index[-1], round(HT.iloc[-1]["Open"],1), params[0], params[1]]
        cycle.set_index("Date", inplace=True)
        timeframes_cycles.append(cycle)
    return timeframes_cycles


def calculation_cycle_flips():
    symbols = getSymbols()
    df = pd.DataFrame(columns=["Stock", "0 W_Flip", "1 W_Flip", "2 W_Flip", "3 W_Flip", "4 W_Flip", "0 M_Flip", "1 M_Flip", "2 M_Flip", "3 M_Flip", "4 M_Flip"])
    for symbol in symbols:
        print(symbol)
        timeframes = getDataStock(symbol) # get data of ticker
        print("1")        
        #timeframes = last_10_years(aux_timeframes)
        data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
        print("2") 
        dfs = cycle_dynamics(data_candles)
        print("3") 
        counts = dfs[0]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
        counts_M = dfs[1]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
        total = sum(counts.values())
        totalM = sum(counts_M.values())
        print("4") 
        df.loc[len(df)] = [symbol, round((counts[0]/total)*100,1), round((counts[1]/total)*100,1), round((counts[2]/total)*100,1), round((counts[3]/total)*100,1), round((counts[4]/total)*100,1), round((counts_M[0]/totalM)*100,1), round((counts_M[1]/totalM)*100,1), round((counts_M[2]/totalM)*100,1), round((counts_M[3]/totalM)*100,1), round((counts_M[4]/totalM)*100,1)]
        print("5") 
    df.to_csv("flips.csv")
    return df

def current_cycle_flips():
    print("i start")
    symbols = getSymbols()
    rows = []
    for symbol in symbols:
        print("i process", symbol)
        timeframes = getDataStock(symbol) # get data of ticker
        data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
        symbol_flips = []
        row = {}
        for i in range (1,3):
            daily = data_candles[0][data_candles[0].index >= data_candles[i].index[-1]]
            open_price = data_candles[i].iloc[-1]["Open"]
            flips, lastFlip = cycle_dynamics_calculation(daily, open_price)
            if flips > 4:
                flips = 4 #represent a 5+ or a cell with the actual number
            symbol_flips.append([flips, lastFlip])
        row = {"symbol": symbol, "weeklyFlip": symbol_flips[0][0], "weeklyLastFlip": symbol_flips[0][1], "monthlyFlip": symbol_flips[1][0], "monthlyLastFlip": symbol_flips[1][1]}
        rows.append(row)   
    df = pd.DataFrame(rows)
    df.to_csv("current_flips.csv")     
    print("i return the csv")
    return df 


def calculation_cycle_returns():
    symbols = getSymbols()
    rows = []
    for symbol in symbols:
        print(symbol)
        timeframes = getDataStock(symbol) # get data of ticker        
        #timeframes = last_10_years(aux_timeframes)
        data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
        returns = data_candles[0].copy()
        returns['weekday'] = returns.index.dayofweek
        returns['day_of_month'] = returns.index.day
        mean_by_weekday = returns.groupby('weekday')['Return'].mean()
        mean_by_monthday = returns.groupby('day_of_month')['Return'].mean()
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
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        df["extension_ema50"] = ((df["Close"] - df["EMA50"]) / df["EMA50"])*100
        df["EMA100"] = df["Close"].ewm(span=100, adjust=False).mean()
        df["extension_ema100"] = ((df["Close"] - df["EMA100"]) / df["EMA100"])*100
        df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()
        df["extension_ema200"] = ((df["Close"] - df["EMA200"]) / df["EMA200"])*100
        df = df.iloc[20:].copy()   
        ema_extensions.append(df)
    
    #ema_extensions.to_csv("ema_extension"+stock+".csv")
    return ema_extensions    


def symbols_probability_list():
    symbols = getSymbols()
    for symbol in symbols:
        timeframes = getDataStock(symbol) # get data of ticker 
        data_candles = preparingData(timeframes)
        probabilities, colours  = calculation_StrikesProbabilities(data_candles)











                
                
                
               
                
      
   
               
 