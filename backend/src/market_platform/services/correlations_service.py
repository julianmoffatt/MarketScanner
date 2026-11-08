import pandas as pd
from .. import pipeline
from ..analysis import correlations

# Activos con los que se compara: indices, materias primas y bitcoin.
PEERS = [
    ("SP500", "Index"),
    ("NASDAQ", "Index"),
    ("GOLD", "Commodity"),
    ("SILVER", "Commodity"),
    ("OIL", "Commodity"),
    ("BTC", "Crypto"),
]


def peer_list() -> list[tuple[str, str]]:
    return list(PEERS)


def _daily_close(symbol: str) -> pd.Series:
    close = pipeline.processedTimeframes(symbol, 0)[0]["Close"].dropna()
    index = close.index.tz_localize(None) if close.index.tz is not None else close.index
    close = close.set_axis(index.normalize())
    return close[~close.index.duplicated(keep="last")]


def get_correlations(ticker: str) -> dict:
    selected = ticker.upper()
    peers = peer_list()
    closes = {selected: _daily_close(selected)}  # si el activo seleccionado falla, el error sube
    missing = []
    for symbol, _ in peers:
        if symbol in closes:
            continue
        try:
            closes[symbol] = _daily_close(symbol)
        except Exception as e:  # un activo de referencia sin datos no debe tumbar la pantalla
            print(f"Correlaciones: sin datos de {symbol}: {e}")
            missing.append(symbol)
    result = correlations.compute(selected, closes, peers)
    return {**result, "missing": missing}
