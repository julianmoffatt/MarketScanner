from backend.src.market_platform.backtesting.backtesting import *
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from backend.src.market_platform.data.ingestion import *
from itertools import product

def backtesting(symbols, strategys): 
    try:
        pair_symbol_strategy = list(product(symbols, strategys)) # Todas las combinaciones (símbolo, strategy)
        columns = ["Asset", "Strategy", "n_Trades", "Return", "Holding_return", "OutPerformed", "Underperformed"]  
        with ProcessPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(backtesting_strategy_aux, pair_symbol_strategy))
            data_rows = []
            for r in results:
                if r is not False:
                    data_rows.append(r)   # r es una sola fila plana por (symbol, strategy)
            df = pd.DataFrame(data_rows, columns=columns)
            outperformed = len(df[df["Return"] > df["Holding_return"]])
            underperformed = len(df)-outperformed
            general_row = ["ALL", "-", "-", round(df["Return"].mean(),1), round(df["Holding_return"].mean(),1), outperformed, underperformed]
            general_df = pd.DataFrame([general_row], columns=columns)
            df = pd.concat([general_df, df], ignore_index=True)
            return df
    except Exception as e:
        print(e)

def backtesting_strategy_aux(pair_symbol_strategy):
    symbol, strategy = pair_symbol_strategy
    return backtesting_strategy(symbol, strategy)

def backtesting_strategy(symbol, strategy):
    try:
        print(symbol, " strategy: ", strategy.getName())
        row, _ = backtesting_strategy_run(symbol, strategy)
        return row
    except Exception as e:
        print(e)
        return False


def backtesting_equity_curve(symbol, strategy):
    try:
        _, equity_df = backtesting_strategy_run(symbol, strategy)
        return equity_df
    except Exception as e:
        print(e)
        return None


def backtesting_strategy_run(symbol, strategy):
    start = -3000
    assets = Assets()
    timeframes = assets.loadStatistics(assets.loadTimeframes(symbol))
    timeframes = timeframes[0].copy() # tal vez convenga traerse las velas de 1h de los ultimos 2 años y contruir el daily
    training = timeframes[0:start] # Before the last 3 years for training
    daily = timeframes[start:].copy() # Last 3 years for testing
    entry_price = training["Close"].iloc[-1]
    strategy.setBalance(0)
    strategy.setShares(1000/entry_price)
    strategy.setOrders(training)

    equity_rows = []
    for i in range(len(daily)):
        strategy.trading(daily.iloc[i], training)
        strategy_equity = strategy.getBalance() + strategy.getShares() * daily["Close"].iloc[i]
        hold_equity = (daily["Close"].iloc[i] / entry_price) * 1000
        equity_rows.append((daily.index[i], strategy_equity, hold_equity))
        if i < len(daily) - 1:
            training = timeframes[0:start+i+1]
            strategy.setOrders(training)

    equity_df = pd.DataFrame(equity_rows, columns=["Date", "Strategy", "Hold"]).set_index("Date")

    trades = round(strategy.getSells() + strategy.getBuys(), 0)
    strategy_return = round(strategy.getBalance() + (strategy.getShares() * daily["Close"].iloc[-1]), 1)
    holding_return = round((daily["Close"].iloc[-1]/entry_price)*1000, 1)
    row = [assets.name_sustitution(symbol), strategy.getName(), trades, strategy_return, holding_return, 0, 0]
    return row, equity_df




