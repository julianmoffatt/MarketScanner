import numpy as np
import pandas as pd
import pytest

from backend.src.market_platform.features.stats import create_percentile_scores


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
