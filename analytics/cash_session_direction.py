from data.assets import *
from data.data import *
import pandas as pd

def calculation_cashsession_dynamics():
    assets = Assets()
    rows = []
    symbols = assets.getAssets("mysymbols")
    for symbol in symbols:
        print("CASH SESSION", symbol)
        try:
            data = assets.loadTimeframes(symbol)
            data_HT = data[0].copy()
            data = assets.loadLowerTimeframes(symbol, False)
            data_LT = data[0].copy()
            data_MicroT = getDataStock_MT(symbol)

            if not data_HT.empty and not data_LT.empty and not data_MicroT.empty:
                nameField = ["Return1H", "type1H", "Return15m", "type15m"]
                timeframes = ["1h","15m"]
                x = 0
                row = {}
                for df in [data_LT, data_MicroT]:
                    data_HT = data_HT[data_HT.index >= df.index[0]]  
                    df = df[df.index >= data_HT.index[0]]           
                    data_HT = data_HT[1:].copy()
                    data_HT[nameField[0+x]] = data_HT["Return"]
                    data_HT[nameField[1+x]] = data_HT["type"]    
                    for i in range(0, len(data_HT)):
                        aux = data_LT[data_LT.index.date == data_HT.index[i].date()]
                        idx = data_HT.index[i]
                        if not aux.empty:
                            data_HT.loc[idx, nameField[0+x]] = ((aux["Close"].iloc[0]/aux["Open"].iloc[0])-1) * 100
                            if data_HT.loc[idx, nameField[0+x]] >= 0:
                                data_HT.loc[idx, nameField[1+x]] = "Green"
                            else:
                                data_HT.loc[idx, nameField[1+x]] = "Red"
                    print("pre-filtro", len(data_HT))
                    data_HT = data_HT[abs((data_HT["Close"]/data_HT["Open"])-1) >= 0.0025]
                    print("filtro completado", len(data_HT))
                    Green = data_HT[(data_HT[nameField[1+x]]) == "Green"]
                    Green_Green = Green[Green["type"] == "Green"]
                    Green_Green_Beyond = Green_Green[Green_Green["Return"] > Green_Green[nameField[0+x]]]
                    Green_Red= Green[Green["type"] == "Red"]
                    Red = data_HT[data_HT[nameField[1+x]] == "Red"] 
                    Red_Green = Red[Red["type"] == "Green"]
                    Red_Red = Red[Red["type"] == "Red"]
                    Red_Red_Beyond = Red_Red[Red_Red["Return"] < Red_Red[nameField[0+x]]]
                    row["symbol"] = assets.name_sustitution(symbol)
                    name = "NumGreen" + timeframes[x]
                    row[name] = len(Green)
                    name = "Green " + timeframes[x] + " (GreenDay)"
                    row[name] = round(len(Green_Green)/len(Green),2)
                    name = "Green " + timeframes[x] + " (RedDay)"
                    row[name] = round(len(Green_Red)/len(Green),2)
                    name = "Day higher vs" + timeframes[x] + " (Green)"
                    row[name] = round(len(Green_Green_Beyond)/len(Green_Green),2)
                    name = "NumRed" + timeframes[x]
                    row[name] = len(Red)
                    name = "Red " + timeframes[x] + " (RedDay)"
                    row[name] = round(len(Red_Red)/len(Red),2)
                    name = "Red " + timeframes[x] + " (GreenDay)"
                    row[name] = round(len(Red_Green)/len(Red),2)
                    name = "Day lower vs " + timeframes[x]
                    row[name] = round(len(Red_Red_Beyond)/len(Red_Red),2)
                    x += 1
                print(row)
                rows.append(row)
        except Exception as e:
            print(e)
            break    
        #pillar distintos timeframes y filtrar quedandome a partir del primer dia de data
        # montar las probabilidades segun el primer close de 15min, 30min, 1h, 2h (opcional)
    df = pd.DataFrame(rows)
    database = Database()
    database.save_csv(df, "cash_session_open_momentum")
    return df