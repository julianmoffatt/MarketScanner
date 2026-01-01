from concurrent.futures import ProcessPoolExecutor
import random
import pandas as pd
import ccxt
import time
import yfinance as yf
from statistics import *
from datetime import datetime, timezone, timedelta
kucoin = ccxt.kucoinfutures({'enableRateLimit': True,'timeout': 90000})

def getDataStock(ticker):
    #stock_4h = yf.download(ticker, interval="4h", auto_adjust=False, progress=False)
    stock = yf.download(ticker, interval="1d", auto_adjust=False, progress=False, period="max")
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = stock.columns.get_level_values(0)
    stock_daily = stock.copy()
    #Weekly
    stock_weekly = stock_daily.resample('W', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    #Monthly
    stock_monthly = stock_daily.resample('ME', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    return [stock_daily, stock_weekly, stock_monthly]

def stock_statistics(ticker):
    timeframes = getDataStock(ticker) # get data of ticker
    data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
    strikes = statistics_strikes(data_candles) # calculation strikes probabilities
    rsiReversalZones, currentRsi = statistics_rsi(data_candles) #calculation rsi reversal points

    screen_statistics(rsiReversalZones, currentRsi, data_candles, strikes) # screen rsi and candle color probabilities
    screen_candles(data_candles) # screen with daily, weekly and monthly candles, opens included

def getTradingDataFrame2(symbol, date, timeframe, candles):
    import time
    since = int(date.timestamp() * 1000)
    dataframes = []
    last = False
    loop = True
    while loop:
        time.sleep(round(random.uniform(3, 5), 0))
        ticker = kucoin.fetch_ohlcv(symbol, timeframe=timeframe, limit=candles, since = since)
        df = pd.DataFrame(ticker, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])  
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df = df.set_index('timestamp')
            df["candle_range"] = df["high"] - df["low"]
            df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
            df["lower_wick"] = abs(df["low"] - df[["open", "close"]].min(axis=1))
            df['rsi'] = rsi_tradingview(df['close'])
            if last and last != df.index[-1]:
                dataframes.append(df)
            elif last == df.index[-1]: 
                loop = False                    
            last = df.index[-1]
            since = int(df.index[-1].timestamp() * 1000) + 1
        elif dataframes:
            loop = False
        else:
            since += 30 * 24 * 60 * 60 * 1000   # ✅ milliseconds

    if dataframes:
        return pd.concat(dataframes, ignore_index=False)
    else:
        return pd.DataFrame()

def getTradingDataFrame(symbol, date, timeframe, candles):
    since = int(date.timestamp() * 1000)
    dataframes = []
    now = datetime.now(timezone.utc)
    today = now.date()  # YYYY-MM-DD
    #current_hour = now.hour   # 0–23
    lastDay = date.date()
    while lastDay < today:
        ticker = kucoin.fetch_ohlcv(symbol, timeframe=timeframe, limit=candles, since = since)
        df = pd.DataFrame(ticker, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])  
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df = df.set_index('timestamp')
            df["candle_range"] = df["high"] - df["low"]
            df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
            df["lower_wick"] = abs(df["low"] - df[["open", "close"]].min(axis=1))
            df['rsi'] = rsi_tradingview(df['close'])
            if not (last_df == df):
                dataframes.append(df)
                last_df = df
            else: 
                break
        date += timedelta(days=candles)
        since = int(date.timestamp() * 1000)
    if dataframes:
        df_daily = pd.concat(dataframes, ignore_index=False)
        return df_daily
    else:
        return pd.DataFrame()

def rsi_tradingview(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def build_df_HigherTimeframe(HT, df_LowerTimeframe):
    df_HigherTimeframe = df_LowerTimeframe
    if (HT == '4h'):
        df_HigherTimeframe = df_LowerTimeframe.resample('4H').agg({'open': 'first','high': 'max','low': 'min','close': 'last','volume': 'sum'})
    elif (HT == '1d'):
        df_HigherTimeframe = df_LowerTimeframe.resample('1D',label='left', closed='left').agg({'open': 'first','high': 'max','low': 'min','close': 'last','volume': 'sum'})
    elif (HT == '1w'):
        df_HigherTimeframe = df_LowerTimeframe.resample('W-SUN').agg({'open': 'first','high': 'max','low': 'min','close': 'last','volume': 'sum'})
        df_HigherTimeframe.index = df_HigherTimeframe.index - pd.Timedelta(days=6)
    elif (HT == '1m'):
        df_HigherTimeframe = df_LowerTimeframe.resample('M').agg({'open': 'first','high': 'max','low': 'min','close': 'last','volume': 'sum'})
        df_HigherTimeframe.index = df_HigherTimeframe.index - pd.offsets.MonthBegin(1)
    df_HigherTimeframe['rsi'] = rsi_tradingview(df_HigherTimeframe['close'])
    return df_HigherTimeframe

def createCurrentCandle(df_HigherTimeframe_base, df_LowerTimeframe):
    if df_LowerTimeframe.empty:
        return df_HigherTimeframe_base
    else:    
        new_candle = df_LowerTimeframe.resample('W-SUN').agg({'open': 'first','high': 'max','low': 'min','close': 'last','volume': 'sum'})
        df = pd.concat([df_HigherTimeframe_base, new_candle])
        df['rsi'] = rsi_tradingview(df['close'])
        return df
    
def test_simulation():
    df = pd.read_csv("simulation_parameters_SL_TP.csv", sep=";", decimal=',')
    df["Start"] = pd.to_datetime(df['Start'])
    df["End"] = pd.to_datetime(df['End'])
    df = df[(df["End"] - df["Start"]).dt.days >= 60] #filtro simbolos con al menos dos meses de historico - analisis diario y semanal (4h puede ser menos, pero no recomendado)
    rows = []
    for x in range(0, len(df)):
        parts = []
        set = 1
        symbol = df.iloc[x]["Symbol"]
        print(symbol)
        df_symbol = getTradingDataFrame(symbol, datetime(2021, 4, 1), "1d", 100)
        if not df_symbol.empty:
            num = 0
            vsSpotAVG = 0
            vsSpotMin = float('inf')
            vsSpotMax = 0
            vsCashAVG = 0
            vsCashMin = float('inf')
            vsCashMax = 0
            parts.append({"Symbol":symbol})
            begin = df_symbol.iloc[0]["timestamp"]
            print(df_symbol.iloc[0]["timestamp"])
            print(begin)
            while begin < df_symbol.iloc[-1]["timestamp"]:
                df_aux = df_symbol[(df_symbol["timestamp"] >= begin) & (df_symbol["timestamp"] <= (begin+ pd.Timedelta(days=60)))]
                df_aux = df_aux.reset_index(drop=True)
                creditos, num_trades = tradeSystem(df_aux, df.iloc[x]["BullWick"], df.iloc[x]["BearWick"], df.iloc[x]["BullRsi"], df.iloc[x]["BearRsi"], df.iloc[x]["Long_Coefficient"], df.iloc[x]["Short_Coefficient"])
                end = begin + pd.Timedelta(days=60)
                df_window = df_aux[(df_aux["timestamp"] >= begin) & (df_aux["timestamp"] <= end)]
                spotResult = 1000 * (df_window.iloc[-1]["close"]/df_window.iloc[0]["close"])
                aux = {"SpotSet"+str(set): spotResult, "SimulationSet"+str(set): creditos, "TradesSet"+str(set): num_trades, "vsSpot"+str(set): round(creditos/spotResult, 1), "vsCash"+str(set): round(creditos/1000, 1)}
                num = num + 1
                vsSpotAVG = vsSpotAVG + round(creditos/spotResult, 1)
                vsCashAVG = vsCashAVG + round(creditos/1000, 1)
                if round(creditos/spotResult, 1) > vsSpotMax:
                    vsSpotMax = round(creditos/spotResult, 1)
                if round(creditos/spotResult, 1) < vsSpotMin:
                    vsSpotMin = round(creditos/spotResult, 1)
                if round(creditos/1000, 1) > vsSpotMax:
                    vsCashMax = round(creditos/1000, 1)
                if round(creditos/1000, 1) < vsSpotMin:
                    vsCashMin = round(creditos/1000, 1)
                parts.append(aux)
                begin = begin + pd.Timedelta(days=61)
                set = set + 1
            vsSpotAVG = round(vsSpotAVG/num, 1)
            vsCashAVG = round(vsCashAVG/num, 1)
            parts.append({"vsSpotAVG": vsSpotAVG, "vsCashAVG": vsCashAVG, "vsSpotMax": vsSpotMax, "vsSpotMin": vsSpotMin, "vsCashMax": vsCashMax, "vsCashMin": vsCashMin})
            row = {}
            for d in parts:
                row.update(d)
            rows.append(row)
            parts = []

    df = pd.DataFrame(rows)   
    df.to_csv("test_results_SL_TP.csv", index=False, encoding="utf-8", sep=";", decimal=',') 


def get_symbol_data(symbol):
    timeframes = ['1h','4h', '1d', '1w']
    data = {}
    try:
        for timeframe in timeframes:
            time.sleep(2)
            ohlcv = kucoin.fetch_ohlcv(symbol, timeframe=timeframe, limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df = df.set_index('timestamp')
            df['candle_size'] = ((df['close']/df['open'])-1).abs()
            df['avg_candle_size'] = df['candle_size'].rolling(window=10, min_periods=1).mean()
            df["candle_range"] = df["high"] - df["low"]
            df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
            df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
            df['rsi'] = rsi_tradingview(df['close'])
            df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
            df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
            data[timeframe] = df
        return data
    except:
        return False


def market_status_clasification(symbol):
    data = get_symbol_data(symbol)
    if data:
        long, short = False, False
        longConfluence, shortConfluence = 0, 0
        # filters
        if data["4h"].iloc[-1]["rsi"] <= 65 and data["1d"].iloc[-1]["rsi"] <= 70 and data["1w"].iloc[-1]["rsi"] <= 70 and data["1h"].iloc[-1]["ema12"] > data["1h"].iloc[-1]["ema21"] and data["4h"].iloc[-1]["ema12"] < data["4h"].iloc[-1]["ema21"]: 
            long = True
            weight = 10
            for timeframe in ['4h']:
                cont = len(timeframe) - 1
                for i in range (0, 3): 
                    if (data[timeframe].iloc[cont]["lower_wick"] / data[timeframe].iloc[cont]["candle_range"]) >= 0.5 and data[timeframe].iloc[cont]["candle_size"] >= (0.75 * data[timeframe].iloc[cont]["avg_candle_size"]) and (data[timeframe].iloc[cont]["upper_wick"] / data[timeframe].iloc[cont]["candle_range"]) <= 0.35:
                        longConfluence = longConfluence + weight
                    cont = cont - 1

        if data["4h"].iloc[-1]["rsi"] >= 35 and data["1d"].iloc[-1]["rsi"] >= 30 and data["1w"].iloc[-1]["rsi"] >= 30 and data["1h"].iloc[-1]["ema12"] < data["1h"].iloc[-1]["ema21"] and data["4h"].iloc[-1]["ema12"] > data["4h"].iloc[-1]["ema21"]:
            short = True
            weight = 10
            for timeframe in ['4h']:
                cont = len(timeframe) - 1
                for i in range (0, 3): 
                    if (data[timeframe].iloc[cont]["upper_wick"] / data[timeframe].iloc[cont]["candle_range"]) >= 0.5 and data[timeframe].iloc[cont]["candle_size"] >= (0.75 * data[timeframe].iloc[cont]["avg_candle_size"]) and (data[timeframe].iloc[cont]["lower_wick"] / data[timeframe].iloc[cont]["candle_range"]) <= 0.35:
                        shortConfluence = shortConfluence + weight
                    cont = cont - 1

        if longConfluence > shortConfluence:
            short = False
        elif shortConfluence > longConfluence:
            long = False
        else: 
            return False
        
        if long and longConfluence >= 20:
            return symbol, "LONG", longConfluence
        elif short and shortConfluence >= 20: 
            return symbol, "SHORT", shortConfluence
    return False


def crypto_market_scanner():
    markets = kucoin.load_markets() #Load all available markets (contracts)
    symbols = [symbol for symbol in markets if 'USDT' in symbol and markets[symbol]['linear']] # Filter for USDT-margined futures only - # List of symbols to use
    
    with ProcessPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(market_status_clasification, symbols))
    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df.to_csv("crypto_market_clasification.csv", index=False, encoding="utf-8", sep=";", decimal=',') 


def stock_market_scanner():
    symbols = ["NVDA","MSFT","AAPL","AMZN","GOOGL","GOOG","META","AVGO","BRK.B","TSLA","JPM","V","LLY","NFLX","XOM","MA","WMT","ORCL","JNJ","HD"]

    with ProcessPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(market_status_clasification, symbols))
    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df.to_csv("stock_market_clasification.csv", index=False, encoding="utf-8", sep=";", decimal=',') 






