import yfinance as yf
import pandas as pd
import numpy as np
from functions import *

def getDataStock(ticker):
    #stock_4h = yf.download(ticker, interval="4h", auto_adjust=False, progress=False)
    stock = yf.download(ticker, interval="1d", auto_adjust=False, progress=False, period="max")
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    stock_daily = stock.copy()
    stock_weekly = stock_daily.resample('W', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    stock_monthly = stock_daily.resample('ME', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    return [stock_daily, stock_weekly, stock_monthly]

def rsi_tradingview(prices, period=14): #calculation of rsi
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def preparingData(data):
    for df in data:
        df["Last_Close"] = df["Close"].shift(1)
        df["type"] = np.where(df["Close"] > df["Last_Close"], "Green", "Red")
        df["rsi"] = rsi_tradingview(df['Close'])
        df["Candle_Lenght"] = df["High"] - df["Low"]
        df["Upper_wick"] = df["High"] - df[["Open", "Close"]].max(axis=1)
        df["Lower_wick"] = df[["Open", "Close"]].min(axis=1) - df["Low"]
    return data