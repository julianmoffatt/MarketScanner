from backend.src.market_platform.backtesting.strategies.strategy import Strategy
from .registry import register_model

@register_model("buy_and_hold")
class BuyAndHold(Strategy):
    def compute(self, df, coef) -> float:
        return 1.0
