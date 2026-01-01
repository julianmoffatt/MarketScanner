import yfinance as yf
import numpy as np
import pandas as pd
from functions import *
from statistics import *

def getData_SP500(date):
    spx = yf.download("^GSPC", start="1957-03-04", interval="1d", auto_adjust=False, progress=False)
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = spx.columns.get_level_values(0)
    spx_daily = spx[spx.index >= date].copy()
    #Weekly
    spx_weekly = spx_daily.resample('W', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    #Monthly
    spx_monthly = spx_daily.resample('ME', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    return spx_daily, spx_weekly, spx_monthly

   
def sp500_screen():
    print("SP500 Statistics")
    dates = input("Dates to display statistics ('AAAA-MM-DD'): ")
    dates_sp500 = dates.split(",")
    for current_date in dates_sp500:
      print("------------------------------------------------------------------------------------")
      print("DATA FROM", current_date)
      print("------------------------------------------------------------------------------------")
      spx_daily, spx_weekly, spx_monthly = getData_SP500(current_date)
      data_candles = preparingData([spx_daily, spx_weekly, spx_monthly])
      cont = 0
      data = statistics_strikes(data_candles)
      conditionalProbability(data, data_candles)
      print("------------------------------------------------------------------------------------")
      print("RSI statistics")
      print("------------------------------------------------------------------------------------")
      timeframe2 = ["Daily", "Weekly", "Monthly"]
      cont1 = 0
      for spx in [spx_daily, spx_weekly, spx_monthly]:
          spx['rsi'] = rsi_tradingview(spx['Close'])
          above = (spx["rsi"] >= (spx.iloc[-1]["rsi"] * 1.01)).sum()
          same =  spx[(spx["rsi"] < (spx.iloc[-1]["rsi"] * 1.01)) & (spx["rsi"] > (spx.iloc[-1]["rsi"] * 0.99))].shape[0]
          below  = (spx["rsi"] <= (spx.iloc[-1]["rsi"] * 0.99)).sum()
          total = above + same + below
          print(timeframe2[cont1], "is at", str(round(spx.iloc[-1]["rsi"],1)) + ",", "historically it has been", str(round((below/total)*100, 1)) + "%", "below,", str(round((same/total)*100,1)) + "%", "equal,", str(round((above/total)*100,1)) + "%", "above") 
          cont1 = cont1 + 1
      cont = cont + 1
      data, currentRsi = statistics_rsi(data_candles)
      display(data, currentRsi, data_candles)


