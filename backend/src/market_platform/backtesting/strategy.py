from abc import ABC, abstractmethod

class Strategy(ABC):
    def __init__(self, name):
        self.name = name
        self.balance = 0
        self.shares = 0
        self.buyPrice = 0
        self.sellPrice = 0
        self.sells = 0
        self.buys = 0
        self.tolerance = 0    

    def getName(self):
            return self.name

    def getBalance(self):
        return self.balance

    def setBalance(self, balance):
        self.balance = balance

    def getShares(self):
        return self.shares

    def setShares(self, shares):
        self.shares = shares

    def getBuys(self):
        return self.buys

    def getSells(self):
        return self.sells

    def incrementBuys(self):
        self.buys += 1        

    def incrementSells(self):
        self.sells += 1

    def selling(self, sold):
        self.shares = 0
        self.setBalance(self.getBalance() + sold)
        self.incrementSells()

    @abstractmethod
    def setOrders(self, training, weight=0.1):
        pass
        
    @abstractmethod
    def trading(self, candle, daily, training):
        pass