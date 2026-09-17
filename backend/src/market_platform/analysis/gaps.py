import pandas as pd
import numpy as np
from backend.src.market_platform.data.ingestion import Assets

def calculation_closing_gaps(symbol):
    try:
        assets = Assets()
        df = assets.loadTimeframes(symbol)
        df = df[0].copy()
        gaps = []
        for i in range (1, len(df)):
            # LOGICA QUE DETECTA CIERRE DE GAPS
            for gap in gaps:
                if gap["Status"] == "Open":
                    if (df["Low"].iloc[i] <= gap["GapLow"]) and (df["High"].iloc[i] >= gap["GapHigh"]): #AÑADIR MARGEN DE ERROR (NO ES PERFECTO UN CIERRE DE GAP)
                        gap["GapFilled"] = True
                        gap["Status"] = "Closed"
                        gap["DaysOpen"] = (df.index[i] - gap["Date"]).days
                    elif (df["Low"].iloc[i] >= gap["GapLow"]) and (df["High"].iloc[i] <= gap["GapHigh"]):
                        gap["GapFilled"] = True
                        gap["GapHigh"] = round(df["High"].iloc[i], 2)
                        gap["GapLow"] = round(df["Low"].iloc[i], 2)
                        if gap["FirstRetest"] == False: 
                            gap["FirstRetest"] == True 
                            gap["DaysOpen"] = (df.index[i] - gap["Date"]).days
                    elif (df["Low"].iloc[i] <= gap["GapLow"]) and (df["High"].iloc[i] > gap["GapLow"]) and (df["High"].iloc[i] > gap["GapHigh"]):
                        gap["GapHigh"] = round(df["High"].iloc[i], 2)
                        gap["GapFilled"] = True
                        if gap["FirstRetest"] == False: 
                            gap["FirstRetest"] == True 
                            gap["DaysOpen"] = (df.index[i] - gap["Date"]).days
                    elif (df["High"].iloc[i] >= gap["GapHigh"]) and (df["Low"].iloc[i] > gap["GapLow"]) and (df["Low"].iloc[i] < gap["GapHigh"]):
                        gap["GapLow"] = round(df["Low"].iloc[i], 2)
                        gap["GapFilled"] = True
                        if gap["FirstRetest"] == False: 
                            gap["FirstRetest"] == True 
                            gap["DaysOpen"] = (df.index[i] - gap["Date"]).days

            # LOGICA QUE DETECTA Y GUARDA UN GAP
            gap_high, gap_low = 0, 0
            if (df["Low"].iloc[i] > df["Close"].iloc[i-1]) or (df["High"].iloc[i] < df["Close"].iloc[i-1]):
                gapSize = 0
                if (df["Low"].iloc[i] > df["Close"].iloc[i-1]):
                    gapSize = round((round(df["Low"].iloc[i] / df["Close"].iloc[i-1], 3)-1) * 100, 1)
                    gap_high = round(df["Low"].iloc[i], 2)
                    gap_low = round(df["Close"].iloc[i-1], 2)
                else:
                    gapSize = round(abs(round(df["High"].iloc[i] / df["Close"].iloc[i-1], 3) - 1) * 100, 1)
                    gap_high = round(df["Close"].iloc[i-1], 2)
                    gap_low = round(df["High"].iloc[i], 2)
                if (gap_high/gap_low) >= 1.0075:
                    gaps.append({"Date": df.index[i], "Status": "Open", "DaysOpen": -1, "GapSize": round(gapSize,1), "GapHigh": gap_high, "GapLow": gap_low, "GapFilled": False, "FirstRetest": False})
        for gap in gaps:
            if gap["Status"] == "Open":
                gap["DaysOpen"] = (df.index[-1] - gap["Date"]).days
        df_gaps = pd.DataFrame(gaps) 
        name = "excels/gaps/" + symbol + ".csv"
        df_gaps.to_csv(name)
        return df_gaps 
    except Exception as e:
        print("The exception was:", e)


def calculation_closing_gaps_all_symbols():
    assets = Assets()
    database = database()
    symbols = assets.getAssets("mysymbols")
    gaps_study = pd.DataFrame(columns=["Symbol", "Total Gaps", "Closed Ratio", "Days Open p20", "Days Open p50", "Days Open p80"])

    for symbol in symbols:
        if symbol != "BTC-USD" and symbol != "ETH-USD":
            print("Processing gaps", symbol)
            df = calculation_closing_gaps(symbol)
            df = df[df["GapSize"] >= 0.5] # filtrar por una fraccion de la volatilidad de los ultimos 10 años por ejemplo (dinamico al activo)
            totalGaps = len(df)
            closedGaps = df[df["Status"] == "Closed"]
            percentil_10 = round(closedGaps["DaysOpen"].quantile(0.20), 2)
            percentil_50 = round(closedGaps["DaysOpen"].quantile(0.50), 2)
            percentil_90 = round(closedGaps["DaysOpen"].quantile(0.80), 2)
            gaps_study.loc[len(gaps_study)] = [assets.name_sustitution(symbol), totalGaps, round(len(closedGaps)/totalGaps, 2), percentil_10, percentil_50, percentil_90] 
            print("END GAPS", symbol)
    database.save_csv(gaps_study, "gaps", "gaps_all_symbols")
    return gaps_study