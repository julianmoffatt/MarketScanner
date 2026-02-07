#pressure/absortion code, weekly and monthly charts
from functions import *
from sp500 import *
from statistics_calculations import *
from screens import *
from screens_web import *
from data import *

stock = "ASTS"

def undervalued_scanner():
    for ticker in ["NVDA", "TSLA", "AAPL", "GOOGL", "IREN", "MU", "ASTS"]:
        timeframes = getDataStock(ticker) # get data of ticker
        data_candles = preparingData(timeframes) # prepare candles and rsi, wicks values
        probabilities, colours  = calculation_StrikesProbabilities(data_candles) # calculation strikes probabilities
        print(ticker, (1-probabilities[0][-3])*100)

def tradeSystem(LT, HT, df_LowerTimeframe, parameter_BullWick, parameter_BearWick, rsiLong_LT, rsiLong_HT, rsiShort_LT, rsiShort_HT, LongK_LT, LongK_HT, ShortK_LT, ShortK_HT):
    df_HigherTimeframe_base = build_df_HigherTimeframe(HT, df_LowerTimeframe)
    tradeLong, tradeShort, trade = False, False, False
    creditos, cont, entry, x = 1000, 0, 0, 14 #diccionarios funcion para importar offset
    if df_HigherTimeframe_base.index[0] < df_LowerTimeframe.index[0]: # emparejar dataframes
        df_HigherTimeframe_base = df_HigherTimeframe_base[df_LowerTimeframe.index[0]:]
    df_LowerTimeframe = df_LowerTimeframe[df_HigherTimeframe_base.index[0]:]

    for i in range(105, len(df_LowerTimeframe)): #diccionarios funcion para importar offset
        if df_HigherTimeframe_base.index[x] + pd.Timedelta(days=13) == df_LowerTimeframe.index[i] and x < len(df_HigherTimeframe_base)-2:
            x = x+1
        #print("NOW:",df_LowerTimeframe.index[i])
        #print(df_HigherTimeframe_base.index[x])
        #print(df_LowerTimeframe.index[i])
        #df_HigherTimeframe = createCurrentCandle(df_HigherTimeframe_base.iloc[x-14:x+1], df_LowerTimeframe.iloc[7*(x+1):i+1])
        df_HigherTimeframe_RSI = df_HigherTimeframe_base.iloc[x]["rsi"]

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
            if (df_LowerTimeframe.iloc[i]["lower_wick"] / df_LowerTimeframe.iloc[i]["candle_range"]) >= parameter_BullWick and df_LowerTimeframe.iloc[i]["rsi"] <= rsiLong_LT and df_HigherTimeframe_RSI <= rsiLong_HT: #hit the proper weekly rsi
                trade = True
                tradeLong = True
                entry = df_LowerTimeframe.iloc[i]["close"]
                SL = df_LowerTimeframe.iloc[i]["low"]
                TP = df_LowerTimeframe.iloc[i]["close"] + ((df_LowerTimeframe.iloc[i]["high"]-df_LowerTimeframe.iloc[i]["low"]) * round((((LongK_LT*rsiLong_LT)+(LongK_HT*rsiLong_HT))/2), 2))
                cont = cont + 1
            elif (df_LowerTimeframe.iloc[i]["upper_wick"] / df_LowerTimeframe.iloc[i]["candle_range"]) >= parameter_BearWick and df_LowerTimeframe.iloc[i]["rsi"] >= rsiShort_LT and df_HigherTimeframe_RSI >= rsiShort_HT:
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

def simulation(symbol):
    LT = '1d'
    HT = '1w'
    df = getTradingDataFrame(symbol, datetime(2021, 4, 1), LT, 100)
    print("hi", symbol)
    if not df.empty:
        cont, numTrades, max, creditos = 0, 0, 0, 1000        
        new_row = {}
        while cont < 10000:
            print(cont, symbol)
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
        print("bye", symbol)
        return new_row
    else:
        print("bye", symbol)
        return False
    
def symbols_simulation():
    markets = kucoin.load_markets() #Load all available markets (contracts)
    symbols = [symbol for symbol in markets if 'USDT' in symbol and markets[symbol]['linear']] # Filter for USDT-margined futures only - # List of symbols to use
    symbols = symbols[:3]

    with ProcessPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(simulation, symbols))
    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df.to_csv("simulation_absortions.csv", index=False, encoding="utf-8", sep=";", decimal=',') 
    

def volumeSystem(df, volatility_X, invalidation_X, rangeVolatility):
    creditos = 1000
    trade = False
    entry = 0
    numTrades = 0
    cross = False
    df['candle_size'] = ((df['close']/df['open'])-1).abs()
    df['avg_candle_size'] = df['candle_size'].rolling(window=rangeVolatility, min_periods=1).mean()
    df['volume_mean'] = df['volume'].rolling(window=rangeVolatility, min_periods=1).mean()
    df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()

    for i in range(rangeVolatility, len(df)):
        if df.iloc[i]["ema12"] > df.iloc[i]["ema21"]:
            cross = True

        if not trade and df.iloc[i]["volume"] >= (volatility_X * df.iloc[i]["volume_mean"]) and df.iloc[i]["close"] > df.iloc[i]["open"] and df.iloc[i]["candle_size"] >=  df.iloc[i]["avg_candle_size"]:
            trade = True
            entry = df.iloc[i]["close"]
            sl = df.iloc[i]["close"] - round((invalidation_X * (df.iloc[i]["high"] - df.iloc[i]["low"])),1)

        if cross and trade and df.iloc[i]["close"] < df.iloc[i]["ema21"]:
            creditos = creditos * (df.iloc[i]["close"]/entry) #(creditos * (df.iloc[i]["close"]/entry)) - (0.003 * creditos) - (0.003 * (creditos * (df.iloc[i]["close"]/entry)))
            trade = False
            cross = False
            numTrades = numTrades + 1

        if trade and df.iloc[i]["close"] <= sl:
            creditos = creditos * (sl/entry) #(creditos * (df.iloc[i]["close"]/entry)) - (0.003 * creditos) - (0.003 * (creditos * (df.iloc[i]["close"]/entry)))
            trade = False
            cross = False
            numTrades = numTrades + 1

    if trade:
            creditos = creditos * (df.iloc[i]["close"]/entry)
            numTrades = numTrades + 1

    return creditos, numTrades 

   
def simulation2(symbol):
    timeframe = '5m'
    df = getTradingDataFrame2(symbol, datetime(2025, 10, 1), timeframe, 100)
    print("start", symbol)
    if not df.empty:
        cont, numTrades, max, creditos = 0, 0, 0, 1000        
        new_row = {}
        while cont < 10000:
            print(symbol, cont)
            volatility_X = int(round(random.uniform(1.5, 50), 1))
            rangeVolatility = int(round(random.uniform(50, 2000), 0))
            invalidation_X = round(random.uniform(0.2, 5), 1)
            rangeVolatility = int(round(random.uniform(50, 1000), 0))
            creditos, trades = volumeSystem(df, volatility_X, invalidation_X, rangeVolatility)
            if creditos > max:
                max = creditos
                numTrades = trades
                new_row = {'Symbol': symbol, 'Start': df.index.min(), 'End': df.index.max(), 'Start_Price': df["close"].iloc[0], 'End_Price': df["close"].iloc[-1], 'SpotPnl': round((df["close"].iloc[-1]/df["close"].iloc[0]) * 1000,1), 'SimulationPnl': round(max,1), 'NumTrades': numTrades, 'Volatility_X': volatility_X, 'rangeVolatility': rangeVolatility, 'invalidation_X': invalidation_X } #, 'BullWick': parameter_BullWick,  'BearWick': parameter_BearWick, 'BullRsi': rsiLongTrigger, 'BearRsi': rsiShortTrigger, "Long_Coefficient": LK, "Short_Coefficient": SK}
            cont = cont + 1
        print("done", symbol)
        return new_row
    else:
        return False

def volumen_simulation():
    markets = kucoin.load_markets() #Load all available markets (contracts)
    symbols = [symbol for symbol in markets if 'USDT' in symbol and markets[symbol]['linear']] # Filter for USDT-margined futures only - # List of symbols to use
    symbols = ["BTC/USDT:USDT","ETH/USDT:USDT","SOL/USDT:USDT", "LINK/USDT:USDT", "XRP/USDT:USDT", "ASTER/USDT:USDT", "AVAX/USDT:USDT", "HYPE/USDT:USDT"] #symbols[:6]

    with ProcessPoolExecutor(max_workers=12) as executor:
        rows = list(executor.map(simulation2, symbols))
    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df.to_csv("simulation_volume_parameters.csv", index=False, encoding="utf-8", sep=";", decimal=',') 
    

def supply_demand_scanner(symbol):
    time.sleep(random.uniform(2, 5))
    ticker = kucoin.fetch_ohlcv(symbol, timeframe='4h', limit=3)
    df = pd.DataFrame(ticker, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])  
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df = df.set_index('timestamp')
    df["candle_range"] = df["high"] - df["low"]
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)-1
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
    df['rsi'] = rsi_tradingview(df['close'])
    i = len(df)-1
    time.sleep(random.uniform(2, 5))
    shortPoints = 0
    longPoints = 0
    points = 5
    
    while i >= 0:
        try:
            if (df.iloc[i]["upper_wick"] / df.iloc[i]["candle_range"]) >= 0.5 and df.iloc[i]["rsi"]:# and df.iloc[i]["candle_size"] >= (df.iloc[i]["avg_candle_size"]*0.7):
                shortPoints = shortPoints + points
        except:
            pass
        try:
            if (df.iloc[i]["lower_wick"] / df.iloc[i]["candle_range"]) >= 0.5 and df.iloc[i]["Close"] > df.iloc[i]["Open"] :# and df.iloc[i]["candle_size"] >= (df.iloc[i]["avg_candle_size"]*0.7):
                longPoints = longPoints + points
        except: 
            pass
        i = i - 1
    
    if shortPoints > longPoints:
        return {"SYMBOL": symbol, "SIDE":"SHORT", "POINTS": shortPoints}
    elif longPoints > shortPoints:
        return {"SYMBOL": symbol, "SIDE":"LONG", "POINTS": longPoints}
    else:
        return False

def supply_demand_scanner_paralelizacion():
    markets = kucoin.load_markets() #Load all available markets (contracts)
    symbols = [symbol for symbol in markets if 'USDT' in symbol and markets[symbol]['linear']] # Filter for USDT-margined futures only - # List of symbols to use
    
    with ProcessPoolExecutor(max_workers=12) as executor:
        rows = list(executor.map(supply_demand_scanner, symbols))
    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df.to_csv("triggers.csv", index=False, encoding="utf-8", sep=";", decimal=',') 


#def main():
#    while True:
#        print("\n=== Main Menu ===")
#        print("1. Statistics")
#        print("2. Cycle Study")
#        print("3. Crypto Market Clasification")
#        print("4. SP500 statistics")
#        print("5. TradingTriggers")
#        choice = input("Choose an option (1-5): ")
#        if choice == "6":
#            undervalued_scanner()
#        elif choice == "0":
#            break
#        elif choice == "1":
#            #symbols_simulation()
#            print("Which stock?")
#            ticker = input()
#            stock_statistics(ticker)
#        elif choice == "2":
#            cycles_study()
#        elif choice == "3":
#            crypto_market_scanner()
#        elif choice == "4":
#            sp500_screen()
#        elif choice == "5":
#            supply_demand_scanner_paralelizacion()
#        else:
#            print("Try again a valid input.")
#
#if __name__ == "__main__":
#    main()


# FIBONACCI FOR TPS? CON RSI TAL VEZ, Y KEY LEVELS AND LIQUIDITY LEVELS I CAN DETECT ALSO WITH CODE
# STUDY OF LIQUIDITY GRABS
# PARA MEDIR LOS MOVIMIENTOS TENGO QUE UTILIZAR LA VOLATILIDAD DE LOS ULTIMOS AÑOS O ALGO Y HACERLO PROPORCIONAL
# study of trailing stops optimization
# multiple consecutive wicks detection for reversals !!!!

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

import dash
from dash import dcc, html, Input, Output

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='Daily & Opens', value='tab-1'),
        dcc.Tab(label='Weekly & Opens', value='tab-2'),
        dcc.Tab(label='Monthly & Opens', value='tab-3'),
        dcc.Tab(label='Strikes probability', value='tab-4'),
        dcc.Tab(label='Rsi reversal points', value='tab-5'),
        dcc.Tab(label='Open reclaims', value='tab-6'),
        dcc.Tab(label='Returns', value='tab-7'),
        dcc.Tab(label='EMA extension 10 & 50', value='tab-8'),
        dcc.Tab(label='EMA extension 100 & 200', value='tab-9')
    ]),
    # Contenedor para el gráfico
    html.Div(
        dcc.Graph(
            id='graph',
            style={
                'width': '100%',   # ocupa todo el ancho
                'height': '95vh',  # casi toda la altura de la ventana
            }
        ),
        style={
        'margin': '0',
        'padding': '0',
        'height': '100vh'
        }
    )
])

@app.callback(
    Output('graph', 'figure'),
    Input('tabs', 'value')
)

def render_content(tab):    
    stock = "ASTS"
    timeframes = getDataStock(stock) # get data of ticker
    data = preparingData(timeframes) # prepare candles and rsi, wicks values

    if tab == 'tab-1':
        fig = screen_daily_chart(data)
        return fig
    elif tab == 'tab-2':
        fig = screen_weekly_chart(data)
        return fig
    elif tab == 'tab-3':
        fig = screen_monthly_chart(data)
        return fig
    elif tab == 'tab-4':
        probabilities, colours  = calculation_StrikesProbabilities(data) # calculation strikes probabilities
        return screen_strikes_plotly(probabilities, colours)
    elif tab == 'tab-5':
        rsiReversalZones, currentRsi = calculation_RsiReversals(data) #calculation rsi reversal points
        return screen_rsi_plotly(rsiReversalZones, currentRsi)
    elif tab == 'tab-6':
        df1 = load_data("flips")
        current_flips = load_data("current_flips")
        current_stock = getCurrentStockPos(stock)
        colours = colour_painting(df1, "flips", current_flips, current_stock)
        return table_fig(df1, colours)
    elif tab == 'tab-7':
        df2 = load_data("returns")
        current_stock_pos = getCurrentStockPos(stock)
        current_returns = pd.DataFrame()
        colours = colour_painting(df2, "returns", current_returns, current_stock_pos)
        return table_fig(df2, colours)
    elif tab == 'tab-8':
        df3 = load_data("ema_"+stock)
        return screen_ema_extension_plotly(df3, stock, -1)
    elif tab == 'tab-9':
        df3 = load_data("ema_"+stock)
        return screen_ema_extension_plotly(df3, stock, 1)
    else:
        pass #funciones que devuelvan Figs


if __name__ == "__main__":
    app.run(debug=True)







    


