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
    #YEARLY_OPEN = data_candles[2].index = '2026-01-01'
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
    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04)

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
        fig.add_hline(y=0, line_color="green", line_width=6, row=1, col=i + 1)
        fig.add_hline(y=1, line_color="red", line_width=6, row=1, col=i + 1)
        fig.add_hline(y=0.5, line_color="gray", opacity=0.5, row=1, col=i + 1)

        # Annotations
        for xi, yi in zip(x_vals, y_vals):
            fig.add_annotation(
                x=xi,
                y=yi,
                text=f"{yi*100:.0f}%", # red probability
                showarrow=False,
                yshift=13,
                font=dict(size=12, color="red", family="Arial Black"),
                row=1,
                col=i + 1
            )
            fig.add_annotation(
                x=xi,
                y=yi,
                text=f"{(1-yi)*100:.0f}%", # green probability (inverse of red probability)
                showarrow=False,
                yshift=-14,
                font=dict(size=12, color="green", family="Arial Black"),
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
    return fig


def screen_rsi_plotly(rsiReversalZones, currentRsi):
    timeframes = ["Daily", "Weekly", "Monthly"]
    parameters = [0.50, 0.55, 0.59]

    fig = make_subplots(
        rows=2,
        cols=3,
        vertical_spacing=0.10,
        horizontal_spacing=0.04
    )

    # ---------- ROW 1: RSI charts ----------
    for i in range(len(rsiReversalZones)):
        df_rsi = rsiReversalZones[i]

        fechas, rsi = clean_timestamp_rsi(df_rsi)

        # RSI scatter
        fig.add_trace(
            go.Scatter(
                x=fechas,
                y=rsi,
                mode="markers",
                marker=dict(color="blue", size=6),
                showlegend=False
            ),
            row=1,
            col=i + 1
        )

        # Current RSI
        rsi_dict = currentRsi[i]
        rsi_time = list(rsi_dict.keys())[0]
        rsi_value = list(rsi_dict.values())[0]

        fig.add_hline(
            y=rsi_value,
            line_color="orange",
            line_width=2,
            row=1,
            col=i + 1
        )

        fig.add_hline(
            y=parameters[i],
            line_color="gray",
            opacity=0.5,
            row=1,
            col=i + 1
        )

        fig.add_trace(
            go.Scatter(
                x=[rsi_time],
                y=[rsi_value],
                mode="markers",
                marker=dict(color="orange", size=12),
                showlegend=False
            ),
            row=1,
            col=i + 1
        )

        fig.update_xaxes(
            title_text=f"RSI {timeframes[i]}: {int(rsi_value)}",
            row=1,
            col=i + 1
        )
    return fig


def screen_ema_extension_plotly(ema_extensions, stock, k):
    col_name_ema = ["extension_ema10", "extension_ema50", "extension_ema100", "extension_ema200"]
    timeframes = ["DAILY","WEEKLY","MONTHLY"]
    EMAS = ["10","50","100","200"]
    titles = []
    t = 0
    text = ""
    e = 0
    if k == 1:
        e = 2

    for a in range (0,6):
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
        if a == 2:
            t = 0
            e = e + 1  

    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.15, horizontal_spacing=0.05,subplot_titles=[titles[0],titles[1],titles[2],titles[3],titles[4],titles[5]])

    for i in range(3):
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

        fig.update_layout(margin=dict(l=30, r=30, t=75, b=30))
    return fig


def colour_painting(df, name, current_colours, current_stock_pos):
    print("start")
    colours = []
    if name == "flips":
        for i, col in enumerate(df.columns):
            if i == 0:
                colours.append(["white"] * len(df))
            elif i <= 5:
                colours.append(["lightgreen"] * len(df))
            else:
                colours.append(["lightblue"] * len(df))
    elif name == "returns":
        for i, col in enumerate(df.columns):
            if i == 0:
                colours.append(["white"] * len(df))
            elif i <= 5:
                colours.append(["lightgreen"] * len(df))
            else:
                colours.append(["lightblue"] * len(df))

    print("BEFORE")
    for x in range (0, len(colours)): # i highlight the current stock
        if x == 0:
            colours[x][current_stock_pos] = "#a6a6a6"        
        elif x <= 5:
            colours[x][current_stock_pos] = "#a6a6a6"   
        else:        
            colours[x][current_stock_pos] = "#a6a6a6"
    print("AFTER")

    if not current_colours.empty: # i override the current flips of opens situation in weekly and monthly
        i = 0
        for row in current_colours.itertuples(index=False):
            row_columns = list(row)
            posWeekly = row_columns[1] + 1
            posMonthly = row_columns[3] + 6
            if i != current_stock_pos:
                colours[posWeekly][i] = "yellow"
                colours[posMonthly][i] = "yellow"
            else:
                colours[posWeekly][i] = "lightyellow"
                colours[posMonthly][i] = "lightyellow"

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
