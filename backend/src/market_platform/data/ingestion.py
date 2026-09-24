import pandas as pd
import yfinance as yf
import numpy as np
import time
from backend.src.market_platform.data.storage import *

# Timeframe RAW
def loadBaseTimeframe(symbol, timeframe_base, premarket_postmarket):
    name = symbol + "_" + timeframe_base
    df = import_csv(name, "raw/")
    if df is False:
        df = yf.download(name_sustitution(symbol), interval=timeframe_base, auto_adjust=False, progress=False, period="max", prepost = premarket_postmarket) #parametrizo por eficiencia para algunos metodos?
        if df.empty:
            raise ValueError(f"No se encontraron datos en Yahoo Finance para '{symbol}'")
        save_csv(df, name, "raw/")
    elif "Ticker" in df.index or df.index.name == "Price":
        url = url_database() + "raw/" + name + ".csv"
        df = pd.read_csv(url, header=[0, 1], index_col=0, parse_dates=True, skiprows=[2])
    print(df)
    return df


# se hace en ingest y no hace falta mas
def name_sustitution(name):
    key = name.upper()
    if key == "SP500":
        return "^GSPC"
    elif key == "GOLD":
        return "GC=F"
    elif key == "SILVER":
        return "SI=F"
    elif key == "OIL":
        return "CL=F"
    elif key == "PLATINUM":
        return "PL=F"
    elif key == "PALLADIUM":
        return "PA=F"
    elif key == "BTC":
        return "BTC-USD"
    elif key == "ETH":
        return "ETH-USD"
    else:
        return name


