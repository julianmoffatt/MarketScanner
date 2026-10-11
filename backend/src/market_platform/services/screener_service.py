# services/screener_service.py
from ..analysis.screeners import mean_reversion
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
