#pressure/absortion code, weekly and monthly charts
import os
import glob
from functions import *
from sp500 import *
from statistics_calculations import *
from screens_web import *
from data import *
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

stock = "ASTS"

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
    ticker = kucoin.fetch_ohlcv(symbol, timeframe='1w', limit=5)
    df = pd.DataFrame(ticker, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])  
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df = df.set_index('timestamp')
    df["candle_range"] = df["high"] - df["low"]
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)-1
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]

    i = len(df)-1
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

# Altura de la barra un poco más generosa (de 35px a 42px)
tabs_styles = {
    'height': '60px',
    'alignItems': 'center',
    'backgroundColor': '#F0F2F5', # Un gris muy suave de fondo
}

tab_style = {
    'borderBottom': '1px solid #D6D6D6',
    'whiteSpace': 'nowrap',
    'padding': '0px',        # Más espacio para que no se vea "apretado"
    'fontSize': '14px',      # Tamaño intermedio perfecto
    'backgroundColor': 'white',
    'color': '#4A4A4A',      # Gris oscuro para suavizar el contraste
    'lineHeight': '50px',    # Centrado vertical suave
    'fontWeight': '600'      # Un toque más de grosor para legibilidad
}

tab_selected_style = {
    'borderTop': '1px solid #007BFF', # Línea azul un poco más gruesa
    'borderBottom': 'none',
    'backgroundColor': 'white',
    'color': '#007BFF',
    'padding': '1px',
    'fontSize': '13px',
    'lineHeight': '50px',
    'fontWeight': 'bold'
}

ticker_options = [
    # INDEX
    #{'label': 'S&P 500', 'value': '^GSPC'},
    # TECH GIANTS & SEMIS
    {'label': '🚀 ASTS - SpaceMobile', 'value': 'ASTS'},
    {'label': '⛏️ IREN - Iris Energy', 'value': 'IREN'},
    {'label': '💾 MU - Micron Technology', 'value': 'MU'},
    #{'label': '🟢 NVDA - Nvidia', 'value': 'NVDA'},
    {'label': '🔍 GOOGL - Alphabet', 'value': 'GOOGL'},
    {'label': '🍎 AAPL - Apple', 'value': 'AAPL'},
    {'label': '📦 AMZN - Amazon', 'value': 'AMZN'},
    #{'label': '🏎️ AMD - Micro Devices', 'value': 'AMD'},
    {'label': '💻 MSFT - Microsoft', 'value': 'MSFT'},
    {'label': '🍿 NFLX - Netflix', 'value': 'NFLX'},
    {'label': '📱 META - Meta Platforms', 'value': 'META'},
    {'label': '☁️ ORCL - Oracle', 'value': 'ORCL'},
    {'label': '🔵 INTC - Intel', 'value': 'INTC'},
    #{'label': '⚡ TSLA - Tesla', 'value': 'TSLA'},
    {'label': '👁️ PLTR - Palantir', 'value': 'PLTR'},
    {'label': '📊 MSTR - MicroStrategy', 'value': 'MSTR'},
    #
    ## CHINA TECH
    {'label': '🐉 BABA - Alibaba', 'value': 'BABA'},
    {'label': '🏮 BIDU - Baidu', 'value': 'BIDU'},
    {'label': '🛒 JD - JD.com', 'value': 'JD'},
    #
    ## COMMODITIES
    {'label': '🟡 GC=F - Gold Futures', 'value': 'GC=F'},
    {'label': '⚪ SI=F - Silver Futures', 'value': 'SI=F'},
    {'label': '⚪ CL=F - OIL Futures', 'value': 'CL=F'},
    
    # CRYPTO
    {'label': '🟠 BTC-USD - Bitcoin', 'value': 'BTC-USD'},
    {'label': '🔷 ETH-USD - Ethereum', 'value': 'ETH-USD'}
]

app = dash.Dash(__name__)

app.layout = html.Div([
    # --- BLOQUE DE CONTROL SUPERIOR (Contenedor Maestro) ---
    html.Div([
        
        # 1. Espaciador a la izquierda (para que el centro sea el centro real)
        html.Div(style={'flex': '1'}),

        # 2. BLOQUE CENTRAL: Selector de Activo
        html.Div([
            html.Label("Seleccionar Activo:", style={'color': 'white', 'margin-right': '15px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='ticker-selector',
                options=ticker_options,
                value='ASTS',
                clearable=False,
                searchable=True,
                style={'width': '280px', 'color': 'black'}
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'flex': '1', 'justifyContent': 'center'}),

        # 3. BLOQUE DERECHO: Botón Update
        html.Div([
            html.Span(id="clear-all-status", style={'margin-right': '10px', 'color': '#848E9C', 'font-size': '12px'}),
            html.Button(
                "UPDATE DATA", 
                id="btn-clear-all", 
                n_clicks=0,
                style={
                    'backgroundColor': '#1e1e1e',
                    'color': "#FFCF4B",
                    'border': '1px solid #FF4B4B',
                    'borderRadius': '4px',
                    'padding': '5px 15px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold'
                }
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'flex': '1', 'justifyContent': 'flex-end'}),

    ], style={
        'display': 'flex', 
        'alignItems': 'center', 
        'padding': '10px 20px', 
        'backgroundColor': '#1e1e1e',
        'borderBottom': '1px solid #333'
    }),

    dcc.Tabs(
    id="tabs", 
    value='tab-1', 
    style=tabs_styles, 
    children=[
        dcc.Tab(label='DAILY', value='tab-1', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='WEEKLY', value='tab-2', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='MONTHLY', value='tab-3', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='EMA 10/20', value='tab-4', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='EMA 50/200', value='tab-5', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='DEVIATIONS', value='tab-6', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='STRIKES', value='tab-7', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='RSI', value='tab-8', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='FLIPS(D)', value='tab-9', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='FLIPS(W)', value='tab-10', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='SCREENER', value='tab-12', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='BACK MEAN', value='tab-13', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='LAST FLIP', value='tab-14', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='PEAKS', value='tab-15', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='GAPS', value='tab-16', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='OPEN GAPS', value='tab-17', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='+FLIPS (D)', value='tab-18', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='+FLIPS (W)', value='tab-19', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='CORR.', value='tab-20', style=tab_style, selected_style=tab_selected_style)
    ]
    ),

    # --- CONTENEDOR DEL GRÁFICO ---
    html.Div(
        dcc.Graph(
            id='graph',
            style={
                'width': '100%',
                'height': '90vh', # Bajamos a 90 para dejar espacio al menú superior
            }
        ),
        style={'margin': '0', 'padding': '0'}
    )
], style={
    'backgroundColor': '#1e1e1e', 
    'margin': '0', 
    'padding': '0', 
    'minHeight': '100vh',
    'width': '98vw' # Fuerza el ancho total
})

@app.callback(
    Output('clear-all-status', 'children'),
    Input('btn-clear-all', 'n_clicks'),
    prevent_initial_call=True
)

def bulk_clear_cache(n_clicks):
    import glob, os, time
    ruta = "excels/dataframe_symbol/"
    archivos = glob.glob(os.path.join(ruta, "*.csv"))
    
    # Un pequeño truco: esperamos 0.1s para que cualquier lectura previa suelte el archivo
    time.sleep(0.5) 
    
    eliminados = 0
    for f in archivos:
        try:
            os.remove(f)
            eliminados += 1
        except Exception as e:
            print(f"No se pudo borrar {f}: {e}")
            
    return f"✨ {eliminados} files deleted"

@app.callback(
    Output('graph', 'figure'),
    [Input('ticker-selector', 'value'),
     Input('tabs', 'value'),
     Input('btn-clear-all', 'n_clicks')]
)

def render_content(stock, tab, n_clicks):
    ruta = "excels/dataframe_symbol/"
    if not os.listdir(ruta):
        print("DATABASE")
        getDataframesDatabase()

    timeframes = getDataStock(stock) # get data of ticker
    data = preparingData(timeframes) # prepare candles and rsi, wicks values
    current_stock = getCurrentStockPos(stock) #posicion del stock seleccionado en la lista para remarcar

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
        df_tab_4 = calculation_ema_extension(data)
        return screen_ema_extension_plotly(df_tab_4, stock, -1)
    elif tab == 'tab-5':
        df_tab_5 = calculation_ema_extension(data)
        return screen_ema_extension_plotly(df_tab_5, stock, 1)
    elif tab == 'tab-6':
        df_tab_6 = calculation_average_deviation(data)
        return screen_deviations(df_tab_6, stock)
    elif tab == 'tab-7':
        probabilities, colours  = calculation_StrikesProbabilities(data) # calculation strikes probabilities
        return screen_strikes_plotly(probabilities, colours, stock)
    elif tab == 'tab-8':
        df_tab_8 = calculation_Rsi(data) #calculation rsi reversal points
        return screen_rsi_plotly(df_tab_8, stock)
    elif tab == 'tab-9':
        df_tab_9 = load_data("excels/flipsdaily")
        current_flips = load_data("excels/currentflipsdaily")
        colours = colour_painting(df_tab_9, "flips", current_flips, current_stock)
        return table_fig(df_tab_9, colours)    
    elif tab == 'tab-10':
        df_tab_10 = load_data("excels/flipsweekly")
        current_flips = load_data("excels/currentflipsweekly")
        colours = colour_painting(df_tab_10, "flips", current_flips, current_stock)
        return table_fig(df_tab_10, colours)    
    elif tab == 'tab-12':
        longs, shorts = screener_ema_extensions()
        return screen_screener_ema_extensions(longs, shorts)
    elif tab == 'tab-13':
        df_tab_13 = calculation_retest_bands(data)
        return screen_ema_retests(df_tab_13, stock)
    elif tab == 'tab-14':
        names = ["excels/LastFlipOpen/daily_flip_on_" + x + "_" + stock for x in ["weekly", "monthly", "quarterly"]]
        data = [load_data(names[x]) for x in range(0,3)] 
        names = ["excels/LastFlipOpen/weekly_flip_on_" + x + "_" + stock for x in ["monthly", "quarterly", "yearly"]]
        data = data + [load_data(names[x]) for x in range(0,3)] 
        return screen_last_flip_open(data, stock)
    elif tab == 'tab-15':
        df_tab_15 = load_data("excels/peaksoverview")
        colours_tab_15 = colour_painting_simple_table(df_tab_15, current_stock)
        return table_fig(df_tab_15, colours_tab_15)
    elif tab == 'tab-16':
        df_tab_16 = load_data("excels/gapsallsymbols")
        colours_tab_16 = colour_painting_simple_table(df_tab_16, current_stock)
        return table_fig(df_tab_16, colours_tab_16)
    elif tab == 'tab-17':
        df_tab_17 = load_data("excels/gaps/"+stock)
        fig_tab_17 = screen_gaps_stock(df_tab_17, stock)
        return title_stock(fig_tab_17, stock)
    elif tab == 'tab-18':
        df_tab_18 = load_data("excels/flips_detail_daily")
        colours_tab_18 = colour_painting_detailed_flips(df_tab_18, current_stock)
        return table_fig(df_tab_18, colours_tab_18)
    elif tab == 'tab-19':
        df_tab_19 = load_data("excels/flips_detail_weekly")
        colours_tab_19 = colour_painting_detailed_flips(df_tab_19, current_stock)
        return table_fig(df_tab_19, colours_tab_19)
    elif tab == 'tab-20':
        name_tab_20 = "excels/analysis/monthly_" + stock
        df_tab_20= load_data(name_tab_20)
        name_tab_21 = "excels/analysis/quarterly_" + stock
        df_tab_21 = load_data(name_tab_21)
        fig_tab_20 = screen_cycle_correlations(df_tab_20[1:], df_tab_21[1:], stock)
        return fig_tab_20
    else:
        pass #funciones que devuelvan Figs


if __name__ == "__main__":
    app.run(debug=True)







    


