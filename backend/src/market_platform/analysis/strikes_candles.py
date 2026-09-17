import pandas as pd

# Calculation of strikes probabilities
def calculation_StrikesProbabilities(timeframes):
    timeframes = timeframes[0:3].copy()
    strikes = []
    for df in timeframes:
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
        x0 = (len(timeframes[cont]) - 1) - number_points 
        num = 1
        candle = timeframes[cont].iloc[x0]["type"]
        x = x0 - 1
        while x >= 0 and timeframes[cont].iloc[x]["type"] == candle:
            num += 1
            x -= 1
        probability = round(next_candle_probability(candle, probability_green, probability_red, num) * 100, 0)
        probability_list.append(probability)
        for i in range(len(timeframes[cont]) - number_points, len(timeframes[cont])):
            if timeframes[cont].iloc[i]["type"] == timeframes[cont].iloc[i-1]["type"]:
                num = num + 1
            else:
                num = 1
            probability = next_candle_probability(timeframes[cont].iloc[i]["type"], probability_green, probability_red, num) # returns red prob, get green with 1 - red prob
            probability_list.append(probability)

        color_list = []
        for i in range((len(timeframes[cont]) - 1) - number_points, len(timeframes[cont])):
            color_list.append(timeframes[cont].iloc[i]["type"])
        # proyected continuation of 2 candle with proyected probabilities
        for k in range (1,4):
            probability = next_candle_probability(timeframes[cont].iloc[i]["type"], probability_green, probability_red, num+k)
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