import os
from concurrent.futures import ProcessPoolExecutor
from data.assets import Assets 
from screens.screens_web import *
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from functools import partial # para pasar mas de un parametro a la Pool de procesos
from itertools import product
import numpy as np
import pandas as pd

def flips_calculation_all_symbols(x_timeframe_name):
    try:
        assets = Assets()
        timeframe_name = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        x_timeframe = timeframe_name.index(x_timeframe_name)
        data_rows = []
        columns = ["Asset"]
        for i in range (x_timeframe+1, len(timeframe_name)):
            columns.append("n"+str(timeframe_name[i][0]).upper())
            columns.append(str(timeframe_name[i][0]).upper()+"%")
            for j in range (0,2+i): #se registran mas cantidad de flips por timeframe, acotar esto para que tenga sentido
                columns.append(str(j) + " " + timeframe_name[i][0:3] + "_F")

        symbols = assets.getAssets("mysymbols")
        combos = list(product(symbols, [x_timeframe])) # Todas las combinaciones (símbolo, timeframe)

        with ProcessPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(flips_calculation_aux, combos))

        data_rows = [r for r in results if r is not False]
        df = pd.DataFrame(data_rows, columns = columns)
        name = "excels/flips_" + timeframe_name[x_timeframe] + ".csv"
        df.to_csv(name)    
        return df    
    except Exception as e:
        print(e)


def flips_calculation_aux(args):
    symbol, x_timeframe = args
    return flips_calculation(symbol, x_timeframe)    


def flips_calculation(symbol, x_timeframe):
    assets = Assets()
    timeframes = assets.loadStatistics(assets.loadTimeframes(symbol))
    if len(timeframes[x_timeframe]) <= 20:
        return False
    dfs = flips_dynamics(symbol, timeframes, x_timeframe)
    if any(df_item.empty for df_item in dfs):
        return False
    config = [[0, 1, 2], [0, 1, 2, 3], [0, 1, 2, 3, 4], [0, 1, 2, 3, 4, 5]] # 4, True para mon y quar
    new_row = [assets.name_sustitution(symbol)]
    for i, df_item in enumerate(dfs):
        flips_to_show = config[i+x_timeframe]
        counts = df_item["Flips"].value_counts().reindex(range(20), fill_value=0)
        total = counts.sum()
        new_row.append(round(total, 0))
        new_row.append(str(round(np.quantile(df_item["Threshold"], 0), 1))+" | "+str(round(np.quantile(df_item["Threshold"], 1), 1)))
        for f in flips_to_show:
            percentage = round((counts[f] / total) * 100, 1) if total > 0 else 0
            new_row.append(percentage)
    return new_row


def flips_dynamics(symbol, timeframes, x_timeframe):
    assets = Assets()
    timeframe_name = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    parameters = [pd.Timedelta(days=7), pd.offsets.MonthBegin(1), pd.offsets.MonthBegin(3), pd.offsets.MonthBegin(12)]

    # volatilidad histórica del LT completo — log-returns rolling 20, percentiles para clamps
    LT_full = timeframes[x_timeframe].copy()
    LT_vol_full = np.log(LT_full["Close"] / LT_full["Close"].shift(1)).rolling(20).std() * 100
    vol_p20 = LT_vol_full.quantile(0.20)
    vol_p80 = LT_vol_full.quantile(0.80)

    timeframes_cycles = []
    end = []
    for k in range(0 + x_timeframe, len(parameters)):
        end.append(pd.to_datetime((timeframes[k + 1].index[-1] + parameters[k]), utc=True))

    for t, k in enumerate(range(0 + x_timeframe, len(parameters))):
        higher_timeframe = k + 1
        HT = timeframes[higher_timeframe].copy()
        LT = LT_full[LT_full.index < end[t]]

        cycle = pd.DataFrame(columns=["Date", "Open", "Flips", "LastFlip", "Threshold", "Direction", "Return"])
        for x in range(0, len(HT)-1):
            df = LT[(LT.index >= HT.index[x]) & (LT.index < HT.index[x+1])]
            if df.empty:
                continue
            df_vol = LT_vol_full.reindex(df.index)
            print(timeframe_name[higher_timeframe], "| OPEN:", HT.iloc[x]["Open"], "| CLOSE:", HT.iloc[x]["Close"], "| DATE:", HT.index[x])

            params = flips_dynamics_calculation(symbol, df, HT.iloc[x]["Open"], timeframe_name[higher_timeframe], df_vol, vol_p20, vol_p80, assets.getWeightVol(x_timeframe, t))
            cycle.loc[len(cycle)] = [HT.index[x], round(HT.iloc[x]["Open"], 1), params[0], params[1], params[2], HT.iloc[x]["type"], HT.iloc[x]["Return"]]

        df = LT[(LT.index >= HT.index[-1])]
        if not df.empty:
            df_vol = LT_vol_full.reindex(df.index)
            params = flips_dynamics_calculation(symbol, df, HT.iloc[-1]["Open"], timeframe_name[higher_timeframe], df_vol, vol_p20, vol_p80, assets.getWeightVol(x_timeframe, t))
            cycle.loc[len(cycle)] = [HT.index[-1], round(HT.iloc[-1]["Open"],1), params[0], params[1], params[2], HT.iloc[-1]["type"], HT.iloc[-1]["Return"]]
        cycle.set_index("Date", inplace=True)
        timeframes_cycles.append(cycle)
    return timeframes_cycles


def flips_dynamics_calculation(symbol, df, open, timeframe, df_vol, vol_p20, vol_p80, timeframe_weight):
    try:
        threshold = 0
        vol_k = 1
        weight = timeframe_weight
        flips, lastFlip, side = 0, 1, 0
        sides = {1: 0, 0: 1}
        side = 1 if df.iloc[0]["Close"] >= open else 0

        for k in range(1, len(df)):
            vol_now = df_vol.iloc[k] if k < len(df_vol) and not np.isnan(df_vol.iloc[k]) else vol_p20
            threshold = np.clip(vol_now * vol_k * weight, vol_p20 * vol_k * weight, vol_p80 * vol_k * weight)
            upper_threshold = open * (1 + threshold / 100)
            lower_threshold = open * (1 - threshold / 100)

            if ((df.iloc[k]["Close"] > upper_threshold) and (side == 0)) or \
               ((df.iloc[k]["Close"] < lower_threshold) and (side == 1)):
                side = sides[side]
                flips += 1
                lastFlip = k + 1
                print(symbol, "|| FLIP ||", df.index[k], "||", df.iloc[k]["Close"], "|| threshold:", round(threshold, 2), "%", timeframe)
        return flips, lastFlip, round(threshold, 2)
    except Exception as e:
        print(e) 


def current_flips_calculation_all_symbols(x_timeframe_name):
    try:
        assets = Assets()
        timeframe_name = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        x_timeframe = timeframe_name.index(x_timeframe_name)
        data_rows = []

        symbols = assets.getAssets("mysymbols")
        combos = list(product(symbols, [x_timeframe])) # Todas las combinaciones (símbolo, timeframe)
        
        with ProcessPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(current_flips_calculation_aux, combos))

        data_rows = [r for r in results if r is not False]  
        df = pd.DataFrame(data_rows)
        name_csv = "excels/currentflips_" + x_timeframe_name + ".csv"
        df.to_csv(name_csv)    
        print("i return the csv of current flips")
        return df 
    except Exception as e:
        print(e)


def current_flips_calculation_aux(args):
    symbol, x_timeframe = args
    return current_flips_calculation(symbol, x_timeframe)   


def current_flips_calculation(symbol, x_timeframe):
    timeframe_name = ["daily", "weekly", "monthly", "quarterly", "yearly"]
    print("i process", symbol)
    assets = Assets()
    timeframes = assets.loadTimeframes(symbol)
    LT_full = timeframes[x_timeframe]
    LT_vol = np.log(LT_full["Close"] / LT_full["Close"].shift(1)).rolling(20).std() * 100
    vol_p20 = LT_vol.quantile(0.20)
    vol_p80 = LT_vol.quantile(0.80)
    symbol_flips = []
    t = 0

    for i in range (x_timeframe + 1, len(timeframes)):
        lowerTimeframeCandles = timeframes[x_timeframe][timeframes[x_timeframe].index >= timeframes[i].index[-1]]
        open_price = timeframes[i].iloc[-1]["Open"]
        df_vol = LT_vol.reindex(lowerTimeframeCandles.index)
        flips, lastFlip, threshold = flips_dynamics_calculation(symbol, lowerTimeframeCandles, open_price, timeframe_name[i], df_vol, vol_p20, vol_p80, assets.getWeightVol(x_timeframe, t))

        max_flips = t + x_timeframe + 2 # coincide con el ultimo indice "j {tf}_F" que genera flips_calculation_all_symbols para este bloque
        if flips > max_flips:
            flips = max_flips
        symbol_flips.append([flips, lastFlip])
        t += 1

    higher_timeframes = timeframe_name[x_timeframe + 1:] # symbol_flips solo trae datos de estos, no de todos los timeframe_name
    row = {"symbol": assets.name_sustitution(symbol)}
    for i, tf in enumerate(higher_timeframes):
        row[f"{tf}Flip"] = symbol_flips[i][0]
        row[f"{tf}LastFlip"] = symbol_flips[i][1]
    return row