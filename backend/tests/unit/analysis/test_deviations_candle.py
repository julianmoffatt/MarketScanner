import pandas as pd
import pytest

from backend.src.market_platform.analysis import deviations_candle


def frame(rows):
    """rows: (open, high, low, close). El tipo se calcula como en el pipeline (cierre vs cierre anterior)."""
    df = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"],
                      index=pd.date_range("2024-01-01", periods=len(rows), freq="D"))
    df["type"] = ["Green" if c > p else "Red" for c, p in zip(df["Close"], df["Close"].shift(1).fillna(0))]
    return df


def panels_for(df):
    result = deviations_candle.compute([df] * 5)
    return {(p["timeframe"], p["type"]): p for p in result}


def test_current_is_the_open_candle_deviation_below_and_above():
    # Ultima vela ROJA: abre 100, sube hasta 105, cae hasta 90, cierra 92.
    df = frame([(100, 102, 98, 101), (101, 104, 99, 103), (100, 105, 90, 92)])

    panels = panels_for(df)

    assert panels[("daily", "Green")]["current_value"] == pytest.approx(-10.0)  # (100-90)/100 por abajo
    assert panels[("daily", "Red")]["current_value"] == pytest.approx(5.0)      # (105-100)/100 por arriba


def test_current_does_not_depend_on_the_candle_color():
    # Misma estructura pero la ultima vela es VERDE: los dos paneles siguen marcando la vela actual.
    df = frame([(100, 102, 98, 99), (99, 101, 97, 100), (100, 106, 96, 104)])

    panels = panels_for(df)

    assert panels[("daily", "Green")]["current_value"] == pytest.approx(-4.0)
    assert panels[("daily", "Red")]["current_value"] == pytest.approx(6.0)


def test_current_is_not_taken_from_an_older_candle_of_the_same_color():
    # La ultima vela verde del historico (indice 1) tiene -1 %; la actual (roja) cae -10 %.
    df = frame([(100, 102, 98, 99), (100, 103, 99, 105), (105, 106, 94.5, 95)])

    green = panels_for(df)[("daily", "Green")]

    assert green["rows"][-1]["deviation"] == pytest.approx(-1.0)
    assert green["current_value"] == pytest.approx(-10.0)


def test_rows_and_percentile_still_use_the_history_of_each_color():
    # Velas: 1 verde (-2 %), 2 verde (-1 %), 3 roja (+0.95 % por arriba).
    df = frame([(100, 102, 98, 99), (100, 103, 99, 105), (105, 106, 94.5, 95)])

    panels = panels_for(df)

    assert [r["deviation"] for r in panels[("daily", "Green")]["rows"]] == pytest.approx([-2.0, -1.0])
    assert [r["deviation"] for r in panels[("daily", "Red")]["rows"]] == pytest.approx([100 / 105])
    # Percentil del valor actual (-10 %) dentro del historico verde (-2, -1): ninguno es menor o igual.
    assert panels[("daily", "Green")]["percentile"] == 0.0
