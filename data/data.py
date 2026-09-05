import yfinance as yf
import pandas as pd
import numpy as np
import time
from analytics.statistics_calculations import *
from analytics.flips_calculation import *
 
def getDataframesDatabase():
    assets = Assets()
    symbols = assets.getAssets("mysymbols")
    for symbol in symbols:
        time.sleep(1) 
        name = "excels/dataframe_symbol/" + symbol + ".csv"
        try:
            stock_daily = pd.read_csv(name, index_col=0, parse_dates=True, date_format='%Y-%m-%d')
        except FileNotFoundError:
            stock_daily = yf.download(symbol, interval="1d", auto_adjust=False, progress=False, period="max") #parametrizo por eficiencia para algunos metodos?
            if isinstance(stock_daily.columns, pd.MultiIndex):
                stock_daily.columns = stock_daily.columns.get_level_values(0)
            stock_daily.to_csv(name)
    print("Symbols dataframes saved")


def getDataStock_LT(symbol, prepost):
    name = "excels/dataframe_symbol_LT/" + symbol + ".csv"
    load = True
    try:
        data_1H = pd.read_csv(name, index_col=0)
        if "Ticker" in data_1H.columns or "Price" in data_1H.columns:
            data_1H = pd.read_csv(name, header=[0, 1], index_col=0, parse_dates=True)
            data_1H.columns = data_1H.columns.get_level_values(0)
    except FileNotFoundError:
        data_1H = yf.download(tickers = symbol, period = "max", interval = "1h", prepost = prepost)
        load = False
    if isinstance(data_1H.columns, pd.MultiIndex):
        data_1H.columns = data_1H.columns.get_level_values(0)
    if not load:
        data_1H.to_csv(name)
    data_1H.index = pd.to_datetime(data_1H.index)
    if data_1H.index.tz is None:
        data_1H.index = data_1H.index.tz_localize('UTC')
    else:
        data_1H.index = data_1H.index.tz_convert('UTC')
    data_4H = data_1H.resample('4h', label='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    data_4H.dropna(inplace=True)
    print(data_1H)
    return [data_1H, data_4H]


def getDataStock_MT(symbol):
    data_MicroT = yf.download(symbol, interval="15m", auto_adjust=False, progress=False, period="max") 
    if isinstance(data_MicroT.columns, pd.MultiIndex):
        data_MicroT.columns = data_MicroT.columns.get_level_values(0)
    data_MicroT.index = pd.to_datetime(data_MicroT.index)
    if data_MicroT.index.tz is None:
        data_MicroT.index = data_MicroT.index.tz_localize('UTC')
    else:
        data_MicroT.index = data_MicroT.index.tz_convert('UTC')
    return data_MicroT













    