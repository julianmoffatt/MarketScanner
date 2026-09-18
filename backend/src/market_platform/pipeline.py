# pipeline.py
from backend.src.market_platform.data import ingestion, preprocessing, storage
from backend.src.market_platform.features import build_features
from backend.src.market_platform.utils.config import load_config
import time

#lectura de simbolos de archivo yaml
config = load_config()
timeframe_base = ["daily", "1h", "1m"] # t: que timeframes con que base de estas se necesitan
premarket_postmarket = [False, True, True]
timeframe_names = [["daily", "weekly", "monthly", "quarterly", "yearly"], ["1h", "4h"], ["1min", "5min", "15min", "30min"]]


def createTimeframes_pipeline(symbol, t):
    #ingestion
    df_base = ingestion.loadBaseTimeframe(symbol, timeframe_base[t], premarket_postmarket[t])
    #preprocessing
    timeframes_aux = preprocessing.preprocessing(df_base, t)
    #build features
    timeframes = build_features.build_features(timeframes_aux)
    #save csv's
    for i, timeframe_name in enumerate(timeframe_names[t]):
        storage.save_csv(timeframes[i], symbol + "_" + timeframe_name, "processed")
    return timeframes


def processedTimeframes(symbol, t):
    timeframes = []
    for t, name in enumerate(timeframe_names[t]):
        df = storage.import_csv(symbol + "_" + name, "processed")
        if df is False:
            return createTimeframes_pipeline(symbol, t)
        timeframes.append(df)
    return timeframes


#cargar database antes de que me pidan los simbolos concretos
def loadDatabase():
    symbols =  config["universes"]["mysymbols"]
    for symbol in symbols:
        time.sleep(0.25) 
        createTimeframes_pipeline(symbol, 0)