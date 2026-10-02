import numpy as np
import pandas as pd
import pytest
from backend.src.market_platform.data.data_validation import (
    check_basic_sanity,
    clean_ohlcv,
    detect_illiquid_onset,
    detect_price_spikes,
    validation_report_to_df,
)

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


def with_spike(df, position, factor, revert=1.0):
    out = df.copy()
    col = out.columns.get_loc("Close")
    base = out.iloc[position - 1, col]
    out.iloc[position, col] = base * factor
    out.iloc[position + 1, col] = base * revert
    return out


def test_clean_data_has_no_spikes(ohlcv):
    assert detect_price_spikes(ohlcv).empty


@pytest.mark.parametrize("factor", [1.8, 0.4])
def test_reverting_jump_is_detected_only_on_spike_day(ohlcv, factor):
    df = with_spike(ohlcv, 10, factor)

    result = detect_price_spikes(df)

    assert list(result.index) == [df.index[10]]
    assert result["return"].iloc[0] == pytest.approx(factor - 1)


def test_jump_that_does_not_revert_is_not_detected(ohlcv):
    df = ohlcv.copy()
    df.iloc[10:, df.columns.get_loc("Close")] *= 1.8

    assert detect_price_spikes(df).empty


@pytest.mark.parametrize("factor, expected", [(1.29, False), (1.31, True), (0.71, False), (0.69, True)])
def test_jump_threshold_boundary(ohlcv, factor, expected):
    result = detect_price_spikes(with_spike(ohlcv, 10, factor))

    assert (len(result) == 1) == expected


@pytest.mark.parametrize("revert, expected", [(1.04, True), (1.06, False), (0.96, True), (0.94, False)])
def test_revert_tolerance_boundary(ohlcv, revert, expected):
    result = detect_price_spikes(with_spike(ohlcv, 10, 1.8, revert=revert))

    assert (len(result) == 1) == expected


def test_custom_thresholds_change_detection(ohlcv):
    df = with_spike(ohlcv, 10, 1.15)

    assert detect_price_spikes(df).empty
    assert len(detect_price_spikes(df, jump_threshold=0.10)) == 1


def test_multiple_spikes_are_all_detected(ohlcv):
    df = with_spike(with_spike(ohlcv, 10, 1.8), 50, 0.4)

    result = detect_price_spikes(df)

    assert list(result.index) == [df.index[10], df.index[50]]


def test_spike_on_last_row_is_not_detected(ohlcv):
    df = ohlcv.copy()
    col = df.columns.get_loc("Close")
    df.iloc[-1, col] = df.iloc[-2, col] * 1.8

    assert detect_price_spikes(df).empty


def test_jump_on_first_row_is_not_detected(ohlcv):
    df = ohlcv.copy()
    df.iloc[0, df.columns.get_loc("Close")] *= 1.8

    assert df.index[0] not in detect_price_spikes(df).index


def test_spikes_output_columns(ohlcv):
    result = detect_price_spikes(with_spike(ohlcv, 10, 1.8))

    assert list(result.columns) == ["return", "spike_candidate"]
    assert result["spike_candidate"].all()


def test_spikes_on_empty_dataframe_returns_empty(ohlcv):
    assert detect_price_spikes(ohlcv.iloc[0:0]).empty


def returns_series(*segments, seed=42):
    rng = np.random.default_rng(seed)
    return np.concatenate([rng.normal(0, sigma, n) for n, sigma in segments])


def price_frame(returns, freq="B", start="2022-01-03"):
    close = 100 * np.exp(np.cumsum(returns))
    return pd.DataFrame({"Close": close}, index=pd.date_range(start, periods=len(returns), freq=freq))


def test_homogeneous_series_has_no_onset():
    result = detect_illiquid_onset(price_frame(returns_series((2000, 0.01))))

    assert result["onset_date"] is None
    assert result["vol_ratio"] < 3


@pytest.mark.parametrize("factor", [10, 20, 50])
def test_illiquid_start_is_cut_at_regime_change(factor):
    df = price_frame(returns_series((300, 0.01 / factor), (1700, 0.01)))

    result = detect_illiquid_onset(df)

    assert abs(df.index.get_loc(result["onset_date"]) - 300) <= 2
    assert result["vol_ratio"] == pytest.approx(factor, rel=0.3)


def test_moderately_lower_start_is_not_cut():
    result = detect_illiquid_onset(price_frame(returns_series((300, 0.0067), (1700, 0.01))))

    assert result["onset_date"] is None


def test_higher_volatility_at_start_is_not_cut():
    result = detect_illiquid_onset(price_frame(returns_series((300, 0.03), (1700, 0.01))))

    assert result["onset_date"] is None
    assert result["vol_ratio"] < 1


def test_low_volatility_regime_in_the_middle_is_not_cut():
    df = price_frame(returns_series((700, 0.01), (300, 0.0005), (1000, 0.01)))

    assert detect_illiquid_onset(df)["onset_date"] is None


def test_ratio_min_controls_detection():
    df = price_frame(returns_series((300, 0.0025), (1700, 0.01)))

    assert detect_illiquid_onset(df, ratio_min=3)["onset_date"] is not None
    assert detect_illiquid_onset(df, ratio_min=10)["onset_date"] is None


def test_max_fraction_limits_the_cut():
    df = price_frame(returns_series((300, 0.0005), (700, 0.01)))

    limited = detect_illiquid_onset(df, max_fraction=0.2)
    free = detect_illiquid_onset(df, max_fraction=0.5)

    assert df.index.get_loc(limited["onset_date"]) <= 0.2 * len(df)
    assert abs(df.index.get_loc(free["onset_date"]) - 300) <= 2


def test_min_period_controls_shortest_detectable_segment():
    df = price_frame(returns_series((30, 0.0005), (1970, 0.01)))

    assert detect_illiquid_onset(df, min_period="60D")["onset_date"] is None
    assert abs(df.index.get_loc(detect_illiquid_onset(df, min_period="20D")["onset_date"]) - 30) <= 3


def test_frozen_price_start_is_cut():
    df = price_frame(returns_series((300, 0.0), (1700, 0.01)))

    result = detect_illiquid_onset(df)

    assert abs(df.index.get_loc(result["onset_date"]) - 300) <= 2


def test_tz_aware_index_is_supported():
    df = price_frame(returns_series((300, 0.0005), (1700, 0.01)))
    df.index = df.index.tz_localize("UTC")

    result = detect_illiquid_onset(df)

    assert abs(df.index.get_loc(result["onset_date"]) - 300) <= 2


def test_hourly_data_uses_time_based_min_period():
    df = price_frame(returns_series((1500, 0.0005), (6000, 0.01)), freq="h")

    result = detect_illiquid_onset(df, min_period="10D")

    assert abs(df.index.get_loc(result["onset_date"]) - 1500) <= 5


def test_short_series_returns_no_onset():
    result = detect_illiquid_onset(price_frame(returns_series((50, 0.01))))

    assert result == {"onset_date": None, "vol_ratio": None}


def test_empty_dataframe_returns_no_onset():
    result = detect_illiquid_onset(price_frame(returns_series((10, 0.01))).iloc[0:0])

    assert result == {"onset_date": None, "vol_ratio": None}


def test_onset_output_keys():
    result = detect_illiquid_onset(price_frame(returns_series((300, 0.0005), (1700, 0.01))))

    assert set(result) == {"onset_date", "vol_ratio"}


def invalid_columns(flags, ts):
    return {c for c in flags.columns if c.startswith("invalid_") and flags.loc[ts, c]}


@pytest.mark.parametrize(
    "column, reference, sign, expected",
    [
        ("Open", "High", +1, {"invalid_open"}),
        ("Open", "Low", -1, {"invalid_open"}),
        ("Close", "High", +1, {"invalid_close"}),
        ("Close", "Low", -1, {"invalid_close"}),
        ("High", "Low", -1, {"invalid_open", "invalid_high", "invalid_low", "invalid_close"}),
    ],
)
def test_invalid_column_attribution_for_range_violations(ohlcv, column, reference, sign, expected):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = df.loc[bad_ts, reference] + sign

    flags = check_basic_sanity(df)

    assert invalid_columns(flags, bad_ts) == expected


@pytest.mark.parametrize(
    "column, expected",
    [
        ("Open", {"invalid_open"}),
        ("Low", {"invalid_low"}),
        ("Close", {"invalid_close"}),
        ("High", {"invalid_open", "invalid_high", "invalid_low", "invalid_close"}),
    ],
)
def test_invalid_column_attribution_for_zero_price(ohlcv, column, expected):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = 0

    flags = check_basic_sanity(df)

    assert invalid_columns(flags, bad_ts) == expected


def test_invalid_column_attribution_for_negative_volume(ohlcv):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, "Volume"] = -5

    flags = check_basic_sanity(df)

    assert invalid_columns(flags, bad_ts) == {"invalid_volume"}


def flat_ohlcv(close):
    return pd.DataFrame(
        {"Open": close, "High": close, "Low": close, "Close": close, "Volume": 1000.0},
        index=pd.bdate_range("2020-01-01", periods=len(close)),
    )


def actions(df):
    return [row["action"] for row in df.attrs["validation_report"]]


def test_clean_ohlcv_leaves_clean_data_unchanged(ohlcv):
    result = clean_ohlcv(ohlcv)

    pd.testing.assert_frame_equal(result, ohlcv, check_freq=False)
    assert result.attrs["validation_report"] == []


def test_clean_ohlcv_does_not_modify_input(ohlcv):
    df = with_spike(ohlcv, 10, 1.8)
    before = df.copy()

    clean_ohlcv(df)

    pd.testing.assert_frame_equal(df, before)


def test_clean_ohlcv_sorts_and_removes_duplicate_dates(ohlcv):
    messy = pd.concat([ohlcv, ohlcv.iloc[[5]]]).sample(frac=1, random_state=0)

    result = clean_ohlcv(messy)

    pd.testing.assert_frame_equal(result, ohlcv, check_freq=False)


def test_clean_ohlcv_converts_string_index_to_datetime(ohlcv):
    df = ohlcv.copy()
    df.index = df.index.strftime("%Y-%m-%d")

    result = clean_ohlcv(df)

    assert isinstance(result.index, pd.DatetimeIndex)
    assert len(result) == len(ohlcv)


def test_clean_ohlcv_supports_tz_aware_index(ohlcv):
    df = ohlcv.copy()
    df.index = df.index.tz_localize("UTC")

    assert len(clean_ohlcv(df)) == len(ohlcv)


@pytest.mark.parametrize(
    "column, reference, sign",
    [("Open", "High", +1), ("Close", "Low", -1)],
)
def test_clean_ohlcv_interpolates_out_of_range_price_instead_of_dropping(ohlcv, column, reference, sign):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, column] = df.loc[bad_ts, reference] + sign

    result = clean_ohlcv(df)

    expected = (ohlcv[column].iloc[9] + ohlcv[column].iloc[11]) / 2
    assert len(result) == len(ohlcv)
    assert result.loc[bad_ts, column] == pytest.approx(expected)
    assert f"invalid_{column.lower()}_interpolated" in actions(result)


def test_clean_ohlcv_interpolates_negative_volume(ohlcv):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, "Volume"] = -5

    result = clean_ohlcv(df)

    assert result.loc[bad_ts, "Volume"] == pytest.approx((ohlcv["Volume"].iloc[9] + ohlcv["Volume"].iloc[11]) / 2)
    assert actions(result) == ["invalid_volume_interpolated"]


def test_clean_ohlcv_high_below_low_interpolates_every_price_column(ohlcv):
    df = ohlcv.copy()
    bad_ts = df.index[10]
    df.loc[bad_ts, "High"] = df.loc[bad_ts, "Low"] - 1

    result = clean_ohlcv(df)

    assert len(result) == len(ohlcv)
    assert sorted(actions(result)) == [
        "invalid_close_interpolated",
        "invalid_high_interpolated",
        "invalid_low_interpolated",
        "invalid_open_interpolated",
    ]


def test_clean_ohlcv_interpolates_spike_instead_of_dropping():
    close = 100 * np.exp(np.cumsum(returns_series((300, 0.01))))
    base = close[9]
    close[10], close[11] = base * 1.8, base
    df = flat_ohlcv(close)

    result = clean_ohlcv(df)

    assert len(result) == len(df)
    assert result["Close"].iloc[10] == pytest.approx(base)
    assert actions(result) == ["spike_interpolated"]
    assert result.attrs["validation_report"][0]["return"] == pytest.approx(0.8, abs=1e-3)


def test_clean_ohlcv_drops_row_that_cannot_be_interpolated(ohlcv):
    df = ohlcv.copy()
    df.iloc[10:13, df.columns.get_loc("Close")] = float("nan")

    result = clean_ohlcv(df)

    assert len(result) == len(ohlcv) - 1
    assert actions(result) == ["unfixable_row_drop"]


def test_clean_ohlcv_drops_invalid_first_row(ohlcv):
    df = ohlcv.copy()
    df.iloc[0, df.columns.get_loc("Close")] = float("nan")

    result = clean_ohlcv(df)

    assert result.index[0] == ohlcv.index[1]
    assert actions(result) == ["unfixable_row_drop"]


def test_clean_ohlcv_trims_illiquid_start_and_reports_it():
    df = flat_ohlcv(100 * np.exp(np.cumsum(returns_series((250, 0.0004), (1250, 0.012)))))

    result = clean_ohlcv(df)

    assert abs(df.index.get_loc(result.index[0]) - 250) <= 2
    assert actions(result).count("illiquid_period_dropped") == df.index.get_loc(result.index[0])


def test_clean_ohlcv_keeps_illiquid_start_when_disabled():
    df = flat_ohlcv(100 * np.exp(np.cumsum(returns_series((250, 0.0004), (1250, 0.012)))))

    assert len(clean_ohlcv(df, drop_illiquid_onset=False)) == len(df)


def test_clean_ohlcv_verbose_prints_summary(ohlcv, capsys):
    clean_ohlcv(with_spike(ohlcv, 10, 1.8), verbose=True)

    assert "acciones aplicadas" in capsys.readouterr().out


def test_validation_report_to_df_empty_report():
    result = validation_report_to_df([])

    assert result.empty
    assert list(result.columns) == ["action"]


def test_validation_report_to_df_is_indexed_and_sorted_by_date():
    rows = [
        {"date": pd.Timestamp("2022-01-05"), "action": "b"},
        {"date": pd.Timestamp("2022-01-03"), "action": "a"},
    ]

    result = validation_report_to_df(rows)

    assert list(result["action"]) == ["a", "b"]
    assert result.index.name == "date"
