import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statistics_calculations import *

def title_stock(fig, stock):
    fig.update_layout(margin=dict(l=30, r=30, t=75, b=75), title={'text': stock,'x': 0.5,'y': 0.98,'xanchor': 'center','yanchor': 'top', 'font': {'size': 20, 'color': 'purple'}})
    return fig

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

    
    fig, future_dates = margin_right(fig, df)
    # #CURRENT PRICE
    fig = add_current_price(fig, current_price, future_dates, df)
    #WEEKLY OPEN
    fig = add_timeframe_open(fig, data_candles[1], "Weekly", "red", future_dates)
    # MONTHLY OPEN
    fig = add_timeframe_open(fig, data_candles[2], "Monthly", "purple", future_dates)
    # Obtenemos todas las fechas del rango (desde el inicio al fin)
    #all_dates = pd.date_range(start=df.index.min(), end=df.index.max())
    ## Buscamos qué fechas NO están en nuestros datos (fines de semana + festivos) #### lo puedo añadir cuando calcule opens con dias con datos
    #holidays = all_dates.difference(df.index)
    #fig.update_xaxes(rangebreaks=[dict(bounds=["sat","mon"])])
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


def screen_strikes_plotly(probabilities, colours, stock):
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
    fig.update_layout(height=1000, width=None, plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=30, r=30, t=75, b=30))
    fig = title_stock(fig, stock)
    return fig


def screen_rsi_plotly(data, stock):
    timeframes = ["Daily", "Weekly", "Monthly"]
    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["DAILY RSI","WEEKLY RSI","MONTHLY RSI"])

    for i in range(len(data)):
        df = data[i]

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
    fig = title_stock(fig, stock)
    return fig


def screen_ema_extension_plotly(ema_extensions, stock, k):
    col_name_ema = ["extension_ema10", "extension_ema20", "extension_ema50", "extension_ema200"]
    timeframes = ["DAILY","WEEKLY","MONTHLY"]
    EMAS = ["10","20","50","200"]
    titles = []
    t, e = 0, 0
    text = ""
    if k == 1:
        timeframes = ["DAILY","WEEKLY"]
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
    fig = title_stock(fig, stock)
    return fig


def screen_screener_ema_extensions(longs, shorts):
    fig = make_subplots(rows=1, cols=2, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["LONG SET-UPS", "SHORT SET-UPS"], specs=[[{"type": "domain"}, {"type": "domain"}]])

    fig_long_base = table_fig_variation(longs)
    fig_shorts_base = table_fig_variation(shorts)

    fig.add_trace(fig_long_base.data[0], row=1, col=1)
    fig.add_trace(fig_shorts_base.data[0], row=1, col=2)

    fig.update_layout(height=800, template="plotly_white", title_text="Percentiles EMA Set-Ups", title_x=0.5)    
    return fig


def screen_deviations(data, stock):
    fig = make_subplots(
        rows=2, cols=3, 
        vertical_spacing=0.12, 
        horizontal_spacing=0.04, 
        subplot_titles=["DAILY DEVIATIONS (GREEN)", "WEEKLY DEVIATIONS (GREEN)", "MONTHLY DEVIATIONS (GREEN)", "DAILY DEVIATIONS (RED)", "WEEKLY DEVIATIONS (RED)", "MONTHLY DEVIATIONS (RED)"])
    extra_days = 200
    for i in range(len(data)):
        df = data[i]
        df_green = df[df["type"] == "Green"]
        df_red = df[df["type"] == "Red"]
        k = 0
        current_time = df.index[-1] + pd.Timedelta(days=extra_days)
        candle = df.iloc[-1]
        current_value = [((candle['Open'] - candle['Low']) / candle['Open'])*100, ((candle['High'] - candle['Open']) / candle['Open'])*100]
        cont = 0

        for df_for in [df_green, df_red]:      
            if current_value[cont] < df_for["Deviation"].quantile(0.90):
                ext = df_for["Deviation"]
                low, high = np.percentile(ext, [0.5, 95])
                y_range = np.clip(ext, low, high)
            elif current_value[cont] >= df_for["Deviation"].quantile(0.90):
                ext = df_for["Deviation"]
                low, high = np.percentile(ext, [0.5, 99.5])
                y_range = np.clip(ext, low, high)
            
            fig.add_trace(go.Scatter(x=df_for.index, y=y_range, mode="markers", marker=dict(color="steelblue", size=5), showlegend=False, opacity=0.75),
                row=1+k, col=i + 1) 
            
            percentil_name = ["p90", "p80", "p50", "p20", "p10"]
            percentil_color = ["black", "black", "red", "black", "black"]
            percentil_value = [0.90, 0.80, 0.50, 0.20, 0.10]
            percentil_location = ["top right", "top right", "top right", "top right", "bottom right"]
            for p in range (0, len(percentil_value)):
                percentil = df_for["Deviation"].quantile(percentil_value[p])
                fig.add_hline(line_width=2, row=1+k, col = i+1, annotation_position=percentil_location[p], annotation_font_size=13, annotation_font_color="black",
                y=percentil,  
                line_color=percentil_color[p], 
                annotation_text=percentil_name[p]) 
            fig.add_hline(y=current_value[cont], line_color="#E9B300", line_dash = 'dot', line_width=5, row=1+k, col=i + 1,
                annotation_text=f" {current_value[cont]:.2f}%",
                annotation_position="right", 
                annotation_font_size=13,
                annotation_font_color="blue")
            fig.add_trace(go.Scatter(x=[current_time], y=[current_value[cont]], mode="markers", marker=dict(color="#FFC400", size=14), showlegend=False), row=1+k, col=i + 1)  
            k = k + 1
            cont = cont + 1

    fig = title_stock(fig, stock)
    return fig


def screen_ema_retests(data, stock):
    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["DAILY BANDS RETEST","WEEKLY BANDS RETEST","MONTHLY BANDS RETEST"])

    for i in range(len(data)):
        l = len(data[i])-1
        df = data[i][0:l]
        current_time = data[i]["Date"].iloc[-1]
        current_value = data[i]["TimeAway"].iloc[-1]
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["TimeAway"], mode="markers", marker=dict(color="steelblue", size=8), showlegend=False),
            row=1,
            col=i + 1
        )
        percentil_name = ["p95", "p80", "p50", "p20"]
        percentil_color = ["black", "black", "red", "black"]
        percentil_value = [0.95, 0.80, 0.50, 0.20]
        percentil_location = ["top right", "top right", "top right", "bottom right"]
        for p in range (0, len(percentil_value)):
            percentil = df["TimeAway"].quantile(percentil_value[p])
            fig.add_hline(line_width=2, row=1, col = i+1, annotation_position=percentil_location[p], annotation_font_size=13, annotation_font_color="black",
                y=percentil,  
                line_color=percentil_color[p], 
                annotation_text=percentil_name[p])   
        fig.add_hline(y=current_value, line_color="#E9B300", line_dash = 'dot', line_width=4, row=1, col=i + 1,
                annotation_text=f" {current_value:.0f}",
                annotation_position="right", 
                annotation_font_size=13,
                annotation_font_color="blue")
        fig.add_trace(go.Scatter(x=[current_time], y=[current_value], mode="markers", marker=dict(color="#FFC400", size=14), showlegend=False), row=1, col=i + 1)  
               
    fig.update_layout(margin=dict(l=40, r=40, t=75, b=30))
    fig = title_stock(fig, stock)
    return fig


def screen_last_flip_open(data, stock):
    try:
        fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["Last Daily Flip on Weekly Open","Last Daily Flip on Monthly Open","Last Daily Flip on Quarterly Open", "Last Weekly Flip on Monthly Open","Last Weekly Flip on Quarterly Open", "Last Weekly Flip on Yearly Open"])
        r = 1
        c = 1
        for i in range(len(data)):
            if i == 3:
                c = 1
                r = 2
            l = len(data[i])-1
            df = data[i][0:l]
            current_time = data[i].index[-1]
            current_value = data[i]["LastFlip"].iloc[-1]
            if i != 0 and i != 3:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df["LastFlip"], mode="markers", marker=dict(color="steelblue", size=10), showlegend=False),
                    row=r,
                    col=c
                )
                percentil_name = ["p95", "p80", "p50", "p20"]
                percentil_color = ["black", "black", "purple", "black"]
                percentil_value = [0.95, 0.80, 0.50, 0.20]
                percentil_location = ["top right", "top right", "top right", "bottom right"]
                for p in range (0, len(percentil_value)):
                    percentil = df["LastFlip"].quantile(percentil_value[p])
                    fig.add_hline(line_width=2, row=r, col = c, annotation_position=percentil_location[p], annotation_font_size=13, annotation_font_color="black",
                        y=percentil,  
                        line_color=percentil_color[p], 
                        annotation_text=percentil_name[p])
    
                fig.add_hline(y=current_value, line_color="#E9B300", line_dash = 'dot', line_width=4, row=r, col = c, annotation_text=f" {current_value:.0f}", annotation_position="right", annotation_font_size=13, annotation_font_color="blue")
                fig.add_trace(go.Scatter(x=[current_time], y=[current_value], mode="markers", marker=dict(color="#FFC400", size=14), showlegend=False), row=r, col = c)  
            else:
                orden = [1, 2, 3, 4, 5, 6, 7]
                df_counts = df["LastFlip"].value_counts().reindex(orden).fillna(0)
                df_pct = (df_counts / df_counts.sum()) * 100
                fig.add_trace(
                    go.Bar(
                        x=df_pct.index, 
                        y=df_pct.values, 
                        name="Probabilidad %",
                        marker_color='steelblue',
                        opacity=0.8,
                        text=[f"{val:.1f}%" for val in df_pct.values],
                        textposition='outside'
                    ),
                    row=r, col=c
                )
            c = c + 1
        fig = title_stock(fig, stock)
    except Exception as e:
        print(e)
    return fig


def screen_gaps_stock(df, stock): # gaps abiertos, ratio de filling y closing segun el % de gap, distribucion tiempo en cerrarse
    try:
        fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.02, subplot_titles=["OPEN GAPS","RATIO CLOSING","DISTRIBUTION DAYS TO CLOSE"], specs=[[{"type": "table"}, {"type": "table"}, {"type": "xy"}],[{"type": "xy"}, {"type": "xy"}, {"type": "xy"}]])
        df_aux = df[df["Status"] == "Open"]
        df_open_gaps = df_aux[["Date","GapSize","DaysOpen","GapHigh","GapLow"]]
        df_open_gaps = df_open_gaps.sort_values(by="Date", ascending=False)
        df_open_gaps["Date"] = pd.to_datetime(df_open_gaps["Date"]).dt.strftime("%Y-%m-%d")
        fig_open_gaps = table_fig_variation(df_open_gaps)
        fig.add_trace(fig_open_gaps.data[0], row=1, col=1)

        df_ratios = pd.DataFrame(columns=["Symbol", "GapSize", "Total Gaps", "Closed Ratio", "Days to Close p10", "Days to Close p20", "Days to Close p50", "Days to Close p80", "Days to Close p90"])
        for i in range (1, 4):
            p0 = round(df["GapSize"].quantile((i-1)*0.25),1)
            p1 = round(df["GapSize"].quantile(i*0.25),1)
            df_range = df[(df["GapSize"] >= p0) & (df["GapSize"] < p1)]
            df_range_closed = df_range[df_range["Status"] == "Closed"]
            percentiles = [round(df_range_closed["DaysOpen"].quantile(i), 1) for i in (0.10,0.20,0.50,0.80,0.90)]
            df_ratios.loc[len(df_ratios)] = [stock, str(p0) + "-" + str(p1), len(df_range), round(len(df_range[df_range["Status"] == "Closed"])/len(df_range), 2), percentiles[0], percentiles[1], percentiles[2], percentiles[3], percentiles[4]]
        fig_ratios = table_fig_variation(df_ratios)
        fig.add_trace(fig_ratios.data[0], row=1, col=2)

        df_closed = df[df["Status"] == "Closed"] 
        ext_df = df_closed[df_closed["DaysOpen"] <= df_closed["DaysOpen"].quantile(0.9)] #represento p0 a p90 de dias en cerrarse
        y_range = ext_df["DaysOpen"]
        fig.add_trace(go.Scatter(x=df_closed["Date"], y=y_range, mode="markers", marker=dict(color="steelblue", size=5), showlegend=False), row=1, col=3)
        return fig
    except Exception as e:
        print(e)



def screen_cycle_correlations(df1, df2, stock):
    df_green1 = df1[df1["Direction"] == "Green"]
    df_red1 =  df1[df1["Direction"] == "Red"]
    df_green2 = df2[df2["Direction"] == "Green"]
    df_red2 =  df2[df2["Direction"] == "Red"]
    fig = make_subplots(rows=2, cols=4, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["Num Flips x Returns (Green)[MONTHLY]", "Day Last Flip x Returns (Green)[MONTHLY]", "Num Flips x Returns (Red)[MONTHLY]", "Day LastFlip x Returns (Red)[MONTHLY]", "Num Flips x Returns (Green)[QUARTERLY]", "Week Last Flip x Returns (Green)[QUARTERLY]", "Num Flips x Returns (Red)[QUARTERLY]", "Week LastFlip x Returns (Red)[QUARTERLY]"])
    r, c = 1, 1
    color = "green"
    for df in [df_green1, df_red1, df_green2, df_red2]:
        fig.add_trace(go.Scatter(x=df["Flips"], y=df["Return"], mode="markers", marker=dict(color=color, size=12), showlegend=False), row=r, col=c)
        c = c + 1
        fig.add_trace(go.Scatter(x=df["LastFlip"], y=df["Return"], mode="markers", marker=dict(color=color, size=12), showlegend=False), row=r, col=c)
        if c == 2:
            c = c + 1
            color = "red"
        elif c == 4:
            r = 2
            c = 1
            color = "green"
    fig = title_stock(fig, stock)
    return fig



def colour_painting(df, name, current_colours, current_stock_pos):
    colours = []
    if name == "flips":
        for i, col in enumerate(df.columns):
            if i == 0:
                colours.append(["white"] * len(df))
            elif i <= 3:
                colours.append(["lightgreen"] * len(df))
            elif i <= 8:
                colours.append(["lightblue"] * len(df))
            elif i == 9 or i == 15: 
                colours.append(["lightgray"] * len(df))
            else:
                colours.append(["lightgreen"] * len(df))

    if current_stock_pos != -1:
        for x in range (0, len(colours)): # i highlight the current stock
            colours[x][current_stock_pos] = "#a6a6a6"        
    
    if not current_colours.empty: # i override the current flips of opens situation in weekly and monthly
        i = 0
        for row in current_colours.itertuples(index=False):
            row_columns = list(row)
            posWeekly = row_columns[1] + 1
            posMonthly = row_columns[3] + 4
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


def colour_painting_detailed_flips (df, current_stock_pos):
    colours = []    
    for i, col in enumerate(df.columns):
        column_colors = []
        for row_idx in range(len(df)):
            # Determinamos el "tipo" de fila según el patrón de 3
            row_pattern = row_idx % 3  # 0: Original/Gris, 1: Verde, 2: Rojo

            # Lógica por columnas (tu lógica original adaptada)
            if i == 0:
                if row_pattern == 0:
                    column_colors.append("#E1E6CF")
                else:
                    column_colors.append("white")
            elif i == 9 or i == 15: 
                column_colors.append("#E6CFE0")
            else:
                if row_pattern != 0:
                    if i > 0 and i <= 3:
                        column_colors.append("white")
                    elif i > 3 and i <= 8:
                        column_colors.append("white")
                    elif i > 9 and i <= 14:
                        column_colors.append("white")
                else:
                    column_colors.append("#E1E6CF")      
        colours.append(column_colors)

    if current_stock_pos != -1:
        for x in range (0, len(colours)): # i highlight the current stock
            colours[x][current_stock_pos*3] = "yellow"        
            colours[x][(current_stock_pos*3)+1] = "lightgreen"   
            colours[x][(current_stock_pos*3)+2] = "#FFB15C"
    print("i return colours")
    return colours


def colour_painting_simple_table(df, current_stock_pos):
    colours = []    
    k = 0
    for i, col in enumerate(df.columns):
        if k == 0:
            colours.append(["lightgray"] * len(df))
        elif k == 3:
            colours.append(["lightyellow"] * len(df))
        else:
            colours.append(["white"] * len(df))

    if current_stock_pos != -1:
        for x in range (0, len(colours)): # i highlight the current stock
            colours[x][current_stock_pos] = "yellow" 
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
    fig.update_layout(title="", margin=dict(l=10, r=10, t=20, b=0))
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

    fig.update_layout(title="", margin=dict(l=10, r=10, t=20, b=0))
    return fig
