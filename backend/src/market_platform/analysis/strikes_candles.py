def _count_streaks(types):
    """Cuenta rachas de velas consecutivas del mismo color.
    Devuelve {"Green": {longitud: conteo}, "Red": {longitud: conteo}}.
    """
    counts = {"Green": {}, "Red": {}}
    streak_len = 1
    for j in range(1, len(types)):
        if types[j] == types[j - 1]:
            streak_len += 1
        else:
            prev_color = types[j - 1]
            counts[prev_color][streak_len] = counts[prev_color].get(streak_len, 0) + 1
            streak_len = 1
    # ultimo strike final 
    counts[types[-1]][streak_len] = counts[types[-1]].get(streak_len, 0) + 1
    return counts, types[-1], streak_len


HIGHER_TIMEFRAME_LABELS = ["daily", "weekly", "monthly"]
LOWER_TIMEFRAME_LABELS = ["1h", "4h"]


def _build_panels(timeframes, labels):
    # zip se detiene en el mas corto: si llegan mas dataframes que etiquetas
    # (ej. quarterly/yearly tras monthly), los sobrantes se ignoran.
    panels = []

    for label, df in zip(labels, timeframes):
        types = df["type"].tolist()
        counts, current_color, current_length = _count_streaks(types)

        for color in ("Green", "Red"):
            total = sum(counts[color].values()) or 1
            rows = [
                {"length": length, "count": count, "pct": count / total * 100}
                for length, count in counts[color].items()
            ]
            rows.sort(key=lambda r: r["length"])

            panels.append({
                "timeframe": label,
                "type": color,
                "current_length": current_length,
                "is_current": color == current_color,
                "rows": rows,
            })
    return panels


def compute(timeframes):
    return _build_panels(timeframes, HIGHER_TIMEFRAME_LABELS)


def compute_lowertimeframe(timeframes):
    return _build_panels(timeframes, LOWER_TIMEFRAME_LABELS)
