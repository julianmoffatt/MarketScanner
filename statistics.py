import numpy as np
from functions import * 
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import mplfinance as mpf
import pandas as pd
import matplotlib.dates as mdates

def preparingData(data):
    for df in data:
        df.loc[:, "last_close"] = df["Close"].shift(1)
        df["type"] = np.where(df["Close"] > df["last_close"], "Green", "Red")
        df["rsi"] = rsi_tradingview(df['Close'])
    return data

def statistics_strikes(data):
    strikesTimeframes = []
    for df in data:
      strikes = {"Green": {}, "Red": {}}
      num = 1
      for i in range (1, len(df)):
          if (df.iloc[i]["type"] == df.iloc[i-1]["type"]) and i != (len(df)-1):
              num = num + 1
          else:
              x = i-1
              if i == (len(df)-1):
                  x = i
              if num in strikes[df.iloc[x]["type"]]:
                strikes[df.iloc[x]["type"]][num] = strikes[df.iloc[x]["type"]][num] + 1
              else:
                strikes[df.iloc[x]["type"]][num] = 1 
              num = 1
      strikesTimeframes.append({"Green": dict(sorted(strikes["Green"].items())),"Red":   dict(sorted(strikes["Red"].items()))})
    return strikesTimeframes   

def conditionalProbability(data, data_candles):
    for cont in range(0,len(data)):                    
        total_green = sum(data[cont]["Green"].values())
        total_red = sum(data[cont]["Red"].values())
        probability_green, probability_red = {}, {}
        for key, value in data[cont]["Green"].items():
          probability_green[key] = value / total_green	
        for key, value in data[cont]["Red"].items():
          probability_red[key] = value / total_red

        x = len(data_candles[cont]) - 1 
        num = 1
        candle = data_candles[cont].iloc[x]["type"]
        x = x - 1
        while x >= 0 and data_candles[cont].iloc[x]["type"] == candle:
          num = num + 1
          x = x - 1     
        streaks = pd.DataFrame()
        if candle == "Green":
            streaks = pd.DataFrame(list(probability_green.items()), columns=["days", "frequency"])
        else:
            streaks = pd.DataFrame(list(probability_red.items()), columns=["days", "frequency"])
        beyond = streaks[streaks["days"]>num]["frequency"].sum()
        equal = streaks[streaks["days"]==num]["frequency"].sum()
        pct = round((beyond / (equal + beyond)) * 100,1)
        pctR = 100 - round((beyond / (equal + beyond)) * 100,1)
        print("Probability of continuation", candle + ":", pct, "and reversal", pctR)
        print("------------------------------------------------------------------------------------")  


def statistics_rsi(data):
    localExtremes = []
    currentRsi = []
    for df in data:
        state, value = 0, 50
        highs, lows = [], []
        lecture = False
        date = df.iloc[0]["rsi"]
        for i in range (0, len(df)):
            if df.iloc[i]["rsi"] >= 65:
                if not lecture:
                   state = 1
                   lecture = True
                   value = df.iloc[i]["rsi"]
                else:
                    if df.iloc[i]["rsi"] > value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]
            elif df.iloc[i]["rsi"] <= 35:
                if not lecture:
                   state = 2
                   lecture = True
                   value = df.iloc[i]["rsi"]
                else:
                    if df.iloc[i]["rsi"] < value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]

            elif df.iloc[i]["rsi"] > 35 and df.iloc[i]["rsi"] < 65 and lecture:
                if state == 1 and df.iloc[i]["rsi"] <= 50:
                    if value >= 65:
                        highs.append({date: value})
                    state = 0
                    lecture = False
                    value = 50
                elif state == 2 and df.iloc[i]["rsi"] >= 50:
                    if value <= 35:
                        lows.append({date: value})
                    state = 0
                    lecture = False
                    value = 50
        currentRsi.append({ df.index[-1] : df.iloc[-1]["rsi"]})
        aux_data = highs + lows
        data = [d for d in aux_data if not (isinstance(list(d.keys())[0], float) and np.isnan(list(d.keys())[0]))]
        localExtremes.append(data)      
    return localExtremes, currentRsi

def clean_timestamp_rsi(data):
    fechas = []
    valores = []
    
    for d in data:          # cada elemento es un dict con 1 clave
        for k, v in d.items():
            # Convertir Timestamp → datetime Python
            if isinstance(k, pd.Timestamp):
                fechas.append(k.to_pydatetime())
            else:
                fechas.append(k)
            
            # Convertir np.float64 → float
            if isinstance(v, np.generic):
                valores.append(float(v))
            else:
                valores.append(v)

    return fechas, valores


def display(data, currentRsi, data_candles, N=60):
    fig = plt.figure(figsize=(20, 12))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 2])  # top row shorter
    timeframes = ["Daily", "Weekly", "Monthly"]
    # ==== Top row: 3 RSI plots ====
    axes_rsi = []
    for i in range(3):
        ax = fig.add_subplot(gs[0, i])
        axes_rsi.append(ax)
        df_rsi = data[i]

        # Suponiendo que clean_timestamp_rsi devuelve listas de fechas y RSI
        fechas, rsi = clean_timestamp_rsi(df_rsi)

        ax.scatter(fechas, rsi, color='blue')

        # Current RSI
        rsi_dict = currentRsi[i]
        rsi_time = list(rsi_dict.keys())[0]
        rsi_value = list(rsi_dict.values())[0]
        ax.axhline(y=rsi_value, color='black', linestyle='-', linewidth=2)
        ax.scatter([rsi_time], [rsi_value], s=70, color='red')
        ax.set_title(f"RSI ({timeframes[i]}: {int(round(list(currentRsi[i].values())[0]))})", color='black')

        ax.tick_params(axis='x', colors='black')
        ax.tick_params(axis='y', colors='black')
        ax.grid(True)
        ax.legend()

    # ==== Bottom row: Candlestick diario ====
    ax_candles = fig.add_subplot(gs[1, :])

    # Últimas N velas diarias
    df_daily = data_candles[0].copy().tail(N)
    df_daily.index = pd.to_datetime(df_daily.index)

    # Calcular xlim para que la última vela quede al 70% del ancho
    dates = df_daily.index
    date_span = (dates[-1] - dates[0]).days
    extra_days = int(date_span * 0.45) if date_span > 0 else 1
    xlim = [dates[0], dates[-1] + pd.Timedelta(days=extra_days)]

    # Plot candlestick con xlim
    mpf.plot(
        df_daily,
        type='candle',
        ax=ax_candles,
        style='charles',
        show_nontrading=False,
        xlim=xlim
    )

    # Líneas horizontales: última apertura semanal y mensual
    week_open = data_candles[1]['Open'].iloc[-1]  
    week_open_date = data_candles[1].index[-1]  
    month_open = data_candles[2]['Open'].iloc[-1]
    month_open_date = data_candles[1].index[-1]  
       
    # Convertir fechas a float para matplotlib
    week_x = mdates.date2num(week_open_date)
    month_x = mdates.date2num(month_open_date)
    x_max = mdates.date2num(df_daily.index[-1]) + 1  # final del plot
    
    ax_candles.hlines(week_open, xmin=week_x, xmax=x_max, color='black', linestyle='-', linewidth=1.5, label=f'Weekly Open {week_open:.2f}')
    ax_candles.hlines(month_open, xmin=month_x, xmax=x_max, color='black', linestyle='-', linewidth=1.5, label=f'Monthly Open {month_open:.2f}')

    ax_candles.set_title("Candlestick Diario + Niveles Horizontales", color='white')
    ax_candles.tick_params(axis='x', colors='black')
    ax_candles.tick_params(axis='y', colors='black')
    ax_candles.grid(True, alpha=0.3)
    ax_candles.legend()

    plt.tight_layout(pad=4)
    plt.show()






def display_opens(data):
    pass
    











                
                
                
               
                
      
   
               
 