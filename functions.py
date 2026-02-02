from concurrent.futures import ProcessPoolExecutor
import random
import pandas as pd
import ccxt
import time
from statistics import *
from data import *
from datetime import datetime, timezone, timedelta
from screens import *
kucoin = ccxt.kucoinfutures({'enableRateLimit': True,'timeout': 90000})

def stock_statistics(ticker):
    timeframes = getDataStock(ticker) # get data of ticker
    data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
    return data_candles
    #print(data_candles[0].index[0])
    #probabilities, colours  = calculation_StrikesProbabilities(data_candles) # calculation strikes probabilities
    #rsiReversalZones, currentRsi = calculation_RsiReversals(data_candles) #calculation rsi reversal points
    #screen_candles(data_candles) # screen with daily, weekly and monthly candles, opens included
    #screen_statistics(rsiReversalZones, currentRsi, probabilities, colours) # screen rsi and candle color probabilities  


def cycles_study():
    df_flips = pd.DataFrame(columns=["Stock", "0 W_Flip", "1 W_Flip", "2 W_Flip", "3 W_Flip", "4 W_Flip", "0 M_Flip", "1 M_Flip", "2 M_Flip", "3 M_Flip", "4 M_Flip"])
    try:
        df_flips = pd.read_csv("flips.csv", index_col=0)
        df_flips.index.name = None
    except FileNotFoundError:    
        symbols = ["ASTS", "IREN", "MU", "RKLB"]#, "NVDA", "MSFT", "RKLB", "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "TSLA", "BABA", "BIDU", "JD", "ADBE", "NVO", "NBIS", "MSTR"]#, "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"]
        df = pd.DataFrame(columns=["Stock", "Weekly Avg Flips", "std deviation", "Weekly Avg Last Flip", "std deviation", "Monthly Avg Flips", "std deviation", "Monthly Avg Last Flip", "std deviation"])
        rows = []
        for symbol in symbols:
            timeframes = getDataStock(symbol) # get data of ticker
            data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
            start = pd.Timestamp('2025-01-01', tz='UTC')
            returns = data_candles[0][data_candles[0].index >= start].copy()
            returns['weekday'] = returns.index.dayofweek
            returns['day_of_month'] = returns.index.day
            mean_by_weekday = returns.groupby('weekday')['Return'].mean()
            mean_by_monthday = returns.groupby('day_of_month')['Return'].mean()
            weekday_mean = mean_by_weekday.reindex(range(5), fill_value=0)   # 0–4
            monthday_mean = mean_by_monthday.reindex(range(1, 32), fill_value=0)       # 1–31
            row = {'symbol': symbol}
            row.update({f'wd_{i}': round((weekday_mean[i]-1)*100,1) for i in range(5)})
            row.update({f'dom_{i}': round((monthday_mean[i]-1)*100,1) for i in range(1, 32)})
            rows.append(row)   # row es dict

            dfs = cycle_dynamics(data_candles)
            counts = dfs[0]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
            counts_M = dfs[1]["Flips"].value_counts().reindex(range(5), fill_value=0).to_dict()
            #dfs[0].to_csv(symbol + "_weekly.csv")
            #dfs[1].to_csv(symbol + "_monthly.csv")
            total = sum(counts.values())
            totalM = sum(counts_M.values())
            df_flips.loc[len(df_flips)] = [symbol, round((counts[0]/total)*100,1), round((counts[1]/total)*100,1), round((counts[2]/total)*100,1), round((counts[3]/total)*100,1), round((counts[4]/total)*100,1), round((counts_M[0]/totalM)*100,1), round((counts_M[1]/totalM)*100,1), round((counts_M[2]/totalM)*100,1), round((counts_M[3]/totalM)*100,1), round((counts_M[4]/totalM)*100,1)]
            df_returns = pd.DataFrame(rows)
            df_returns.to_csv("returns.csv")
            #df.loc[len(df)] = [symbol, round(dfs[0]["Flips"].mean(),2), round(dfs[0]["Flips"].std(),2), round(dfs[0]["LastFlip"].mean(), 2), round(dfs[0]["LastFlip"].std(),2), round(dfs[1]["Flips"].mean(),2), round(dfs[1]["Flips"].std(),2), round(dfs[1]["LastFlip"].mean(),2), round(dfs[1]["LastFlip"].std(),2)]
            #df.to_csv("opens.csv")        
    df_flips.to_csv("flips.csv")
    return df_flips

def cycles_returns():
    df_returns = pd.DataFrame()
    try:
        df_returns = pd.read_csv("returns.csv", index_col=0)
        df_returns.index.name = None
    except FileNotFoundError: 
        pass
    return df_returns


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
    symbols = ["ASTS", "IREN", "MU", "NVDA","MSFT","AAPL","AMZN","GOOGL","META","TSLA","BABA", "BIDU", "JD"]

    with ProcessPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(market_status_clasification, symbols))
    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df.to_csv("stock_market_clasification.csv", index=False, encoding="utf-8", sep=";", decimal=',') 






