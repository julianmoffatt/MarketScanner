import numpy as np
from functions import * 
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import mplfinance as mpf
import pandas as pd

def rsi_tradingview(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def preparingData(data):
    for df in data:
        df["Last_Close"] = df["Close"].shift(1)
        df["type"] = np.where(df["Close"] > df["Last_Close"], "Green", "Red")
        df["rsi"] = rsi_tradingview(df['Close'])
        df["Candle_Lenght"] = df["High"] - df["Low"]
        df["Upper_wick"] = df["High"] - df[["Open", "Close"]].max(axis=1)
        df["Lower_wick"] = df[["Open", "Close"]].min(axis=1) - df["Low"]
    return data

# Calculation of strikes probabilities
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


def next_candle_probability(candle, probability_green, probability_red, num):
    streaks = pd.DataFrame()
    if candle == "Green":
        streaks = pd.DataFrame(list(probability_green.items()), columns=["days", "frequency"])
    else:
        streaks = pd.DataFrame(list(probability_red.items()), columns=["days", "frequency"])
    beyond = streaks[streaks["days"]>num]["frequency"].sum()
    equal = streaks[streaks["days"]==num]["frequency"].sum()
    probRed = round((beyond / (equal + beyond)), 2)
    if candle == "Green":
        return 1-probRed
    else:
        return probRed
    

# Screen with Rsi reversal points and next candle probability
def screen_statistics(rsiReversalZones, currentRsi, data_candles, strikes, N=60):
    #x  = input("How many timeframes?")
    timeframes = ["Daily", "Weekly", "Monthly"]
    parameters = [0.50,0.55,0.59]
    fig = plt.figure(figsize=(20, 12))
    gs = gridspec.GridSpec(2, 3)

    for i in range(len(rsiReversalZones)):
        ax = fig.add_subplot(gs[0, i])
        df_rsi = rsiReversalZones[i]

        fechas, rsi = clean_timestamp_rsi(df_rsi)
        ax.scatter(fechas, rsi, color='blue')

        # RSI actual
        rsi_dict = currentRsi[i]
        rsi_time = list(rsi_dict.keys())[0]
        rsi_value = list(rsi_dict.values())[0]

        ax.axhline(y=rsi_value, color='orange', linewidth=2)
        ax.axhline(parameters[i], color="gray", linestyle="-", alpha=0.5)
        ax.scatter([rsi_time], [rsi_value], s=100, color='orange')

        # one-line title with integer RSI
        ax.set_title(f"RSI {timeframes[i]}: {int(rsi_value)}", color='black')

        ax.tick_params(axis='x', colors='black')
        ax.tick_params(axis='y', colors='black')
        ax.grid(True)
        ax.legend()

    for cont in range(len(strikes)):
        ax = fig.add_subplot(gs[1, cont])
        number_points = 10
        total_green = sum(strikes[cont]["Green"].values())
        total_red = sum(strikes[cont]["Red"].values())

        probability_green, probability_red = {}, {}
        for key, value in strikes[cont]["Green"].items():
            probability_green[key] = value / total_green
        for key, value in strikes[cont]["Red"].items():
            probability_red[key] = value / total_red

        probability_list = []
        x0 = len(data_candles[cont]) - number_points
        num = 1
        candle = data_candles[cont].iloc[x0]["type"]
        x = x0 - 1

        while x >= 0 and data_candles[cont].iloc[x]["type"] == candle:
            num += 1
            x -= 1

        probability = next_candle_probability(candle, probability_green, probability_red, num)
        probability_list.append(probability)

        for i in range(len(data_candles[cont]) - number_points + 1, len(data_candles[cont])):
            if data_candles[cont].iloc[i]["type"] == data_candles[cont].iloc[i-1]["type"]:
                num += 1
            else:
                num = 1

            probability = next_candle_probability(candle, probability_green, probability_red, num)
            probability_list.append(probability)

        color_list = []
        for i in range(len(data_candles[cont]) - number_points, len(data_candles[cont])):
            color_list.append(data_candles[cont].iloc[i]["type"])

        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.5, len(probability_list) - 0.5)

        ax.axhline(0, color="green", linewidth=6)
        ax.axhline(1, color="red", linewidth=6)
        ax.axhline(0.5, color="gray", linestyle="-", alpha=0.5)

        x_vals = list(range(len(probability_list)))
        y_vals = probability_list

        ax.scatter(x_vals, y_vals, s=120, c=color_list, alpha=0.7, zorder=10)

        for xi, yi in zip(x_vals, y_vals):
            ax.annotate(
                f"{yi*100:.0f}%",
                (xi, yi),
                (1, 10),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color="red"
            )

            ax.annotate(
                f"{(1 - yi)*100:.0f}%",
                (xi, yi),
                (1, -10),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=8,
                fontweight="bold",
                color="green"
            )

        ax.set_title("", fontsize=10)
        ax.set_xticks([])
        ax.grid(False)

    plt.tight_layout()
    plt.show()


# Screen with daily weekly and monthly candles
def screen_candles(data_candles):
    timeframes = ["Daily", "Weekly", "Monthly"]
    N = 50
    timeframe = 0
    fig = plt.figure(figsize=(16, 6))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 1], hspace=0.12, wspace=0.1, left=0.04, right=0.98, top=0.95, bottom=0.01)
    ax_daily = fig.add_subplot(gs[0, :])
    ax_weekly = fig.add_subplot(gs[1, 0])
    ax_monthly = fig.add_subplot(gs[1, 1])

    for ax in [ax_daily, ax_weekly, ax_monthly]:
        ax.set_ylabel('')
        # Últimas N velas del timeframe para representar en la chart
        df = data_candles[timeframe].copy().tail(N)
        df.index = pd.to_datetime(df.index)

        # Expand x-axis so that last candle is at 70%
        dates = df.index
        extra_days = len(df.index) * 0.7
        xlim = [dates[0], dates[-1] + pd.Timedelta(days=extra_days)]

        mc = mpf.make_marketcolors(
            up='white',        # bullish candles
            down='black',        # bearish candles
            edge='black',      # candle border
            wick='black',      # wick color
        )

        candle_style = mpf.make_mpf_style(marketcolors=mc, edgecolor='black')

        # Draw candlesticks
        mpf.plot(df, type='candle', ax=ax, style=candle_style, show_nontrading=False, xlim=xlim)

        # OPENS
        x_right = ax.get_xlim()[1]
        end_candles = x_right
        if timeframe == 0:
            end_candles = x_right * 0.67

        # Weekly open level and start position
        week_open = data_candles[1]['Open'].iloc[-1]
        monthly_open = data_candles[2]['Open'].iloc[-1]
        week_date = data_candles[1].index[-1] + pd.Timedelta(days=1) 
        month_date = data_candles[2].index[-1] + pd.Timedelta(days=1)

        for i in range(0, len(df)):
            if df.index[i] == week_date:
                posWeekly = i
            if df.index[i] == month_date:
                posMonthly = i

        start_weekly_open = (end_candles/N) * posWeekly
        start_monthly_open = (end_candles/N) * posMonthly
        
        # Draw the horizontal lines starting at their date
        if timeframe == 0:
            ax.hlines(week_open, xmin=start_weekly_open, xmax=x_right, color='blue', linewidth=2, label=f"Weekly Open {week_open:.2f}")
            ax.hlines(monthly_open, xmin=start_monthly_open, xmax=x_right, color='red', linewidth=2, label=f"Monthly Open {monthly_open:.2f}")

        # Title and axes
        ax.set_title(timeframes[timeframe], color='black')
        ax.tick_params(axis='x', colors='black', labelsize=0)
        ax.tick_params(axis='y', colors='black')
        ax.grid(True, alpha=0.5)
        ax.legend()    
        N = N - 15
        timeframe = timeframe + 1

    plt.tight_layout()
    plt.show()


def conditionalProbability(data, data_candles):
    timeframes = ["Daily", "Weekly", "Monthly"]
    fig, axs = plt.subplots(1, 3, figsize=(12, 6), sharey=True)

    for cont in range(len(data)):

        ax = axs[cont]   # <-- USE THE CORRECT SUBPLOT
        print(data_candles[cont])

        total_green = sum(data[cont]["Green"].values())
        total_red = sum(data[cont]["Red"].values())

        probability_green, probability_red = {}, {}
        for key, value in data[cont]["Green"].items():
            probability_green[key] = value / total_green
        for key, value in data[cont]["Red"].items():
            probability_red[key] = value / total_red

        probability_list = []
        x0 = len(data_candles[cont]) - 15
        num = 1
        candle = data_candles[cont].iloc[x0]["type"]
        x = x0 - 1

        while x >= 0 and data_candles[cont].iloc[x]["type"] == candle:
            num += 1
            x -= 1

        probability = next_candle_probability(candle, probability_green, probability_red, num)
        probability_list.append(probability)

        for i in range(len(data_candles[cont]) - 14, len(data_candles[cont])):
            if data_candles[cont].iloc[i]["type"] == data_candles[cont].iloc[i-1]["type"]:
                num += 1
            else:
                num = 1

            probability = next_candle_probability(candle, probability_green, probability_red, num)
            probability_list.append(probability)

        # --- COLORS ---
        color_list = []
        for i in range(len(data_candles[cont]) - 15, len(data_candles[cont])):
            color_list.append(data_candles[cont].iloc[i]["type"])

        # --- PLOT ---
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.5, len(probability_list) - 0.5)

        ax.axhline(0, color="green", linewidth=6)
        ax.axhline(1, color="red", linewidth=6)
        ax.axhline(0.5, color="gray", linestyle="--", alpha=0.3)

        x_vals = list(range(len(probability_list)))
        y_vals = probability_list

        ax.scatter(x_vals, y_vals, s=120, c=color_list, alpha=0.7, zorder=10)

        for xi, yi in zip(x_vals, y_vals):
            ax.annotate(
                f"{yi*100:.0f}%",
                (xi, yi),
                (1, 10),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color="red"
            )

            ax.annotate(
                f"{(1 - yi)*100:.0f}%",
                (xi, yi),
                (1, -10),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=8,
                fontweight="bold",
                color="green"
            )

        ax.set_title(f"Next {timeframes[cont]} Candles", fontsize=10)
        ax.set_xticks([])
        ax.grid(False)

    # --- SHOW ONCE ---
    plt.tight_layout()
    plt.show()


def statistics_rsi(data): # Calculo de los reversal points del rsi para las graficas
    localExtremes = []
    currentRsi = []
    parameters = [[65, 50, 35],[64, 55, 41],[68, 59, 50]] #daily, weekly, montly (umbral highs, mid confirmation, umbral low)
    cont = 0
    for df in data:
        df = df[df.index > df.index[0]+pd.Timedelta(days=1400)]
        print("-------------------------------------------------------------------------------------------------------------")
        state, value = 0, 50
        highs, lows = [], []
        lecture = False
        date = df.index[0]
        for i in range (0, len(df)):
            if df.iloc[i]["rsi"] >= parameters[cont][0]:
                if not lecture:
                   state = 1
                   lecture = True
                   value = df.iloc[i]["rsi"]
                   date = df.index[i]
                else:
                    if df.iloc[i]["rsi"] > value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]
            elif df.iloc[i]["rsi"] <= parameters[cont][2]:
                if not lecture:
                   state = 2
                   lecture = True
                   value = df.iloc[i]["rsi"]
                   date = df.index[i]
                else:
                    if df.iloc[i]["rsi"] < value:
                        value = df.iloc[i]["rsi"]
                        date = df.index[i]

            elif df.iloc[i]["rsi"] > parameters[cont][2] and df.iloc[i]["rsi"] < parameters[cont][0] and lecture and state > 0:
                if state == 1 and df.iloc[i]["rsi"] <= parameters[cont][1]:
                    if value >= parameters[cont][0]:
                        highs.append({date: value})
                    state = 0
                    lecture = False
                    value = parameters[cont][1]
                elif state == 2 and df.iloc[i]["rsi"] >= parameters[cont][1]:
                    if value <= parameters[cont][2]:
                        lows.append({date: value})
                    state = 0
                    lecture = False
                    value = parameters[cont][1]
        currentRsi.append({ df.index[-1] : df.iloc[-1]["rsi"]})
        aux_data = highs + lows
        print(aux_data)
        data = [d for d in aux_data if not (isinstance(list(d.keys())[0], float) and np.isnan(list(d.keys())[0]))]
        localExtremes.append(data)
        if cont == 2:
            print(data)
        cont = cont + 1    
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










                
                
                
               
                
      
   
               
 