import numpy as np

class Portfolio():

    def __init__(self, assets, initial_exposure, starting_capital):
        self.starting_capital = starting_capital
        self.coefficients_exposure = np.array([initial_exposure for asset in assets], dtype=float)
        self.equity_value_history = [self.starting_capital]
        self.coefficients_exposure_history = [self.coefficients_exposure]
        self.assets = assets
        self.shares = np.zeros(len(assets))
        self.last_share_price = np.zeros(len(assets))
        self.cash = np.array([(self.starting_capital * (1 - initial_exposure))/len(assets) for asset in assets]) 

    def cash_initial_purchase(self):
        return [((self.starting_capital - sum(self.cash))/len(self.assets)) for asset in self.assets]

    def update_shares_initial_purchase(self, shares):
        self.shares = shares

    def setLastSharePrice(self, share_prices):
        for i, price in enumerate(share_prices):
            if price:
                self.last_share_price[i] = share_prices[i]

    def balancing_portfolio(self, coefficients): # positivo = cash para comprar, negativo es shares a vender, 0 es mantener
        orders = []
        differences = coefficients - self.coefficients_exposure
        for i, asset_diff in enumerate(differences):
            if asset_diff < 0:
                ratio_shares_to_sell = -asset_diff / self.coefficients_exposure[i]
                orders.append(-ratio_shares_to_sell * self.shares[i])
            elif asset_diff > 0:
                ratio_cash_to_buy = asset_diff / (1 - self.coefficients_exposure[i]) # ratio of cash needed for purchase
                orders.append(ratio_cash_to_buy * self.cash[i])
            else:
                orders.append(0)
        self.coefficients_exposure = np.array(coefficients, dtype=float)
        return orders

    def update_shares_and_cash(self, shares, cash):
        self.shares += shares
        self.cash += cash

    def update_metrics(self):
        current_value_portfolio = sum(self.cash)
        for i, asset in enumerate(self.assets):
            current_value_portfolio += (self.shares[i] * self.last_share_price[i])
        self.equity_value_history.append(current_value_portfolio)
        self.coefficients_exposure_history.append(self.coefficients_exposure)


        

        