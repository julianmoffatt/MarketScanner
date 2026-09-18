def build_features_ML(df):
    # creating target variable y
    df["y_type"] = df["type"].shift(-1)
    X = df.drop('y_type', axis=1)
    y = df['y_type']
    return X, y