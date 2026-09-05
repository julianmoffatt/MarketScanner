from data.assets import *
from backtesting import *

def backtesting_strategy(symbol, strategy):
    assets = Assets()
    timeframes = assets.loadStatistics(assets.loadTimeframes(symbol))
    timeframes = timeframes[0].copy()

    training = timeframes[0:-1000]
    daily = timeframes[-1000:].copy()
    strategy.setBalance(0)
    strategy.setShares(1000/training["Close"].iloc[-1])
    strategy.setOrders(training)

    for i in range(len(daily)):
        strategy.trading(daily.iloc[i])
        training = timeframes[0:-1000+i+1]
        strategy.setOrders(training)



