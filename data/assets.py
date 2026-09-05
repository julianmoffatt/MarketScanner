import pandas as pd
import yfinance as yf
import numpy as np
import time
from data.database import *

class Assets:
    sp500 = ["MMM","AOS","ABT","ABBV","ACN","ADBE","AMD","AES","AFL","A","APD","AKAM","ALK","ALB","ARE","ALGN","ALLE","LNT","ALL","GOOGL","MO","AMZN","AMCR","AEE","AAL","AEP","AXP","AIG","AMT","AWK","AMP","AME","AMGN","APH","ADI","AON","APA","AAPL","AMAT","APTV","ACGL","ADM","ANET","AJG","AIZ","T","ATO","ADSK","ADP","AZO","AVB","AVY","AXON","BKR","BALL","BAC","BBWI","BAX","BDX","BBY","BIO","TECH","BIIB","BLK","BX","BA","BK","BWA","BSX","BMY","AVGO","BR","BRO","CHRW","CDNS","CZR","CPT","CPB","COF","CAH","KMX","CCL","CARR","CAT","CBOE","CBRE","CDW","CE","COR","CNC","CNP","CF","CRL","SCHW","CHTR","CVX","CMG","CB","CHD","CI","CINF","CTAS","CSCO","C","CFG","CLX","CME","CMS","KO","CTSH","CL","CMCSA","CAG","COP","ED","STZ","CEG","COO","CPRT","GLW","CTVA","CSGP","COST","CTRA","CRWD","CCI","CSX","CMI","CVS","DHI","DHR","DRI","DVA","DECK","DE","DAL","DVN","DXCM","FANG","DLR","DG","DLTR","D","DPZ","DOV","DOW","DTE","DUK","DD","EMN","ETN","EBAY","ECL","EIX","EW","EA","ELV","LLY","EMR","ENPH","ETR","EOG","EPAM","EQT","EFX","EQIX","EQR","ESS","EL","EG","EVRG","ES","EXC","EXPE","EXPD","EXR","XOM","FFIV","FDS","FICO","FAST","FRT","FDX","FIS","FITB","FSLR","FE","FI","FMC","F","FTNT","FTV","FOXA","FOX","BEN","FCX","GRMN","IT","GE","GEHC","GEV","GEN","GNRC","GD","GIS","GM","GPC","GILD","GPN","GL","GDDY","GS","HAL","HIG","HAS","HCA","DOC","HSIC","HSY","HES","HPE","HLT","HOLX","HD","HON","HRL","HST","HWM","HPQ","HUBB","HUM","HBAN","HII","IBM","IEX","IDXX","ITW","INCY","IR","PODD","INTC","ICE","IFF","IP","IPG","INTU","ISRG","IVZ","INVH","IQV","IRM","JBHT","JBL","JKHY","J","JNJ","JCI","JPM","JNPR","K","KVUE","KDP","KEY","KEYS","KMB","KIM","KMI","KKR","KLAC","KHC","KR","LHX","LH","LRCX","LW","LVS","LDOS","LEN","LII","LLY","LIN","LYV","LKQ","LMT","L","LOW","LULU","LYB","MTB","MRO","MPC","MKTX","MAR","MMC","MLM","MAS","MA","MTCH","MKC","MCD","MCK","MDT","MRK","META","MET","MTD","MGM","MCHP","MU","MSFT","MAA","MRNA","MHK","MOH","TAP","MDLZ","MPWR","MNST","MCO","MS","MOS","MSI","MSCI","NDAQ","NTAP","NFLX","NEM","NWSA","NWS","NEE","NKE","NI","NDSN","NSC","NTRS","NOC","NCLH","NRG","NUE","NVDA","NVR","NXPI","ORLY","OXY","ODFL","OMC","ON","OKE","ORCL","OTIS","PCAR","PKG","PLTR","PANW","PARA","PH","PAYX","PAYC","PYPL","PNR","PEP","PFE","PCG","PM","PSX","PNW","PXD","PNC","POOL","PPG","PPL","PFG","PG","PGR","PLD","PRU","PEG","PTC","PSA","PHM","QRVO","PWR","QCOM","DGX","RL","RJF","RTX","O","REG","REGN","RF","RSG","RMD","RVTY","ROK","ROL","ROP","ROST","RCL","SPGI","CRM","SBAC","SLB","STX","SRE","NOW","SHW","SPG","SWKS","SJM","SW","SNA","SOLV","SO","LUV","SWK","SBUX","STT","STLD","STE","SYK","SYF","SNPS","SYY","TMUS","TROW","TTWO","TPR","TRGP","TGT","TEL","TDY","TFX","TER","TSLA","TXN","TXT","TMO","TJX","TSCO","TT","TDG","TRV","TRMB","TFC","TYL","TSN","USB","UBER","UDR","ULTA","UNP","UAL","UPS","URI","UNH","UHS","VLO","VTR","VLTO","VRSN","VRSK","VZ","VRTX","VFC","VTRS","VICI","V","VST","VMC","WRB","GWW","WAB","WBA","WMT","DIS","WBD","WM","WAT","WEC","WFC","WELL","WST","WDC","WY","WSM","WMB","WTW","WYNN","XEL","XYL","YUM","ZBRA","ZBH","ZION","ZTS"]
    nasdaq = ["ASML", "KLAC", "LRCX", "MCHP", "MPWR", "ENTG", "OLED", "AMKR", "COHR", "MRVL", "SWKS", "QRVO", "AMBA", "DIOD", "DDOG", "MDB", "ZS", "CRWD", "NET", "OKTA", "DOCU", "BILL", "ROKU", "TTD", "APP", "MANH", "PCTY", "PAYC", "GWRE", "HUBS", "APPN", "SMAR", "APPF", "REGN", "MRNA", "SRPT", "NBIX", "BPMC", "CRSP", "ALNY", "IONS", "EXEL", "ARWR", "ACAD", "JAZZ", "LGND", "PRGO", "ETSY", "PINS", "CELH", "CVNA", "ABNB", "DASH", "FIVE", "WING", "CHWY", "LULU", "MARA", "RIOT", "ENPH", "FSLR", "LPLA", "IBKR", "MKTX", "ILMN", "LYFT", "WIX", "EPAM", "GLOB", "CSGP", "EXLS", "ASTS", "COIN", "HOOD", "SOFI", "PLTR", "AFRM", "UPST", "CLSK", "CIFR", "HUT", "IREN", "SNOW", "AI", "PATH", "U", "S", "GTLB", "ESTC", "SMAR", "ARM", "ALAB", "SMCI", "RIVN", "LCID", "RKLB", "JOBY", "ACHR", "VKTX", "RXRX", "BEAM", "EDIT", "NTLA", "SEDG", "RUN", "ARRY", "CHPT", "ONON", "CAVA", "RDDT", "BMBL", "IOT", "FOUR", "PAYO", "APP", "APLD", "GRAB", "TEM", "SYM"]
    japan = ["TM","SONY","HMC","MUFG","SMFG","MFG","NMR","NTTYY","KDDIY","SFTBY","NTDOY"]
    china = ["BABA", "JD", "PDD", "BIDU", "TCEHY", "NTES", "BILI", "NIO", "XPEV", "LI", "BYDDY", "TME", "WB", "VIPS", "YMM", "DADA", "MNSO", "ZTO", "BEKE", "HTHT", "EDU", "TAL", "RLX", "QFIN", "LU", "KC", "TUYA"]
    europe = ["SIE.DE", "SAP.DE", "AIR.PA", "ALV.DE", "MUV2.DE", "BAYN.DE", "BMWG.DE", "VOW3.DE", "MBG.DE", "DTE.DE", "DBK.DE", "BAS.DE", "EOAN.DE", "RWE.DE", "HEN3.DE", "MRK.DE", "FRE.DE", "FME.DE", "IFX.DE", "ZAL.DE", "P911.DE", "PAH3.DE", "CON.DE", "SHL.DE", "QIA.DE", "BEI.DE", "1COV.DE", "MTX.DE", "OR.PA", "MC.PA", "RMS.PA", "BNP.PA", "ACA.PA", "CS.PA", "KER.PA", "DSY.PA", "CAP.PA", "SU.PA", "AI.PA", "EL.PA", "TTE.PA", "SAF.PA", "ENGI.PA", "STM.PA", "PUB.PA", "HO.PA", "ATO.PA", "VIE.PA", "LR.PA", "ASML.AS", "ADYEN.AS", "ASMI.AS", "BESI.AS", "HEIA.AS", "PHIA.AS", "NN.AS", "ABN.AS", "INGA.AS", "RAND.AS", "WKL.AS", "PRX.AS", "UMG.AS", "MT.AS", "AKZA.AS", "AZN.L", "SHEL.L", "BP.L", "HSBA.L", "GSK.L", "ULVR.L", "RIO.L", "AAL.L", "BT.L", "VOD.L", "LSEG.L", "BA.L", "REL.L", "DGE.L", "GLEN.L", "BARC.L", "NWG.L", "STAN.L", "PRU.L", "AV.L", "NG.L", "SMIN.L", "RR.L", "III.L", "EXPN.L", "AUTO.L", "HLMA.L", "CRH.L", "BATS.L", "IMB.L", "CPG.L", "FERG.L", "WPP.L", "NESN.SW", "ROG.SW", "NOVN.SW", "ABBN.SW", "ZURN.SW", "LONN.SW", "SREN.SW", "UBSG.SW", "SIKA.SW", "CFR.SW", "GIVN.SW", "HOLN.SW", "SCMN.SW", "LOGN.SW", "TEMN.SW", "CSGN.SW", "SAN.MC", "BBVA.MC", "ITX.MC", "IBE.MC", "REP.MC", "TEF.MC", "CABK.MC", "AMS.MC", "FER.MC", "AENA.MC", "GRF.MC", "ANA.MC", "COL.MC", "MAP.MC", "ENI.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "LDO.MI", "RACE.MI", "STLAM.MI", "PIRC.MI", "TEN.MI", "MONC.MI", "AMP.MI", "PRY.MI", "BAMI.MI", "ERICB.ST", "VOLVA.ST", "ATCOA.ST", "SAND.ST", "ESSITY.ST", "NDA-SE.ST", "SEB-A.ST", "SKF-B.ST", "EVO.ST", "HEXAB.ST", "SWMA.ST", "INVE-B.ST", "NOVO-B.CO", "MAERSK-B.CO", "ORSTED.CO", "DSV.CO", "CARL-B.CO", "DEMANT.CO", "COLO-B.CO", "NOKIA.HE", "KNEBV.HE", "UPM.HE", "STERV.HE", "FORTUM.HE", "EQNR.OL", "DNB.OL", "AKER.OL", "MOWI.OL", "TEL.OL", "UCB.BR", "SOLB.BR", "KBC.BR", "ABI.BR", "COFB.BR", "RYA.IR", "A5G.IR", "CRH.IR"]
    crypto = ["BTC-USD", "ETH-USD", "SOL-USD", "LINK-USD", "BNB-USD"]
    commodities = ["GC=F", "SI=F", "CL=F", "PL=F", "PA=F"]
    forex = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X"]
    hyperliquid = ["BTC-USD", "ETH-USD","NVDA", "TSLA", "MU", "GOOGL", "PLTR", "INTC", "AAPL", "AMZN", "AMD", "MSFT", "NFLX", "META", "ORCL", "BABA", "GC=F", "SI=F"]
    mysymbols = ["^GSPC", "ASTS", "RKLB", "IREN", "MU", "NVDA", "GOOGL", "AAPL", "AMZN", "AMD", "MSFT", "NFLX", "META", "ORCL", "INTC", "TSLA", "NVO", "BABA", "BIDU", "JD", "GC=F", "SI=F", "CL=F", "BTC-USD", "ETH-USD"]

    def __init__(self):
        pass

    @classmethod
    def getAssets(cls, name):
        universes = {"sp500":cls.sp500,"nasdaq":cls.nasdaq,"japan":cls.japan,"china":cls.china,"europe":cls.europe,"crypto":cls.crypto,"commodities":cls.commodities,"forex":cls.forex,"hyperliquid":cls.hyperliquid,"mysymbols":cls.mysymbols}
        if name == "all":
            return list(dict.fromkeys(cls.sp500 + cls.nasdaq + cls.japan + cls.china + cls.europe + cls.commodities + cls.crypto + cls.forex))
        return universes.get(name, [])

    @staticmethod
    def loadTimeframes(symbol):
        try:
            database = Database()
            url = database.symbol_url() + symbol + ".csv"
            daily = pd.read_csv(url, index_col=0)
            if "Ticker" in daily.columns or "Price" in daily.columns:
                daily = pd.read_csv(url, header=[0, 1], index_col=0, parse_dates=True)
                daily.columns = daily.columns.get_level_values(0)
        except FileNotFoundError:
            daily = yf.download(symbol, interval="1d", auto_adjust=False, progress=False, period="max") #parametrizo por eficiencia para algunos metodos?
        if isinstance(daily.columns, pd.MultiIndex):
            daily.columns = daily.columns.get_level_values(0)

        daily = daily[daily["Low"] > 0]
        daily.index = pd.to_datetime(daily.index, utc=True)
        daily.index = daily.index.normalize()
        daily = daily.sort_index()
        last_date = daily.index.max()
        cutoff_date = last_date - pd.DateOffset(years=40) #me quedo los ultimos 40 años
        daily = daily.loc[daily.index >= cutoff_date].copy()
        weekly = daily.resample('W-MON', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
        monthly = daily.resample('MS', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
        quarterly = monthly.resample('QS', label='left', closed='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
        yearly = quarterly.resample('YS').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'})
        database.save_csv(daily, symbol)
        return [daily, weekly, monthly, quarterly, yearly]

    @classmethod
    def loadStatistics(cls, timeframes):
        ema_number = [10,20,50,200]
        ema_name = ["ema10", "ema20", "ema50", "ema200"] 
        new_data = []
        for df in timeframes:
            df = df.copy()
            if not df.empty:
                df["Last_Close"] = df["Close"].shift(1)
                df["Next_Close"] = df["Close"].shift(-1)
                df["type"] = np.where(df["Close"] > df["Last_Close"], "Green", "Red")
                df["rsi"] = cls.rsi_tradingview(df['Close'])
                df["Return"] = round(((df["Close"] / df["Last_Close"])-1)*100,1)
                df["Return_NextDay"] = round(((df["Close"] / df["Next_Close"])-1)*100,1)
                df["Volatility"] = np.abs(1-(df["High"]/df["Low"]))*100
                df["Upper_wick"] = df["High"] - df[["Open", "Close"]].max(axis=1)
                df["Lower_wick"] = df[["Open", "Close"]].min(axis=1) - df["Low"]
                for i, ema in enumerate(ema_name):
                    df[ema] = df["Close"].ewm(span=ema_number[i], adjust=False).mean()
                    df["extension_"+ema] = ((df["Close"] - df[ema]) / df[ema])*100
                    df["extension_low_"+ema] = ((df["Low"] - df[ema]) / df[ema])*100
                    df["extension_high_"+ema] = ((df["High"] - df[ema]) / df[ema])*100
            new_data.append(df)
        return new_data

    @classmethod
    def last_X_years(cls, timeframes, num_years):
        aux_timeframes = []
        for df_aux in timeframes:
            df = df_aux.copy()
            df.index = pd.to_datetime(df.index)   
            last_date = df.index.max()
            cutoff_date = last_date - pd.DateOffset(years=num_years)
            timeframe = df.loc[df.index >= cutoff_date].copy()
            aux_timeframes.append(timeframe)
        return aux_timeframes

    @classmethod
    def rsi_tradingview(cls, prices, period=14): #calculation of rsi
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @classmethod
    def getCurrentPos(cls, symbols, asset):
        pos = 0
        for symbol in symbols:
            if symbol == asset:
                return pos
            pos = pos + 1
        return 0

    @staticmethod
    def loadLowerTimeframes(symbol, prepost):
        database = Database()
        load = True
        try:
            database = Database()
            url = database.symbol_url() + symbol + "LT.csv"
            data_1H = pd.read_csv(url, index_col=0)
            if "Ticker" in data_1H.columns or "Price" in data_1H.columns:
                data_1H = pd.read_csv(url, header=[0, 1], index_col=0, parse_dates=True)
                data_1H.columns = data_1H.columns.get_level_values(0)
        except FileNotFoundError:
            data_1H = yf.download(tickers = symbol, period = "max", interval = "1h", prepost = prepost)
            load = False
        if isinstance(data_1H.columns, pd.MultiIndex):
            data_1H.columns = data_1H.columns.get_level_values(0)
        if not load:
            database.save_csv(data_1H, symbol+"LT")
        data_1H.index = pd.to_datetime(data_1H.index)
        if data_1H.index.tz is None:
            data_1H.index = data_1H.index.tz_localize('UTC')
        else:
            data_1H.index = data_1H.index.tz_convert('UTC')
        data_4H = data_1H.resample('4h', label='left').agg({'Open': 'first','High': 'max','Low': 'min','Close': 'last','Volume': 'sum'})
        data_4H.dropna(inplace=True)
        return [data_1H, data_4H]

    @classmethod
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

    @classmethod
    def getDataframesDatabase(cls):
        symbols = cls.getAssets("all")
        for symbol in symbols:
            time.sleep(1) 
            name = "excels/dataframe_symbol/" + symbol + ".csv"
            try:
                stock_daily = pd.read_csv(name, index_col=0, parse_dates=True, date_format='%Y-%m-%d')
            except FileNotFoundError:
                stock_daily = yf.download(symbol, interval="1d", auto_adjust=False, progress=False, period="max") #parametrizo por eficiencia para algunos metodos?
                if isinstance(stock_daily.columns, pd.MultiIndex):
                    stock_daily.columns = stock_daily.columns.get_level_values(0)
                stock_daily.to_csv(name)
        print("Symbols dataframes saved")


    @staticmethod
    def name_sustitution(name):
        if name == "^GSPC":
            return "SP500"
        elif name == "GC=F":
            return "GOLD"
        elif name == "SI=F":
            return "SILVER"
        elif name == "CL=F":
            return "OIL"
        elif name == "BTC-USD":
            return "BTC"
        elif name == "ETH-USD":
            return "ETH"
        else:
            return name


    @staticmethod
    def getWeightVol(x_timeframe, higher_timeframe):
        matrix_weights = [[0.5, 0.65, 0.75, 0.9], [0.75, 1, 1.25], [0.15, 0.2], [0.25]]
        return matrix_weights[x_timeframe][higher_timeframe]

    @classmethod
    def calculate_volatility(cls, close, window=20, p_low=0.20, p_high=0.80):
        """Volatilidad realizada: rolling std (%) de log-returns, con bandas de clamp por percentil."""
        log_returns = np.log(close / close.shift(1))
        vol = log_returns.rolling(window).std() * 100
        vol_low = vol.quantile(p_low)
        vol_high = vol.quantile(p_high)
        return vol, vol_low, vol_high

    

