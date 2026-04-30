import yfinance as yf
import pandas as pd
import numpy as np
import time
import random

def getSymbols():
    symbols = ["^GSPC", "ASTS", "IREN", "MU", "NVDA", "GOOGL", "AAPL", "AMZN", "AMD", "MSFT", "NFLX", "META", "ORCL", "INTC", "TSLA", "BABA", "BIDU", "JD", "PLTR",  "MSTR", "GC=F", "SI=F", "CL=F", "BTC-USD", "ETH-USD"]
    return symbols

def get_hyperliquid_symbols():
    symbols = ["BTC-USD", "ETH-USD","NVDA", "TSLA", "MU", "GOOGL", "PLTR", "INTC", "AAPL", "AMZN", "AMD", "MSFT", "NFLX", "META", "ORCL", "BABA", "GC=F", "SI=F"]
    return symbols

def getCurrentStockPos(stock):
    symbols = getSymbols()
    pos = 0
    for symbol in symbols:
        if symbol == stock:
            return pos
        pos = pos + 1
    return 0

def get_sp500_symbols():
    symbols = ["MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","AKAM","ALK","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN","APH","ADI","AON","APA","AAPL","AMAT","APTV","ACGL","ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC","BBWI","BAX","BDX","BBY","BIO","TECH","BIIB","BLK","BX","BA","BK","BWA","BSX","BMY","AVGO","BR","BRO","CHRW","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CAT","CBOE","CBRE","CDW","CE","COR","CNC","CNP","CF","CRL","SCHW","CHTR","CVX","CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CTVA","CSGP","COST","CTRA","CRWD","CCI","CSX","CMI","CVS","DHI","DHR","DRI","DVA","DAY","DECK","DE","DAL","DVN","DXCM","FANG","DLR","DG","DLTR","D","DPZ","DOV","DOW","DTE","DUK","DD","EMN","ETN","EBAY","ECL","EIX","EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR","ESS","EL","EG","EVRG","ES","EXC","EXPE","EXPD","EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB","FSLR","FE","FI","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL","GDDY","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF","IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","JNPR","K","KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KKR","KLAC","KHC","KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN","LII","LLY","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PLTR","PANW","PARA","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PXD","PNC","POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM","DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV","SWK","SBUX","STT","STLD","STE","SYK","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VFC","VTRS","VICI","V","VST","VMC","WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST","WDC","WY","WSM","WMB","WTW","WYNN","XEL","XYL","YUM","ZBRA","ZBH","ZION","ZTS"]
    return symbols

def get_crypto_symbols():
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "BNB-USD"]
    return symbols

def valid_stock(stock):
    symbols = getSymbols()
    if stock in symbols:
        return True
    else:
        return False    
    
    
def getDataframesDatabase():
    symbols = getSymbols()
    for symbol in symbols:
        time.sleep(2) 
        name = "excels/dataframe_symbol/" + symbol + ".csv"
        try:
            stock_daily = pd.read_csv(name, index_col=0, parse_dates=True, date_format='%Y-%m-%d')
        except FileNotFoundError:
            stock_daily = yf.download(symbol, interval="1d", auto_adjust=False, progress=False, period="max") #parametrizo por eficiencia para algunos metodos?
            if isinstance(stock_daily.columns, pd.MultiIndex):
                stock_daily.columns = stock_daily.columns.get_level_values(0)
            stock_daily.to_csv(name)
    print("Symbols dataframes saved")


def getDataStock(symbol):  
    name = "excels/dataframe_symbol/" + symbol + ".csv"
    load = True
    try:
        stock_daily = pd.read_csv(name, index_col=0)
        if "Ticker" in stock_daily.columns or "Price" in stock_daily.columns:
            stock_daily = pd.read_csv(name, header=[0, 1], index_col=0, parse_dates=True)
            stock_daily.columns = stock_daily.columns.get_level_values(0)
    except FileNotFoundError:
        stock_daily = yf.download(symbol, interval="1d", auto_adjust=False, progress=False, period="max") #parametrizo por eficiencia para algunos metodos?
        load = False
    if isinstance(stock_daily.columns, pd.MultiIndex):
        stock_daily.columns = stock_daily.columns.get_level_values(0)
    
    stock_daily = stock_daily[stock_daily["Low"] > 0]

    if not load:
        stock_daily.to_csv(name)
    stock_daily.index = pd.to_datetime(stock_daily.index, utc=True)
    stock_daily.index = stock_daily.index.normalize()
    stock_daily = stock_daily.sort_index()
    stock_weekly = stock_daily.resample('W-MON', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    stock_monthly = stock_daily.resample('MS', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    return [stock_daily, stock_weekly, stock_monthly]


def getDataStock_LT(symbol):
    time.sleep(2) 
    name = "excels/dataframe_symbol_LT/" + symbol + ".csv"
    load = True
    try:
        data_1H = pd.read_csv(name, index_col=0)
        if "Ticker" in data_1H.columns or "Price" in data_1H.columns:
            data_1H = pd.read_csv(name, header=[0, 1], index_col=0, parse_dates=True)
            data_1H.columns = data_1H.columns.get_level_values(0)
    except FileNotFoundError:
        data_1H = yf.download(tickers = symbol, period = "max", interval = "1h", prepost = True)
        load = False
    if isinstance(data_1H.columns, pd.MultiIndex):
        data_1H.columns = data_1H.columns.get_level_values(0)
    if not load:
        data_1H.to_csv(name)
    data_1H.index = pd.to_datetime(data_1H.index)
    if data_1H.index.tz is None:
        data_1H.index = data_1H.index.tz_localize('UTC')
    else:
        data_1H.index = data_1H.index.tz_convert('UTC')
    data_4H = data_1H.resample('4h', label='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
    data_4H.dropna(inplace=True)
    return [data_1H, data_4H]


def getDataStock_MT(symbol):
    data_MicroT = yf.download(symbol, interval="15m", auto_adjust=False, progress=False, period="max") 
    if isinstance(data_MicroT.columns, pd.MultiIndex):
        data_MicroT.columns = data_MicroT.columns.get_level_values(0)
    data_MicroT.index = pd.to_datetime(data_MicroT.index)
    if data_MicroT.index.tz is None:
        data_MicroT.index = data_MicroT.index.tz_localize('UTC')
    else:
        data_MicroT.index = data_MicroT.index.tz_convert('UTC')
    return data_MicroT


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
        if not df.empty:
            df["Last_Close"] = df["Close"].shift(1)
            df["type"] = np.where(df["Close"] > df["Last_Close"], "Green", "Red")
            df["rsi"] = rsi_tradingview(df['Close'])
            df["Return"] = round(((df["Close"] / df["Last_Close"])-1)*100,1)
            df["Volatility"] = abs(1-(df["High"]/df["Low"]))
            df['Volatility_Rolling'] = df["Volatility"].ewm(alpha=1/14, adjust=False).mean()
            df["EMA_10"] = df["Close"].ewm(span=10, adjust=False).mean()
            df["EMA_25"] = df["Close"].ewm(span=10, adjust=False).mean()
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
        timeframes.append(df_quarters)
        timeframes.append(df_years)
        return timeframes
    

def merge_partialweek(df, df_partialweek):
    row_data = {'Open':   df_partialweek['Open'].iloc[0],'High':   df_partialweek['High'].max(),'Low':    df_partialweek['Low'].min(),'Close':  df_partialweek['Close'].iloc[-1],'Volume': df_partialweek['Volume'].sum()}
    row_data["Volatility"] = abs(1-(df["High"]/df["Low"]))
    row_data['Volatility_Rolling'] = abs(1-(df["High"]/df["Low"]))
    weekly_candle = pd.DataFrame([row_data], index=[df_partialweek.index[0]])
    df_merged = pd.concat([weekly_candle, df], axis=0).sort_index()
    return df_merged


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
        df.index = pd.to_datetime(df.index)   
        last_date = df.index.max()
        cutoff_date = last_date - pd.DateOffset(years=num_years)
        timeframe = df.loc[df.index >= cutoff_date].copy()
        timeframes.append(timeframe)
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
    