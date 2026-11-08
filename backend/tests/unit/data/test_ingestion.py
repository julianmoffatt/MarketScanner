import datetime as dt

import numpy as np
import pandas as pd
import pytest

from backend.src.market_platform.data import ingestion
from backend.src.market_platform.data.ingestion import complete_last_daily_bar, fetch_last_regular_close

DAYS = pd.to_datetime(["2026-10-27", "2026-10-28", "2026-10-29"])


def daily(last_close, columns=None):
    df = pd.DataFrame(
        {
            "Adj Close": [320.0, 324.0, last_close],
            "Close": [320.0, 324.0, last_close],
            "High": [323.0, 326.0, 288.0],
            "Low": [316.0, 322.0, 280.0],
            "Open": [317.0, 323.0, 286.0],
            "Volume": [1.0, 2.0, 3.0],
        },
        index=DAYS,
    )
    if columns == "yfinance":
        df.columns = pd.MultiIndex.from_product([df.columns, ["GOOGL"]], names=["Price", "Ticker"])
    return df


def never_called(symbol, day):
    raise AssertionError("no deberia pedir el precio intradia")


@pytest.mark.parametrize("columns", [None, "yfinance"])
def test_incomplete_last_bar_is_completed_with_the_regular_session_price(columns):
    df = daily(np.nan, columns)

    result = complete_last_daily_bar(df, "GOOGL", fetch_close=lambda symbol, day: 283.75)

    close, adj_close = result.iloc[-1, 1], result.iloc[-1, 0]
    assert close == 283.75
    assert adj_close == 283.75


def test_only_the_last_bar_changes():
    df = daily(np.nan)

    result = complete_last_daily_bar(df, "GOOGL", fetch_close=lambda symbol, day: 283.75)

    pd.testing.assert_frame_equal(result.iloc[:-1], df.iloc[:-1])
    assert result.iloc[-1][["High", "Low", "Open", "Volume"]].tolist() == [288.0, 280.0, 286.0, 3.0]


def test_the_price_is_requested_for_the_date_of_the_last_bar():
    asked = []

    complete_last_daily_bar(daily(np.nan), "GOOGL", fetch_close=lambda symbol, day: asked.append((symbol, day)))

    assert asked == [("GOOGL", dt.date(2026, 10, 29))]


def test_complete_data_is_returned_untouched_without_any_request():
    df = daily(283.0)

    result = complete_last_daily_bar(df, "GOOGL", fetch_close=never_called)

    pd.testing.assert_frame_equal(result, df)


def test_bar_stays_incomplete_when_no_price_is_available():
    df = daily(np.nan)

    result = complete_last_daily_bar(df, "GOOGL", fetch_close=lambda symbol, day: None)

    assert np.isnan(result["Close"].iloc[-1])


def test_complete_last_daily_bar_does_not_modify_its_input():
    df = daily(np.nan)
    before = df.copy()

    complete_last_daily_bar(df, "GOOGL", fetch_close=lambda symbol, day: 283.75)

    pd.testing.assert_frame_equal(df, before)


def test_empty_dataframe_is_returned_as_is():
    empty = daily(1.0).iloc[0:0]

    assert complete_last_daily_bar(empty, "GOOGL", fetch_close=never_called).empty


class FakeTicker:
    def __init__(self, hourly=None, error=None):
        self.hourly, self.error = hourly, error

    def history(self, **kwargs):
        if self.error:
            raise self.error
        return self.hourly


def hourly_bars(closes_by_timestamp):
    index = pd.DatetimeIndex(list(closes_by_timestamp), tz="America/New_York")
    return pd.DataFrame({"Close": list(closes_by_timestamp.values())}, index=index)


def patch_yahoo(monkeypatch, ticker):
    monkeypatch.setattr(ingestion.yf, "Ticker", lambda name: ticker)


def test_regular_close_is_the_last_hourly_bar_of_that_day(monkeypatch):
    bars = hourly_bars({
        "2026-10-28 15:30": 325.0,
        "2026-10-29 09:30": 286.0,
        "2026-10-29 15:30": 283.75,
    })
    patch_yahoo(monkeypatch, FakeTicker(bars))

    assert fetch_last_regular_close("GOOGL", dt.date(2026, 10, 29)) == 283.75


def test_regular_close_is_none_when_there_are_no_bars_that_day(monkeypatch):
    patch_yahoo(monkeypatch, FakeTicker(hourly_bars({"2026-10-28 15:30": 325.0})))

    assert fetch_last_regular_close("GOOGL", dt.date(2026, 10, 29)) is None


def test_regular_close_is_none_when_the_download_fails(monkeypatch):
    patch_yahoo(monkeypatch, FakeTicker(error=ConnectionError("sin red")))

    assert fetch_last_regular_close("GOOGL", dt.date(2026, 10, 29)) is None


def test_regular_close_asks_yahoo_for_the_translated_symbol(monkeypatch):
    asked = []
    monkeypatch.setattr(ingestion.yf, "Ticker", lambda name: asked.append(name) or FakeTicker(hourly_bars({})))

    fetch_last_regular_close("SP500", dt.date(2026, 10, 29))

    assert asked == ["^GSPC"]
