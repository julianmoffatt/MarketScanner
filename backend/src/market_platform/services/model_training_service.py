from pipeline import processedTimeframes
from features.build_features_ML import build_features_ML
from ML.training_service import train_model

def run_training(asset="sp500", model_name="random_forest_classifier", model_params=None):
    timeframes = processedTimeframes(asset, timeframe_group = 0) #daily, weekly, etc
    daily = timeframes[0].copy()
    X, y = build_features_ML(daily)
    result = train_model(model_name, X, y, model_params=model_params, feature_names=list(X.columns) if hasattr(X, "columns") else None,)
    return result