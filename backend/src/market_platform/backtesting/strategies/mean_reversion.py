from backend.src.market_platform.backtesting.strategies.strategy import Strategy
from backend.src.market_platform.features.stats import create_percentile_scores
from .registry import register_model

@register_model("mean_reversion_distance")
class MeanReversion(Strategy):
    def __init__(self):
        pass

    def compute(self, df, coef) -> float:
        min_coef = 0
        max_coef = 0
        percentil_ema_10 = df["percentile_extension_ema10"].iloc[-1]
        percentil_ema_200 = df["percentile_extension_ema200"].iloc[-1]
        #macro exposure
        if percentil_ema_200 < 5:
            min_coef = 1
            max_coef = 1
        elif (percentil_ema_200 >= 10) and (percentil_ema_200 < 50):
            min_coef = 0.75
            max_coef = 1
        elif (percentil_ema_200 >= 50) and (percentil_ema_200 < 90):
            min_coef = 0.5
            max_coef = 0.75
        elif (percentil_ema_200 >= 95) :
            min_coef = 0.25
            max_coef = 0.50

        #short term rebalancing
        if percentil_ema_10 >= 90:
            coef = min_coef
        elif (percentil_ema_10 < 60) and (percentil_ema_10 > 40):
            coef = (max_coef + min_coef) / 2
        elif percentil_ema_10 <= 10:
            coef = max_coef
        return coef
    
        
    def prepare_features(self, df):
        df = create_percentile_scores(df, ["extension_ema10", "extension_ema200"])
        return df