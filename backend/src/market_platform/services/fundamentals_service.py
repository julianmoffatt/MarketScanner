import yfinance as yf
from ..analysis import fundamentals
from ..data.ingestion import name_sustitution

# Los fundamentales cambian poco: se guardan por simbolo para no pedir a Yahoo en cada
# visita. Solo se guardan las respuestas correctas; un fallo de red se reintenta la
# proxima vez en lugar de quedarse guardado como "no disponible".
_cache: dict[str, dict] = {}


def fetch_info(symbol: str) -> dict:
    return yf.Ticker(name_sustitution(symbol)).info


def get_fundamentals(ticker: str, fetch=None) -> dict:
    fetch = fetch or fetch_info  # se resuelve al llamar, para poder sustituirla en los tests
    symbol = ticker.upper()
    if symbol in _cache:
        return _cache[symbol]
    try:
        info = fetch(symbol)
    except Exception as e:
        print(f"No se pudieron obtener los fundamentales de {symbol}: {e}")
        return fundamentals.compute({})
    result = fundamentals.compute(info)
    _cache[symbol] = result
    return result


def clear_cache():
    _cache.clear()
