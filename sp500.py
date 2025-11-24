import yfinance as yf
import numpy as np
import pandas as pd
from functions import *

def getData_SP500(date):
    spx = yf.download("^GSPC", start="1957-03-04", interval="1d", auto_adjust=False, progress=False)
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = spx.columns.get_level_values(0)
    spx_daily = spx[spx.index >= date].copy()
    #Daily
    spx_daily.loc[:, "last_close"] = spx_daily["Close"].shift(1)
    spx_daily["type"] = np.where(spx_daily["Close"] > spx_daily["last_close"], "Green", "Red")
    #Weekly
    spx_weekly = spx_daily.resample('W').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    spx_weekly.loc[:, "last_close"] = spx_weekly["Close"].shift(1)
    spx_weekly["type"] = np.where(spx_weekly["Close"] > spx_weekly["Open"], "Green", "Red")
    #Monthly
    spx_monthly = spx_daily.resample('ME').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    spx_monthly.loc[:, "last_close"] = spx_monthly["Close"].shift(1)
    spx_monthly["type"] = np.where(spx_monthly["Close"] > spx_monthly["Open"], "Green", "Red")
    return spx_daily, spx_weekly, spx_monthly

def sp500_screen():
    print("SP500 Statistics")
    dates = input("Dates to display statistics ('AAAA-MM-DD'): ")
    dates_sp500 = dates.split(",")
    for date in dates_sp500:
        print("------------------------------------------------------------------------------------")
        print("DATA FROM", date)
        print("------------------------------------------------------------------------------------")
        spx_daily, spx_weekly, spx_monthly = getData_SP500(date)
        cont = 0
        timeframe = ["day", "week", "month"]
        for spx in [spx_daily, spx_weekly, spx_monthly]:
            Green, Red = False, False
            numGreen, numRed = 0, 0
            frequencyGreen, frequencyRed = {}, {}
            for i in range (0, len(spx)):
                if spx.iloc[i]["type"] == 'Green':
                  if not Green:
                    Green = True
                    numGreen = 0
                    if Red:
                      Red = False
                      if numRed in frequencyRed:
                        frequencyRed[numRed] = frequencyRed[numRed] + 1
                      else:
                        frequencyRed[numRed] = 1
                  numGreen = numGreen + 1

                elif spx.iloc[i]["type"] == 'Red':
                  if not Red:
                    Red = True
                    numRed = 0
                    if Green:
                      Green = False
                      if numGreen in frequencyGreen:
                        frequencyGreen[numGreen] = frequencyGreen[numGreen] + 1
                      else:
                        frequencyGreen[numGreen] = 1
                  numRed = numRed + 1
                else:
                  pass
            sorted_green = dict(sorted(frequencyGreen.items()))
            sorted_red = dict(sorted(frequencyRed.items()))
            total_green = sum(sorted_green.values())
            total_red = sum(sorted_red.values())
            probability_green, probability_red = {}, {}
            for key, value in sorted_green.items():
              probability_green[key] = value / total_green	
            for key, value in sorted_red.items():
              probability_red[key] = value / total_red
            if cont == 2:
                x = len(spx) - 1
            else:
               x = len(spx) - 2
            num = 1
            candle = spx.iloc[x]["type"]
            x = x - 1
            while x >= 0 and spx.iloc[x]["type"] == candle:
              num = num + 1
              x = x - 1

            if cont < 2:
                text = "We had a"
            else:
                text = "We are in a"  

            if candle == "Green":
              df_green_frequency = pd.DataFrame(list(probability_green.items()), columns=["days", "frequency"])
              df = df_green_frequency[df_green_frequency["days"]>num]
              pct = round(df["frequency"].sum() * 100, 1)
              pct_2 = round(100-pct, 1)
              print(text ,"green", timeframe[cont] +", making it " + str(num) + " green", timeframe[cont] + "(s) in a row. It continues green", str(pct) + "%" + " and it changes", str(pct_2) + "%")
            else:
              df_red_frequency = pd.DataFrame(list(probability_red.items()), columns=["days", "frequency"])
              df = df_red_frequency[df_red_frequency["days"]>num]
              pct = round(df["frequency"].sum() * 100, 1)
              pct_2 = round(100-pct, 1)
              print(text, "red", timeframe[cont] + ", making it " + str(num) + " red", timeframe[cont] + "(s) in a row. It continues red", str(pct) + "%" + " and it changes", str(pct_2) + "%")
            cont = cont + 1
    print("------------------------------------------------------------------------------------")
    print("RSI statistics")
    print("------------------------------------------------------------------------------------")
    timeframe = ["Daily", "Weekly", "Monthly"]
    cont = 0
    spx_daily, spx_weekly, spx_monthly = getData_SP500('1957-03-04')
    for spx in [spx_daily, spx_weekly, spx_monthly]:
        spx['rsi'] = rsi_tradingview(spx['Close'])
        above = (spx["rsi"] >= (spx.iloc[-1]["rsi"] * 1.01)).sum()
        same =  spx[(spx["rsi"] < (spx.iloc[-1]["rsi"] * 1.01)) & (spx["rsi"] > (spx.iloc[-1]["rsi"] * 0.99))].shape[0]
        below  = (spx["rsi"] <= (spx.iloc[-1]["rsi"] * 0.99)).sum()
        total = above + same + below
        print(timeframe[cont], "is at", str(round(spx.iloc[-1]["rsi"],1)) + ",", "historically it has been", str(round((below/total)*100, 1)) + "%", "below,", str(round((same/total)*100,1)) + "%", "equal,", str(round((above/total)*100,1)) + "%", "above") 
        cont = cont + 1

