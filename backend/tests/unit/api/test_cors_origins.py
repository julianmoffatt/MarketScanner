import pytest

from backend.src.market_platform.api.main import DEFAULT_CORS_ORIGINS, cors_origins


def test_default_origin_is_the_vite_dev_server(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert cors_origins() == [DEFAULT_CORS_ORIGINS]


def test_origins_are_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:8080")

    assert cors_origins() == ["http://localhost:8080"]


@pytest.mark.parametrize("raw", [
    "http://a.com,http://b.com",
    " http://a.com , http://b.com ",
    "http://a.com,,http://b.com,",
])
def test_multiple_origins_are_split_and_trimmed(monkeypatch, raw):
    monkeypatch.setenv("CORS_ORIGINS", raw)

    assert cors_origins() == ["http://a.com", "http://b.com"]
