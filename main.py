#pressure/absortion code, weekly and monthly charts
from concurrent.futures import ProcessPoolExecutor
import random
import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone
import ccxt
#import numpy as np

kucoin = ccxt.kucoinfutures() #Connect to KuCoin Futures

def createCurrentCandle(df_HigherTimeframe_base, df_LowerTimeframe):
    #print(df_HigherTimeframe_base)
    #print("----------------------")
    #print(df_LowerTimeframe)
    if df_LowerTimeframe.empty:
        return df_HigherTimeframe_base
    else:    
        new_candle = df_LowerTimeframe.resample('W-SUN').agg({'open': 'first','high': 'max','low': 'min','close': 'last','volume': 'sum'})
        df = pd.concat([df_HigherTimeframe_base, new_candle])
        df['rsi'] = rsi_tradingview(df['close'])
        return df

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


def tradeSystem(LT, HT, df_LowerTimeframe, parameter_BullWick, parameter_BearWick, rsiLong_LT, rsiLong_HT, rsiShort_LT, rsiShort_HT, LongK_LT, LongK_HT, ShortK_LT, ShortK_HT):
    df_HigherTimeframe_base = build_df_HigherTimeframe(HT, df_LowerTimeframe)
    tradeLong, tradeShort, trade = False, False, False
    creditos, cont, entry, x = 1000, 0, 0, 14 #diccionarios funcion para importar offset
    if df_HigherTimeframe_base.index[0] < df_LowerTimeframe.index[0]: # emparejar dataframes
        df_HigherTimeframe_base = df_HigherTimeframe_base[df_LowerTimeframe.index[0]:]
    df_LowerTimeframe = df_LowerTimeframe[df_HigherTimeframe_base.index[0]:]

    for i in range(105, len(df_LowerTimeframe)): #diccionarios funcion para importar offset
        if df_HigherTimeframe_base.index[x] + pd.Timedelta(days=13) == df_LowerTimeframe.index[i]:
            x = x+1
        #print("NOW:",df_LowerTimeframe.index[i])
        #print(df_HigherTimeframe_base.index[x])
        #print(df_LowerTimeframe.index[i])
        df_HigherTimeframe = createCurrentCandle(df_HigherTimeframe_base.iloc[x-14:x+1], df_LowerTimeframe.iloc[7*(x+1):i+1])        

        print("i:", i)
        print("Lower len:", len(df_LowerTimeframe))
        print("Higher len:", len(df_HigherTimeframe))

        if trade:
            if tradeLong: 
                if ((df_LowerTimeframe.iloc[i]["upper_wick"] / df_LowerTimeframe.iloc[i]["candle_range"]) >= parameter_BearWick): #que no cierre hasta que la vela cierre
                    creditos = ((df_LowerTimeframe.iloc[i]["close"] / entry) * creditos) 
                    trade, tradeLong = False, False
                elif df_LowerTimeframe.iloc[i]["high"] >= TP:
                    creditos = ((TP/entry) * creditos) 
                    trade, tradeLong = False, False
                elif df_LowerTimeframe.iloc[i]["low"] <= SL:
                    creditos = ((SL/entry) * creditos) 
                    trade, tradeLong = False, False
            elif tradeShort:
                if ((df_LowerTimeframe.iloc[i]["lower_wick"] / df_LowerTimeframe.iloc[i]["candle_range"]) >= parameter_BullWick): #que no cierre hasta que la vela cierre
                    creditos = (entry / (df_LowerTimeframe.iloc[i]["close"]) * creditos)  
                    trade, tradeShort = False, False
                elif df_LowerTimeframe.iloc[i]["low"] <= TP:
                    creditos = ((entry/TP) * creditos) 
                    trade, tradeShort = False, False
                elif df_LowerTimeframe.iloc[i]["high"] >= SL:
                    creditos = ((entry/SL) * creditos) 
                    trade, tradeShort = False, False
        else :
            if (df_LowerTimeframe.iloc[i]["lower_wick"] / df_LowerTimeframe.iloc[i]["candle_range"]) >= parameter_BullWick and df_LowerTimeframe.iloc[i]["rsi"] <= rsiLong_LT and df_HigherTimeframe.iloc[-1]["rsi"] <= rsiLong_HT: #hit the proper weekly rsi
                trade = True
                tradeLong = True
                entry = df_LowerTimeframe.iloc[i]["close"]
                SL = df_LowerTimeframe.iloc[i]["low"]
                TP = df_LowerTimeframe.iloc[i]["close"] + ((df_LowerTimeframe.iloc[i]["high"]-df_LowerTimeframe.iloc[i]["low"]) * round((((LongK_LT*rsiLong_LT)+(LongK_HT*rsiLong_HT))/2), 2))
                cont = cont + 1
            elif (df_LowerTimeframe.iloc[i]["upper_wick"] / df_LowerTimeframe.iloc[i]["candle_range"]) >= parameter_BearWick and df_LowerTimeframe.iloc[i]["rsi"] >= rsiShort_LT and df_HigherTimeframe.iloc[-1]["rsi"] >= rsiShort_HT:
                trade = True
                tradeShort = True
                entry = df_LowerTimeframe.iloc[i]["close"]
                SL = df_LowerTimeframe.iloc[i]["high"]
                TP = df_LowerTimeframe.iloc[i]["close"] - ((df_LowerTimeframe.iloc[i]["high"]-df_LowerTimeframe.iloc[i]["low"]) * round((((ShortK_LT*rsiShort_LT)+(ShortK_HT*rsiShort_HT))/2), 2))
                cont = cont + 1

    if trade:
        if tradeLong:
            creditos = creditos * (df_LowerTimeframe.iloc[-1]["close"]/entry)
        elif tradeShort:
            creditos = creditos * (entry/df_LowerTimeframe.iloc[-1]["close"])

    return creditos, cont

def rsi_tradingview(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

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
            dataframes.append(df)
        date += timedelta(days=candles)
        since = int(date.timestamp() * 1000)
        lastDay = df.index[-1].date()
    if dataframes:
        df_daily = pd.concat(dataframes, ignore_index=False)
        return df_daily
    else:
        return pd.DataFrame()


def simulation(symbol):
    LT = '1d'
    HT = '1w'
    df = getTradingDataFrame(symbol, datetime(2021, 4, 1), LT, 100)
    if not df.empty:
        cont, numTrades, max, creditos = 0, 0, 0, 1000        
        new_row = {}
        while cont < 1:
            if cont == 30000 or cont == 100000 or cont == 150000:
                print(cont)
            parameter_BullWick = round(random.uniform(0.25, 0.95), 2) 
            parameter_BearWick = round(random.uniform(0.25, 0.95), 2) 
            rsiLong_LT = round(random.uniform(15, 80), 0)
            rsiLong_HT = round(random.uniform(15, 80), 0)
            rsiShort_LT = round(random.uniform(20, 85), 0)
            rsiShort_HT = round(random.uniform(20, 85), 0)
            LongK_LT = round(random.uniform(3, 50), 0)
            LongK_HT = round(random.uniform(3, 50), 0)
            ShortK_LT = round(random.uniform(3, 50), 0)
            ShortK_HT = round(random.uniform(3, 50), 0)
            creditos, trades = tradeSystem(LT, HT, df, parameter_BullWick, parameter_BearWick, rsiLong_LT, rsiLong_HT, rsiShort_LT, rsiShort_HT, LongK_LT, LongK_HT, ShortK_LT, ShortK_HT)
            if creditos > max: 
                max = creditos
                numTrades = trades
                new_row = {'Symbol': symbol, 'Start': df.index.min(), 'End': df.index.max(), 'Start_Price': df["close"].iloc[0], 'End_Price': df["close"].iloc[-1], 'SpotPnl': round((df["close"].iloc[-1]/df["close"].iloc[0]) * 1000,1), 'SimulationPnl': round(max,1), 'NumTrades': numTrades} #, 'BullWick': parameter_BullWick,  'BearWick': parameter_BearWick, 'BullRsi': rsiLongTrigger, 'BearRsi': rsiShortTrigger, "Long_Coefficient": LK, "Short_Coefficient": SK}
            cont = cont + 1

        return new_row
    else:
        return False


def symbols_simulation():
    markets = kucoin.load_markets() #Load all available markets (contracts)
    symbols = [symbol for symbol in markets if 'USDT' in symbol and markets[symbol]['linear']] # Filter for USDT-margined futures only - # List of symbols to use
    symbols = symbols[:10]

    with ProcessPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(simulation, symbols))
    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df.to_csv("simulation_NEW_CODE.csv", index=False, encoding="utf-8", sep=";", decimal=',') 

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

def trading_triggers():
    df = pd.read_csv("test_results.csv", sep=";", decimal=',')

def main():
    while True:
        print("\n=== Main Menu ===")
        print("1. Simulation")
        print("2. Test Simulation")
        print("3. Trading Triggers")
        print("4. Exit")
        choice = input("Choose an option (1-4): ")
        if choice == "1":
            symbols_simulation()
        elif choice == "2":
            test_simulation()
        elif choice == "3":
            trading_triggers()
        elif choice == "4":
            df = getTradingDataFrame('BTC/USDT:USDT', datetime(2021, 4, 1), "1d", 100)
            print("Goodbye!")
            break
        else:
            print("Try again a valid input.")

if __name__ == "__main__":
    main()


# FIBONACCI FOR TPS? CON RSI TAL VEZ, Y KEY LEVELS AND LIQUIDITY LEVELS I CAN DETECT ALSO WITH CODE
# STUDY OF LIQUIDITY GRABS
# PARA MEDIR LOS MOVIMIENTOS TENGO QUE UTILIZAR LA VOLATILIDAD DE LOS ULTIMOS AÑOS O ALGO Y HACERLO PROPORCIONAL

# SimulationPnl > SpotPnl (time-range)
# SimulationPnl > CashPosition (time-range)
# ventana deslizante
# Groups of absortions in lower timeframes?

# el codigo que compra y vende lo tengo que adaptar, para simulacion ejecutarse parametrizando, para test haciendo ventana deslizante del dataframe y 
# si quiero simular alguna situacion particular metiendo yo los parametros y el simbolo (opcion single test)

# ventanas deslizantes
# 4h - 1 semana
# 1d - 1 mes
# 1w - 3-6 meses



    


