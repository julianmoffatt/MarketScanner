import yfinance as yf
import pandas as pd
import numpy as np
import time

def getSymbols():
    symbols = ["^GSPC", "GOOGL", "ASTS", "IREN", "MU", "RKLB", "INTC", "NVDA", "MSFT", "AAPL", "AMZN", "META", "TSLA", "BABA", "BIDU", "JD", "ADBE", "NVO", "MSTR", "BTC-USD", "ETH-USD"]
    return symbols

def get_sp500_symbols():
    symbols = ["MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","AKAM","ALK","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN","APH","ADI","AON","APA","AAPL","AMAT","APTV","ACGL","ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC","BBWI","BAX","BDX","BBY","BIO","TECH","BIIB","BLK","BX","BA","BK","BWA","BSX","BMY","AVGO","BR","BRO","CHRW","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CAT","CBOE","CBRE","CDW","CE","COR","CNC","CNP","CF","CRL","SCHW","CHTR","CVX","CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CTVA","CSGP","COST","CTRA","CRWD","CCI","CSX","CMI","CVS","DHI","DHR","DRI","DVA","DAY","DECK","DE","DAL","DVN","DXCM","FANG","DLR","DG","DLTR","D","DPZ","DOV","DOW","DTE","DUK","DD","EMN","ETN","EBAY","ECL","EIX","EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR","ESS","EL","EG","EVRG","ES","EXC","EXPE","EXPD","EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB","FSLR","FE","FI","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL","GDDY","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF","IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","JNPR","K","KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KKR","KLAC","KHC","KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN","LII","LLY","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PLTR","PANW","PARA","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PXD","PNC","POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM","DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV","SWK","SBUX","STT","STLD","STE","SYK","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VFC","VTRS","VICI","V","VST","VMC","WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST","WDC","WY","WSM","WMB","WTW","WYNN","XEL","XYL","YUM","ZBRA","ZBH","ZION","ZTS"]
    return symbols

def get_crypto_symbols():
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "BNB-USD"]
    return symbols

def get_hyperliquid_symbols():
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "BNB-USD", "NVDA", "TSLA", "MU", "GOOGL", "PLTR", "MSTR", "INTC", "AAPL", "AMZN", "AMD", "MSFT", "NFLX", "META", "ORCL", "BABA", "GC=F", "SI=F"]
    return symbols



def valid_stock(stock):
    symbols = getSymbols()
    if stock in symbols:
        return True
    else:
        return False    

def getCurrentStockPos(stock):
    symbols = getSymbols()
    pos = 0
    for symbol in symbols:
        if symbol == stock:
            return pos
        pos = pos + 1
    return -1

def getDataStock(ticker):
    time.sleep(2)
    stock_daily = yf.download(ticker, interval="1d", auto_adjust=False, progress=False, period="max")
    if isinstance(stock_daily.columns, pd.MultiIndex):
        stock_daily.columns = stock_daily.columns.get_level_values(0)
    #stock_daily = stock_daily.loc[pd.to_datetime("2016-01-01"):]
    # FORCE UTC ONCE — DO NOT REMOVE
    stock_daily.index = pd.to_datetime(stock_daily.index, utc=True)
    # Optional but recommended: normalize to 00:00 UTC
    stock_daily.index = stock_daily.index.normalize()
    stock_daily = stock_daily.sort_index()
    # Monday-based weeks (unchanged)
    stock_weekly = stock_daily.resample('W-MON', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    # Month START (TradingView monthly open logic)
    stock_monthly = stock_daily.resample('MS', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    return [stock_daily, stock_weekly, stock_monthly]

def rsi_tradingview(prices, period=14): #calculation of rsi
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def preparingData(data):
    for df in data:
        df["Last_Close"] = df["Close"].shift(1)
        df["type"] = np.where(df["Close"] > df["Last_Close"], "Green", "Red")
        df["rsi"] = rsi_tradingview(df['Close'])
        df["Return"] = df["Close"] / df["Last_Close"]
        df["Volatility"] = abs(1-(df["High"]/df["Low"]))
        df['Volatility_Rolling'] = df["Volatility"].ewm(alpha=1/14, adjust=False).mean()
        #df["Upper_wick"] = df["High"] - df[["Open", "Close"]].max(axis=1)
        #df["Lower_wick"] = df[["Open", "Close"]].min(axis=1) - df["Low"]
    return data

def create_hightimeframes(timeframes, lower_timeframe):
    df_quarters = timeframes[2].resample('QS', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    df_years = df_quarters.resample('YS').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
    if lower_timeframe == "daily":
        timeframes.append(df_quarters)
        return timeframes
    elif lower_timeframe == "weekly":
        timeframes = timeframes[1:]
        timeframes.append(df_quarters)
        timeframes.append(df_years)
        return timeframes


def last_year(data):
    # 1. Aseguramos que el índice sea Datetime antes de operar
    df = data[0].copy()
    df.index = pd.to_datetime(df.index)    
    last_date = df.index.max()
    cutoff_date = last_date - pd.DateOffset(years=1)
    daily_returns = df.loc[df.index >= cutoff_date].copy()    
    return daily_returns


def last_X_years(data, num_years):
    timeframes = []
    for df_aux in data:
        df = df_aux.copy()
        print(2)
        df.index = pd.to_datetime(df.index)  
        print(3)  
        last_date = df.index.max()
        print(4)
        cutoff_date = last_date - pd.DateOffset(years=num_years)
        print(5)
        timeframe = df.loc[df.index >= cutoff_date].copy()
        timeframes.append(timeframe)
    print("Last X years obtained")
    return timeframes


def import_csv(name):
    try:
        df = pd.read_csv(name + ".csv", index_col=0)
        print("Importando", name)
        print(df)
        df.index.name = None
        return df
    except:
        df = pd.DataFrame()
        return df
    