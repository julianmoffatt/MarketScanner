import pandas as pd
from data import *
#kucoin = ccxt.kucoinfutures({'enableRateLimit': True,'timeout': 90000})
        
def symbol_name_sustitution(name):
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
        










