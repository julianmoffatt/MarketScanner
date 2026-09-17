#pressure/absortion code, weekly and monthly charts
import glob, os, time
from backend.src.market_platform.data.storage import *
from backend.src.market_platform.data.ingestion import Assets 
from frontend.screens.screens_web import *
from backend.src.market_platform.data.data import *
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from functools import partial # para pasar mas de un parametro a la Pool de procesos
from itertools import product
from backend.src.market_platform.analytics.statistics_calculations import *
from backend.src.market_platform.analytics.deviations import *
from backend.src.market_platform.analytics.rsi import *
from backend.src.market_platform.analytics.screener_ema_extensions import *
from backend.src.market_platform.analytics.screener_retest_bands import *
from backend.src.market_platform.analytics.retest_bands import *
from backend.src.market_platform.analytics.strikes_candles import *
from backend.src.market_platform.analytics.quarter_patterns import *
from backend.src.market_platform.analytics.candle_patterns import *
from backend.src.market_platform.analytics.cash_session_direction import *
from backend.src.market_platform.analytics.drawdowns import *
from backend.src.market_platform.analytics.peaks import *
from backend.src.market_platform.analytics.gaps import *
from backend.src.market_platform.strategies.mean_reversion_distance import *
from backend.src.market_platform.backtesting.backtesting import *
from backend.src.market_platform.backtesting.mean_reversion import MeanReversion
from backend.src.market_platform.analytics.trend_strikes import *

def parameters_calculation_unpacked(args):
    symbol, param = args
    return parameters_calculation(symbol, pTimeframe=param)

def parameters_calculation_all_symbols():
    try:
        assets = Assets()
        timeframes_name = ["weekly", "monthly", "quarterly"]
        columns = ["Asset", "pWeekly", "p5", "p50", "p95"]
        columns.append("n"+str(timeframes_name[0][0]).upper())
        for i in range (0,3):
            columns.append(str(i) + " " + timeframes_name[0] + "_F")
        symbols = assets.getAssets("sp500")
        symbols = symbols[400:401].copy()
        parameters = [0.05*x for x in range(3, 20)]
        combos = list(product(symbols, parameters)) # Todas las combinaciones (símbolo, parámetro) — 500 × 14 = 7000 tareas
        data_rows = []
        with ProcessPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(parameters_calculation_unpacked, combos))
        data_rows = [r for r in results if r is not False]
        df = pd.DataFrame(data_rows, columns = columns).drop_duplicates()
        df = df.sort_values(by=["Asset", "pWeekly"])
        df["diff_below_0f"] = round(df["0 weekly_F"] - df["0 weekly_F"].shift(1), 2)
        df["diff_above_0f"] = round(df["0 weekly_F"] - df["0 weekly_F"].shift(-1), 2)
        df["total_diff_0f"] = round(abs(df["diff_below_0f"]) + abs(df["diff_above_0f"]), 2)
        idx_min = df.groupby("Asset")["pWeekly"].idxmin()
        idx_max = df.groupby("Asset")["pWeekly"].idxmax()
        df = df.drop(index=idx_min)
        df = df.drop(index=idx_max)

        df_all = pd.DataFrame()
        try:
            df1 = pd.read_csv("parametros_weekly.csv", index_col=0)
        except FileNotFoundError:
            df1 = pd.DataFrame()
        if df1.empty:
            df.to_csv("parametros_weekly.csv")
            df_all = df.copy()
        else:
            df_all = pd.concat([df1, df], ignore_index=True)
            df_all = df_all.drop_duplicates()
            df_all.to_csv("parametros_weekly.csv")

        result = df_all.loc[df_all.groupby("Asset")["total_diff_0f"].idxmin()]
        print(result.groupby("pWeekly").size())
        return df_all
    except Exception as e:
        print(e)
    

def parameters_calculation(symbol, pTimeframe):
    assets = Assets()
    TIMEFRAME_WEIGHT = round(pTimeframe, 2)
    data_candles = assets.loadStatistics(assets.loadTimeframes(symbol))
    if len(data_candles[0]) >= 2000:
        dfs = cycle_dynamics_parameters(symbol, data_candles, "daily", TIMEFRAME_WEIGHT, 1)
        config = [[0, 1, 2]] # 4, True para mon y quar
        new_row = [assets.name_sustitution(symbol), TIMEFRAME_WEIGHT]
        for i, df_item in enumerate(dfs):
            flips_to_show = config[i]
            counts = df_item["Flips"].value_counts().reindex(range(10), fill_value=0)
            for p in [0.05, 0.50, 0.95]:
                new_row.append(round(np.quantile(df_item["Threshold"], p), 2))
            total = counts.sum()
            new_row.append(round(total, 0))
            for f in flips_to_show:
                percentage = round((counts[f] / total) * 100, 1) if total > 0 else 0
                new_row.append(percentage)
        return new_row
    else: 
        return False


def cycle_dynamics_parameters(symbol, data, lower_timeframe, TIMEFRAME_WEIGHT, i):
    t = 0
    if i == 1:
        parameters = [pd.Timedelta(days=7)]
        timeframe = ["WEEKLY"]
    elif i == 2:
        parameters = [pd.offsets.MonthBegin(1)]
        timeframe = ["MONTHLY"]
    elif i == 3:
        parameters = [pd.offsets.MonthBegin(3)]
        timeframe = ["QUARTERLY"]
    
    LT = data[t][14:].copy()

    LT_vol, vol_p20, vol_p80 = Assets.calculate_volatility(LT["Close"])

    timeframes_cycles = []
    end = []
    for k in range(len(parameters)):
        end.append(pd.to_datetime((data[k+1+t].index[-1] + parameters[k]), utc=True))
    p = 0

    HT = data[i].copy()
    LT = LT[LT.index < end[i-1-t]]

    cycle = pd.DataFrame(columns=["Date", "Open", "Flips", "LastFlip", "Threshold", "Direction", "Return"])
    for x in range(0, len(HT)-1):
        df = LT[(LT.index >= HT.index[x]) & (LT.index < HT.index[x+1])]
        if df.empty:
            continue
        df_vol = LT_vol.reindex(df.index)
        print(timeframe[i-1-t], "| OPEN:", HT.iloc[x]["Open"], "| CLOSE:", HT.iloc[x]["Close"], "| DATE:", HT.index[x])
        params = cycle_dynamics_calculation(symbol, df, HT.iloc[x]["Open"], timeframe[p], df_vol, vol_p20, vol_p80, {timeframe[0]:TIMEFRAME_WEIGHT})
        cycle.loc[len(cycle)] = [HT.index[x], round(HT.iloc[x]["Open"], 1), params[0], params[1], params[2], HT.iloc[x]["type"], HT.iloc[x]["Return"]]
    df = LT[(LT.index >= HT.index[-1])]
    if not df.empty:
        df_vol = LT_vol.reindex(df.index)
        params = cycle_dynamics_calculation(symbol, df, HT.iloc[-1]["Open"], timeframe[p], df_vol, vol_p20, vol_p80, {timeframe[0]:TIMEFRAME_WEIGHT})
        cycle.loc[len(cycle)] = [HT.index[-1], round(HT.iloc[-1]["Open"],1), params[0], params[1], params[2], HT.iloc[x]["type"], HT.iloc[x]["Return"]]
    cycle.set_index("Date", inplace=True)
    timeframes_cycles.append(cycle)
    p += 1
    return timeframes_cycles

# FIBONACCI FOR TPS? CON RSI TAL VEZ, Y KEY LEVELS AND LIQUIDITY LEVELS I CAN DETECT ALSO WITH CODE
# STUDY OF LIQUIDITY GRABS
# PARA MEDIR LOS MOVIMIENTOS TENGO QUE UTILIZAR LA VOLATILIDAD DE LOS ULTIMOS AÑOS O ALGO Y HACERLO PROPORCIONAL
# study of trailing stops optimization
# multiple consecutive wicks detection for reversals !!!!  

tabs_styles = {
    'height': '60px',
    'alignItems': 'center',
    'backgroundColor': '#F0F2F5', 
}

tab_style = {
    'borderBottom': '1px solid #D6D6D6',
    'whiteSpace': 'nowrap',
    'padding': '0px',        
    'fontSize': '14px',      
    'backgroundColor': 'white',
    'color': '#4A4A4A',      
    'lineHeight': '50px',    
    'fontWeight': '600' 
}

tab_selected_style = {
    'borderTop': '1px solid #007BFF', # Línea azul un poco más gruesa
    'borderBottom': 'none',
    'backgroundColor': 'white',
    'color': '#007BFF',
    'padding': '1px',
    'fontSize': '14px',
    'lineHeight': '50px',
    'fontWeight': 'bold'
}

ticker_options = [
    # INDEX
    {'label': '📊 S&P 500', 'value': '^GSPC'},
    # TECH GIANTS & SEMIS
    {'label': '🚀 ASTS - SpaceMobile', 'value': 'ASTS'},
    {'label': '🚀 ROCKETLAB', 'value': 'RKLB'},
    {'label': '⚡ NBIS', 'value': 'NBIS'},
    {'label': '💾 MU - Micron Technology', 'value': 'MU'},
    {'label': '🟢 NVDA - Nvidia', 'value': 'NVDA'},
    {'label': '🔍 GOOGL - Alphabet', 'value': 'GOOGL'},
    {'label': '🍎 AAPL - Apple', 'value': 'AAPL'},
    {'label': '📦 AMZN - Amazon', 'value': 'AMZN'},
    {'label': '🏎️ AMD - Micro Devices', 'value': 'AMD'},
    {'label': '💻 MSFT - Microsoft', 'value': 'MSFT'},
    {'label': '🍿 NFLX - Netflix', 'value': 'NFLX'},
    {'label': '📱 META - Meta Platforms', 'value': 'META'},
    {'label': '☁️ ORCL - Oracle', 'value': 'ORCL'},
    {'label': '🔵 INTC - Intel', 'value': 'INTC'},
    {'label': '⚡ TSLA - Tesla', 'value': 'TSLA'},
    {'label': '👁️ PLTR - Palantir', 'value': 'PLTR'},
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
    {'label': '🔷 ETH-USD - Ethereum', 'value': 'ETH-USD'},
    {'label': '🟢 EURUSD', 'value': 'EURUSD=X'},
    {'label': '🟢 GBPUSD', 'value': 'GBPUSD=X'}, 
    {'label': '🟢 USDJPY', 'value': 'USDJPY=X'}
]

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div([
        html.Div(style={'flex': '1'}),

        html.Div([
            html.Label("Asset:", style={'color': 'white', 'margin-right': '15px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                id='ticker-selector',
                options=ticker_options,
                value='^GSPC',
                clearable=False,
                searchable=True,
                style={'width': '280px', 'blue': 'black'}
            ),
        ], style={'display': 'flex', 'alignItems': 'center', 'flex': '1', 'justifyContent': 'center'}),

        html.Div([
            html.Span(id="clear-all-status", style={'margin-right': '10px', 'color': '#848E9C', 'font-size': '12px'}),
            html.Button(
                "UPDATE DATA", 
                id="btn-clear-all", 
                n_clicks=0,
                style={
                    'backgroundColor': "#ffffff",
                    'color': "#0C0C0C",
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
        dcc.Tab(label='D', value='tab-1', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='W', value='tab-2', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='M', value='tab-3', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='ema 10/20', value='tab-4', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='ema 50/200', value='tab-5', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Flips(D)', value='tab-9', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Flips(M)', value='tab-209', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Flips(Q)', value='tab-210', style=tab_style, selected_style=tab_selected_style),
        #dcc.Tab(label='FLIPS(W)', value='tab-10', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='+Flips(D)', value='tab-18', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='LF', value='tab-14', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='DEV', value='tab-6', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Dev(Trend)', value='tab-102', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Strikes', value='tab-7', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='RSI', value='tab-8', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='ema 1h/4h', value='tab-23', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='MR(LT)', value='tab-24', style=tab_style, selected_style=tab_selected_style), 
        dcc.Tab(label='MR(HT)', value='tab-13', style=tab_style, selected_style=tab_selected_style),
        #dcc.Tab(label='OPEN GAPS', value='tab-17', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='F-LFxR%', value='tab-20', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='LFxPEAK', value='tab-21', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='SMxR%', value='tab-29', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Ovr.SMxR%', value='tab-31', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Peaks', value='tab-15', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Gaps', value='tab-16', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Vol', value='tab-26', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='R%', value='tab-27', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Cash.S.', value='tab-25', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Q.Pattern', value='tab-100', style=tab_style, selected_style=tab_selected_style),
        #dcc.Tab(label='Drawdowns', value='tab-101', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Params', value='tab-103', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Scr.Ext', value='tab-12', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Candles', value='tab-104', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Backtesting', value='tab-404', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='EMA Trends', value='tab-405', style=tab_style, selected_style=tab_selected_style)
        #dcc.Tab(label='Scr.Cr', value='tab-30', style=tab_style, selected_style=tab_selected_style),
        #dcc.Tab(label='Test', value='tab-test', style=tab_style, selected_style=tab_selected_style)
    ]
    ),

    html.Div(
        dcc.Graph(
            id='graph',
            style={
                'width': '100%',
                'height': '90vh', 
            }
        ),
        style={'margin': '0', 'padding': '0'}
    )
], style={
    'backgroundColor': '#1e1e1e', 
    'margin': '0', 
    'padding': '0', 
    'minHeight': '100vh',
    'width': '98vw'
})

@app.callback(
    Output('clear-all-status', 'children'),
    Input('btn-clear-all', 'n_clicks'),
    prevent_initial_call=True
)

def bulk_clear_cache(n_clicks):
    database = Database()
    ruta = database.symbol_url()
    archivos = glob.glob(os.path.join(ruta, "*.csv"))        
    eliminados = 0
    for f in archivos:
        try:
            os.remove(f)
            eliminados += 1
        except Exception as e:
            print(f"No se pudo borrar {f}: {e}")            
    return f"{eliminados} files deleted"


def load(name):
    database = Database()
    routes = {"flips_daily": lambda: flips_calculation_all_symbols("daily"),
            "flips_daily_now": lambda: current_flips_calculation_all_symbols("daily"),  
            "flips_monthly": lambda: flips_calculation_all_symbols("monthly"),
            "flips_monthly_now": lambda: current_flips_calculation_all_symbols("monthly"),
            "flips_quarterly": lambda: flips_calculation_all_symbols("quarterly"),
            "flips_quarterly_now": lambda: current_flips_calculation_all_symbols("quarterly"), 
            "peaks_overview": lambda: calculation_cycle_peak_expansion_all_symbols(), 
            "gaps_overview": lambda: calculation_closing_gaps_all_symbols(), 
            "drawdowns_ema_10_20": lambda: calculation_drawdowns_ema_10_20(),
            "quarter_patterns": lambda: calculation_patterns(),
            "cash_session_open_momentum": lambda: calculation_cashsession_dynamics()}
    df = database.import_csv(name)
    if df is False:
        if name[0:4] == "gaps":
            return calculation_closing_gaps(name[6:])
        else:
            df = routes[name]()
            database.save_csv(df, name)
            return df
    return df


@app.callback(
    Output('graph', 'figure'),
    [Input('ticker-selector', 'value'),
     Input('tabs', 'value'),
     Input('btn-clear-all', 'n_clicks')]
)

def render_content(asset, tab, n_clicks):
    database = Database()
    assets = Assets()
    #ruta = "excels/dataframe_symbol/"
    #if not os.listdir(ruta):
    #    print("DATABASE")
    #    getDataframesDatabase()
    
    data = assets.loadStatistics(assets.loadTimeframes(asset))
    current_stock = assets.getCurrentPos(assets.getAssets("mysymbols"), asset)
    #pe_ntm = yf.Ticker(stock).info.get("forwardPE")
    #print(pe_ntm)

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
        return screen_ema_extension_plotly(data, asset, -1)
    elif tab == 'tab-5':
        return screen_ema_extension_plotly(data, asset, 1)
    elif tab == 'tab-6':
        df_tab_6 = calculation_average_deviation(data)
        return screen_deviations(df_tab_6, asset)
    elif tab == 'tab-7':
        probabilities, colours  = calculation_StrikesProbabilities(data) 
        return screen_strikes_plotly(probabilities, colours, asset)
    elif tab == 'tab-8':
        df_tab_8 = calculation_Rsi(data) 
        return screen_rsi_plotly(df_tab_8, asset)
    elif tab == 'tab-9':
        df_tab_9 = load("flips_daily")
        current_flips = load("flips_daily_now")
        colours = colour_painting(df_tab_9, "flips", current_flips, current_stock)
        return table_fig(df_tab_9, colours)
    elif tab == 'tab-209':
        df_209 = load("flips_monthly")
        current_flips = load("flips_monthly_now")
        colours = colour_painting(df_209, "flips", current_flips, current_stock)
        return table_fig(df_209, colours)
    elif tab == 'tab-210':
        df_210 = load("flips_quarterly")
        current_flips = load("flips_quarterly_now")
        colours = colour_painting(df_210, "flips", current_flips, current_stock)
        return table_fig(df_210, colours)     
    elif tab == 'tab-12':
        longs, shorts = screener_ema_extensions()
        return screen_screener_ema_extensions(longs, shorts)
    elif tab == 'tab-14':
        names = ["excels/LastFlipOpen/daily_flip_on_" + x + "_" + asset for x in ["weekly", "monthly", "quarterly"]]
        data = [database.load_data(names[x]) for x in range(0,3)] 
        names = ["excels/LastFlipOpen/weekly_flip_on_" + x + "_" + asset for x in ["monthly", "quarterly", "yearly"]]
        data = data + [database.load_data(names[x]) for x in range(0,3)] 
        return screen_last_flip_open(data, asset)
    elif tab == 'tab-15':
        df_tab_15 = load("peaks_overview")
        colours_tab_15 = colour_painting_detailed_flips(df_tab_15, current_stock)
        return table_fig(df_tab_15, colours_tab_15)
    elif tab == 'tab-16':
        df_tab_16 = load("gaps_overview")
        colours_tab_16 = colour_painting_simple_table(df_tab_16, current_stock)
        return table_fig(df_tab_16, colours_tab_16)
    elif tab == 'tab-17':
        df_tab_17 = load("gaps_"+asset)
        fig_tab_17 = screen_gaps_stock(df_tab_17, asset)
        return title_stock(fig_tab_17, asset)
    elif tab == 'tab-18':
        df_tab_18 = database.load_data("excels/flips_detail_daily")
        colours_tab_18 = colour_painting_detailed_flips(df_tab_18, current_stock)
        return table_fig(df_tab_18, colours_tab_18)
    elif tab == 'tab-19':
        df_tab_19 = database.load_data("excels/flips_detail_weekly")
        colours_tab_19 = colour_painting_detailed_flips(df_tab_19, current_stock)
        return table_fig(df_tab_19, colours_tab_19)
    elif tab == 'tab-20':
        name_tab_20_1 = "excels/analysis/monthly_" + asset
        df_tab_20_1= database.load_data(name_tab_20_1)
        name_tab_20_2 = "excels/analysis/quarterly_" + asset
        df_tab_20_2 = database.load_data(name_tab_20_2)
        fig_tab_20 = screen_cycle_correlations(df_tab_20_1[1:], df_tab_20_2[1:], asset)
        return fig_tab_20
    elif tab == 'tab-21':
        name_tab_21_1 = "excels/LastFlipOpen/daily_flip_on_monthly_" + asset
        df_tab_21_1= database.load_data(name_tab_21_1)
        name_tab_21_2 = "excels/peaks/" + asset + "_monthly"
        df_tab_21_2 = database.load_data(name_tab_21_2)
        fig_tab_21 = screen_lastflip_x_peak(df_tab_21_1, df_tab_21_2, asset)
        return fig_tab_21
    elif tab == 'tab-23':
        data_tab_23 = getDataStock_LT(asset, True)
        df_tab_23 = assets.loadStatistics(data_tab_23)
        return screen_ema_extension_plotly(df_tab_23, asset, 10)
    elif tab == 'tab-13':
        df_tab_13 = calculation_retest_bands(data[0:3])
        return screen_ema_retests(df_tab_13, asset, 0)
    elif tab == 'tab-24':
        data_tab_24 = assets.loadStatistics(assets.loadLowerTimeframes(asset, True))
        df_tab_24 = calculation_retest_bands(data_tab_24)
        return screen_ema_retests(df_tab_24, asset, 1)
    elif tab == 'tab-25':
        data_tab_25 = load("cash_session_open_momentum")
        return table_fig_variation(data_tab_25)
    elif tab == 'tab-26':
        data_tab_26 = screen_volatility(data, asset)
        return data_tab_26
    elif tab == 'tab-27':
        data_tab_27 = screen_returns(data, asset)
        return data_tab_27
    elif tab == 'tab-28':
        df_tab_28 = database.load_data("flipsmonthly")
        df_tab_28 = database.load_data("flips_detail_monthly")
        colours_tab_28 = colour_painting_detailed_flips(df_tab_28, current_stock)
        return table_fig(df_tab_28, colours_tab_28)
    elif tab == 'tab-29':
        data_tab_29 = calculation_open_momentum(data)
        return screen_open_momentum(data_tab_29, asset)
    elif tab == 'tab-30':
        data_tab_30 = golden_cross_screener("daily")
        #return table_fig_variation(data_tab_30)
        data_tab_30_planning, data_tab_30_execution = calculation_12_25_cross()
        return screen_12_25_cross(data_tab_30_planning, data_tab_30_execution)
    elif tab == 'tab-31':
        data_tab_31 = calculation_open_momentum_all_symbols()
        return table_fig_variation(data_tab_31)
    elif tab == 'tab-test':
        df = test_strategy_all_symbols()
        print("ready to paint")
        return table_fig_variation(df)
    elif tab == 'tab-100':
        df_100 = load("quarter_patterns")
        colours_tab_100 = colour_painting_quarter_patterns(df_100, current_stock)
        return table_fig(df_100, colours_tab_100)
    elif tab == 'tab-101':
        df_101 = load("drawdowns_ema_10_20")
        colours_tab_101 = colour_painting_return_color(df_101, current_stock)
        return table_fig(df_101, colours_tab_101)
    elif tab == 'tab-102':
        df_102 = calculation_trend_deviation(data)
        return screen_trend_deviation(df_102, asset)
    elif tab == 'tab-103':
        df_103 = parameters_calculation_all_symbols()
        return table_fig_variation(df_103)
    elif tab == 'tab-104':
        df_104 = candle_pattern(data)
        return table_fig_variation(df_104)
    elif tab == "tab-404":
        strategys = [MeanReversion("Mean Reversion")]
        df_404 = backtesting(assets.getAssets("mysymbols"), strategys)
        equity_df = backtesting_equity_curve(asset, MeanReversion("Mean Reversion"))
        return screen_backtesting(df_404, equity_df, asset)
    elif tab == "tab-405":
        df_405 = calculation_ema_trends()
        return table_fig_variation(df_405)
    else:
        pass


if __name__ == "__main__":
    app.run(debug=True)







    


