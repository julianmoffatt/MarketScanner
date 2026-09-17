from backend.src.market_platform.data.ingestion import *
from backend.src.market_platform.data.data import *
import pandas as pd

def golden_cross(df):
    if df["EMA_12"].iloc[-1] < df["EMA_25"].iloc[-1]:
        incr1 = df["EMA_12"].iloc[-1]/df["EMA_12"].iloc[-2]
        incr2 = df["EMA_25"].iloc[-1]/df["EMA_25"].iloc[-2]
        if (df["EMA_12"].iloc[-1] * incr1 * 1.001) > (df["EMA_25"].iloc[-1] * incr2):
            return True      
    return False

def relative_return(entry, value):
    num = float(value)  
    return round(((num / entry) - 1) * 100, 1)

def golden_cross_performance(entry, df):
    row = []
    for i in range(len(df)):
        for k in ["Open", "Close", "High", "Low"]:
            row.append(relative_return(entry, df[k].iloc[i]))
    return row

def calculation_golden_crosses_history(symbol, timeframes, t):
    if t == "weekly":
        df = timeframes[1].copy()
        df = df[-200:]
        p = 200
    elif t == "daily":
        df = timeframes[0].copy()
        df = df[-1300:]
        p = 1300
    golden_crosses = []
    row = []
    columns = ["D" + str(i) + k for i in range(1, 6) for k in ["Open", "Close", "High", "Low"]]
    columns = ["Symbol", "Date", "Day", "Month(Q)", "D1%Month", "D1%Quarter", "D1%Year", "D0volume", "D1volume", "D0_xEma12", "D1_xEma12", "D0.EXT.10D", "D0.EXT.20D", "D0.EXT.10W", "D0.DAILY.RSI", "%D1vsEXT.10D.P95", "%D1vsEXT.10D.P99"] + columns
    if len(df) >= p: # +- 2 años
        for i in range(1, len(df)-1):
            if golden_cross(df[i-1:i+1]) and ((df["EMA_12"].iloc[i+1] * 1.001) >= df["EMA_25"].iloc[i+1]):
                daily_aux = timeframes[0].copy()
                if t == 'weekly':
                    today = daily_aux[(daily_aux.index > df.index[i]) & (daily_aux.index < df.index[i+1])]
                    today = today.iloc[-1:]
                elif t == 'daily':
                    today = df.iloc[i:i+1]                    
                
                daily_aux = daily_aux[daily_aux.index >= df.index[i+1]].copy()
                D0incr12, D1incr12 = 0, 0
                
                if len(daily_aux) >= 5: 
                    daily = daily_aux[0:5].copy()
                    D0incr12 = round(((df["EMA_12"].iloc[i]/df["EMA_12"].iloc[i-1])-1)*100, 2)
                    D1incr12 = round(((daily["EMA_12"].iloc[0]/df["EMA_12"].iloc[i])-1)*100, 2)
                    daily_extensions = timeframes[0][timeframes[0].index < df.index[i+1]]
                    weekly_extensions = timeframes[1][timeframes[1].index < df.index[i+1]]
                    d10 = stats.percentileofscore(daily_extensions["extension_ema10"].dropna(), df["extension_ema10"].iloc[i], kind='rank')
                    d20 = stats.percentileofscore(daily_extensions["extension_ema20"].dropna(), df["extension_ema20"].iloc[i], kind='rank')
                    w10 = stats.percentileofscore(weekly_extensions["extension_ema10"].dropna(), df["extension_ema10"].iloc[i], kind='rank')
                    rsi = stats.percentileofscore(daily_extensions["rsi"].dropna(), df["rsi"].iloc[i], kind='rank')
                    upsideP95ext10 = round(daily_extensions["extension_ema10"].quantile(0.95) - daily["extension_ema10"].iloc[0], 1)
                    upsideP99ext10 = round(daily_extensions["extension_ema10"].quantile(0.99) - daily["extension_ema10"].iloc[0], 1)
                    monthly = timeframes[2][(timeframes[2].index.year == daily.index[0].year) & (timeframes[2].index.month == daily.index[0].month)]
                    D1vsMO = round(((daily["Close"].iloc[0] / monthly["Open"].iloc[0]) - 1) * 100, 1)
                    q = (daily.index[0].month - 1) // 3 + 1
                    quarter = timeframes[2][(timeframes[2].index.year == daily.index[0].year) & (timeframes[2].index.month == (3*(q-1))+1)]
                    D1vsQO = round(((daily["Close"].iloc[0] / quarter["Open"].iloc[0]) - 1) * 100, 1)
                    yearly = timeframes[2][(timeframes[2].index.year == daily.index[0].year) & (timeframes[2].index.month == 1)]
                    D1vsYO = round(((daily["Close"].iloc[0] / yearly["Open"].iloc[0]) - 1) * 100, 1)
                    D0volume_percentil = stats.percentileofscore(daily_extensions["Volume"].dropna(), df["Volume"].iloc[i], kind='rank')
                    D1volume_percentil = stats.percentileofscore(daily_extensions["Volume"].dropna(), daily["Volume"].iloc[0], kind='rank')
                    row = [symbol, df.index[i], df.index[i].day, ((df.index[i].month - 1) % 3) + 1, D1vsMO, D1vsQO, D1vsYO, round(D0volume_percentil,0), round(D1volume_percentil,0), D0incr12, D1incr12, round(d10,0), round(d20,0), round(w10,0), round(rsi,0), upsideP95ext10,  upsideP99ext10] + golden_cross_performance(df["Close"].iloc[i], daily)
                    golden_crosses.append(row)
        df_stats = pd.DataFrame(golden_crosses, columns=columns)
        if not df_stats.empty:
            return df_stats
    return pd.DataFrame() # calcular la volatilidad del activo general y actual?    
    

def golden_cross_screener(t):
    try:
        assets = Assets()
        symbols = assets.getAssets("all")
        golden_crosses = pd.DataFrame()
        for symbol in symbols:            
            print(symbol)
            data = assets.loadStatistics(assets.loadTimeframes(symbol))
            if len(data[0]) >= 2000:
                try:
                    df_symbol = calculation_golden_crosses_history(symbol, data, t)
                    if not df_symbol.empty:
                        golden_crosses = pd.concat([golden_crosses, df_symbol], ignore_index=True)
                except:
                    pass
        print(golden_crosses)
        golden_crosses["mx1wk"] = golden_crosses[["D2High", "D3High", "D4High", "D5High"]].max(axis=1)
        golden_crosses["min1wk"] = golden_crosses[["D2Low", "D3Low", "D4Low", "D5Low"]].min(axis=1)
        golden_crosses["MoveToCatch"] = round(golden_crosses["mx1wk"] - golden_crosses["D1Close"],2)
        golden_crosses["SL"] = round(golden_crosses["min1wk"] - golden_crosses["D1Close"],2)
        golden_crosses["R:R"] = round(golden_crosses["MoveToCatch"] / golden_crosses["SL"], 2)
        df_ordered = golden_crosses.sort_values(by="mx1wk", ascending=False)
        print("SET-UPS TOTALES", len(df_ordered), round(df_ordered["mx1wk"].mean(), 2), round(df_ordered["min1wk"].mean(), 2))
        df_ordered.to_csv("excels/golden_crosses.csv")
        return df_ordered 
    except Exception as e:
        print(e)   


def row_stats(data):
    try:
        df = data[0].copy()
        d10 = stats.percentileofscore(df["extension_ema10"].dropna(), df["extension_ema10"].iloc[-1], kind='rank')
        d20 = stats.percentileofscore(df["extension_ema20"].dropna(), df["extension_ema20"].iloc[-1], kind='rank')
        w10 = stats.percentileofscore(data[1]["extension_ema10"].dropna(), data[0]["extension_ema10"].iloc[-1], kind='rank')
        upsideP95ext10 = round(df["extension_ema10"].quantile(0.95) - df["extension_ema10"].iloc[-1], 1)
        upsideP99ext10 = round(df["extension_ema10"].quantile(0.99) - df["extension_ema10"].iloc[-1], 1)
        monthly = data[2][(data[2].index.year == df.index[-1].year) & (data[2].index.month == df.index[-1].month)]
        returnMO = round(((df["Close"].iloc[-1] / monthly["Open"].iloc[0]) - 1) * 100, 1)
        returnMOLast = round(((df["Close"].iloc[-2] / monthly["Open"].iloc[0]) - 1) * 100, 1)
        q = (df.index[-1].month - 1) // 3 + 1
        quarter = data[2][(data[2].index.year == df.index[-1].year) & (data[2].index.month == q)]
        returnQO = round(((df["Close"].iloc[-1] / quarter["Open"].iloc[0]) - 1) * 100, 1)
        returnQOLast = round(((df["Close"].iloc[-2] / quarter["Open"].iloc[0]) - 1) * 100, 1)
        yearly = data[2][(data[2].index.year == df.index[-1].year) & (data[2].index.month == 1)]
        returnYO = round(((df["Close"].iloc[-1] / yearly["Open"].iloc[0]) - 1) * 100, 1)
        returnYOLast = round(((df["Close"].iloc[-2] / yearly["Open"].iloc[0]) - 1) * 100, 1)
        volume_percentil = round(stats.percentileofscore(df["Volume"].dropna(), df["Volume"].iloc[-1], kind='rank'), 1)
        xEMA12 = round(((df["EMA_12"].iloc[-1]/df["EMA_12"].iloc[-2])-1)*100, 2)
        DAY = df.index[-1].day
        MonthQ = ((df.index[-1].month - 1) % 3) + 1
        D1Close = round(((df["Close"].iloc[-1] / df["Close"].iloc[-2]) - 1) * 100, 1)
        row = [returnMO, returnQO, returnYO, returnMOLast, returnQOLast, returnYOLast, round(d10,0), round(d20,0), round(w10,0), upsideP95ext10, upsideP99ext10, xEMA12, volume_percentil, D1Close, DAY, MonthQ]
        return row
    except Exception as e:
        print(e)
        return False


def calculation_12_25_cross():
    assets = Assets()
    columns = ["Symbol", "%MonthLast", "%QuarterLast", "%YearLast", "%Month", "%Quarter", "%Year", "Ext10d", "Ext20d", "Ext10w", "Ext10dp95", "Ext10dp99", "xEma12", "Vol", "D1Close", "Day", "Month(Q)"]
    planning = pd.DataFrame(columns=columns)
    execution = pd.DataFrame(columns=columns)
    symbols = assets.getAssets("all")

    for symbol in symbols:
        print(symbol)
        try:
            data = assets.loadStatistics(assets.loadTimeframes(symbol))
            parameters = row_stats(data)
            if parameters:
                display = [symbol] + parameters
                if golden_cross(data[0][-2:].copy()):
                    planning.loc[len(planning)] = display
                elif golden_cross(data[0][-3:-1].copy()):
                    execution.loc[len(execution)] = display
        except Exception as e:
            print(e)    
    planning = planning[(planning["xEma12"]>=0.1) & (planning["%Quarter"]>=-3) & (planning["Ext10dp99"]>=2)] # & (((planning["DAY"]>=1) & (planning["DAY"]<=10)) | ((planning["DAY"]>=25) & (planning["DAY"]<=31)))]  
    execution = execution[(execution["xEma12"]>=0.1) & (execution["%Quarter"]>=0) & (execution["Ext10dp99"]>=2)] # & (((execution["DAY"]>=1) & (execution["DAY"]<=10)) | ((execution["DAY"]>=25) & (execution["DAY"]<=31)))]  
    # & (planning["D1Close"]>=1) , & (planning["MONTH(Q)"] < 3)
    return planning, execution