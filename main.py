#pressure/absortion code, weekly and monthly charts
import os
from functions import *
from sp500 import *
from statistics_calculations import *
from screens_web import *
from data import *
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

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
    #{'label': 'S&P 500', 'value': '^GSPC'},
    # TECH GIANTS & SEMIS
    {'label': '🚀 ASTS - SpaceMobile', 'value': 'ASTS'},
    {'label': '⛏️ IREN - Iris Energy', 'value': 'IREN'},
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
    html.Div([
        html.Div(style={'flex': '1'}),

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
        dcc.Tab(label='MEAN REV.', value='tab-13', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='LAST FLIP', value='tab-14', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='PEAKS', value='tab-15', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='GAPS', value='tab-16', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='OPEN GAPS', value='tab-17', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='+FLIPS (D)', value='tab-18', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='+FLIPS (W)', value='tab-19', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='F-LFxR%', value='tab-20', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='LFxPeak', value='tab-21', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='Test', value='tab-22', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='1h/4h Ext', value='tab-23', style=tab_style, selected_style=tab_selected_style),
        dcc.Tab(label='1h/4h MR', value='tab-24', style=tab_style, selected_style=tab_selected_style), 
        dcc.Tab(label='CashSession', value='tab-25', style=tab_style, selected_style=tab_selected_style)
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
    import glob, os, time
    ruta = "excels/dataframe_symbol/"
    archivos = glob.glob(os.path.join(ruta, "*.csv"))
    
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
    
    timeframes = getDataStock(stock) 
    data = preparingData(timeframes) 
    current_stock = getCurrentStockPos(stock)

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
        probabilities, colours  = calculation_StrikesProbabilities(data) 
        return screen_strikes_plotly(probabilities, colours, stock)
    elif tab == 'tab-8':
        df_tab_8 = calculation_Rsi(data) 
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
        return screen_ema_retests(df_tab_13, stock, 0)
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
        name_tab_20_1 = "excels/analysis/monthly_" + stock
        df_tab_20_1= load_data(name_tab_20_1)
        name_tab_20_2 = "excels/analysis/quarterly_" + stock
        df_tab_20_2 = load_data(name_tab_20_2)
        fig_tab_20 = screen_cycle_correlations(df_tab_20_1[1:], df_tab_20_2[1:], stock)
        return fig_tab_20
    elif tab == 'tab-21':
        name_tab_21_1 = "excels/LastFlipOpen/daily_flip_on_monthly_" + stock
        df_tab_21_1= load_data(name_tab_21_1)
        name_tab_21_2 = "excels/peaks/" + stock + "_monthly"
        df_tab_21_2 = load_data(name_tab_21_2)
        fig_tab_21 = screen_lastflip_x_peak(df_tab_21_1, df_tab_21_2, stock)
        return fig_tab_21
    elif tab == 'tab-22':
        df = test_strategy_all_symbols()
        return table_fig_variation(df)
    elif tab == 'tab-23':
        data_tab_23 = getDataStock_LT(stock)
        df_tab_23 = calculation_ema_extension(data_tab_23)
        return screen_ema_extension_plotly(df_tab_23, stock, 10)
    elif tab == 'tab-24':
        data_tab_24 = getDataStock_LT(stock)
        df_tab_24 = calculation_retest_bands(data_tab_24)
        return screen_ema_retests(df_tab_24, stock, 1)
    elif tab == 'tab-25':
        data_tab_25 = calculation_cashsession_dynamics()
        print("Llega a volver")
        return table_fig_variation(data_tab_25)
    else:
        pass


if __name__ == "__main__":
    app.run(debug=True)







    


