import numpy as np
from functions import * 
import pandas as pd

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

    probabilities, colours = [], []
    for cont in range(len(strikes)):
        number_points = 12
        probability_green = strikes[cont]["Green"]
        probability_red = strikes[cont]["Red"]
        probability_list = []
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
            probability = next_candle_probability(data[cont].iloc[i]["type"], probability_green, probability_red, num)
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

# Gives the probabilityies of the next candle depending on colour and current strike
def next_candle_probability(candle, probability_green, probability_red, num):
    streaks = pd.DataFrame()
    if candle == "Green":
        streaks = pd.DataFrame(list(probability_green.items()), columns=["days", "frequency"])
    else:
        streaks = pd.DataFrame(list(probability_red.items()), columns=["days", "frequency"])
    beyond = streaks[streaks["days"]>num]["frequency"].sum()
    equal = streaks[streaks["days"]==num]["frequency"].sum()
    probRed = round((beyond / (equal + beyond)), 2)
    if candle == "Green":
        return 1-probRed
    else:
        return probRed
    

# Calculo de los reversal points del rsi para las graficas
def calculation_RsiReversals(data): 
    localExtremes = []
    currentRsi = []
    parameters = [[65, 50, 35],[64, 55, 41],[68, 59, 50]] #daily, weekly, montly (umbral highs, mid confirmation, umbral low)
    cont = 0
    for df in data:
        df = df[df.index > df.index[0]+pd.Timedelta(days=1400)]
        print("-------------------------------------------------------------------------------------------------------------")
        state, value = 0, 50
        highs, lows = [], []
        lecture = False
        date = df.index[0]
        for i in range (0, len(df)):
            if df.iloc[i]["rsi"] >= parameters[cont][0]:
                if not lecture:
                   state = 1
                   lecture = True
                   value = df.iloc[i]["rsi"]
                   date = df.index[i]
                else:
                    if df.iloc[i]["rsi"] > value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]
            elif df.iloc[i]["rsi"] <= parameters[cont][2]:
                if not lecture:
                   state = 2
                   lecture = True
                   value = df.iloc[i]["rsi"]
                   date = df.index[i]
                else:
                    if df.iloc[i]["rsi"] < value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]

            elif df.iloc[i]["rsi"] > parameters[cont][2] and df.iloc[i]["rsi"] < parameters[cont][0] and lecture and state > 0:
                if state == 1 and df.iloc[i]["rsi"] <= parameters[cont][1]:
                    if value >= parameters[cont][0]:
                        highs.append({date: value})
                    state = 0
                    lecture = False
                    value = parameters[cont][1]
                elif state == 2 and df.iloc[i]["rsi"] >= parameters[cont][1]:
                    if value <= parameters[cont][2]:
                        lows.append({date: value})
                    state = 0
                    lecture = False
                    value = parameters[cont][1]
        currentRsi.append({ df.index[-1] : df.iloc[-1]["rsi"]})
        aux_data = highs + lows
        data = [d for d in aux_data if not (isinstance(list(d.keys())[0], float) and np.isnan(list(d.keys())[0]))]
        localExtremes.append(data)
        cont = cont + 1    
    return localExtremes, currentRsi


def calculation_RsiReversals2(data):
    localExtremes = []
    currentRsi = []
    for timeframe in data:
        currentRsi.append({ timeframe.index[-1] : timeframe.iloc[-1]["rsi"]})
        aux_extremes = []
        df = timeframe[timeframe.index > timeframe.index[0]+pd.Timedelta(days=1400)]
        percentil_5 = np.percentile(df["rsi"], 95)
        lows = df[df["rsi"] <= percentil_5]
        percentil_95 = np.percentile(df["rsi"], 95)
        highs = df[df["rsi"] >= percentil_95]
        i = 0
        for i in range (0, len(lows)):            
            aux_extremes = [].append({ lows.index[i] : lows.iloc[i]["rsi"]})
        i = 0
        for i in range (0, len(highs)):            
            aux_extremes = [].append({ highs.index[i] : highs.iloc[i]["rsi"]})
        #data = [d for d in aux_extremes if not (isinstance(list(d.keys())[0], float) and np.isnan(list(d.keys())[0]))]
        localExtremes.append(data)
    return localExtremes, currentRsi



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










                
                
                
               
                
      
   
               
 