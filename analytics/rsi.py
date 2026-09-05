import pandas as pd

# Calculo de los reversal points del rsi para las graficas
def calculation_Rsi(timeframes): 
    timeframes = timeframes[0:3].copy()
    lag = [250, 750, 1500]
    timeframes_aux = []
    cont = 0
    for df in timeframes:
        df_filtered = df[df.index > df.index[0]+pd.Timedelta(days=lag[cont])]
        timeframes_aux.append(df_filtered)
        cont = cont + 1
    return timeframes_aux