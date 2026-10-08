def create_percentile_scores(df, col_names, min_periods=252): # receives a list of columns and creates the percentile score columns
    for col in col_names:
        df["percentile_" + col] = df[col].expanding(min_periods=min_periods).rank(method="max", pct=True) * 100
    return df
