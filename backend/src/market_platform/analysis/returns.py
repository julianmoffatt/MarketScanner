def compute(timeframes):
    daily = timeframes[0]
    returns = daily["return"].dropna()
    z_scores = (returns - returns.mean()) / returns.std()

    rows = [
        {"day": int(day), "z_score": float(z)}
        for day, z in zip(z_scores.index.day, z_scores)
    ]
    return {"current_z_score": float(z_scores.iloc[-1]), "rows": rows}
    


