import numpy as np

class SimulatedBroker():

    def __init__(self, fee, spread):
        self.fee = fee
        self.spread = spread

    def execute(self, orders, prices):
        shares = [0 for x in orders]
        cash = [0 for x in orders]

        for i, order in enumerate(orders):
            if not np.isnan(order) and prices[i] > 0:            
                if order < 0:
                    proceeds = abs(order) * (prices[i]*(1 - self.spread))
                    if proceeds > self.fee:
                        shares[i] = order
                        cash[i] = proceeds - self.fee
                elif order > self.fee:
                    shares[i] = (order - self.fee) / (prices[i] * (1 + self.spread))
                    cash[i] = order * -1
            else: 
                cash[i] = 0
                shares[i] = 0
        return shares, cash
