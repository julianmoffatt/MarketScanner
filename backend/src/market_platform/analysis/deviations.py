import numpy as np
import pandas as pd

def calculation_average_deviation(timeframes):
    try:
        timeframes_aux = []
        for df in timeframes:
            df = df.copy()
            df['Deviation'] = np.where(df['type'] == 'Green', ((df['Open'] - df['Low']) / df['Open'])*100, ((df['High'] - df['Open']) / df['Open'])*100)
            #df = df[df['Deviation']>=0]
            timeframes_aux.append(df)
        return timeframes_aux 
    except Exception as e:
        print(e)

def calculation_trend_deviation(timeframes):
    df = timeframes[0].copy()
    df["EMA10_Absortion"] = np.where(((df["Open"]*0.998) > df["ema10"]) & ((df["Close"]*0.998) > df["ema10"]) & ((df["Low"]*1.002) < df["ema10"]), True, False)
    df["EMA10_Rejection"] = np.where(((df["Open"]*1.002) < df["ema10"]) & ((df["Close"]*1.002) < df["ema10"]) & ((df["High"]*0.998) > df["ema10"]), True, False)
    df["EMA20_Absortion"] = np.where(((df["Open"]*0.998) > df["ema20"]) & ((df["Close"]*0.998) > df["ema20"]) & ((df["Low"]*1.002) < df["ema20"]), True, False)
    df["EMA20_Rejection"] = np.where(((df["Open"]*1.002) < df["ema20"]) & ((df["Close"]*1.002) < df["ema20"]) & ((df["High"]*0.998) > df["ema20"]), True, False)
    df["MinClose1"] = pd.concat([df["Close"].shift(-1)], axis=1).min(axis=1)
    df["MinClose2"] = pd.concat([df["Close"].shift(-1), df["Close"].shift(-2)], axis=1).min(axis=1)
    df["MinClose3"] = pd.concat([df["Close"].shift(-1), df["Close"].shift(-2), df["Close"].shift(-3)], axis=1).min(axis=1)
    df["MaxClose"] = pd.concat([df["Close"].shift(-1),df["Close"].shift(-2),df["Close"].shift(-3)], axis=1).max(axis=1)
    df["Low3Days"] = (pd.concat([df["Low"].shift(-1),df["Low"].shift(-2),df["Low"].shift(-3)], axis=1).min(axis=1) / df["ema10"] - 1) * 100
    df["Max3Days"] = (pd.concat([df["High"].shift(-1),df["High"].shift(-2),df["High"].shift(-3)], axis=1).max(axis=1) / df["ema10"] - 1) * 100
    df["LowGrab"] = (pd.concat([df["Low"].shift(-1),df["Low"].shift(-2),df["Low"].shift(-3)], axis=1).min(axis=1) / df["Low"] - 1) * 100
    df["DeviationEMA"] = round(((df["Low"] / df["ema10"])-1)*100,1)
    return df
