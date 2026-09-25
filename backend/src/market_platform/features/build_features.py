import numpy as np

def build_features(timeframes):
    ema_number = [10,20,50,200]
    ema_name = ["ema10", "ema20", "ema50", "ema200"] 
    new_data = []
    for df in timeframes:
        if not df.empty:
            df["last_close"] = df["Close"].shift(1)
            df["next_close"] = df["Close"].shift(-1)
            df["type"] = np.where(df["Close"] > df["last_close"], "Green", "Red")
            df["rsi"] = rsi_tradingview(df['Close'])
            df["return"] = round(((df["Close"] / df["last_close"])-1)*100,1)
            df["return_next_day"] = round(((df["Close"] / df["next_close"])-1)*100,1)
            df["volatility"] = np.abs(1-(df["High"]/df["Low"]))*100
            df["upper_wick"] = (df["High"] - df[["Open", "Close"]].max(axis=1)) / df["Close"] * 100
            df["lower_wick"] = (df[["Open", "Close"]].min(axis=1) - df["Low"]) / df["Close"] * 100
            for i, ema in enumerate(ema_name):
                df[ema] = df["Close"].ewm(span=ema_number[i], adjust=False).mean()
                df["extension_"+ema] = ((df["Close"] - df[ema]) / df[ema])*100
                df["extension_low_"+ema] = ((df["Low"] - df[ema]) / df[ema])*100
                df["extension_high_"+ema] = ((df["High"] - df[ema]) / df[ema])*100
        new_data.append(df)
    return new_data


def rsi_tradingview(prices, period=14): #calculation of rsi
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def getCurrentPos(symbols, asset):
    pos = 0
    for symbol in symbols:
        if symbol == asset:
            return pos
        pos = pos + 1
    return 0

def getWeightVol(x_timeframe, higher_timeframe):
    matrix_weights = [[0.5, 0.65, 0.75, 0.9], [0.75, 1, 1.25], [0.15, 0.2], [0.25]]
    return matrix_weights[x_timeframe][higher_timeframe]

def calculate_volatility(close, window=20, p_low=0.20, p_high=0.80):
    """Volatilidad realizada: rolling std (%) de log-returns, con bandas de clamp por percentil."""
    log_returns = np.log(close / close.shift(1))
    vol = log_returns.rolling(window).std() * 100
    vol_low = vol.quantile(p_low)
    vol_high = vol.quantile(p_high)
    return vol, vol_low, vol_high