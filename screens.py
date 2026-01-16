from functions import * 
from statistics import *
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import mplfinance as mpf
import pandas as pd

# 1. Screen with daily weekly and monthly candles alongside opens (montlhy and weekly opens)
def screen_candles(data_candles):
    timeframes = ["Daily", "Weekly", "Monthly"]
    posWeekly, posMonthly = 0, 0
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

        print(week_date)
        print(monthly_open)
        if timeframe == 0:
            week, month = True, True
            for i in range(0, len(df)):
                if df.index[i] >= week_date and week:
                    posWeekly = i+1
                    week = False
                if df.index[i] >= month_date and month:
                    posMonthly = i+1
                    month = False
            print("Positions lines", posWeekly, posMonthly)

            try:
                start_weekly_open = (end_candles/N) * posWeekly
                start_monthly_open = (end_candles/N) * posMonthly
                # Draw the horizontal lines starting at their date
                ax.hlines(week_open, xmin=start_weekly_open, xmax=x_right, color='blue', linewidth=2, label=f"Weekly Open {week_open:.2f}")
                ax.hlines(monthly_open, xmin=start_monthly_open, xmax=x_right, color='red', linewidth=2, label=f"Monthly Open {monthly_open:.2f}")
            except:
                pass

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


# 2. Screen with Rsi reversal points and next candle probability
def screen_statistics(rsiReversalZones, currentRsi, probabilities, colours):
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

    for cont in range(len(probabilities)):
        ax = fig.add_subplot(gs[1, cont])
        ax.set_ylim(-0.05, 1.05)
        ax.set_xlim(-0.5, len(probabilities[cont]) - 0.5)
        ax.axhline(0, color="green", linewidth=6)
        ax.axhline(1, color="red", linewidth=6)
        ax.axhline(0.5, color="gray", linestyle="-", alpha=0.5)

        x_vals = list(range(len(probabilities[cont])))
        y_vals = probabilities[cont]

        ax.scatter(x_vals, y_vals, s=120, c=colours[cont], alpha=0.7, zorder=10)

        for xi, yi in zip(x_vals, y_vals):
            ax.annotate(f"{yi*100:.0f}%", (xi, yi), (1, 10), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold", color="red")
            ax.annotate(f"{(1 - yi)*100:.0f}%", (xi, yi), (1, -10), textcoords="offset points", ha="center", va="top", fontsize=8, fontweight="bold", color="green")

        ax.set_title("", fontsize=10)
        ax.set_xticks([])
        ax.grid(False)

    plt.tight_layout()
    plt.show()


