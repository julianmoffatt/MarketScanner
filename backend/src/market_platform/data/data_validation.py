"""
Validacion de calidad para dataframes OHLCV crudos de precios de stocks.
Se ejecuta ANTES de cualquier feature engineering
Opera solo sobre el dato crudo para decidir que esta mal, que es sospechoso, y que corresponde a un regimen distinto de liquidez.
Espera un DataFrame indexado por fecha (datetime, ordenado), con columnas: Open, High, Low, Close, Volume
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Chequeos estructurales: precios/volumen imposibles en un mercado real
# ---------------------------------------------------------------------------

def check_basic_sanity(df: pd.DataFrame) -> pd.DataFrame:
    # Un dataframe de flags booleanos, una fila por cada vela del input, marcando cada tipo de violacion.
    flags = pd.DataFrame(index=df.index)

    flags["has_nan"] = df[["Open", "High", "Low", "Close", "Volume"]].isna().any(axis=1)
    flags["neg_or_zero_price"] = (df[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)
    flags["neg_volume"] = df["Volume"] < 0
    flags["high_lt_low"] = df["High"] < df["Low"]
    flags["close_outside_range"] = (df["Close"] > df["High"]) | (df["Close"] < df["Low"])
    flags["open_outside_range"] = (df["Open"] > df["High"]) | (df["Open"] < df["Low"])

    # atribucion por columna: que campo es el sospechoso (el que se anula e interpola)
    flags["invalid_open"] = (df["Open"] <= 0) | (df["Open"] > df["High"]) | (df["Open"] < df["Low"])
    flags["invalid_high"] = (df["High"] <= 0) | (df["High"] < df["Low"])
    flags["invalid_low"] = (df["Low"] <= 0) | (df["High"] < df["Low"])
    flags["invalid_close"] = (df["Close"] <= 0) | (df["Close"] > df["High"]) | (df["Close"] < df["Low"])
    flags["invalid_volume"] = df["Volume"] < 0

    flags["any_violation"] = flags.any(axis=1)
    return flags


# ---------------------------------------------------------------------------
# 2. Spikes imposibles: saltos que se revierten casi exactamente al dia siguiente
# ---------------------------------------------------------------------------

def detect_price_spikes(
    df: pd.DataFrame,
    jump_threshold: float = 0.30,
    revert_tolerance: float = 0.05,
) -> pd.DataFrame:
    """
    Un bad tick clasico se ve asi: retorno de +80% en el dia s, seguido de un retorno 
    que deja el precio en el dia s+1 casi exactamente donde estaba en s-1.
    jump_threshold:   retorno absoluto minimo para considerar "salto"
    revert_tolerance: cuan cerca debe quedar close(s+1) de close(s-1) para considerarlo una reversion completa
    """
    close = df["Close"]
    ret = close.pct_change()  # ret[s] = close[s]/close[s-1] - 1

    is_jump = ret.abs() > jump_threshold

    # round_trip[t] compara close(t) contra close(t-2).
    # Si el salto ocurrio en s y se revirtio al dia siguiente,
    # close(s+1) ~= close(s-1)  =>  round_trip en (s+1) es chico.
    # shift(-1) trae ese valor de (s+1) a la posicion s, donde vive is_jump,
    # para poder marcar directamente el dia del salto.
    round_trip = (close / close.shift(2) - 1).abs()
    is_round_trip = round_trip < revert_tolerance

    spike_candidate = is_jump & is_round_trip.shift(-1).fillna(False)

    out = pd.DataFrame({"return": ret, "spike_candidate": spike_candidate}, index=df.index)
    return out[out["spike_candidate"]]


# ---------------------------------------------------------------------------
# 3. Onset del regimen de volatilidad "normal"
# ---------------------------------------------------------------------------

def detect_illiquid_onset(
    df: pd.DataFrame,
    min_period: str = "60D",
    ratio_min: float = 3.0,
    max_fraction: float = 0.5,
) -> dict:
    """
    Detecta el tramo inicial de baja volatilidad (poco free float, SPAC o
    cotizacion OTC previa) que algunas fuentes mezclan con el historico real.

    Busca el unico punto de corte que mejor separa dos varianzas de retornos
    logaritmicos (maxima verosimilitud gaussiana). Usa toda la serie, incluido
    el futuro: es limpieza historica, no una feature. Solo recorta si
    std_despues / std_antes >= ratio_min; si no, onset_date es None.

    min_period:   duracion minima de cada tramo (basada en tiempo, vale para 1d, 1h o 1min)
    max_fraction: fraccion maxima de la serie que se puede recortar
    onset_date es el primer dia del regimen normal.
    """
    ret = np.log(df["Close"]).diff().replace([np.inf, -np.inf], np.nan).dropna()
    n = len(ret)
    result = {"onset_date": None, "vol_ratio": None}
    if n < 4:
        return result

    span = pd.Timedelta(min_period)
    k_min = max(ret.index.searchsorted(ret.index[0] + span) + 1, 2)
    k_max = min(ret.index.searchsorted(ret.index[-1] - span, side="right") - 1, int(n * max_fraction), n - 2)
    if k_min > k_max:
        return result

    x = ret.to_numpy()
    s1, s2 = np.cumsum(x), np.cumsum(x**2)
    k = np.arange(k_min, k_max + 1)
    var_before = np.maximum((s2[k - 1] - s1[k - 1] ** 2 / k) / k, 1e-18)
    var_after = np.maximum(((s2[-1] - s2[k - 1]) - (s1[-1] - s1[k - 1]) ** 2 / (n - k)) / (n - k), 1e-18)
    best = np.argmin(k * np.log(var_before) + (n - k) * np.log(var_after))

    result["vol_ratio"] = float(np.sqrt(var_after[best] / var_before[best]))
    if result["vol_ratio"] >= ratio_min:
        result["onset_date"] = ret.index[k[best]]
    return result


# ---------------------------------------------------------------------------
# Pipeline de limpieza: una sola llamada, usa las tres funciones anteriores
# ---------------------------------------------------------------------------

def clean_ohlcv(df, drop_illiquid_onset=True, verbose=False):
    """
    Limpieza del dataframe OHLCV crudo, ANTES de cualquier resample o feature engineering.
    Pasos, en orden (cada uno asume que el anterior ya se aplico):
      1. Normaliza el indice (datetime, ordenado, sin duplicados).
      2. Corrige violaciones basicas (precio<=0, volumen<0, High<Low,Close/Open fuera de [Low,High]) 
      3. Interpola spikes tipo bad-tick (salto que se revierte casi exactamente al dia/barra siguiente)
      4. Recorta el tramo inicial de baja liquidez, si lo hay.
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
    flags = check_basic_sanity(df)
    for col in price_cols + ["Volume"]:
        mask = flags[f"invalid_{col.lower()}"]
        for ts in df.index[mask]:
            report_rows.append({"date": ts, "action": f"invalid_{col.lower()}_interpolated"})
        df.loc[mask, col] = np.nan

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
