from backend.src.market_platform.backtesting.strategies.strategy import Strategy
from backend.src.market_platform.features.stats import create_percentile_scores
from .registry import register_model

@register_model("mean_reversion_distance")
class MeanReversion(Strategy):
    def __init__(self):
        pass

    def compute(self, df, coef) -> float:
        percentil_ema_20 = df["percentile_extension_ema20"].iloc[-1]

        if percentil_ema_20 >= 99:
            coef = 0
        elif percentil_ema_20 <= 50:
            coef = 1
        return coef
    
        
    def prepare_features(self, df):
        df = create_percentile_scores(df, ["extension_ema20"])
        return df