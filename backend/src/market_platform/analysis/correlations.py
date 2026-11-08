"""
Correlacion y betas alcista/bajista entre el activo seleccionado y un grupo de activos
de referencia, para varias ventanas de tiempo, mas las curvas de rentabilidad acumulada
del ultimo ano para comparar visualmente.

Funciones puras (reciben series de cierres, no tocan disco ni red).

Metodologia (estandar):
- Retornos logaritmicos diarios sobre las fechas COMUNES a los dos activos: se alinean
  los cierres primero y se calculan los retornos despues, asi un retorno nunca mezcla
  intervalos distintos (p.ej. BTC cotiza fines de semana y las acciones no: el retorno
  del lunes de BTC cubre el mismo periodo que el de la accion).
- Cada ventana (1M, 3M, ...) termina en la ultima fecha comun.
- Beta alcista / bajista: pendiente de regresar el retorno del activo seleccionado sobre
  el del activo de referencia (cov / var), usando solo los dias en que la referencia sube
  (beta+) o baja (beta-). Se filtra por la variable explicativa y no por la respuesta, asi
  la pendiente no se sesga por el corte (la correlacion dentro de cada lado si lo haria).
- Una ventana con pocos retornos comunes, o que el historico comun no llega a cubrir,
  devuelve None. Las betas exigen ademas un minimo de dias en cada lado.
"""
import numpy as np
import pandas as pd

MIN_OBSERVATIONS = 15
MIN_SIDE_OBSERVATIONS = 8
CURVE_YEARS = 1

WINDOWS = {
    "1M": pd.DateOffset(months=1),
    "3M": pd.DateOffset(months=3),
    "1Y": pd.DateOffset(years=1),
    "3Y": pd.DateOffset(years=3),
    "5Y": pd.DateOffset(years=5),
}

EMPTY_STATS = {"correlation": None, "beta_up": None, "beta_down": None,
               "observations": 0, "observations_up": 0, "observations_down": 0}


def _common_log_returns(asset_close, peer_close):
    aligned = pd.concat([asset_close, peer_close], axis=1, join="inner").dropna()
    aligned.columns = ["asset", "peer"]
    return np.log(aligned).diff().dropna()


def _beta(side):
    """Pendiente del retorno del activo sobre el de la referencia dentro de `side`."""
    if len(side) < MIN_SIDE_OBSERVATIONS:
        return None
    variance = side["peer"].var()
    if not variance or pd.isna(variance):
        return None
    return round(float(side["asset"].cov(side["peer"]) / variance), 4)


def _window_stats(returns, offset):
    if returns.empty:
        return dict(EMPTY_STATS)
    cutoff = returns.index[-1] - offset
    window = returns[returns.index > cutoff]
    up, down = window[window["peer"] > 0], window[window["peer"] < 0]
    counts = {"observations": len(window), "observations_up": len(up), "observations_down": len(down)}
    # Si el historico comun no llega a cubrir la ventana, no se comparan periodos distintos.
    if len(window) < MIN_OBSERVATIONS or returns.index[0] > cutoff:
        return {"correlation": None, "beta_up": None, "beta_down": None, **counts}
    correlation = window["asset"].corr(window["peer"])
    return {
        "correlation": None if pd.isna(correlation) else round(float(correlation), 4),
        "beta_up": _beta(up),
        "beta_down": _beta(down),
        **counts,
    }


def pair_stats(asset_close, peer_close):
    """{ventana: {correlation, beta_up, beta_down, observations...}} entre dos series de cierres."""
    returns = _common_log_returns(asset_close, peer_close)
    return {label: _window_stats(returns, offset) for label, offset in WINDOWS.items()}


def cumulative_return_curves(closes, selected):
    """Rentabilidad acumulada (%) del ultimo ano de cada serie, con base 0 en el mismo
    punto de partida. `closes` es {simbolo: serie de cierres}; `selected` es el simbolo
    resaltado. Una serie sin historico suficiente en el periodo se omite."""
    end = max(series.index[-1] for series in closes.values())
    cutoff = end - pd.DateOffset(years=CURVE_YEARS)
    curves = []
    for symbol, series in closes.items():
        window = series[series.index > cutoff]
        if len(window) < 2:
            continue
        before = series[series.index <= cutoff]
        base = before.iloc[-1] if not before.empty else window.iloc[0]
        values = (window / base - 1) * 100
        curves.append({
            "symbol": symbol,
            "selected": symbol == selected,
            "dates": [d.strftime("%Y-%m-%d") for d in window.index],
            "values": [round(float(v), 2) for v in values],
        })
    # El activo seleccionado primero (el grafico lo dibuja el ultimo, por encima del resto).
    return sorted(curves, key=lambda c: not c["selected"])


def compute(selected, closes, peers):
    """selected: simbolo del activo. closes: {simbolo: serie de cierres} (incluye el seleccionado).
    peers: lista [(simbolo, grupo)] de referencia; el propio activo seleccionado se omite de la tabla."""
    asset_close = closes[selected]
    rows = [
        {"symbol": symbol, "group": group, "windows": pair_stats(asset_close, closes[symbol])}
        for symbol, group in peers
        if symbol != selected and symbol in closes
    ]
    return {
        "windows": list(WINDOWS),
        "peers": rows,
        "curves": cumulative_return_curves(closes, selected),
    }
