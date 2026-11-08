import pandas as pd
import yfinance as yf
import numpy as np
import time
from backend.src.market_platform.data.storage import *

def _columns_named(df, name):
    """Columnas cuyo nombre (o primer nivel, si son MultiIndex como las de yfinance) es `name`."""
    return [c for c in df.columns if (c[0] if isinstance(c, tuple) else c) == name]


def fetch_last_regular_close(symbol, day):
    """Ultimo precio de la sesion regular de `day`: cierre de la ultima vela horaria
    de ese dia (sin pre ni post-market). None si Yahoo no lo da o falla la descarga."""
    try:
        hourly = yf.Ticker(name_sustitution(symbol)).history(
            period="5d", interval="1h", prepost=False, auto_adjust=False
        )
        closes = hourly.loc[hourly.index.date == day, "Close"].dropna()
    except Exception as e:
        print(f"No se pudo obtener el precio intradia de {symbol}: {e}")
        return None
    return float(closes.iloc[-1]) if not closes.empty else None


def complete_last_daily_bar(df, symbol, fetch_close=fetch_last_regular_close):
    """Yahoo a veces entrega la ultima vela diaria sin Close/Adj Close (el cierre
    aun no esta publicado) aunque ya traiga Open/High/Low/Volume. Si es el caso,
    se completa con el ultimo precio de la sesion regular y se devuelve una copia;
    si no se puede obtener, se deja igual (la limpieza posterior la descartara)."""
    close_cols = _columns_named(df, "Close")
    if df.empty or not close_cols or pd.notna(df[close_cols[0]].iloc[-1]):
        return df

    last_bar = df.index[-1]
    price = fetch_close(symbol, pd.Timestamp(last_bar).date())
    if price is None:
        return df

    print(f"Vela diaria de {symbol} sin cierre en Yahoo ({last_bar}): se completa con {price:.2f}")
    df = df.copy()
    df.loc[last_bar, close_cols + _columns_named(df, "Adj Close")] = price
    return df


# Timeframe RAW
def loadBaseTimeframe(symbol, timeframe_base, premarket_postmarket):
    name = symbol + "_" + timeframe_base
    df = import_csv(name, "raw/")
    if df is False:
        df = yf.download(name_sustitution(symbol), interval=timeframe_base, auto_adjust=False, progress=False, period="max", prepost = premarket_postmarket) #parametrizo por eficiencia para algunos metodos?
        if df.empty:
            raise ValueError(f"No se encontraron datos en Yahoo Finance para '{symbol}'")
        if timeframe_base == "1d":
            df = complete_last_daily_bar(df, symbol)
        save_csv(df, name, "raw/")
    elif "Ticker" in df.index or df.index.name == "Price":
        url = url_database() + "raw/" + name + ".csv"
        df = pd.read_csv(url, header=[0, 1], index_col=0, parse_dates=True, skiprows=[2])
    print(df)
    return df


# Pares de forex del universo (config.yaml) tal como los escribe/busca el
# usuario en pantalla (sin el sufijo "=X" que exige yfinance) -- sin esta
# traduccion, pedir p.ej. "EURGBP" a secas no es un ticker valido de Yahoo
# Finance y la descarga no devuelve nada.
FOREX_PAIRS = {
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
}


# se hace en ingest y no hace falta mas
def name_sustitution(name):
    key = name.upper()
    if key == "SP500":
        return "^GSPC"
    elif key == "NASDAQ":
        return "^IXIC"
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
    elif key in FOREX_PAIRS:
        return f"{key}=X"
    else:
        return name


