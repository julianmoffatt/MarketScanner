import pandas as pd

ALL_PATTERNS = ["GGG", "GGR", "GRG", "GRR", "RRR", "RRG", "RGR", "RGG"]


def _still_possible(prefix):
    """Patrones completos compatibles con los meses ya conocidos del trimestre
    en curso (0, 1 o 2 letras). Con prefix="" (trimestre recien empezado)
    los 8 siguen siendo posibles."""
    return [p for p in ALL_PATTERNS if p.startswith(prefix)]


def compute(timeframes):
    monthly = timeframes[2].copy()
    monthly["year"] = monthly.index.year
    monthly["quarter"] = monthly.index.quarter
    monthly["month_of_q"] = monthly.index.month - (monthly["quarter"] - 1) * 3
    monthly["letter"] = monthly["type"].map({"Green": "G", "Red": "R"})

    # el ultimo candle mensual puede seguir en curso (el mes calendario actual
    # todavia no ha cerrado) aunque ya aparezca como fila -- no cuenta como
    # mes cerrado. Se separa para sacar el patron parcial del trimestre en
    # curso y no contaminar los patrones completos historicos.
    now = pd.Timestamp.now(tz=monthly.index.tz)
    last_is_open = (monthly.index[-1].year == now.year) and (monthly.index[-1].month == now.month)

    current_quarter, current_prefix = None, ""
    if last_is_open:
        current_year = monthly["year"].iloc[-1]
        current_quarter = monthly["quarter"].iloc[-1]
        closed_this_quarter = monthly.iloc[:-1]
        closed_this_quarter = closed_this_quarter[
            (closed_this_quarter["year"] == current_year) & (closed_this_quarter["quarter"] == current_quarter)
        ].sort_values("month_of_q")
        current_prefix = "".join(closed_this_quarter["letter"].tolist())
        monthly = monthly.iloc[:-1]

    groups = list(monthly.groupby(["year", "quarter"]))

    panels = []
    for quarter_number in [1, 2, 3, 4]:
        patterns = []
        for (_, q), group in groups:
            if q != quarter_number or len(group) != 3:
                continue
            group = group.sort_values("month_of_q")
            patterns.append("".join(group["letter"].tolist()))

        counts = {p: patterns.count(p) for p in ALL_PATTERNS}
        total = sum(counts.values())
        is_current = quarter_number == current_quarter
        possible = _still_possible(current_prefix) if is_current else ALL_PATTERNS

        rows = [
            {
                "pattern": p,
                "count": counts[p],
                "pct": (counts[p] / total * 100) if total > 0 else 0.0,
                "is_possible": p in possible,
            }
            for p in ALL_PATTERNS
        ]
        rows.sort(key=lambda r: r["count"], reverse=True)

        panels.append({
            "quarter": f"Q{quarter_number}",
            "is_current": is_current,
            "current_prefix": current_prefix if is_current else "",
            "occurrences": total,
            "still_possible": len(possible) if is_current else 0,
            "rows": rows,
        })

    return panels
