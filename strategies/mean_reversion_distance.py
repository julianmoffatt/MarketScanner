from data.assets import *
from concurrent.futures import ProcessPoolExecutor
import random

def test_strategy(symbol):
    try:
        assets = Assets()
        test = [] 
        timeframes = assets.loadStatistics(assets.loadTimeframes(symbol))

        for a in range(0, 1):
            #h1 = round(random.uniform(0.85, 0.96),2) #h2 = round(random.uniform(0.97, 0.995),2)
            #phigh = timeframes[0][:-365]["extension_low_ema10"].quantile(h1) #0.93 #phigh_stop = timeframes[0][:-365]["extension_high_ema10"].quantile(h2) #0.96
            l1 = round(random.uniform(0.2, 0.02),2)
            l2 = round(random.uniform(l1, 0.01),2)
            plow = timeframes[0][:-730]["extension_low_ema10"].quantile(l1)
            plow_stop = timeframes[0][:-730]["extension_low_ema10"].quantile(l2) 
            #mean = timeframes[0][:-730]["extension_low_ema10"].mean()
            std = timeframes[0][:-730]["extension_low_ema10"].std()
            #plow = round(mean - std - std, 4)
            #plow = timeframes[0][:-730]["extension_low_ema10"].quantile(0.07)
            #plow_stop = round(mean - std - std - (std/2), 4)
            data = assets.last_X_years(timeframes, 2) 
            df = data[0]
            entry, take_profit, stop_loss = 0, 0, 0
            long, short = False, False
            cash = 1000
            rows = []

            for i in range(1, len(df)):
                if long or short:
                    if long:
                        if df["High"].iloc[i] > take_profit and df["Low"].iloc[i] > stop_loss:
                            profit = cash * ((take_profit/entry)-1)
                            cash = cash + profit - 0.1
                            rows.append({"side": "long", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": profit, "portfolio": cash})
                            print("CLOSED LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "PROFIT:", profit)
                            long = False
                        elif df["High"].iloc[i] < take_profit and df["Low"].iloc[i] < stop_loss:
                            loss = cash * ((stop_loss / entry) - 1)
                            cash = cash + loss - 0.1
                            rows.append({"side": "long", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": loss, "portfolio": cash})
                            print("STOPPED LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "LOSS:", loss)
                            long = False
                        elif df["High"].iloc[i] > take_profit and df["Low"].iloc[i] < stop_loss:
                            rows.append({"side": "cancelled", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": 0, "portfolio": cash})
                            long = False
                        else:
                            correction = round((1-(0.001*abs(std))), 3)
                            take_profit = ((df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]) * correction
                            stop_loss = df["EMA_10"].iloc[i] * (1+(plow_stop/100))  

                    #elif short:
                    #    if df["Low"].iloc[i] < take_profit and df["High"].iloc[i] < stop_loss:
                    #        profit = (cash * (1 - (take_profit / entry)))
                    #        cash = cash + profit - 1
                    #        rows.append({"side": "short", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": profit, "portfolio": cash})
                    #        print("CLOSED SHORT", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "PROFIT:", profit)
                    #        short = False
                    #    elif df["Low"].iloc[i] > take_profit and df["High"].iloc[i] > stop_loss:
                    #        loss = cash * (1 - (stop_loss / entry))
                    #        cash = cash + loss - 1
                    #        rows.append({"side": "short", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": loss, "portfolio": cash})
                    #        print("STOPPED SHORT", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "LOSS:", loss)
                    #        short = False
                    #        stopped = True
                    #    elif df["High"].iloc[i] < take_profit and df["Low"].iloc[i] > stop_loss:
                    #        rows.append({"side": "cancelled", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": 0, "portfolio": cash})
                    #        short = False
                    #    else:
                    #        take_profit = ((df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]) * 1.0025
                    #        #stop_loss = df["EMA_10"].iloc[i] * (1+(phigh_stop/100)) 
                else:                
                    if df["extension_low_ema10"].iloc[i] <= plow:
                        long = True
                        entry = df["EMA_10"].iloc[i] * (1+(plow/100)) #(df["Close"].iloc[i] + df["Low"].iloc[i]) / 2
                        take_profit = ((df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]) * 0.995
                        stop_loss = df["EMA_10"].iloc[i] * (1+(plow_stop/100)) 
                        print("LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss)
                        if df["extension_low_ema10"].iloc[i] <= plow_stop:  
                            loss = cash * ((stop_loss / entry) - 1)
                            cash = cash + loss - 0.1
                            rows.append({"side": "long", "entry": entry, "take_profit": take_profit, "stop_loss": stop_loss, "outcome": loss, "portfolio": cash})
                            print("STOPPED LONG", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss, "LOSS:", loss)
                            long = False

                        #elif df["extension_high_ema10"].iloc[i] >= phigh:
                        #    short = True
                        #    entry = df["EMA_10"].iloc[i] * (1+(phigh/100)) #(df["Close"].iloc[i] + df["High"].iloc[i]) / 2
                        #    take_profit = (df["EMA_10"].iloc[i] / df["EMA_10"].iloc[i-1]) * df["EMA_10"].iloc[i]
                        #    stop_loss = df["EMA_10"].iloc[i] * (1+(phigh_stop/100)) 
                        #    print("SHORT", symbol, df.index[i], "ENTRY", entry, "TP", take_profit, "SL", stop_loss)
            df_strategy = pd.DataFrame(rows)
            if not df_strategy.empty:
                df_win = df_strategy[df_strategy["outcome"] > 0].copy()
                if not df_win.empty:
                    df_win["Return"] = round((df_win["outcome"] / (df_win["portfolio"] - df_win ["outcome"])) * 100,1)
                    returnPerWin = df_win["Return"].mean()
                else:
                    returnPerWin = 0
                df_loss = df_strategy[df_strategy["outcome"] < 0].copy()
                df_cancelled = df_strategy[df_strategy["outcome"] == 0].copy() #que pasa si entro cuando viene rebotando de abajo, por si la primera caida es muy violenta
                if len(df_win) == 0:
                    hitrate = 0
                elif len(df_loss) == 0:
                    hitrate = 1
                else:
                    hitrate = round(len(df_win)/(len(df_loss)+len(df_win)),1)
                test.append({"symbol": symbol, "portfolio": round(cash,1), "trades": len(df_strategy), "hitrate": hitrate, "%ReturnWins": round(returnPerWin,1), "cancelled": len(df_cancelled), "plow": plow, "plow_stop": plow_stop, "correction": correction})    
        print("processing dataframe to show")
        if len(test) > 0:
            df = pd.DataFrame(test)   
            df = df.sort_values(by='portfolio', ascending=False)
            return df.iloc[0].to_dict()
        else:
            return False
    except Exception as e:
        print(e)
        return False


def test_strategy_all_symbols():
    assets = Assets()
    symbols = assets.getAssets("mysymbols")
    with ProcessPoolExecutor(max_workers=10) as executor:
        rows = list(executor.map(test_strategy, symbols))    
    data_rows = [x for x in rows if x is not False]
    df = pd.DataFrame(data_rows)   
    df = df.sort_values(by='portfolio', ascending=False)
    print("plow", df["plow"].mean(), "plow_stop", df["plow_stop"].mean()) #, "phigh", df["phigh"].mean(), "phigh_stop", df["phigh_stop"].mean())
    df.to_csv("test_strategy_symbols.csv") 
    return df