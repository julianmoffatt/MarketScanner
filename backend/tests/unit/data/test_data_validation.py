import pytest
from backend.src.market_platform.data.data_validation import check_basic_sanity

@pytest.mark.parametrize("column", ["Open", "High", "Low", "Close", "Volume"])
def test_nan_is_flagged(ohlcv, column):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = float("nan")

    flags = check_basic_sanity(df)
    assert flags.loc[bad_ts, "has_nan"]  


@pytest.mark.parametrize("column", ["Open", "High", "Low", "Close"])
@pytest.mark.parametrize("bad_value", [0, -1])
def test_non_positive_price_is_flagged(ohlcv, column, bad_value):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = bad_value

    flags = check_basic_sanity(df)
    assert flags.loc[bad_ts, "neg_or_zero_price"]   


def test_negative_volume_is_flagged(ohlcv):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, "Volume"] = -5

    flags = check_basic_sanity(df)

    assert flags.loc[bad_ts, "neg_volume"]
    assert flags["neg_volume"].sum() == 1


@pytest.mark.parametrize("gap", [0.01, 1, 50])
@pytest.mark.parametrize(
    "column, reference, sign, flag",
    [
        ("High", "Low", -1, "high_lt_low"),
        ("Open", "Low", -1, "open_outside_range"),
        ("Open", "High", +1, "open_outside_range"),
        ("Close", "Low", -1, "close_outside_range"),
        ("Close", "High", +1, "close_outside_range"),
    ],
)
def test_price_outside_valid_range_is_flagged(ohlcv, column, reference, sign, flag, gap):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = df.loc[bad_ts, reference] + sign * gap

    flags = check_basic_sanity(df)

    assert flags.loc[bad_ts, flag]
    assert flags[flag].sum() == 1


@pytest.mark.parametrize(
    "column, bad_value",
    [("Volume", -5), ("Open", 0), ("Close", float("nan"))],
)
def test_any_violation_is_true_when_any_flag_is_set(ohlcv, column, bad_value):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = bad_value

    flags = check_basic_sanity(df)
    assert flags.loc[bad_ts, "any_violation"]
    assert flags["any_violation"].sum() == 1


def test_clean_data_has_no_violations(ohlcv):
    flags = check_basic_sanity(ohlcv)
    assert not flags.any().any()


def test_zero_volume_is_not_flagged(ohlcv):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, "Volume"] = 0

    flags = check_basic_sanity(df)

    assert not flags["neg_volume"].any()


@pytest.mark.parametrize("column", ["Open", "High", "Low", "Close"])
def test_small_positive_price_is_not_flagged(ohlcv, column):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = 0.01

    flags = check_basic_sanity(df)

    assert not flags["neg_or_zero_price"].any()


def test_high_equal_to_low_is_not_flagged(ohlcv):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, "High"] = df.loc[bad_ts, "Low"]

    flags = check_basic_sanity(df)

    assert not flags["high_lt_low"].any()


@pytest.mark.parametrize("reference", ["Low", "High"])
@pytest.mark.parametrize("column, flag", [("Open", "open_outside_range"), ("Close", "close_outside_range")])
def test_price_equal_to_range_edge_is_not_flagged(ohlcv, column, flag, reference):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = df.loc[bad_ts, reference]

    flags = check_basic_sanity(df)

    assert not flags[flag].any()
