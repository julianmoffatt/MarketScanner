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
        save_csv(df, name, "raw/")
    elif "Ticker" in df.columns or "Price" in df.columns:
        url = url_database() + "raw/" + name + ".csv"
        df = pd.read_csv(url, header=[0, 1], index_col=0, parse_dates=True)
    return df


# se hace en ingest y no hace falta mas
def name_sustitution(name):
    if name == "SP500":
        return "^GSPC"
    elif name == "GOLD":
        return "GC=F"
    elif name == "SILVER":
        return "SI=F"
    elif name == "OIL":
        return "CL=F"
    elif name == "PLATINUM":
        return "PL=F"
    elif name == "PALLADIUM":
        return "PA=F"
    elif name == "BTC":
        return "BTC-USD"
    elif name == "ETH":
        return "ETH-USD"
    else:
        return name


