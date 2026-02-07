import yfinance as yf
import pandas as pd
import numpy as np

def getSymbols():
    symbols = ["ASTS", "IREN", "MU", "RKLB", "NVDA", "MSFT", "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "TSLA", "BABA", "BIDU", "JD", "ADBE", "NVO", "MSTR", "BTC-USD", "ETH-USD"]
    return symbols

def valid_stock(stock):
    symbols = getSymbols()
    if stock in symbols:
        return True
    else:
        return False    

def getCurrentStockPos(stock):
    symbols = getSymbols()
    pos = 0
    for symbol in symbols:
        if symbol == stock:
            return pos
        pos = pos + 1
    return -1

def getDataStock(ticker):
    stock_daily = yf.download(ticker, interval="1d", auto_adjust=False, progress=False, period="max")
    if isinstance(stock_daily.columns, pd.MultiIndex):
        stock_daily.columns = stock_daily.columns.get_level_values(0)
    #stock_daily = stock_daily.loc[pd.to_datetime("2016-01-01"):]
    # FORCE UTC ONCE — DO NOT REMOVE
    stock_daily.index = pd.to_datetime(stock_daily.index, utc=True)
    # Optional but recommended: normalize to 00:00 UTC
    stock_daily.index = stock_daily.index.normalize()
    stock_daily = stock_daily.sort_index()
    # Monday-based weeks (unchanged)
    stock_weekly = stock_daily.resample('W-MON', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    # Month START (TradingView monthly open logic)
    stock_monthly = stock_daily.resample('MS', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
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
        #df["Candle_Lenght"] = df["High"] - df["Low"]
        #df["Upper_wick"] = df["High"] - df[["Open", "Close"]].max(axis=1)
        #df["Lower_wick"] = df[["Open", "Close"]].min(axis=1) - df["Low"]
        #df["Return"] = df["Close"] / df["Last_Close"]
        #df["Volatility"] = abs(df["Return"])
        
        #df = df.sort_values(by="Return", ascending=False)
        #i = 0
        #for i in range(0, 20):    
        #    num = 0        
        #    num = round(df.iloc[i]["Return"],3)
        #    num = num * 100
        #    num = num - 100
        #    num = round(num, 1)
        #    #print(i + 1, df.index[i], num, "%")
        ##print("-----------------------------------------------------------------")
        #cont = cont + 1
    return data

def last_10_years(data):
    for i in range(0, 3):
        data[i] = data[i].index[pd.to_datetime("2016-01-01"):].copy()
    return data

def import_csv(name):
    try:
        df = pd.read_csv(name + ".csv", index_col=0)
        print("Importando", name)
        print(df)
        df.index.name = None
        return df
    except:
        df = pd.DataFrame()
        return df
    