import pandas as pd
import pytest

from backend.src.market_platform.analysis import strikes_candles
from backend.src.market_platform.analysis.strikes_candles import _count_streaks


def frame(types):
    return pd.DataFrame({"type": types})


def panel(panels, timeframe, color):
    return next(p for p in panels if p["timeframe"] == timeframe and p["type"] == color)


def test_counts_streaks_by_color_and_length():
    counts, current_color, current_length = _count_streaks(["Green", "Green", "Red", "Green"])

    assert counts == {"Green": {2: 1, 1: 1}, "Red": {1: 1}}
    assert current_color == "Green"
    assert current_length == 1


def test_a_single_unbroken_streak_is_also_the_current_one():
    counts, current_color, current_length = _count_streaks(["Red"] * 4)

    assert counts == {"Green": {}, "Red": {4: 1}}
    assert (current_color, current_length) == ("Red", 4)


def test_lower_timeframe_returns_a_green_and_red_panel_for_1h_and_4h():
    panels = strikes_candles.compute_lowertimeframe([frame(["Green", "Red"]), frame(["Red", "Red"])])

    assert [(p["timeframe"], p["type"]) for p in panels] == [
        ("1h", "Green"), ("1h", "Red"), ("4h", "Green"), ("4h", "Red"),
    ]


def test_higher_timeframe_ignores_quarterly_and_yearly():
    dfs = [frame(["Green", "Red"])] * 5

    panels = strikes_candles.compute(dfs)

    assert {p["timeframe"] for p in panels} == {"daily", "weekly", "monthly"}


def test_only_the_color_of_the_running_streak_is_current():
    panels = strikes_candles.compute_lowertimeframe([frame(["Red", "Green", "Green"]), frame(["Green", "Red"])])

    assert panel(panels, "1h", "Green")["is_current"] is True
    assert panel(panels, "1h", "Red")["is_current"] is False
    assert panel(panels, "1h", "Green")["current_length"] == 2
    assert panel(panels, "4h", "Red")["is_current"] is True


def test_rows_are_sorted_by_length_and_percentages_add_up_to_100():
    types = ["Green", "Red"] + ["Green"] * 3 + ["Red"] + ["Green"] * 2 + ["Red"]
    panels = strikes_candles.compute_lowertimeframe([frame(types), frame(types)])

    green = panel(panels, "1h", "Green")
    assert [r["length"] for r in green["rows"]] == [1, 2, 3]
    assert sum(r["pct"] for r in green["rows"]) == pytest.approx(100)
    assert [r["count"] for r in green["rows"]] == [1, 1, 1]


def test_a_color_that_never_appears_has_no_rows():
    panels = strikes_candles.compute_lowertimeframe([frame(["Green"] * 3), frame(["Green"] * 3)])

    assert panel(panels, "1h", "Red")["rows"] == []
