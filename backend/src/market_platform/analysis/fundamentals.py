"""
Fundamentales de una accion a partir del diccionario `info` de Yahoo Finance.
Funcion pura (sin red): recibe el dict y devuelve cinco grupos de metricas.
Cualquier campo que falte, no sea numerico o no sea finito sale como None.
"""
import math

SECTIONS = ("valuation", "profitability", "growth", "balance_dividend", "analysts")


def _num(info, key, scale=1.0, decimals=2):
    value = info.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return round(value * scale, decimals)


def _dividend_yield(info):
    """Dividendo anual por accion / precio, en %. Se calcula en vez de leer
    'dividendYield', cuya escala (fraccion o porcentaje) ha cambiado entre versiones de yfinance."""
    rate = _num(info, "dividendRate", decimals=6)
    price = _num(info, "currentPrice", decimals=6) or _num(info, "regularMarketPrice", decimals=6)
    if rate is None or not price:
        return None
    return round(rate / price * 100, 2)


def _recommendation(info):
    value = info.get("recommendationKey")
    return value if isinstance(value, str) and value and value != "none" else None


def compute(info):
    """Devuelve {"available": bool, <seccion>: {metrica: valor}}.
    Solo las acciones (quoteType EQUITY) tienen fundamentales: indices, divisas,
    cripto, materias primas y ETFs devuelven available=False y secciones vacias."""
    if not info or info.get("quoteType") != "EQUITY":
        return {"available": False, **{section: {} for section in SECTIONS}}

    return {
        "available": True,
        "valuation": {
            "trailing_pe": _num(info, "trailingPE"),
            "forward_pe": _num(info, "forwardPE"),
            "peg": _num(info, "trailingPegRatio") if info.get("trailingPegRatio") is not None else _num(info, "pegRatio"),
            "price_to_sales": _num(info, "priceToSalesTrailing12Months"),
            "price_to_book": _num(info, "priceToBook"),
            "ev_to_ebitda": _num(info, "enterpriseToEbitda"),
            "market_cap": _num(info, "marketCap", decimals=0),
        },
        "profitability": {
            "revenue": _num(info, "totalRevenue", decimals=0),  # ultimos 12 meses
            "gross_margin": _num(info, "grossMargins", 100, 1),
            "operating_margin": _num(info, "operatingMargins", 100, 1),
            "net_margin": _num(info, "profitMargins", 100, 1),
            "roe": _num(info, "returnOnEquity", 100, 1),
            "roa": _num(info, "returnOnAssets", 100, 1),
        },
        "growth": {
            "revenue_growth": _num(info, "revenueGrowth", 100, 1),
            "earnings_growth": _num(info, "earningsGrowth", 100, 1),
        },
        "balance_dividend": {
            # Yahoo da debtToEquity en % (150 = 1.5x); se pasa a ratio.
            "debt_to_equity": _num(info, "debtToEquity", 0.01),
            "current_ratio": _num(info, "currentRatio"),
            "dividend_yield": _dividend_yield(info),
            "payout_ratio": _num(info, "payoutRatio", 100, 1),
        },
        "analysts": {
            "target_price": _num(info, "targetMeanPrice"),
            "recommendation": _recommendation(info),
            "analyst_count": _num(info, "numberOfAnalystOpinions", decimals=0),
        },
    }
