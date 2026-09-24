from scipy.stats import percentileofscore

def build_features_ML(df):
    # Handling look ahead bias features
    df.drop('next_close', axis=1) 
    df.drop('return_next_day', axis=1)
    # Creating calendar info features
    df["day_of_week"] = df["date"].dt.day_name()
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter  
    df["week_of_year"] = df["date"].dt.isocalendar().week 
    # Creating advanced features
    df["rsi_percentile"] = [percentileofscore(df["rsi"].iloc[:i], df["rsi"].iloc[i], kind="rank") for i in range(len(df))]
    df.drop('rsi', axis=1) 
    # creating target variable y
    df["y_type"] = df["type"].shift(-1)    
    X = df.drop('y_type', axis=1)
    y = df['y_type']
    return X, y