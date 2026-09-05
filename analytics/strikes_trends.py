import numpy as np
import pandas as pd
from data.assets import * 

def calculation_ema_trends():
    assets = Assets()
    symbols = assets.getAssets("all")
    symbols = list(dict.fromkeys(symbols))
    rows = []
    
    for symbol in symbols:
        print("EMA DRAWDOWN:", symbol)
        try:
            data_aux = assets.loadStatistics(assets.loadTimeframes(symbol))
        except Exception as e:
            print(e)