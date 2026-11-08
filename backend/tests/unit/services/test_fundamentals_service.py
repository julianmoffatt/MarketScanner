import pytest

from backend.src.market_platform.services import fundamentals_service


@pytest.fixture(autouse=True)
def empty_cache():
    fundamentals_service.clear_cache()
    yield
    fundamentals_service.clear_cache()


def test_successful_response_is_cached_per_symbol():
    calls = []

    def fetch(symbol):
        calls.append(symbol)
        return {"quoteType": "EQUITY", "trailingPE": 20}

    first = fundamentals_service.get_fundamentals("aapl", fetch=fetch)
    second = fundamentals_service.get_fundamentals("AAPL", fetch=fetch)

    assert first["available"] is True and first is second
    assert calls == ["AAPL"]


def test_failed_download_is_not_cached():
    def failing(symbol):
        raise ConnectionError("sin red")

    assert fundamentals_service.get_fundamentals("AAPL", fetch=failing)["available"] is False

    result = fundamentals_service.get_fundamentals("AAPL", fetch=lambda s: {"quoteType": "EQUITY"})
    assert result["available"] is True


def test_clear_cache_forces_a_new_download():
    calls = []

    def fetch(symbol):
        calls.append(symbol)
        return {"quoteType": "EQUITY"}

    fundamentals_service.get_fundamentals("MSFT", fetch=fetch)
    fundamentals_service.clear_cache()
    fundamentals_service.get_fundamentals("MSFT", fetch=fetch)

    assert calls == ["MSFT", "MSFT"]
