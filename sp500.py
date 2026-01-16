import yfinance as yf
import pandas as pd
from functions import *
from statistics import *
from screens import *

def getData_SP500(date):
    spx = yf.download("^GSPC", start="1957-03-04", interval="1d", auto_adjust=False, progress=False)
    if isinstance(spx.columns, pd.MultiIndex):
        spx.columns = spx.columns.get_level_values(0)
    spx_daily = spx[spx.index >= date].copy()
    #Weekly
    spx_weekly = spx_daily.resample('W', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    #Monthly
    spx_monthly = spx_daily.resample('ME', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    return [spx_daily, spx_weekly, spx_monthly]


def sp500_screen():
    print("SP500 Statistics")
    dates = input("Dates to display statistics ('AAAA-MM-DD'): ")
    dates_sp500 = dates.split(",")
    for current_date in dates_sp500:
        print("------------------------------------------------------------------------------------")
        print("DATA FROM", current_date)
        print("------------------------------------------------------------------------------------")
        data_candles = getData_SP500(current_date)
        data = preparingData(data_candles)
        probabilities, colours  = calculation_StrikesProbabilities(data) # calculation strikes probabilities
        rsiReversalZones, currentRsi = calculation_RsiReversals(data_candles) #calculation rsi reversal points
        screen_candles(data_candles) # screen with daily, weekly and monthly candles, opens included
        screen_statistics(rsiReversalZones, currentRsi, probabilities, colours) # screen rsi and candle color probabilities  
        flips, lastFlips = cycle_dynamics(data_candles)
        print("SP500", flips[0], lastFlips[0], flips[1], lastFlips[1])
