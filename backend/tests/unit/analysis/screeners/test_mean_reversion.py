import math

import pandas as pd
import pytest

from backend.src.market_platform.analysis.screeners.mean_reversion import compute
from backend.src.market_platform.api.schemas import MeanReversionScreener_Row
from backend.src.market_platform.features.stats import create_mean_reversion_statistics

PERCENTILE_SUFFIX = "_percentile"


def test_row_starts_with_the_ticker(screener_timeframes):
    assert compute("AAPL", screener_timeframes)["ticker"] == "AAPL"


def test_row_has_exactly_the_fields_of_the_response_schema(screener_timeframes):
    row = compute("AAPL", screener_timeframes)

    assert set(row) == set(MeanReversionScreener_Row.model_fields)


def test_values_are_plain_python_floats_strings_or_none(screener_timeframes):
    row = compute("AAPL", screener_timeframes)

    assert all(value is None or type(value) in (float, str) for value in row.values())
    assert not any(isinstance(value, float) and math.isnan(value) for value in row.values())


def test_candle_type_is_the_color_of_the_last_candle(screener_timeframes):
    row = compute("AAPL", screener_timeframes)

    assert row["daily_type"] == screener_timeframes[0]["type"].iloc[-1]
    assert row["weekly_type"] == screener_timeframes[1]["type"].iloc[-1]
    assert row["monthly_type"] == screener_timeframes[2]["type"].iloc[-1]


def test_strike_is_a_positive_whole_number(screener_timeframes):
    row = compute("AAPL", screener_timeframes)

    assert row["daily_strike"] >= 1 and row["daily_strike"] == int(row["daily_strike"])


def test_percentiles_are_between_zero_and_one_hundred(screener_timeframes):
    row = compute("AAPL", screener_timeframes)

    percentiles = [v for k, v in row.items() if k.endswith(PERCENTILE_SUFFIX) and v is not None]
    assert percentiles and all(0 <= p <= 100 for p in percentiles)


def test_trend_side_is_plus_or_minus_one(screener_timeframes):
    row = compute("AAPL", screener_timeframes)

    assert row["trend_ema10_side"] in (1.0, -1.0)
    assert row["trend_ema20_side"] in (1.0, -1.0)


def test_percentile_without_enough_history_is_none(screener_timeframes):
    row = compute("AAPL", screener_timeframes)

    assert row["monthly_strike_percentile"] is None


def test_input_frames_are_not_modified(screener_timeframes):
    before = [df.copy() for df in screener_timeframes]

    compute("AAPL", screener_timeframes)

    for original, current in zip(before, screener_timeframes):
        pd.testing.assert_frame_equal(original, current)


def test_same_input_gives_the_same_row(screener_timeframes):
    assert compute("AAPL", screener_timeframes) == compute("AAPL", screener_timeframes)


@pytest.mark.parametrize("missing", ["type", "ema50", "extension_ema10"])
def test_missing_input_column_raises(screener_timeframes, missing):
    broken = [df.drop(columns=missing) for df in screener_timeframes]

    with pytest.raises(KeyError):
        compute("AAPL", broken)


FIELD_SOURCES = {
    "daily_strike": (0, "strike"),
    "weekly_strike": (1, "strike"),
    "monthly_strike": (2, "strike"),
    "daily_strike_percentile": (0, "percentile_strike"),
    "weekly_strike_percentile": (1, "percentile_strike"),
    "monthly_strike_percentile": (2, "percentile_strike"),
    "daily_time_away_ema10": (0, "time_away_ema10"),
    "daily_time_away_ema20": (0, "time_away_ema20"),
    "daily_time_away_ema50": (0, "time_away_ema50"),
    "daily_time_away_ema10_percentile": (0, "percentile_time_away_ema10"),
    "daily_time_away_ema20_percentile": (0, "percentile_time_away_ema20"),
    "daily_time_away_ema50_percentile": (0, "percentile_time_away_ema50"),
    "weekly_time_away_ema10": (1, "time_away_ema10"),
    "weekly_time_away_ema10_percentile": (1, "percentile_time_away_ema10"),
    "daily_extension_ema10_percentile": (0, "percentile_extension_ema10"),
    "daily_extension_ema20_percentile": (0, "percentile_extension_ema20"),
    "weekly_extension_ema10_percentile": (1, "percentile_extension_ema10"),
    "weekly_extension_ema20_percentile": (1, "percentile_extension_ema20"),
    "trend_ema10_side": (0, "trend_side_ema10"),
    "trend_ema10_duration": (0, "duration_trend_ema10"),
    "trend_ema10_percentile": (0, "percentile_duration_trend_ema10"),
    "trend_ema20_side": (0, "trend_side_ema20"),
    "trend_ema20_duration": (0, "duration_trend_ema20"),
    "trend_ema20_percentile": (0, "percentile_duration_trend_ema20"),
}


@pytest.mark.parametrize("field", FIELD_SOURCES)
def test_each_field_reads_the_last_value_of_its_timeframe_and_column(screener_timeframes, field):
    prepared = [create_mean_reversion_statistics(df.copy()) for df in screener_timeframes]
    index, column = FIELD_SOURCES[field]
    expected = prepared[index][column].iloc[-1]

    value = compute("AAPL", screener_timeframes)[field]

    if pd.isna(expected):
        assert value is None
    else:
        assert value == pytest.approx(float(expected))


def test_every_numeric_field_is_covered_by_the_source_table(screener_timeframes):
    row = compute("AAPL", screener_timeframes)
    types = {"daily_type", "weekly_type", "monthly_type"}

    assert set(row) - {"ticker"} - types == set(FIELD_SOURCES)
