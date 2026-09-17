from frontend.screens.screen_components import *

def screen_daily_chart (data_candles):
    df = data_candles[0].tail(50).copy()
    current_price = df["Close"].iloc[-1]
    df.index = pd.to_datetime(df.index)
    fig = candlestick_chart(df)    
    fig, future_dates = margin_right(fig, df)   
    fig = add_current_price(fig, current_price, future_dates, df) # #CURRENT PRICE
    fig = add_timeframe_open(fig, data_candles[1], "Weekly", "red", future_dates) #WEEKLY OPEN
    fig = add_timeframe_open(fig, data_candles[2], "Monthly", "purple", future_dates) # MONTHLY OPEN
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
    fig = candlestick_chart(df)  
    #fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig, future_dates = margin_right(fig, df)
    fig = add_current_price(fig, current_price, future_dates, df) #CURRENT PRICE
    fig = add_timeframe_open(fig, data_candles[2], "Monthly", "purple", future_dates) # MONTHLY OPEN
    januarys = data_candles[2][(data_candles[2].index.month == 1)] #YEARLY OPEN
    fig = add_timeframe_open(fig, januarys, "Yearly", "Orange", future_dates)
    return fig


def screen_monthly_chart (data_candles):
    df = data_candles[2].tail(50).copy()
    current_price = df["Close"].iloc[-1]
    df.index = pd.to_datetime(df.index)
    fig = candlestick_chart(df)
    #fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    fig, future_dates = margin_right(fig, df)
    fig = add_current_price(fig, current_price, future_dates, df) #CURRENT PRICE
    januarys = data_candles[2][(data_candles[2].index.month == 1)] 
    fig = add_timeframe_open(fig, januarys, "Yearly", "Orange", future_dates) #YEARLY OPEN
    return fig


def screen_strikes_plotly(probabilities, colours, stock):
    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["DAILY CANDLES","WEEKLY CANDLES","MONTHLY CANDLES"])

    for i in range(len(probabilities)):
        x_vals = list(range(len(probabilities[i])))
        y_vals = probabilities[i]

        fig.add_trace(
            go.Scatter(x=x_vals, y=y_vals, mode="markers", marker=dict(size=14, color=colours[i], opacity=0.7), showlegend=False),
            row=1, col=i + 1)

        fig.add_hline(y=0, line_color="green", opacity=0.75, line_width=6, row=1, col=i + 1)
        fig.add_hline(y=1, line_color="red", opacity=0.75, line_width=6, row=1, col=i + 1)
        fig.add_hline(y=0.5, line_color="gray", opacity=0.5, row=1, col=i + 1)

        for xi, yi in zip(x_vals, y_vals):
            # red probability
            fig.add_annotation(x=xi, y=yi, text=f"{yi*100:.0f}%", showarrow=False, yshift=15, font=dict(size=15, color="red", family="Arial Black"),
                row=1, col=i + 1)
            # green probability (inverse of red probability)
            fig.add_annotation(x=xi, y=yi, text=f"{(1-yi)*100:.0f}%", showarrow=False, yshift=-16, font=dict(size=15, color="green", family="Arial Black"),
                row=1, col=i + 1)
        fig.update_yaxes(range=[-0.05, 1.05], row=1, col=i + 1)
        fig.update_xaxes(showticklabels=False, row=1, col=i + 1)

    fig.update_layout(height=1000, width=None, plot_bgcolor="white", paper_bgcolor="white", margin=dict(l=30, r=30, t=75, b=30))
    fig = title_stock(fig, stock)
    return fig


def screen_rsi_plotly(data, stock):
    fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["DAILY RSI","WEEKLY RSI","MONTHLY RSI"])

    for i in range(len(data)):
        df = data[i].copy()

        fig.add_trace(
            go.Scatter(x=df.index, y=df["rsi"], mode="markers", marker=dict(color="steelblue", size=5), showlegend=False),
            row=1, col=i + 1)

        rsi_value = df["rsi"].iloc[-1]
        percentil_value = [0.95, 0.50, 0.05]
        percentil_colour = ["black", "gray", "black"]
        percentil_name = ["p95", "p50", "p05"]
        percentil_location = ["top right" for _ in range(3)]
        fig = percentiles_and_currentValue(fig, df, 1, i+1, "rsi", rsi_value, df.index[-1], percentil_value, percentil_name, percentil_colour, percentil_location)
        fig = right_margin_chart(fig, df, 1, i+1, 4)
    fig.update_layout(margin=dict(l=30, r=30, t=75, b=30))
    fig = title_stock(fig, stock)
    return fig


def screen_ema_extension_plotly(ema_extensions, stock, k):
    try:
        col_name_ema = ["extension_ema10", "extension_ema20", "extension_ema50", "extension_ema200"]
        col_name_ema_high = ["extension_high_ema10", "extension_high_ema20", "extension_high_ema50", "extension_high_ema200"]
        col_name_ema_low = ["extension_low_ema10", "extension_low_ema20", "extension_low_ema50", "extension_low_ema200"]
        timeframes = ["DAILY","WEEKLY","MONTHLY"]
        EMAS = ["10","20","50","200"]
        titles, t, e, text  = [], 0, 0, ""
        if k == 1:
            timeframes = ["DAILY","WEEKLY"]
            e = 2
        elif k == 10:
            timeframes = ["1h", "4h"]
            e = 0
            EMAS = ["10","20"]
            k = 1

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
                df_aux = df[(df[col_name] >= df[col_name].quantile(0.005)) & (df[col_name] <= df[col_name].quantile(0.995))]
                y_range = df_aux[col_name]
                current_ext = df[col_name].iloc[-1]
                p95 = df[col_name].quantile(0.95)
                p05 = df[col_name].quantile(0.05)
                p995 = df[col_name].quantile(0.995)
                p005 = df[col_name].quantile(0.005)
                fechas = df_aux.index
                if len(EMAS) > 2:
                    ext_high_pts = df[(df[col_name_ema_high[x + k]] >= p95) & (df[col_name_ema_high[x + k]] <= p995)][col_name_ema_high[x + k]]
                    ext_low_pts = df[(df[col_name_ema_low[x + k]] <= p05) & (df[col_name_ema_low[x + k]] >= p005)][col_name_ema_low[x + k]]
                    fig.add_trace(go.Scatter(x=ext_high_pts.index, y=ext_high_pts, mode="markers", marker=dict(size=4, color="red"), showlegend=False), row=x, col=i + 1)
                    fig.add_trace(go.Scatter(x=ext_low_pts.index, y=ext_low_pts, mode="markers", marker=dict(size=4, color="red"), showlegend=False), row=x, col=i + 1)

                fig.add_trace(go.Scatter(x=fechas, y=y_range, mode="markers", marker=dict(size=6, color="steelblue"), showlegend=False, name="Timeframe" + str(i)),
                    row=x, col=i + 1)
                fig.add_trace(go.Scatter(x=[df.index[-1]], y=[current_ext], mode="markers", marker=dict(size=14, color="orange"), showlegend=False),
                    row=x, col=i + 1)
                
                percentil_value = [0.95, 0, 0.05]
                percentil_name = ["p95", "EMA", "p05"]
                percentil_colour = ["black", "purple", "black"]
                percentil_location = ["top right", "top right", "bottom right"]
                fig = percentiles_and_currentValue(fig, df, x, i+1, col_name, current_ext, df.index[-1], percentil_value, percentil_name, percentil_colour, percentil_location)
                fig = right_margin_chart(fig, df, x, i+1, 5)            
        fig = title_stock(fig, stock)    
        return fig
    except Exception as e:
        print(e)


def screen_screener_ema_extensions(longs, shorts):
    fig = make_subplots(rows=1, cols=2, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["LONG SET-UPS", "SHORT SET-UPS"], specs=[[{"type": "domain"}, {"type": "domain"}]])
    fig_long_base = table_fig_variation(longs)
    fig_shorts_base = table_fig_variation(shorts)
    fig.add_trace(fig_long_base.data[0], row=1, col=1)
    fig.add_trace(fig_shorts_base.data[0], row=1, col=2)
    fig.update_layout(height=800, template="plotly_white", title_text="EMA Extension and Mean Reversion time", title_x=0.5)    
    return fig


def screen_deviations(data, stock): 
    try:
        fig = make_subplots(rows=2, cols=5, vertical_spacing=0.11, horizontal_spacing=0.04, subplot_titles=["DAILY DEVIATIONS (GREEN DAY)", "WEEKLY DEVIATIONS (GREEN WEEK)", "MONTHLY DEVIATIONS (GREEN MONTH)", "QUARTERLY DEVIATIONS (GREEN QUARTER)", "YEARLY DEVIATIONS (GREEN YEAR)", "DAILY DEVIATIONS (RED DAY)", "WEEKLY DEVIATIONS (RED WEEK)", "MONTHLY DEVIATIONS (RED MONTH)", "QUARTERLY DEVIATIONS (RED QUARTER)", "YEARLY DEVIATIONS (RED YEAR)"])
        for i in range(len(data)):
            df = data[i]
            df_green = df[df["type"] == "Green"]
            df_red = df[df["type"] == "Red"]
            k = 0
            #current_time = df.index[-1] + pd.Timedelta(days=extra_days)
            candle = df.iloc[-1]
            current_value = [((candle['Open'] - candle['Low']) / candle['Open'])*100, ((candle['High'] - candle['Open']) / candle['Open'])*100]
            cont = 0
            color = "green"
            for df_for in [df_green, df_red]:      
                if current_value[cont] < df_for["Deviation"].quantile(0.90):
                    ext = df_for[df_for["Deviation"] <= df_for["Deviation"].quantile(0.98)]
                    y_range = ext["Deviation"]
                elif current_value[cont] >= df_for["Deviation"].quantile(0.90):
                    ext = df_for[df_for["Deviation"] <= df_for["Deviation"].quantile(0.99)]
                    y_range = ext["Deviation"]
                value = current_value[cont]

                percentil_value = [0.95, 0.80, 0.50, -1]
                percentil_name = ["p95", "p80", "p50", "OPEN"]
                percentil_color = ["black", "black", "purple", "black"]
                percentil_location = ["top right", "top right", "top right", "right"] 
                if color == "green":
                    y_range = y_range * -1
                    df_for["Deviation"] = np.negative(df_for["Deviation"])
                    value = value * -1
                    percentil_value = [0.1, 0.20, 0.50, -1]

                fig.add_trace(go.Scatter(x=df_for.index, y=y_range, mode="markers", marker=dict(color=color, size=6), showlegend=False, opacity=0.75), row=1+k, col=i+1) 
                fig = percentiles_and_currentValue(fig, df_for, 1+k, i+1, "Deviation", value, df_for.index[-1], percentil_value, percentil_name, percentil_color, percentil_location)
                fig = right_margin_chart(fig, df, 1+k, i+1, 5)  
                cont = cont + 1
                k = k + 1
                color = "red"
        fig = title_stock(fig, stock)
        return fig
    except Exception as e:
        print(e)


def screen_ema_retests(data, stock, k):
    try:
        cols = 0
        timeframes = []
        if k == 0:
            timeframes = ["DAILY MEAN REVERSION EMA 10","WEEKLY MEAN REVERSION EMA 10", "MONTHLY MEAN REVERSION EMA 10"]
            cols = 3
        elif k == 1:
            timeframes = ["1H MEAN REVERSION EMA 10","4H MEAN REVERSION EMA 10"]
            cols = 2
        specs = [[{"type": "table"}] * cols, [{"type": "xy"}] * cols]
        fig = make_subplots(rows=2, cols=cols, row_heights=[0.35, 0.65], vertical_spacing=0.12, horizontal_spacing=0.04,
            subplot_titles=timeframes + [""] * cols, specs=specs)

        rankings = []
        for i in range(cols):
            if data[i].empty:
                fig.add_trace(go.Scatter(x=[], y=[], mode="markers", showlegend=False), row=2, col=i+1)
                rankings.append((pd.DataFrame({"TimeAway": ["-"], "Occurrences": ["-"], "%": ["-"]}), None))
                continue

            l = len(data[i])-1
            df = data[i][0:l].copy()
            fig.add_trace(
                go.Scatter(x=df.index, y=df["TimeAway"], mode="markers", marker=dict(color="steelblue", size=12), showlegend=False),
                row=2, col=i+1)

            current_value = data[i]["TimeAway"].iloc[-1]
            current_time = data[i].index[-1]
            percentil_value = [0.95, 0.80, 0.50, 0.20]
            percentil_name = ["p95", "p80", "p50", "p20"]
            percentil_color = ["black", "black", "red", "black"]
            percentil_location = ["top right", "top right", "top right", "bottom right"]
            fig = percentiles_and_currentValue(fig, df, 2, i+1, "TimeAway", current_value, current_time, percentil_value, percentil_name, percentil_color, percentil_location)
            fig = right_margin_chart(fig, df, 2, i+1, 5)

            counts = df["TimeAway"].value_counts()
            total = counts.sum()
            ranking = pd.DataFrame({"TimeAway": counts.index, "Occurrences": counts.values})
            ranking = ranking.sort_values("TimeAway", ascending=True).reset_index(drop=True)
            pct = ranking["Occurrences"] / total * 100
            ranking["%"] = pct.round(1)
            ranking["Cum%"] = pct.cumsum().round(1)
            ranking["%"] = ranking.apply(lambda r: f"{r['%']}% ({r['Cum%']}%)", axis=1)
            rankings.append((ranking, current_value))

        # las trazas de tabla se añaden al final: go.Table no tiene "xaxis", y los add_hline()
        # de arriba fallan si ya existe una tabla en fig.data al momento de llamarlos
        for i, (ranking, current_value) in enumerate(rankings):
            row_colors = ["yellow" if tv == current_value else "white" for tv in ranking["TimeAway"]]
            fig.add_trace(
                go.Table(
                    header=dict(values=["TimeAway", "Occ.", "%"], fill_color="black", font=dict(color="white", size=11), align="center"),
                    cells=dict(values=[ranking["TimeAway"], ranking["Occurrences"], ranking["%"]], fill_color=[row_colors, row_colors, row_colors], font=dict(color="black", size=11), align="center", height=22)
                ),
                row=1, col=i+1)
        fig = title_stock(fig, stock)
        return fig
    except Exception as e:
        print(e)


def screen_last_flip_open(data, stock):
    try:
        fig = make_subplots(rows=2, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["Day Last Flip of Weekly Open","Day Last Flip of Monthly Open","Day Last Flip of Quarterly Open", "Week Last Flip of Monthly Open","Week Last Flip of Quarterly Open", "Week Last Flip of on Yearly Open"])
        r, c = 1, 1
        for i in range(len(data)):
            if i == 3:
                c = 1
                r = 2
            l = len(data[i])-1
            df = data[i][0:l].copy()
            current_time = data[i].index[-1]
            current_value = data[i]["LastFlip"].iloc[-1]
            if i != 0 and i != 3:
                fig.add_trace(
                    go.Scatter(x=df.index, y=df["LastFlip"], mode="markers", marker=dict(color="steelblue", size=10), showlegend=False),
                    row=r, col=c)
                
                percentil_value = [0.95, 0.80, 0.50, 0.20]
                percentil_name = ["p95", "p80", "p50", "p20"]
                percentil_color = ["black", "black", "purple", "black"]
                percentil_location = ["top right", "bottom right", "top right", "bottom right"]
                fig = percentiles_and_currentValue(fig, df, r, c, "LastFlip", current_value, current_time, percentil_value, percentil_name, percentil_color, percentil_location)
                df.index = pd.to_datetime(df.index)
                fig = right_margin_chart(fig, df, r, c, 5)
            else:
                orden = [1, 2, 3, 4, 5, 6, 7]
                df_counts = df["LastFlip"].value_counts().reindex(orden).fillna(0)
                df_pct = (df_counts / df_counts.sum()) * 100
                fig.add_trace(go.Bar(x=df_pct.index, y=df_pct.values, marker_color='steelblue', opacity=0.8, text=[f"{val:.1f}%" for val in df_pct.values], textposition='outside'),
                    row=r, col=c)
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
    fig = make_subplots(rows=2, cols=4, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["Daily Close Flips x Returns (Green)[MONTHLY OPEN]", "Day Last Flip x Returns (Green)[MONTHLY OPEN]", "Daily Close Flips x Returns (Red)[MONTHLY OPEN]", "Day Last Flip x Returns (Red)[MONTHLY OPEN]", "Weekly Close Flips x Returns (Green)[QUARTERLY OPEN]", "Week Last Flip x Returns (Green)[QUARTERLY OPEN]", "Weekly Close Flips x Returns (Red)[QUARTERLY OPEN]", "Week Last Flip x Returns (Red)[QUARTERLY OPEN]"])
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


def screen_lastflip_x_peak(df1, df2, stock):
    try:       
        fig = make_subplots(rows=2, cols=2, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["Distance LastFlip to Peak (Mean and standard deviation)[GREEN - MONTHLY]", "List of Last flips with Peaks [MONTHLY]","Distance LastFlip to Peak (Mean and standard deviation)[RED - MONTHLY]",""], specs=[[{"type": "xy"}, {"type": "domain"}],[{"type": "xy"}, {"type": "domain"}]]) 
        df_merged = pd.merge(df1, df2, left_index=True, right_on='Date', how='inner')
        df_aux = df_merged[df_merged["LastFlip"] < df_merged["PeakExpansion"]]
        df_green = df_aux[df_aux["Return"]>=0]
        df_red = df_aux[df_aux["Return"]<0]
        r = 1
        for df in [df_green, df_red]:
            df["TrendTime"] = df["PeakExpansion"]-df["LastFlip"]
            df_group = df.groupby("LastFlip")["TrendTime"].agg(['mean', 'std']).reset_index()
            df_group.columns = ['LastFlip', 'Mean', 'Std']
            df_group['Std'] = df_group['Std'].fillna(0)
            fig.add_trace(go.Scatter(x=df_group["LastFlip"], y=df_group["Mean"], 
                error_y=dict(type='data', array=df_group["Std"], visible=True, color='red', thickness=2, width=6), 
                mode="markers", marker=dict(color="black", size=12), showlegend=False), row=r, col=1)  
            if r == 1:
                df_sorted = df.sort_values(by='Return', ascending=False)
            else:
                df_sorted = df.sort_values(by='Return', ascending=True) 
            df_sorted = df_sorted.reindex(columns=['Date', 'Return', 'LastFlip', 'PeakExpansion', 'TrendTime'])
            fig_open_gaps = table_fig_variation(df_sorted)
            fig.add_trace(fig_open_gaps.data[0], row=r, col=2) 
            r = r+1     
        fig = title_stock(fig, stock)
        return fig
    except Exception as e:
        print(e)


def screen_volatility(data, stock):
    fig = make_subplots(rows=1, cols=3, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["Daily Volatility History", "Weekly Volatility History", "Monthly Volatility History"])
    column = 1
    parameter = [-365, -50, -12]
    for df in data:  
        min = df[parameter[column-1]:]["Volatility"].min()        
        df = df[df["Volatility"] >= min].copy()
        total_time = df.index[-1] - df.index[0]  
        padding = total_time / 5
        new_x_limit = df.index[-1] + padding
        fig.add_trace(go.Scatter(x=df.index, y=df["Volatility"], mode="markers", marker=dict(color="red", size=6), showlegend=False, opacity=0.75),
                row=1, col=column) 
        fig.update_xaxes(range=[df.index[0], new_x_limit], row=1, col=column)
        fig = percentiles_and_currentValue(fig, df, 1, column, "Volatility", round(df["Volatility"].iloc[-1],1), df.index[-1], [0.7, 0.95], ["p70", "p95"], ["black" for _ in range(2)], ["top right" for _ in range(2)])
        column += 1
    fig = title_stock(fig, stock)
    return fig


def screen_returns(data, stock):
    fig = make_subplots(rows=2, cols=5, vertical_spacing=0.10, horizontal_spacing=0.04, subplot_titles=["Daily Returns (Green)", "Weekly Returns (Green)", "Monthly Returns (Green)", "Quarterly Returns (Green)", "Yearly Returns (Green)", "Daily Returns (Red)", "Weekly Returns (Red)", "Monthly Returns (Red)", "Quarterly Returns (Red)", "Yearly Returns (Red)"])
    column = 1
    for df in data:
        total_time = df.index[-1] - df.index[0]            
        padding = total_time / 5
        new_x_limit = df.index[-1] + padding
        df_green = df[df["Return"]>=0]
        fig.add_trace(go.Scatter(x=df_green.index, y=df_green["Return"], mode="markers", marker=dict(color="green", size=5), showlegend=False, opacity=0.75),
                row=1, col=column) 
        fig.update_xaxes(range=[df.index[0], new_x_limit], row=1, col=column)
        fig = percentiles_and_currentValue(fig, df_green, 1, column, "Return", round(((df["High"].iloc[-1] / df["Last_Close"].iloc[-1])-1)*100,1), df_green.index[-1], [0.7, 0.95], ["p70", "p95"], ["black" for _ in range(2)], ["top right" for _ in range(2)])

        df_red = df[df["Return"]<0]
        fig.add_trace(go.Scatter(x=df_red.index, y=df_red["Return"], mode="markers", marker=dict(color="red", size=5), showlegend=False, opacity=0.75),
                row=2, col=column) 
        fig.update_xaxes(range=[df.index[0], new_x_limit], row=2, col=column)
        fig = percentiles_and_currentValue(fig, df_red, 2, column, "Return", round(((df["Low"].iloc[-1] / df["Last_Close"].iloc[-1])-1)*100,1), df_red.index[-1], [1-0.7, 1-0.95], ["p70", "p95"], ["black" for _ in range(2)], ["top right" for _ in range(2)])
        column += 1
    fig = title_stock(fig, stock)
    return fig


def screen_open_momentum(df, stock):
    try:
        target_days = [1, 3, 5]
        sigmas = [1.0, 1.5, 2]
        
        plot_titles = []
        for day in target_days:
            for sigma in sigmas:
                plot_titles.append(f"Day {day} | Filtro: {sigma}σ")
                
        # 6 filas (días) x 3 columnas (sigmas)
        fig = make_subplots(
            rows=3, cols=3, 
            vertical_spacing=0.15,     
            horizontal_spacing=0.05,   
            subplot_titles=plot_titles
        )
        
        subplot_index = 0
        
        for row_idx, day in enumerate(target_days, start=1):
            current_col = f"Added_Return_{day}"
            
            if current_col not in df.columns:
                continue
                
            # 'Return' es el rendimiento mensual completo (Eje Y con solapamiento)
            df_clean = df[["Return", current_col]].dropna()
            
            for col_idx, sigma in enumerate(sigmas, start=1):
                
                # Aplicamos el filtro de desviación estándar dinámico por columna
                if len(df_clean) > 5:
                    mean_k = df_clean[current_col].mean()
                    std_k = df_clean[current_col].std()
                    df_filtered = df_clean[(df_clean[current_col] - mean_k).abs() >= (sigma * std_k)]
                else:
                    df_filtered = df_clean.copy()
                
                r_value = 0.0
                if len(df_filtered) > 1:
                    r_value = df_filtered["Return"].corr(df_filtered[current_col])
                
                # Título dinámico para que tu ojo controle el r y el n de cada escenario
                new_title = f"Day {day} ({sigma}σ) | r: {round(r_value, 2)} | n: {len(df_filtered)}"
                fig.layout.annotations[subplot_index].text = new_title
                subplot_index += 1
                
                # Puntos (Scatter)
                fig.add_trace(
                    go.Scatter(
                        x=df_filtered["Return"], 
                        y=df_filtered[current_col], 
                        mode="markers", 
                        marker=dict(color="blue", size=6, opacity=0.6), 
                        showlegend=False
                    ),
                    row=row_idx, col=col_idx
                ) 
                
                # Línea de regresión lineal (Roja)
                if len(df_filtered) > 1:
                    m, b = np.polyfit(df_filtered["Return"], df_filtered[current_col], 1)
                    x_line = np.array([df_filtered["Return"].min(), df_filtered["Return"].max()])
                    y_line = m * x_line + b
                    if sigma == 1:
                        color = "green"
                    elif sigma == 1.5:
                        color = "purple"
                    elif sigma == 2:
                        color = "red"
                        
                    fig.add_trace(
                        go.Scatter(
                            x=x_line, 
                            y=y_line, 
                            mode="lines", 
                            line=dict(color=color, width=2), 
                            showlegend=False
                        ),
                        row=row_idx, col=col_idx
                    )
                
                # Cruces por cero (Negro y Naranja)
                fig.add_vline(x=0, line_width=1.2, line_dash="solid", line_color="black", row=row_idx, col=col_idx)
                fig.add_hline(y=0, line_width=1.0, line_dash="solid", line_color="orange", row=row_idx, col=col_idx)
        fig = title_stock(fig, stock)
        return fig
    except Exception as e:
        print(f"Error: {e}")


def screen_12_25_cross(planning, execution):
    try:
        fig = make_subplots(rows=1, cols=2, vertical_spacing=0.11, horizontal_spacing=0.05,subplot_titles=["Next Cross", "Crossing"], specs=[[{"type": "table"}, {"type": "table"}]])
        fig_long_base = table_fig_variation(planning)
        fig_shorts_base = table_fig_variation(execution)
        fig.add_trace(fig_long_base.data[0], row=1, col=1)
        fig.add_trace(fig_shorts_base.data[0], row=1, col=2)
        fig.update_layout(height=800, template="plotly_white", title_x=0.5)    
        return fig
    except Exception as e:
        print(e)


def screen_trend_deviation(data, stock):
    # total velas que abrieron >0.2% arriba de EMA10 y tuvieron low >0.2% abajo
    open_above_low_below = data[(data["Open"] > data["ema10"] * 1.002) & (data["Low"] < data["ema10"] * 0.998)]
    total_touches = len(open_above_low_below)
    absorbed = len(open_above_low_below[open_above_low_below["Close"] > open_above_low_below["ema10"] * 1.002])
    abs_pct = round(absorbed / total_touches * 100, 1) if total_touches > 0 else 0
    stock_label = f"{stock} | Abs: {absorbed}/{total_touches} ({abs_pct}%)"

    df1 = data[(data["EMA10_Absortion"] == True)].copy()
    df2 = data[(data["EMA10_Absortion"] == True) & (data["MinClose1"] >= data["ema10"])].copy()
    df3 = data[(data["EMA10_Absortion"] == True) & (data["MinClose2"] >= data["ema10"])].copy()
    
    try:
        dfs = [df1, df2, df3]
        titles = []
        for df in dfs:
            n = len(df)
            avg_max = round(df["Max3Days"].median(), 2) if n > 0 else 0
            avg_low = round(df["Low3Days"].mean(), 2) if n > 0 else 0
            pct_lowgrab = round((df["LowGrab"] < 0).sum() / n * 100, 1) if n > 0 else 0
            grab_mask = df["LowGrab"] < 0
            grab_vals = df.loc[grab_mask, "LowGrab"]
            low5_grab_vals = df.loc[grab_mask, "Low3Days"]
            if not grab_vals.empty:
                gmin = round(grab_vals.min(), 2)
                gmed = round(grab_vals.median(), 2)
                gmax = round(grab_vals.max(), 2)
                lmin = round(low5_grab_vals.min(), 2)
                lmed = round(low5_grab_vals.median(), 2)
                lmax = round(low5_grab_vals.max(), 2)
            else:
                gmin = gmed = gmax = lmin = lmed = lmax = 0
            titles.append(f"n={n} | Max3D={avg_max}% Low5D={avg_low}%<br>Grab<0={pct_lowgrab}% LG:{gmin}/{gmed}/{gmax} L3:{lmin}/{lmed}/{lmax}")

        fig = make_subplots(rows=1, cols=3, vertical_spacing=0.11, horizontal_spacing=0.04, subplot_titles=titles)
        color = "blue"
        percentil_value = [0.10, 0.50, 0]
        percentil_name = ["p90", "p50", "EMA"]
        percentil_color = ["black", "purple", "black"]
        percentil_location = ["top right", "top right", "right"]
        for col, df in enumerate(dfs):
            if df.empty:
                continue
            df = df.iloc[:-3].copy() if len(df) > 3 else df.copy()
            if df.empty:
                continue
            current_value = df["DeviationEMA"].iloc[-1]
            current_day = df.index[-1]
            fig.add_trace(go.Scatter(x=df.index, y=df["DeviationEMA"], mode="markers", marker=dict(color=color, size=6), showlegend=False, opacity=0.75), row=1, col=1+col)
            fig = percentiles_and_currentValue(fig, df, 1, 1+col, "DeviationEMA", current_value, current_day, percentil_value, percentil_name, percentil_color, percentil_location)
        fig = title_stock(fig, stock_label)
        return fig
    except Exception as e:
        print(e)


def screen_backtesting(df, equity_df, stock):
    try:
        table_trace = table_fig_variation(df).data[0]
        fig = make_subplots(rows=2, cols=1, row_heights=[0.5, 0.5], vertical_spacing=0.08,
            specs=[[{"type": "table"}], [{"type": "xy"}]],
            subplot_titles=["", "EQUITY CURVE (Strategy vs Hold)"])
        fig.add_trace(table_trace, row=1, col=1)

        if equity_df is not None and not equity_df.empty:
            fig.add_trace(go.Scatter(x=equity_df.index, y=equity_df["Strategy"], mode="lines",
                name="Strategy", line=dict(color="steelblue", width=2)), row=2, col=1)
            fig.add_trace(go.Scatter(x=equity_df.index, y=equity_df["Hold"], mode="lines",
                name="Hold", line=dict(color="gray", width=2, dash="dash")), row=2, col=1)

        fig = title_stock(fig, stock)
        return fig
    except Exception as e:
        print(e)



