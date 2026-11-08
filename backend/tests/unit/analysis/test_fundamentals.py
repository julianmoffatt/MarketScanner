import math

from backend.src.market_platform.analysis import fundamentals

INFO = {
    "quoteType": "EQUITY",
    "trailingPE": 31.456, "forwardPE": 27.1, "trailingPegRatio": 2.2,
    "priceToSalesTrailing12Months": 8.04, "priceToBook": 45.0, "enterpriseToEbitda": 22.5,
    "marketCap": 3_000_000_000_000,
    "totalRevenue": 400_000_000_000, "grossMargins": 0.462, "operatingMargins": 0.31, "profitMargins": 0.2531,
    "returnOnEquity": 1.5, "returnOnAssets": 0.22,
    "revenueGrowth": 0.061, "earningsGrowth": -0.02,
    "debtToEquity": 150.0, "currentRatio": 0.87,
    "dividendRate": 1.0, "currentPrice": 200.0, "payoutRatio": 0.15,
    "targetMeanPrice": 230.5, "recommendationKey": "buy", "numberOfAnalystOpinions": 40,
}


def test_stock_info_is_converted_to_the_five_sections():
    result = fundamentals.compute(INFO)

    assert result["available"] is True
    assert result["valuation"]["trailing_pe"] == 31.46
    assert result["valuation"]["peg"] == 2.2
    assert result["valuation"]["market_cap"] == 3_000_000_000_000
    assert result["profitability"]["revenue"] == 400_000_000_000
    assert result["profitability"]["gross_margin"] == 46.2  # fraccion -> %
    assert result["profitability"]["roe"] == 150.0
    assert result["growth"]["earnings_growth"] == -2.0
    assert result["balance_dividend"]["debt_to_equity"] == 1.5  # % de Yahoo -> ratio
    assert result["balance_dividend"]["dividend_yield"] == 0.5  # 1 / 200
    assert result["balance_dividend"]["payout_ratio"] == 15.0
    assert result["analysts"] == {"target_price": 230.5, "recommendation": "buy", "analyst_count": 40}


def test_non_equity_is_not_available():
    for info in ({}, None, {"quoteType": "INDEX"}, {"quoteType": "ETF", "trailingPE": 20}):
        result = fundamentals.compute(info)
        assert result["available"] is False
        assert all(result[section] == {} for section in fundamentals.SECTIONS)


def test_missing_or_invalid_values_become_none():
    info = {"quoteType": "EQUITY", "trailingPE": "n/a", "forwardPE": math.nan,
            "priceToBook": math.inf, "marketCap": True, "recommendationKey": "none"}

    result = fundamentals.compute(info)

    assert result["valuation"]["trailing_pe"] is None
    assert result["valuation"]["forward_pe"] is None
    assert result["valuation"]["price_to_book"] is None
    assert result["valuation"]["market_cap"] is None
    assert result["analysts"]["recommendation"] is None
    assert result["balance_dividend"]["dividend_yield"] is None


def test_peg_falls_back_to_legacy_key_and_price_to_regular_market_price():
    info = {"quoteType": "EQUITY", "pegRatio": 1.7, "dividendRate": 2.0, "regularMarketPrice": 100.0}

    result = fundamentals.compute(info)

    assert result["valuation"]["peg"] == 1.7
    assert result["balance_dividend"]["dividend_yield"] == 2.0
