import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statistics_calculations import *

def margin_right(fig, df):
    fig.update_layout(xaxis_rangeslider_visible=False)
    RIGHT_PADDING_BARS = 35 # ---- Right-side padding ----
    freq = pd.infer_freq(df.index) or 'D'
    future_dates = pd.date_range(start=df.index[-1],periods=RIGHT_PADDING_BARS + 1,freq=freq)
    fig.update_xaxes(range=[df.index[0], future_dates[-1]])
    return fig, future_dates

def add_current_price(fig, price, future_dates, df):
    current_price = round(price, 2)
    fig.add_trace(go.Scatter(x=[df.index[0], future_dates[-1]], y=[current_price, current_price], mode="lines", line=dict(color="black", width=1, dash="dash"), name="Price"))
    fig.add_annotation(x=1.01, xref="paper", y=current_price, yref="y", text=current_price, showarrow=False, xanchor="left", align="left", font=dict(color="black",size=20,family="Arial Black"),bgcolor="rgba(255,255,255,0.8)",borderpad=2)
    return fig

def add_timeframe_open(fig, df, timeframe, colour, future_dates):
    timeframe_open = df['Open'].iloc[-1]
    timeframe_open_time = df.index[-1]
    fig.add_trace(go.Scatter(x=[timeframe_open_time, future_dates[-1]], y=[timeframe_open, timeframe_open], mode="lines", line=dict(color=colour, width=5), name = timeframe + " Open"))
    fig.add_annotation(x=future_dates[-7],  xref="x", y=timeframe_open, yref = "y", text = timeframe +" open", showarrow=False, xanchor="left", yanchor="middle", font=dict(color="red",size=15,family="Arial Black"),bgcolor="rgba(255,255,255,0.8)",borderpad=2)
    return fig 
    

def screen_daily_chart (data_candles):
    df = data_candles[0].tail(50).copy()
    current_price = df["Close"].iloc[-1]
    df.index = pd.to_datetime(df.index)

    fig = go.Figure()

    # ---- Candlestick ----
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing=dict(fillcolor='white', line=dict(color='black')),
            decreasing=dict(fillcolor='black', line=dict(color='black')),
            showlegend=False
        )
    )

    # ---- Layout ----
    fig.update_layout(
        height=800,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )

    #fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig, future_dates = margin_right(fig, df)

    #CURRENT PRICE
    fig = add_current_price(fig, current_price, future_dates, df)
    #WEEKLY OPEN
    fig = add_timeframe_open(fig, data_candles[1], "Weekly", "red", future_dates)
    # MONTHLY OPEN
    fig = add_timeframe_open(fig, data_candles[2], "Monthly", "purple", future_dates)
    return fig


def screen_weekly_chart(data_candles):
    df = data_candles[1].tail(50).copy()
    current_price = df["Close"].iloc[-1]
    df.index = pd.to_datetime(df.index)

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing=dict(fillcolor='white', line=dict(color='black')),
            decreasing=dict(fillcolor='black', line=dict(color='black')),
            showlegend=False
        )
    )

    fig.update_layout(
        height=800,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )

    #fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig, future_dates = margin_right(fig, df)

    #CURRENT PRICE
    fig = add_current_price(fig, current_price, future_dates, df) 
    # MONTHLY OPEN
    fig = add_timeframe_open(fig, data_candles[2], "Monthly", "purple", future_dates)
    #YEARLY OPEN
    januarys = data_candles[2][(data_candles[2].index.month == 1)]
    fig = add_timeframe_open(fig, januarys, "Yearly", "Orange", future_dates)
    return fig


def screen_monthly_chart (data_candles):
    df = data_candles[2].tail(50).copy()
    current_price = df["Close"].iloc[-1]
    df.index = pd.to_datetime(df.index)

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing=dict(fillcolor='white', line=dict(color='black')),
            decreasing=dict(fillcolor='black', line=dict(color='black')),
            showlegend=False
        )
    )

    fig.update_layout(
        height=800,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )

    #fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig, future_dates = margin_right(fig, df)

    #CURRENT PRICE
    fig = add_current_price(fig, current_price, future_dates, df)
    #YEARLY OPEN
    januarys = data_candles[2][(data_candles[2].index.month == 1)]
    fig = add_timeframe_open(fig, januarys, "Yearly", "Orange", future_dates)

    #YEARLY_OPEN = data_candles[2].index = '2026-01-01'
    return fig


def screen_strikes_plotly(probabilities, colours):
    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["DAILY CANDLES","WEEKLY CANDLES","MONTHLY CANDLES"])

    # ---------- ROW 2: Probabilities ----------
    for i in range(len(probabilities)):
        x_vals = list(range(len(probabilities[i])))
        y_vals = probabilities[i]

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers",
                marker=dict(
                    size=14,
                    color=colours[i],
                    opacity=0.7
                ),
                showlegend=False
            ),
            row=1,
            col=i + 1
        )

        # Horizontal reference lines
        fig.add_hline(y=0, line_color="green", opacity=0.75, line_width=6, row=1, col=i + 1)
        fig.add_hline(y=1, line_color="red", opacity=0.75, line_width=6, row=1, col=i + 1)
        fig.add_hline(y=0.5, line_color="gray", opacity=0.5, row=1, col=i + 1)

        # Annotations
        for xi, yi in zip(x_vals, y_vals):
            fig.add_annotation(
                x=xi,
                y=yi,
                text=f"{yi*100:.0f}%", # red probability
                showarrow=False,
                yshift=15,
                font=dict(size=15, color="red", family="Arial Black"),
                row=1,
                col=i + 1
            )
            fig.add_annotation(
                x=xi,
                y=yi,
                text=f"{(1-yi)*100:.0f}%", # green probability (inverse of red probability)
                showarrow=False,
                yshift=-16,
                font=dict(size=15, color="green", family="Arial Black"),
                row=1,
                col=i + 1
            )

        fig.update_yaxes(range=[-0.05, 1.05], row=1, col=i + 1)
        fig.update_xaxes(showticklabels=False, row=1, col=i + 1)

    # ---------- Layout ----------
    fig.update_layout(
        height=1000,
        width=None,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    fig.update_layout(margin=dict(l=30, r=30, t=75, b=30))
    return fig


def screen_rsi_plotly(data):
    timeframes = ["Daily", "Weekly", "Monthly"]
    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["DAILY RSI","WEEKLY RSI","MONTHLY RSI"])

    # ---------- RSI charts ----------
    for i in range(len(data)):
        df = data[i]

        # RSI scatter
        fig.add_trace(
            go.Scatter(x=df.index, y=df["rsi"], mode="markers", marker=dict(color="steelblue", size=5), showlegend=False),
            row=1,
            col=i + 1
        )

        # Current RSI
        rsi_time = df["rsi"].index[-1]
        rsi_value = df["rsi"].iloc[-1]

        p95 = df["rsi"].quantile(0.95)
        p50 = df["rsi"].quantile(0.50)
        p05 = df["rsi"].quantile(0.05)
        fig.add_hline(y=p95, line_color="black", line_width=3, row=1, col=i + 1)
        fig.add_hline(y=p50, line_color="gray", line_width=2, row=1, col=i + 1)
        fig.add_hline(y=p05, line_color="black", line_width=3, row=1, col=i + 1)        

        fig.add_trace(
            go.Scatter(x=[rsi_time], y=[rsi_value], mode="markers", marker=dict(color="orange", size=15), showlegend=False),
            row=1,
            col=i + 1
        )
        fig.add_hline(y=rsi_value, line_color="orange", line_width=2, row=1, col=i + 1) 

        fig.update_xaxes(
            title_text=f"RSI {timeframes[i]}: {int(rsi_value)}",
            row=1,
            col=i + 1
        )
    fig.update_layout(margin=dict(l=30, r=30, t=75, b=30))
    return fig


def screen_ema_extension_plotly(ema_extensions, stock, k):
    col_name_ema = ["extension_ema10", "extension_ema20", "extension_ema50", "extension_ema200"]
    timeframes = ["DAILY","WEEKLY","MONTHLY"]
    if k == 1:
        timeframes = ["DAILY","WEEKLY"]
    EMAS = ["10","20","50","200"]
    titles = []
    t = 0
    text = ""
    e = 0
    if k == 1:
        e = 2

    for a in range (0,2*(len(timeframes))):
        current_point = ema_extensions[t][col_name_ema[e]].iloc[-1]
        current_series = ema_extensions[t][col_name_ema[e]]
        df_high = current_series[current_series > 0]   # extended HIGH
        df_low = current_series[current_series < 0]   # extended LOW

        if current_point > 0:
            position = (df_high > current_point).sum() + 1
            text = str(position) + "th highest"
        elif current_point < 0:
            position = (df_low < current_point).sum() + 1
            text = str(position) + "th lowest"
        aux = timeframes[t] + " EMA " + EMAS[e] + " | " + text
        titles.append(aux)
        t = t + 1
        if a == (len(timeframes)-1):
            t = 0
            e = e + 1  

    fig = make_subplots(rows=2, cols=len(timeframes), vertical_spacing=0.11, horizontal_spacing=0.05,subplot_titles=titles)

    for i in range(len(timeframes)):
        for x in range (1,3):
            col_name = col_name_ema[x + k]
            df = ema_extensions[i]
            ext = df[col_name]
            current_ext = df[col_name].iloc[-1]
            p95 = df[col_name].quantile(0.95)
            p05 = df[col_name].quantile(0.05)
            low, high = np.percentile(ext, [0.05, 99.95])
            y_range = np.clip(ext, low, high)
            fechas = df.index

            fig.add_trace(
                go.Scatter(
                    x=fechas,
                    y=y_range,
                    mode="markers",
                    marker=dict(size=6, color="steelblue"),
                    showlegend=False,
                    name="Timeframe" + str(i)
                ),
                row=x,
                col=i + 1
            )
            current_time = df.index[-1]

            fig.add_trace(
                go.Scatter(
                    x=[current_time],
                    y=[current_ext],
                    mode="markers",
                    marker=dict(size=12, color="orange"),
                    showlegend=False
                ),
                row=x,
                col=i + 1
            )

            fig.add_hline(y=p95, line_color="black", opacity=0.7, row=x, col=i + 1)
            fig.add_hline(y=0, line_color="purple", opacity=0.6, row=x, col=i + 1)
            fig.add_hline(y=p05, line_color="black", opacity=0.7, row=x, col=i + 1)

        fig.update_layout(margin=dict(l=30, r=30, t=75, b=30), title={
        'text': stock,
        'x': 0.5,               # Posición horizontal al 50% (centro)
        'y': 0.98,
        'xanchor': 'center',    # El punto de anclaje del texto es su centro
        'yanchor': 'top',       # Anclaje superior para que no pise los gráficos
        'font': {'size': 20, 'color': 'purple'} # Ajusta el tamaño y color según tu tema
        })
    return fig


def screen_screener_ema_extensions(longs, shorts):
    fig = make_subplots(
        rows=1, cols=2, 
        vertical_spacing=0.10, 
        horizontal_spacing=0.04, 
        subplot_titles=["LONG SET-UPS", "SHORT SET-UPS"],
        specs=[[{"type": "domain"}, {"type": "domain"}]]
    )

    # Generamos las figuras base (asumiendo que devuelven go.Figure)
    fig_long_base = table_fig_variation(longs)
    fig_shorts_base = table_fig_variation(shorts)

    # Extraemos el "trace" (la tabla pura) y la posicionamos
    fig.add_trace(fig_long_base.data[0], row=1, col=1)
    fig.add_trace(fig_shorts_base.data[0], row=1, col=2)

    # Ajustes estéticos finales para que se vea profesional
    fig.update_layout(
        height=800, 
        template="plotly_white", 
        title_text="Comando de Momentum: Percentiles EMA",
        title_x=0.5
    )    
    return fig


def screen_deviations(data):
    fig = make_subplots(
        rows=2, cols=3, 
        vertical_spacing=0.12, 
        horizontal_spacing=0.04, 
        subplot_titles=["DAILY DEVIATIONS (GREEN)", "WEEKLY DEVIATIONS (GREEN)", "MONTHLY DEVIATIONS (GREEN)", "DAILY DEVIATIONS (RED)", "WEEKLY DEVIATIONS (RED)", "MONTHLY DEVIATIONS (RED)"])
    
    for i in range(len(data)):
        df = data[i]
        df_green = df[df["type"] == "Green"]
        df_red = df[df["type"] == "Red"]
        k = 0
        current_time = df.index[-1]
        candle = df.iloc[-1]
        current_value = [((candle['Open'] - candle['Low']) / candle['Open'])*100, ((candle['High'] - candle['Open']) / candle['Open'])*100]
        cont = 0

        for df_for in [df_green, df_red]:      
            if current_value[cont] < df_for["Deviation"].quantile(0.90):
                ext = df_for["Deviation"]
                low, high = np.percentile(ext, [0, 95])
                y_range = np.clip(ext, low, high)
            elif current_value[cont] >= df_for["Deviation"].quantile(0.90):
                ext = df_for["Deviation"]
                low, high = np.percentile(ext, [0, 100])
                y_range = np.clip(ext, low, high)
            
            fig.add_trace(go.Scatter(x=df_for.index, y=y_range, mode="markers", marker=dict(color="#66b2ff", size=5), showlegend=False),
                row=1+k, col=i + 1) 
            p90 = df_for["Deviation"].quantile(0.90)
            p80 = df_for["Deviation"].quantile(0.80)
            p50 = df_for["Deviation"].quantile(0.50)
            p20 = df_for["Deviation"].quantile(0.20)
            p10 = df_for["Deviation"].quantile(0.10)
            fig.add_hline(y=p90, line_color="black", line_width=3, row=1+k, col=i + 1)
            fig.add_hline(y=p80, line_color="black", line_width=3, row=1+k, col=i + 1,
                annotation_text=f" {p80:.2f}%",
                annotation_position="right",   
                annotation_font_size=13,
                annotation_font_color="black")
            fig.add_hline(y=p50, line_color="black", line_width=6, row=1+k, col=i + 1,
                annotation_text=f" {p50:.2f}%",
                annotation_position="right",   
                annotation_font_size=13,
                annotation_font_color="black")
            fig.add_hline(y=p20, line_color="black", line_width=3, row=1+k, col=i + 1,
                annotation_text=f" {p20:.2f}%",
                annotation_position="right", 
                annotation_font_size=13,
                annotation_font_color="black")
            fig.add_hline(y=p10, line_color="black", line_width=3, row=1+k, col=i + 1) 
            fig.add_hline(y=current_value[cont], line_color="#E9B300", line_dash = 'dot', line_width=4, row=1+k, col=i + 1)
            fig.add_trace(go.Scatter(x=[current_time], y=[current_value[cont]], mode="markers", marker=dict(color="#FFC400", size=14), showlegend=False), row=1+k, col=i + 1)  
            k = k + 1
            cont = cont + 1

    fig.update_layout(margin=dict(l=30, r=60, t=75, b=30), plot_bgcolor="#FFFEB7", paper_bgcolor="white")
    return fig


def colour_painting(df, name, current_colours, current_stock_pos):
    print("start")
    colours = []
    if name == "flips":
        for i, col in enumerate(df.columns):
            if i == 0:
                colours.append(["white"] * len(df))
            elif i <= 4:
                colours.append(["lightgreen"] * len(df))
            elif i <= 9:
                colours.append(["lightblue"] * len(df))
            else:
                colours.append(["lightgreen"] * len(df))
    elif name == "returns":
        for i, col in enumerate(df.columns):
            if i == 0:
                colours.append(["white"] * len(df))
            elif i <= 5:
                colours.append(["lightgreen"] * len(df))
            else:
                colours.append(["lightblue"] * len(df))
    else:
        for i, col in enumerate(df.columns):
            colours.append(["white"] * len(df))
        print("i got to the else")
        return colours

    if current_stock_pos != -1:
        for x in range (0, len(colours)): # i highlight the current stock
            if x == 0:
                colours[x][current_stock_pos] = "#a6a6a6"        
            elif x <= 4:
                colours[x][current_stock_pos] = "#a6a6a6"   
            else:        
                colours[x][current_stock_pos] = "#a6a6a6"

    if not current_colours.empty: # i override the current flips of opens situation in weekly and monthly
        i = 0
        for row in current_colours.itertuples(index=False):
            row_columns = list(row)
            posWeekly = row_columns[1] + 1
            posMonthly = row_columns[3] + 5
            posQuarterly = row_columns[5] + 10
            if i != current_stock_pos:
                colours[posWeekly][i] = "yellow"
                colours[posMonthly][i] = "yellow"
                colours[posQuarterly][i] = "yellow"
            else:
                colours[posWeekly][i] = "lightyellow"
                colours[posMonthly][i] = "lightyellow"
                colours[posQuarterly][i] = "lightyellow"

            i = i + 1
    print("i return colours")
    return colours


def table_fig(df, colours):
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=list(df.columns),
                    fill_color="black",
                    font=dict(color="white", size=12),
                    align="center"
                ),
                cells=dict(
                values=[df[col] for col in df.columns],
                fill_color=colours,
                font=dict(color="black", size=15),
                align="center",
                height=28   # prueba 28–40
                )
            )
        ]
    )

    fig.update_layout(
        title="",
        margin=dict(l=10, r=10, t=20, b=0)
    )
    return fig

def table_fig_variation(df):
    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=list(df.columns),
                    fill_color="black",
                    font=dict(color="white", size=12),
                    align="center"
                ),
                cells=dict(
                values=[df[col] for col in df.columns],
                font=dict(color="black", size=15),
                align="center",
                height=28   # prueba 28–40
                )
            )
        ]
    )

    fig.update_layout(
        title="",
        margin=dict(l=10, r=10, t=20, b=0)
    )
    return fig


#def screen_rsi_plotly(rsiReversalZones, currentRsi):
#    timeframes = ["Daily", "Weekly", "Monthly"]
#    parameters = [0.50, 0.55, 0.59]
#
#    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["DAILY RSI","WEEKLY RSI","MONTHLY RSI"])
#
#    # ---------- ROW 1: RSI charts ----------
#    for i in range(len(rsiReversalZones)):
#        df_rsi = rsiReversalZones[i]
#
#        fechas, rsi = clean_timestamp_rsi(df_rsi)
#
#        # RSI scatter
#        fig.add_trace(
#            go.Scatter(
#                x=fechas,
#                y=rsi,
#                mode="markers",
#                marker=dict(color="blue", size=6),
#                showlegend=False
#            ),
#            row=1,
#            col=i + 1
#        )
#
#        # Current RSI
#        rsi_dict = currentRsi[i]
#        rsi_time = list(rsi_dict.keys())[0]
#        rsi_value = list(rsi_dict.values())[0]
#
#        fig.add_hline(
#            y=rsi_value,
#            line_color="orange",
#            line_width=2,
#            row=1,
#            col=i + 1
#        )
#
#        fig.add_hline(
#            y=parameters[i],
#            line_color="gray",
#            opacity=0.5,
#            row=1,
#            col=i + 1
#        )
#
#        fig.add_trace(
#            go.Scatter(
#                x=[rsi_time],
#                y=[rsi_value],
#                mode="markers",
#                marker=dict(color="orange", size=12),
#                showlegend=False
#            ),
#            row=1,
#            col=i + 1
#        )
#
#        fig.update_xaxes(
#            title_text=f"RSI {timeframes[i]}: {int(rsi_value)}",
#            row=1,
#            col=i + 1
#        )
#    fig.update_layout(margin=dict(l=30, r=30, t=75, b=30))
#    return fig
