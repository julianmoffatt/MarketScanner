"""
Flips: cuantas veces se "disputa" la direccion de una vela de timeframe alto, medido con
las velas de un timeframe bajo.

Adaptado de _legacy_statistics_calculation/flips_calculation.py. Idea:
- Dentro de cada vela de timeframe alto (semana, mes, trimestre, anio) se miran los cierres
  de las velas bajas (dia, mes...) respecto al OPEN de esa vela alta.
- El precio esta "encima" o "debajo" del open. Cambia de lado (un FLIP) solo cuando cierra al
  otro lado Y fuera de una banda de volatilidad alrededor del open: asi un cruce de pocos
  puntos no cuenta. La banda es la volatilidad realizada de las velas bajas (en %) por un
  peso que depende del par de timeframes (getWeightVol), acotada entre sus percentiles 20 y 80.
- Con todas las velas altas COMPLETAS se obtiene la distribucion historica del numero de
  flips (0, 1, 2...) y la mediana de en que vela baja ocurrio el ultimo. La vela alta en
  curso se calcula aparte: su numero de flips actual se compara con esa distribucion.

Cambio frente al legacy: la vela alta en curso NO entra en la distribucion historica (esta
incompleta y sesgaria el recuento hacia pocos flips).
"""
import numpy as np
import pandas as pd

from ...features.build_features import calculate_volatility, getWeightVol

TIMEFRAMES = ["daily", "weekly", "monthly", "quarterly", "yearly"]

# Casillas de la distribucion para cada (timeframe bajo -> timeframe alto). La ultima agrupa
# "ese numero o mas" para que los porcentajes sumen 100.
BUCKETS = {
    "daily": {"weekly": 3, "monthly": 5, "quarterly": 6, "yearly": 6},
    "monthly": {"quarterly": 3, "yearly": 6},
}

MIN_LOWER_CANDLES = 20  # como el legacy: con menos velas bajas no hay volatilidad fiable


def bucket_labels(count):
    return [str(i) for i in range(count - 1)] + [f"{count - 1}+"]


def count_flips(closes, vols, open_price, weight, vol_low, vol_high):
    """Flips de un ciclo. `closes` y `vols` son arrays de las velas bajas dentro de la vela alta.
    Devuelve (flips, last_flip): last_flip es la posicion (1 = primera vela) donde ocurrio el
    ultimo; vale 1 si no hubo ninguno."""
    side = 1 if closes[0] >= open_price else 0  # 1 = encima del open, 0 = debajo
    flips, last_flip = 0, 1
    for k in range(1, len(closes)):
        vol_now = vols[k]
        if np.isnan(vol_now):
            vol_now = vol_low
        threshold = min(max(vol_now * weight, vol_low * weight), vol_high * weight) / 100
        if (side == 0 and closes[k] > open_price * (1 + threshold)) or (
            side == 1 and closes[k] < open_price * (1 - threshold)
        ):
            side = 1 - side
            flips += 1
            last_flip = k + 1
    return flips, last_flip


def _cycles(lower_index, higher_index):
    """Posiciones [inicio, fin) de las velas bajas de cada vela alta. La ultima llega hasta el final."""
    starts = lower_index.searchsorted(higher_index, side="left")
    ends = np.append(starts[1:], len(lower_index))
    return starts, ends


def higher_timeframe_cycles(lower, higher, weight, vol, vol_low, vol_high, higher_df):
    """Una lista de (flips, last_flip) por vela alta, en orden; la ultima es la vela en curso.
    Las velas altas sin ninguna vela baja se omiten."""
    closes = lower["Close"].to_numpy(dtype=float)
    vols = vol.reindex(lower.index).to_numpy(dtype=float)
    opens = higher_df["Open"].to_numpy(dtype=float)
    starts, ends = _cycles(lower.index, higher_df.index)

    results = []
    for i, (start, end) in enumerate(zip(starts, ends)):
        if end <= start:
            continue
        flips, last_flip = count_flips(closes[start:end], vols[start:end], opens[i], weight, vol_low, vol_high)
        results.append((flips, last_flip, i == len(starts) - 1))
    return results


def compute(ticker, lower, timeframes):
    """Fila del screener para un activo, o None si no hay historia suficiente.
    `timeframes` es la lista [daily, weekly, monthly, quarterly, yearly] del pipeline."""
    lower_index = TIMEFRAMES.index(lower)
    lt = timeframes[lower_index]
    if len(lt) <= MIN_LOWER_CANDLES:
        return None
    vol, vol_low, vol_high = calculate_volatility(lt["Close"])
    if pd.isna(vol_low) or pd.isna(vol_high):
        return None

    blocks = []
    for t, (higher, bucket_count) in enumerate(BUCKETS[lower].items()):
        ht = timeframes[TIMEFRAMES.index(higher)]
        weight = getWeightVol(lower_index, t)
        cycles = higher_timeframe_cycles(lt, higher, weight, vol, vol_low, vol_high, ht)
        completed = [(f, lf) for f, lf, is_current in cycles if not is_current]
        current = next(((f, lf) for f, lf, is_current in cycles if is_current), None)

        if completed:
            flips = np.array([f for f, _ in completed])
            counts = np.bincount(np.minimum(flips, bucket_count - 1), minlength=bucket_count)
            distribution = [round(float(c) / len(completed) * 100, 1) for c in counts]
            last_flip_p50 = round(float(np.median([lf for _, lf in completed])), 1)
        else:
            distribution, last_flip_p50 = [0.0] * bucket_count, None

        blocks.append({
            "timeframe": higher,
            "occurrences": len(completed),
            "distribution": distribution,
            "last_flip_p50": last_flip_p50,
            "current_flips": None if current is None else current[0],
            "current_bucket": None if current is None else min(current[0], bucket_count - 1),
        })
    return {"ticker": ticker, "blocks": blocks}
