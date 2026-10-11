import numpy as np
import pandas as pd
import pytest

from backend.src.market_platform.analysis.strikes_trend import _ema_trend_streaks
from backend.src.market_platform.features.stats import (
    create_candle_strikes_and_percentile_score,
    create_duration_trend_and_percentile_score,
    create_percentile_scores,
    create_time_away_mean_and_percentile_score,
)


def frame(values):
    return pd.DataFrame({"x": values}, index=pd.bdate_range("2022-01-03", periods=len(values)))


def test_expanding_percentile_matches_a_hand_computed_example():
    out = create_percentile_scores(frame([10, 30, 20, 40, 25]), ["x"], min_periods=1)

    assert out["percentile_x"].tolist() == pytest.approx([100, 100, 200 / 3, 100, 60])


def test_values_before_min_periods_are_nan():
    out = create_percentile_scores(frame(range(10)), ["x"], min_periods=5)

    assert out["percentile_x"].iloc[:4].isna().all()
    assert out["percentile_x"].iloc[4:].notna().all()


def test_default_min_periods_is_252():
    out = create_percentile_scores(frame(range(300)), ["x"])

    assert out["percentile_x"].first_valid_index() == out.index[251]


def test_scores_are_floats_in_the_open_zero_closed_hundred_interval():
    values = np.random.default_rng(0).normal(size=400)

    scores = create_percentile_scores(frame(values), ["x"], min_periods=1)["percentile_x"]

    assert scores.dtype == float
    assert ((scores > 0) & (scores <= 100)).all()


def test_a_new_maximum_scores_one_hundred():
    scores = create_percentile_scores(frame([5, 3, 9, 1, 12]), ["x"], min_periods=1)["percentile_x"]

    assert scores.iloc[2] == 100
    assert scores.iloc[4] == 100


def test_ties_are_ranked_with_the_max_method():
    scores = create_percentile_scores(frame([5, 5, 5]), ["x"], min_periods=1)["percentile_x"]

    assert scores.tolist() == [100, 100, 100]


def test_scores_do_not_use_future_data():
    values = np.random.default_rng(1).normal(size=400)
    full = create_percentile_scores(frame(values), ["x"], min_periods=1)["percentile_x"]
    truncated = create_percentile_scores(frame(values[:300]), ["x"], min_periods=1)["percentile_x"]

    pd.testing.assert_series_equal(full.iloc[:300], truncated)


def test_each_requested_column_gets_its_own_score():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [3, 2, 1]})

    out = create_percentile_scores(df, ["a", "b"], min_periods=1)

    assert out["percentile_a"].tolist() == [100, 100, 100]
    assert out["percentile_b"].iloc[-1] == pytest.approx(100 / 3)


def test_ignore_zeros_ranks_only_among_the_non_zero_values():
    out = create_percentile_scores(frame([0, 3, 0, 5, 4, 0, 2]), ["x"], min_periods=1, ignore_zeros=True)

    assert out["percentile_x"].tolist() == pytest.approx([0, 100, 0, 100, 200 / 3, 0, 25])


def test_ignore_zeros_gives_zero_to_zeros_even_before_min_periods():
    out = create_percentile_scores(frame([0, 3, 0, 5, 4, 0, 2]), ["x"], min_periods=3, ignore_zeros=True)

    assert out["percentile_x"].iloc[[0, 2, 5]].tolist() == [0, 0, 0]
    assert out["percentile_x"].iloc[[1, 3]].isna().all()


def test_ignore_zeros_min_periods_counts_only_non_zero_values():
    out = create_percentile_scores(frame([0, 0, 0, 1, 2, 3]), ["x"], min_periods=3, ignore_zeros=True)

    assert out["percentile_x"].iloc[3:5].isna().all()
    assert out["percentile_x"].iloc[5] == 100


def test_ignore_zeros_does_not_use_future_data():
    values = np.random.default_rng(2).integers(0, 6, size=300)
    full = create_percentile_scores(frame(values), ["x"], min_periods=1, ignore_zeros=True)["percentile_x"]
    truncated = create_percentile_scores(frame(values[:200]), ["x"], min_periods=1, ignore_zeros=True)["percentile_x"]

    pd.testing.assert_series_equal(full.iloc[:200], truncated)


def test_zeros_are_included_by_default():
    out = create_percentile_scores(frame([0, 3, 0]), ["x"], min_periods=1)

    assert out["percentile_x"].tolist() == pytest.approx([100, 100, 200 / 3])


def candles(types):
    return pd.DataFrame({"type": types}, index=pd.bdate_range("2022-01-03", periods=len(types)))


def test_strike_counts_consecutive_candles_of_the_same_color():
    df = candles(["Green", "Green", "Green", "Red", "Red", "Green", "Red"])

    create_candle_strikes_and_percentile_score(df)

    assert df["strike"].tolist() == [1, 2, 3, 1, 2, 1, 1]


def test_strike_restarts_after_a_color_change_even_if_the_color_returns():
    df = candles(["Green", "Red", "Green", "Green"])

    create_candle_strikes_and_percentile_score(df)

    assert df["strike"].tolist() == [1, 1, 1, 2]


def test_strike_percentile_only_compares_candles_of_the_same_color():
    df = candles(["Green", "Green", "Green", "Red", "Red", "Green", "Red"])

    create_candle_strikes_and_percentile_score(df, min_periods=1)

    assert df["percentile_strike"].tolist() == pytest.approx([100, 100, 100, 100, 100, 50, 200 / 3])


def test_strike_percentile_is_nan_until_the_color_has_min_periods_candles():
    df = candles(["Green", "Red", "Green", "Red", "Green"])

    create_candle_strikes_and_percentile_score(df, min_periods=2)

    assert df["percentile_strike"].isna().tolist() == [True, True, False, False, False]


def test_strike_percentile_does_not_use_future_data():
    types = ["Green", "Red", "Red", "Green", "Green", "Green", "Red", "Green"] * 20
    full, truncated = candles(types), candles(types[:100])

    create_candle_strikes_and_percentile_score(full, min_periods=1)
    create_candle_strikes_and_percentile_score(truncated, min_periods=1)

    pd.testing.assert_series_equal(full["percentile_strike"].iloc[:100], truncated["percentile_strike"])


WARMUP = 30


def away_frame(pattern):
    pattern = "N" * WARMUP + pattern
    low = {"N": 99.0, "U": 101.0, "D": 98.0}
    high = {"N": 101.0, "U": 102.0, "D": 99.0}
    n = len(pattern)
    return pd.DataFrame(
        {
            "Close": [100.0] * n,
            "Low": [low[p] for p in pattern],
            "High": [high[p] for p in pattern],
            "ema10": [100.0] * n,
            "ema20": [100.0] * n,
            "ema50": [100.0] * n,
        },
        index=pd.bdate_range("2022-01-03", periods=n),
    )


def after_warmup(df, column):
    return df[column].iloc[WARMUP:]


def test_time_away_counts_consecutive_candles_outside_the_band_and_is_zero_inside():
    df = away_frame("NNUUNDD")

    create_time_away_mean_and_percentile_score(df, min_periods=1)

    assert after_warmup(df, "time_away_ema10").tolist() == [0, 0, 1, 2, 0, 1, 2]


def test_time_away_is_zero_during_the_warmup():
    df = away_frame("UU")

    create_time_away_mean_and_percentile_score(df, min_periods=1)

    assert (df["time_away_ema10"].iloc[:WARMUP] == 0).all()


def test_time_away_is_computed_for_each_ema_column():
    df = away_frame("NUU")
    df.loc[df.index[-1], "ema20"] = 101.5

    create_time_away_mean_and_percentile_score(df, min_periods=1)

    assert after_warmup(df, "time_away_ema10").tolist() == [0, 1, 2]
    assert after_warmup(df, "time_away_ema20").tolist() == [0, 1, 0]


def test_candle_touching_the_band_is_not_away():
    df = away_frame("N")
    df["Low"] = 100.0

    create_time_away_mean_and_percentile_score(df, min_periods=1)

    assert after_warmup(df, "time_away_ema10").tolist() == [0]


def test_time_away_percentile_is_zero_inside_the_band_and_ranks_only_away_candles():
    df = away_frame("NNUUNU")

    create_time_away_mean_and_percentile_score(df, min_periods=1)

    assert after_warmup(df, "percentile_time_away_ema10").tolist() == pytest.approx([0, 0, 100, 100, 0, 200 / 3])


def test_time_away_percentile_is_nan_while_away_history_is_short():
    df = away_frame("UUNUU")

    create_time_away_mean_and_percentile_score(df, min_periods=3)

    percentile = after_warmup(df, "percentile_time_away_ema10")
    assert percentile.isna().tolist() == [True, True, False, False, False]
    assert percentile.iloc[2] == 0


def test_time_away_returns_the_same_frame_it_modifies():
    df = away_frame("NUU")

    result = create_time_away_mean_and_percentile_score(df, min_periods=1)

    assert result is df
    assert after_warmup(df, "time_away_ema10").tolist() == [0, 1, 2]


def trend_frame(pattern):
    ema = {"A": 90.0, "B": 110.0, "S": 100.0}
    n = len(pattern)
    values = [ema[p] for p in pattern]
    return pd.DataFrame(
        {"Close": [100.0] * n, "ema10": values, "ema20": values, "ema50": values},
        index=pd.bdate_range("2022-01-03", periods=n),
    )


def random_walk_frame(seed, n=700):
    rng = np.random.default_rng(seed)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, n))), index=pd.bdate_range("2019-01-01", periods=n))
    df = pd.DataFrame({"Close": close})
    for period in (10, 20, 50):
        df[f"ema{period}"] = close.ewm(span=period, adjust=False).mean()
    return df


def test_trend_duration_counts_days_on_each_side_of_the_ema():
    df = trend_frame("A" * 40 + "BBSBAAB")

    create_duration_trend_and_percentile_score(df, min_periods=1)

    assert df["duration_trend_ema10"].iloc[-7:].tolist() == [1, 2, 3, 4, 1, 2, 1]
    assert df["trend_side_ema10"].iloc[-7:].tolist() == [-1, -1, -1, -1, 1, 1, -1]


def test_trend_continues_while_the_close_stays_between_the_bands():
    df = trend_frame("A" * 40 + "SSSS")

    create_duration_trend_and_percentile_score(df, min_periods=1)

    assert (df["trend_side_ema10"].iloc[-4:] == 1).all()
    assert df["duration_trend_ema10"].iloc[-1] == df["duration_trend_ema10"].iloc[-5] + 4


def test_trend_duration_is_nan_during_the_ema_warmup():
    df = trend_frame("A" * 60)

    create_duration_trend_and_percentile_score(df, min_periods=1)

    assert df["duration_trend_ema10"].iloc[:10].isna().all()
    assert df["duration_trend_ema10"].iloc[10] == 1
    assert df["duration_trend_ema50"].iloc[:50].isna().all()
    assert df["duration_trend_ema50"].iloc[50] == 1


@pytest.mark.parametrize("seed", range(4))
def test_trend_duration_matches_the_trend_duration_screen(seed):
    df = random_walk_frame(seed)
    above, below, side, current_length = _ema_trend_streaks(df.copy())

    create_duration_trend_and_percentile_score(df, min_periods=1)

    run = (df["trend_side_ema10"] != df["trend_side_ema10"].shift()).cumsum()
    lengths = df.dropna(subset=["trend_side_ema10"]).groupby(run)["duration_trend_ema10"].max().astype(int)
    assert sorted(lengths.tolist()) == sorted(r["num_days"] for r in above + below)
    assert df["duration_trend_ema10"].iloc[-1] == current_length
    assert (df["trend_side_ema10"].iloc[-1] == 1) == (side == "Above")


def test_trend_duration_percentile_only_compares_days_of_the_same_side():
    df = random_walk_frame(7, n=400)

    create_duration_trend_and_percentile_score(df, min_periods=1)

    valid = df.dropna(subset=["trend_side_ema10"])
    sides, durations = valid["trend_side_ema10"].to_numpy(), valid["duration_trend_ema10"].to_numpy()
    expected = [
        100 * np.mean([d <= durations[i] for d, s in zip(durations[: i + 1], sides[: i + 1]) if s == sides[i]])
        for i in range(len(valid))
    ]
    assert valid["percentile_duration_trend_ema10"].tolist() == pytest.approx(expected)


def test_trend_duration_percentile_is_nan_until_the_side_has_min_periods_days():
    df = trend_frame("A" * 40 + "BBBB")

    create_duration_trend_and_percentile_score(df, min_periods=3)

    percentile = df["percentile_duration_trend_ema10"]
    assert percentile.iloc[:12].isna().all()
    assert percentile.iloc[-4:-2].isna().all()
    assert percentile.iloc[-2:].notna().all()


def test_series_shorter_than_the_ema_warmup_leaves_nan_instead_of_failing():
    df = trend_frame("A" * 40)

    create_duration_trend_and_percentile_score(df, min_periods=1)

    assert df["duration_trend_ema10"].notna().sum() == 30
    for column in ("trend_side_ema50", "duration_trend_ema50", "percentile_duration_trend_ema50"):
        assert df[column].isna().all()
