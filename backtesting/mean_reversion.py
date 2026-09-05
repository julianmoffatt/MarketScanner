import numpy as np

class MeanReversion:
    def __init__(self):
        self.balance = 0
        self.shares = 0
        self.buyPrice = 0
        self.sellPrice = 0

    @staticmethod
    def getBalance(self):
        return self.balance

    @staticmethod
    def setBalance(self, balance):
        self.balance = balance

    @staticmethod
    def getShares(self):
        return self.shares

    @staticmethod
    def setShares(self, balance):
        self.balance = balance    

    @staticmethod
    def setOrders(self, training):
        self.buyPrice = np.quantile(training["extension_10"], 0.05)    
        self.sellPrice = np.quantile(training["extension_10"], 0.95)    

    @classmethod
    def trading(cls, self, candle):
        if self.shares > 0 and candle["High"] >= self.sellPrice:
            sold = self.shares * self.sellPrice
            self.shares = 0
            cls.setBalance(cls.getBalance()+sold)
        elif candle["Low"] <= self.buyPrice:
            bought = cls.getBalance / self.buyPrice
            cls.setShares(cls.getShares()+bought)



        



