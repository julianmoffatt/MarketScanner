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
# 3. Rachas de precio "congelado" -- sintoma directo de baja liquidez
# ---------------------------------------------------------------------------

def detect_stale_price_runs(df: pd.DataFrame, min_run: int = 5) -> pd.DataFrame:
    """
    Rachas de cierres identicos consecutivos. Es exactamente el patron de
    "apenas volatilidad" de un periodo poco publico: no es que el precio
    sea estable, es que no hay suficiente negociacion para que se mueva.
    Util como señal complementaria para acotar el regimen inicial ilíquido.
    """
    same_as_prev = df["Close"] == df["Close"].shift(1)
    run_id = (~same_as_prev).cumsum()
    run_length = same_as_prev.groupby(run_id).cumsum() + 1

    stale = run_length >= min_run
    return df.loc[stale, ["Close"]].assign(run_length=run_length[stale])


# ---------------------------------------------------------------------------
# 4. Onset del regimen de liquidez "normal"
# ---------------------------------------------------------------------------

def detect_illiquid_onset(
    df: pd.DataFrame,
    window: str = "60D",
    volume_ratio_threshold: float = 0.25,
    vol_ratio_threshold: float = 0.5,
) -> dict:
    """
    Estima desde que fecha el activo empieza a comportarse como "el
    mercado real" en vez del periodo inicial de baja negociacion (poco
    free float, cotizacion OTC previa, etc.) que algunas fuentes de datos
    mezclan sin avisar dentro de la serie historica.

    window es una ventana BASADA EN TIEMPO (p. ej. "60D"), no en numero
    de barras -- funciona igual sobre datos diarios, horarios o de 1 min,
    porque pandas la interpreta contra el indice datetime real, no contra
    un conteo de filas. Requiere indice datetime ordenado (sin duplicados).

    Metodo (heuristico -- confirma siempre con un grafico de volumen y
    volatilidad rolling antes de recortar nada): compara volumen y
    volatilidad realizada de una ventana movil contra la mediana de todo
    el historico, y exige que ambas se sostengan por encima de un umbral
    relativo durante toda la ventana, no solo un cruce aislado.
    """
    volume_roll = df["Volume"].rolling(window).median()
    volume_ratio = volume_roll / df["Volume"].median()

    ret = df["Close"].pct_change()
    vol_roll = ret.rolling(window).std()
    # la referencia se calcula sobre retornos recortados en los percentiles
    # extremos: un solo salto grande en la transicion illiquido -> normal
    # (no un bad-tick, un cambio real de nivel de precio) puede inflar la
    # std de toda la serie y hacer que el resto nunca supere el umbral.
    ret_for_scale = ret.clip(lower=ret.quantile(0.01), upper=ret.quantile(0.99))
    vol_ratio = vol_roll / ret_for_scale.std()

    qualifies = (volume_ratio > volume_ratio_threshold) & (vol_ratio > vol_ratio_threshold)
    sustained = qualifies.rolling(window).min().fillna(0).astype(bool)

    onset_date = sustained[sustained].index.min() if sustained.any() else None

    return {
        "onset_date": onset_date,
        "note": (
            f"El cambio de regimen real probablemente ocurrio ~{window} "
            "antes de onset_date -- la ventana de sostenimiento desplaza "
            "la deteccion hacia adelante."
        ),
        "volume_ratio": volume_ratio,
        "vol_ratio": vol_ratio,
    }


# ---------------------------------------------------------------------------
# 5. Funcion de pipeline: una sola llamada, devuelve (df_limpio, reporte)
# ---------------------------------------------------------------------------

def preprocess_ohlcv(
    df: pd.DataFrame,
    *,
    on_invalid: str = "drop",          # "drop" o "nan"
    fix_spikes: bool = True,
    spike_jump_threshold: float = 0.30,
    spike_revert_tolerance: float = 0.05,
    interpolate_limit: int = 2,
    drop_illiquid_onset: bool = True,
    illiquid_window: str = "60D",
    illiquid_volume_ratio_threshold: float = 0.25,
    illiquid_vol_ratio_threshold: float = 0.5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aplica la limpieza completa sobre un dataframe OHLCV crudo y devuelve
    (df_limpio, reporte). El reporte es un log fila a fila de cada accion
    tomada -- la limpieza nunca es silenciosa, siempre queda auditable.

    Orden de las operaciones (importa: cada paso asume que el anterior
    ya se aplico):
      1. Filas con violaciones basicas (precio<=0, volumen<0, OHLC
         incoherente, NaN) -> se eliminan o se marcan NaN segun on_invalid.
      2. Spikes tipo bad-tick -> se ponen a NaN y se interpolan
         linealmente, con un limite de huecos consecutivos para no
         tapar un gap real (p. ej. un halt de varios dias) con un
         valor inventado.
      3. Periodo inicial de baja liquidez -> se recorta desde el inicio
         de la serie hasta la fecha de onset detectada.

    on_invalid="drop" rompe la continuidad del indice de fechas (deja
    huecos donde antes habia una vela invalida). Si tu pipeline necesita
    un indice de calendario continuo, reindexa contra el calendario de
    trading real DESPUES de llamar a esta funcion, no antes.
    """
    df = df.copy()
    log = []
    price_cols = ["Open", "High", "Low", "Close"]

    # -- 1. violaciones basicas ---------------------------------------
    flags = check_basic_sanity(df)
    invalid_idx = df.index[flags["any_violation"]]
    for ts in invalid_idx:
        log.append({
            "date": ts,
            "action": f"invalid_row_{on_invalid}",
            "detail": [c for c in flags.columns if c != "any_violation" and flags.loc[ts, c]],
        })

    if on_invalid == "drop":
        df = df.drop(index=invalid_idx)
    elif on_invalid == "nan":
        df.loc[invalid_idx, price_cols + ["Volume"]] = np.nan
    else:
        raise ValueError('on_invalid debe ser "drop" o "nan"')

    # -- 2. spikes tipo bad-tick ---------------------------------------
    if fix_spikes:
        spikes = detect_price_spikes(df, spike_jump_threshold, spike_revert_tolerance)
        for ts, row in spikes.iterrows():
            log.append({"date": ts, "action": "spike_interpolated", "detail": {"return": round(row["return"], 4)}})

        df.loc[spikes.index, price_cols] = np.nan
        df[price_cols] = df[price_cols].interpolate(method="linear", limit=interpolate_limit)

    # -- 3. periodo inicial de baja liquidez ---------------------------
    if drop_illiquid_onset:
        onset = detect_illiquid_onset(
            df,
            window=illiquid_window,
            volume_ratio_threshold=illiquid_volume_ratio_threshold,
            vol_ratio_threshold=illiquid_vol_ratio_threshold,
        )
        if onset["onset_date"] is not None:
            dropped = df.loc[: onset["onset_date"]].iloc[:-1]
            for ts in dropped.index:
                log.append({"date": ts, "action": "illiquid_period_dropped", "detail": {}})
            df = df.loc[onset["onset_date"] :]

    report = (
        pd.DataFrame(log).set_index("date").sort_index()
        if log else pd.DataFrame(columns=["action", "detail"])
    )
    return df, report


# ---------------------------------------------------------------------------
# Uso
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df_raw = pd.read_csv("precios_crudos.csv", index_col=0, parse_dates=True)

    df_clean, report = preprocess_ohlcv(df_raw)

    print(f"Filas originales: {len(df_raw)}  ->  filas limpias: {len(df_clean)}")
    print(f"\nAcciones aplicadas ({len(report)}):")
    print(report["action"].value_counts())
    print("\nDetalle:")
    print(report)