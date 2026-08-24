import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from analytics.statistics_calculations import *
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np 

def candlestick_chart(df):
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            increasing=dict(fillcolor='white', line=dict(color='black')),
            decreasing=dict(fillcolor='black', line=dict(color='black')),
            showlegend=False
        )
    )

    fig.update_layout(height=800, plot_bgcolor='white', paper_bgcolor='white', xaxis_rangeslider_visible=False, xaxis=dict(showgrid=False),
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(showgrid=True, gridcolor='lightgray')
    )
    return fig


def title_stock(fig, stock):
    fig.update_layout(margin=dict(l=55, r=55, t=75, b=80), title={'text': stock,'x': 0.5,'y': 0.98,'xanchor': 'center','yanchor': 'top', 'font': {'size': 20, 'color': 'purple'}})
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

def right_margin_chart(fig, df, row, col, parameter):
    total_time = df.index[-1] - df.index[0]            
    padding = total_time / (parameter-1)
    new_x_limit = df.index[-1] + padding
    fig.update_xaxes(range=[df.index[0], new_x_limit], row=row, col=col)
    return fig

def percentiles_and_currentValue(fig, df, row, column, study_variable, current_value, current_time, percentile_value, percentil_name, percentil_colour, percentil_location):
    for p in range (0, len(percentile_value)):
        if percentile_value[p] > 0:
            percentil = np.quantile(df[study_variable].values, percentile_value[p])
            annotation = "(" + str(round(percentil,1)) +") "+ percentil_name[p] 
        elif percentile_value[p] == 0:
            annotation = "EMA"
            percentil = 0
        elif percentile_value[p] == -1:
            annotation = "OPEN"
            percentil = 0
        fig.add_hline(line_width=2, row=row, col=column, annotation_position=percentil_location[p], annotation_font_size=13, annotation_font_color="black",
        y=percentil,  
        line_color=percentil_colour[p], 
        annotation_text=annotation) 
    fig.add_hline(y=current_value, line_color="#E9B300", line_dash = 'dot', line_width=5, row=row, col=column,
        annotation_text=f" {current_value:.1f}%",
        annotation_position="right", 
        annotation_font_size=13,
        opacity=0.7,
        annotation_font_color="blue")
    fig.add_trace(go.Scatter(x=[current_time], y=[current_value], mode="markers", marker=dict(color="#FFC400", size=14), showlegend=False, opacity=1), row=row, col=column)  
    return fig


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
                font=dict(color="black", size=12),
                align="center",
                height=28   # prueba 28–40
                )
            )
        ]
    )
    fig.update_layout(title="", margin=dict(l=10, r=10, t=20, b=0))
    return fig


def table_fig_variation(df, colours=None):
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
                fill_color=colours if colours is not None else "white",
                font=dict(color="black", size=12),
                align="center",
                height=28   # prueba 28–40
                )
            )
        ]
    )
    fig.update_layout(title="", margin=dict(l=10, r=10, t=20, b=0))
    return fig


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


def colour_painting(df, name, current_colours, current_stock_pos):
    try:
        if df is None or df.empty:
            return []
        colours = []
        if name == "flips":
            # bloques de columnas: "Asset", luego por cada timeframe superior: "nX", "X%", "0 xxx_F", "1 xxx_F", ...
            palette = ["lightgreen", "lightblue"]
            block_idx = -1
            for i, col in enumerate(df.columns):
                if i == 0:
                    colours.append(["white"] * len(df))
                elif col.startswith("n") and len(col) == 2 and col[1].isupper():
                    block_idx += 1 # arranca un nuevo bloque de timeframe (nW, nM, nQ, nY...)
                    colours.append(["lightgray"] * len(df))
                elif col.endswith("%"):
                    colours.append(["lightgray"] * len(df))
                else:
                    colours.append([palette[block_idx % len(palette)]] * len(df))

        if current_stock_pos != -1:
            for x in range (0, len(colours)): # i highlight the current stock
                colours[x][current_stock_pos] = "#a6a6a6"

        if name == "flips" and current_colours is not None and not current_colours.empty:
            # i override the current flips of opens situation, matcheando por simbolo y por columna "j xxx_F"
            symbol_col = df.columns[0]
            symbol_to_row = {sym: idx for idx, sym in enumerate(df[symbol_col])}
            for _, row in current_colours.iterrows():
                symbol = row["symbol"]
                if symbol not in symbol_to_row:
                    continue
                row_idx = symbol_to_row[symbol]
                highlight = "lightyellow" if row_idx == current_stock_pos else "yellow"
                for flip_col in current_colours.columns:
                    if not flip_col.endswith("Flip") or flip_col.endswith("LastFlip"):
                        continue
                    tf = flip_col[:-len("Flip")]
                    target_col = f"{int(row[flip_col])} {tf[0:3]}_F"
                    if target_col not in df.columns:
                        continue
                    col_pos = df.columns.get_loc(target_col)
                    colours[col_pos][row_idx] = highlight
        return colours
    except Exception as e:
        print(e)


def colour_painting_detailed_flips(df, current_stock_pos):
    if not df.empty:
        colours = []    
        for i, col in enumerate(df.columns):
            column_colors = []
            for row_idx in range(len(df)):
                # Nuevo patrón de 2 -> 0: Verde, 1: Rojo
                row_pattern = row_idx % 3  
    
                # Lógica por columnas
                if i == 11 or i == 19: 
                    # Columnas especiales con tu color original
                    column_colors.append("#E6CFE0")
                else:
                    # El resto de columnas de datos por defecto van en blanco
                    column_colors.append("white")                    
            colours.append(column_colors)
    
        # Resaltado del stock actual (ahora ocupa 2 filas en lugar de 3)
        if current_stock_pos != -1:
            base_idx = current_stock_pos * 3
            for x in range(len(colours)): 
                colours[x][base_idx] = "lightgray"
                colours[x][base_idx + 1] = "lightgreen"  # Fila Verde de la empresa actual
                colours[x][base_idx + 2] = "#FFB15C" # Fila Roja de la empresa actual                
        print("i return colours")
        return colours
    return []


def colour_painting_quarter_patterns(df, current_stock_pos):
    if not df.empty:
        colours = []
        for i, col in enumerate(df.columns):
            column_colors = ["white"] * len(df)
            colours.append(column_colors)

        if current_stock_pos != -1:
            base_idx = current_stock_pos * 3
            for x in range(len(colours)):
                if x == 0:
                    colours[x][base_idx] = "white"
                    colours[x][base_idx+1] = "white"
                    colours[x][base_idx+2] = "white"
                else:
                    colours[x][base_idx] = "#F4FF94"
                    if x <= 4:
                        colours[x][base_idx + 1] = "lightgreen"
                    else:                    
                        colours[x][base_idx + 1] = "#FFA667"                    
                    if x <= 2:
                        colours[x][base_idx + 2] = "lightgreen"
                    elif x >= 3 and x <= 4:                    
                        colours[x][base_idx + 2] = "#FFA667"
                    elif x >= 5 and x <= 6:                    
                        colours[x][base_idx + 2] = "#FFA667"
                    elif x >= 7 and x <= 8:                    
                        colours[x][base_idx + 2] = "lightgreen"                   
        return colours
    return []

def value_to_color(val, is_current):
        try:
            v = float(val)
        except (TypeError, ValueError):
            return "white"
        if is_current:
            if v >= 3:    return "#FFD700"
            elif v >= 1:  return "#FFE566"
            elif v >= 0:  return "#FFF4A3"
            elif v >= -1: return "#FFD580"
            elif v >= -3: return "#FFA040"
            else:         return "#FF6600"
        else:
            if v >= 3:    return "#2f872f"
            elif v >= 1:  return "#4caf50"
            elif v >= 0:  return "#a8d5a2"
            elif v >= -1: return "#f4a8a8"
            elif v >= -3: return "#e36666"
            else:         return "#942d2d"

def colour_painting_return_color(df, current_stock_pos):
    SUMMARY_ROW_COLORS = {
        "ALL":  "#FFF9C4",
        "HIGH": "#FFF176",
        "MID":  "#FFD54F",
        "LOW":  "#FFB300",
    }

    def summary_row_color(symbol_val):
        s = str(symbol_val)
        for group in ("ALL", "HIGH", "MID", "LOW"):
            if s.startswith(group):
                return SUMMARY_ROW_COLORS[group]
        return None

    symbol_col = df.columns[0]

    colours = []
    for i, col in enumerate(df.columns):
        is_tol_col = "Tol%" in str(col) or "Vol Avg%" in str(col)
        column_colors = []
        for row_idx in range(len(df)):
            sym_val = df[symbol_col].iloc[row_idx]
            sr_color = summary_row_color(sym_val)
            if sr_color is not None:
                column_colors.append("#D3D3D3" if i == 0 else ("#BBBBBB" if is_tol_col else sr_color))
            elif i == 0:
                column_colors.append("lightgray")
            elif is_tol_col:
                column_colors.append("#CCCCCC")
            elif str(df[col].iloc[row_idx]).strip().lower() in ("null", "none", "nan", ""):
                column_colors.append("black")
            else:
                is_current = (row_idx == current_stock_pos)
                column_colors.append(value_to_color(df[col].iloc[row_idx], is_current))
        colours.append(column_colors)
    return colours



     


