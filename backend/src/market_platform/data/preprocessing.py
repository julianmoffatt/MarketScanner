import numpy as np
import pandas as pd
from backend.src.market_platform.data.data_validation import check_basic_sanity, detect_price_spikes, detect_illiquid_onset

def dataValidation(df, drop_illiquid_onset=True, verbose=False):
    """
    Limpieza del dataframe OHLCV crudo, ANTES de cualquier resample o
    feature engineering. Se aplica sobre la resolucion base (1min, 1h o
    1d): un dato corrupto en la base contamina todos los timeframes
    derivados via resample (un solo bad tick en 1min puede convertirse
    en el High/Low de la vela de 4h que lo contiene).

    Pasos, en orden (cada uno asume que el anterior ya se aplico):
      1. Normaliza el indice (datetime, ordenado, sin duplicados).
      2. Corrige violaciones basicas (precio<=0, volumen<0, High<Low,
         Close/Open fuera de [Low,High]) columna por columna via NaN +
         interpolacion -- NUNCA elimina el dia solo por esto. Perder una
         fecha de mercado real en medio de la serie (no al inicio) rompe
         cualquier cosa que dependa del calendario: resamples, conteo de
         dias, alineacion con otros activos. Solo si una fila queda sin
         poder interpolarse (borde de la serie, o hueco mayor al limite)
         se elimina, y es la excepcion, no la regla -- queda logueada
         como "unfixable_row_drop", distinta de una limpieza normal.
      3. Interpola spikes tipo bad-tick (salto que se revierte casi
         exactamente al dia/barra siguiente), con el mismo criterio:
         se corrige el valor, no se borra el dia.
      4. Recorta el tramo inicial de baja liquidez, si lo hay -- este es
         el UNICO paso que recorta calendario, y solo al principio de la
         serie, nunca en medio (ventana de deteccion basada en tiempo,
         no en numero de barras, para que funcione igual sobre 1min, 1h
         o 1d).

    El log de que se hizo y por que queda en df.attrs["validation_report"]
    -- no se pierde, pero tampoco estorba si solo usas el dataframe.
    """
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]

    report_rows = []
    price_cols = ["Open", "High", "Low", "Close"]

    # -- violaciones basicas: fix columna por columna, no borrar el dia --
    # Se atribuye cada violacion a la(s) columna(s) mas plausiblemente
    # responsables, en vez de invalidar las 4 solo porque una fallo.
    fixes = {
        "Open": (df["Open"] <= 0) | (df["Open"] > df["High"]) | (df["Open"] < df["Low"]),
        "High": (df["High"] <= 0) | (df["High"] < df["Low"]),
        "Low": (df["Low"] <= 0) | (df["High"] < df["Low"]),
        "Close": (df["Close"] <= 0) | (df["Close"] > df["High"]) | (df["Close"] < df["Low"]),
        "Volume": df["Volume"] < 0,
    }
    for col, mask in fixes.items():
        for ts in df.index[mask.fillna(False)]:
            report_rows.append({"date": ts, "action": f"invalid_{col.lower()}_interpolated"})
        df.loc[mask.fillna(False), col] = np.nan

    cols_to_fill = price_cols + ["Volume"]
    df[cols_to_fill] = df[cols_to_fill].astype(float).interpolate(method="linear", limit=2)

    # lo que siga en NaN (borde de la serie sin vecino valido, o un hueco
    # mayor al limite) no se puede arreglar sin inventar un dato -- ahi
    # si se elimina el dia, pero deberia ser raro, no la via principal.
    unfixable = df[cols_to_fill].isna().any(axis=1)
    for ts in df.index[unfixable]:
        report_rows.append({"date": ts, "action": "unfixable_row_drop"})
    df = df.loc[~unfixable]

    # -- spikes tipo bad-tick ------------------------------------------
    spikes = detect_price_spikes(df)
    for ts, row in spikes.iterrows():
        report_rows.append({"date": ts, "action": "spike_interpolated", "return": round(row["return"], 4)})
    if len(spikes):
        df.loc[spikes.index, price_cols] = np.nan
        df[price_cols] = df[price_cols].interpolate(method="linear", limit=2)

    # -- periodo inicial de baja liquidez -- unico paso que recorta calendario,
    #    y solo desde el principio de la serie hacia adelante -------------
    if drop_illiquid_onset and len(df) > 1:
        onset = detect_illiquid_onset(df)
        if onset["onset_date"] is not None:
            dropped = df.loc[: onset["onset_date"]].iloc[:-1]
            for ts in dropped.index:
                report_rows.append({"date": ts, "action": "illiquid_period_dropped"})
            df = df.loc[onset["onset_date"] :]

    # Se guarda como lista de dicts, NO como DataFrame: pandas compara los
    # attrs con "==" en operaciones internas (resample, concat) via
    # __finalize__, y comparar un DataFrame con "==" ahi rompe con un
    # ValueError de verdad ambigua. Una lista de dicts compara sin problema.
    df.attrs["validation_report"] = report_rows
    if verbose and report_rows:
        report = validation_report_to_df(report_rows)
        print(f"dataValidation: {len(report)} acciones aplicadas")
        print(report["action"].value_counts())

    return df


def validation_report_to_df(report_rows):
    """Convierte el log de dataValidation (lista de dicts) a DataFrame
    para inspeccion -- uso: validation_report_to_df(df.attrs["validation_report"])"""
    if not report_rows:
        return pd.DataFrame(columns=["action"])
    return pd.DataFrame(report_rows).set_index("date").sort_index()


def last_X_years(df, num_years):
    df.index = pd.to_datetime(df.index)
    last_date = df.index.max()
    cutoff_date = last_date - pd.DateOffset(years=num_years)
    return df.loc[df.index >= cutoff_date].copy()

    
def preprocessing(df_base, t):
    if isinstance(df_base.columns, pd.MultiIndex):
        df_base.columns = df_base.columns.get_level_values(0)
        df_base.index = pd.to_datetime(df_base.index, utc=True)   

    if t == 0:
        df_base.index = df_base.index.normalize()
        df_base = df_base.sort_index()
    else:
        if df_base.index.tz is None:
            df_base.index = df_base.index.tz_localize('UTC')
        else:
            df_base.index = df_base.index.tz_convert('UTC') 
    timeframe_preprocessing = {0: lambda: preprocessing_highertimeframe(df_base), 1: lambda: preprocessing_lowertimeframe(df_base), 2: lambda: preprocessing_microtimeframe(df_base)}
    return timeframe_preprocessing[t]()


def preprocessing_highertimeframe(df_base):
    df_base = last_X_years(df_base, 40)
    timeframes = []
    df_base = dataValidation(df_base)
    weekly = df_base.resample('W-MON', label='left', closed='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    monthly = df_base.resample('MS', label='left', closed='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    quarterly = monthly.resample('QS', label='left', closed='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    yearly = quarterly.resample('YS').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    for t in [df_base, weekly, monthly, quarterly, yearly]:
        timeframes.append(t)
    return timeframes


def preprocessing_lowertimeframe(df_base):
    timeframes = []
    df_base = dataValidation(df_base)
    data4H = df_base.resample('4h', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data4H.dropna(inplace=True)
    for t in [df_base, data4H]:
        timeframes.append(t)
    return timeframes


def preprocessing_microtimeframe(df_base):
    timeframes = []
    df_base = dataValidation(df_base)
    data5min = df_base.resample('5min', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data5min.dropna(inplace=True)
    data15min = df_base.resample('15min', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data15min.dropna(inplace=True)
    data30min = df_base.resample('30min', label='left').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    data30min.dropna(inplace=True)
    for t in [df_base, data5min, data15min, data30min]:
        timeframes.append(t)
    return timeframes
