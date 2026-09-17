import numpy as np
from backend.src.market_platform.analytics.retest_bands import *
from backend.src.market_platform.backtesting.strategy import Strategy

class MeanReversion(Strategy):
    def __init__(self, name):
        super().__init__(name)

    def setOrders(self, training, weight=0.1):
        vol, vol_p20, vol_p80 = Assets.calculate_volatility(training["Close"])
        tolerance = (vol.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight
        self.tolerance = tolerance.iloc[-1]
        self.sellPrice = training["ema10"].iloc[-1] * (1 + np.quantile(training["extension_ema10"], 0.99) / 100)
        self.buyPrice = training["ema10"].iloc[-1] * (1 + self.tolerance) #recomprar en ema

    def trading(self, candle, training):
        time_away = self.time_away_from_ema(training) #bajar a velas de 1h para aumentar precision intradia
        #ema extension logic
        if (time_away >= 5) and self.shares > 0 and candle["High"] >= self.sellPrice and candle["Low"] > training["ema10"].iloc[-1]:
            sold = self.shares * self.sellPrice
            self.selling(sold)
            print("I sell the day", candle.name, " at ", self.sellPrice, " for extension to the mean")        
        elif self.balance > 0 and candle["Low"] <= self.buyPrice:
            bought = self.balance / self.buyPrice
            self.setShares(self.getShares() + bought)
            self.setBalance(0)
            self.incrementBuys()
            print("order buy margin %: ", self.tolerance, " the day ", candle.name)
        elif (time_away >= 9) and (self.shares > 0) and (candle["High"] >= (training["ema10"].iloc[-1] * (1 + ((np.quantile(training["extension_ema10"], 0.95))*0.65)/100))): 
            sold = self.shares * (training["ema10"].iloc[-1] * (1 + ((np.quantile(training["extension_ema10"], 0.95)*0.65)/100)))
            self.selling(sold)
            print("I sell the day", candle.name, " at ", candle["Close"], " for time-away from the mean")
        
    @staticmethod
    def time_away_from_ema(training, weight=0.3):
        _, vol_p20, vol_p80 = Assets.calculate_volatility(training["Close"])
        vol_daily, _, _ = Assets.calculate_volatility(training["Close"])
        tolerance = (vol_daily.fillna(vol_p20).clip(vol_p20, vol_p80) / 100) * weight
        time_away = 0
        for i in range(len(training)-1, -1, -1):
            if ((training['Low'].iloc[i] * (1 - tolerance.iloc[i])) > training['ema10'].iloc[i]) or ((training['High'].iloc[i] * (1 + tolerance.iloc[i])) < training['ema10'].iloc[i]):
               time_away += 1
            else:
                return time_away

