# services/screener_service.py
from ..analysis.screeners import flips, mean_reversion
from .. import pipeline
from ..utils.config import load_config

def _universe_tickers(universe: str) -> list[str]:
    universes = load_config()["universes"]
    if universe not in universes:
        raise ValueError(f"Universo '{universe}' no existe. Disponibles: {sorted(universes)}")
    return list(dict.fromkeys(universes[universe])) # sin duplicados y conservando el orden

def get_mean_reversion_screener(universe: str) -> list[dict]:
    return [
        mean_reversion.compute(ticker, pipeline.processedTimeframes(ticker, 0)[:3])
        for ticker in _universe_tickers(universe)
    ]


def get_flips_screener(universe: str, lower: str) -> dict:
    """Una fila por valor del universo con la distribucion historica de flips. Un valor sin
    datos o sin historia suficiente no tumba la tabla: se informa en 'missing'."""
    rows, missing = [], []
    for ticker in _universe_tickers(universe):
        try:
            row = flips.compute(ticker, lower, pipeline.processedTimeframes(ticker, 0))
        except Exception as e:
            print(f"Flips: sin datos de {ticker}: {e}")
            row = None
        if row is None:
            missing.append(ticker)
        else:
            rows.append(row)
    buckets = {tf: flips.bucket_labels(n) for tf, n in flips.BUCKETS[lower].items()}
    return {"universe": universe, "lower": lower, "buckets": buckets, "rows": rows, "missing": missing}
