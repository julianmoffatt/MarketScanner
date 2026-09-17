from backend.src.market_platform.data.ingestion import *
from backend.src.market_platform.data.data import *
import pandas as pd

def calculation_open_momentum(timeframes):
    try:
        daily = timeframes[0].copy()
        daily['month_period'] = daily.index.tz_localize(None).to_period('M')        
        monthly = timeframes[2].copy()
        monthly['month_period'] = monthly.index.tz_localize(None).to_period('M')        
        start_period = monthly['month_period'].iloc[0]
        end_period = monthly['month_period'].iloc[-1]
        daily = daily[(daily['month_period'] >= start_period) & (daily['month_period'] <= end_period)]
        daily['Return_Decimal'] = daily['Return'] / 100 if daily['Return'].max() > 1 else daily['Return']

        for k in (1, 3, 5):
            firstdays_df = daily.groupby('month_period').head(k)
            prod_retornos = firstdays_df.groupby('month_period')['Return_Decimal'].apply(lambda x: (1 + x).prod() - 1)
            prod_retornos_pct = prod_retornos * 100            
            name = 'Added_Return_' + str(k)
            monthly[name] = monthly['month_period'].map(prod_retornos_pct)            
        return monthly 
    except Exception as e:
        print(e)


def calculation_open_momentum_all_symbols():
    assets = Assets()
    symbols = assets.getAssets("hyperliquid")
    target_days = [1, 3, 5]
    sigmas = [1.0, 1.5, 2]
    columns = ["Asset"]
    rows = []
    for d in target_days:
        for s in sigmas:
            columns.append("ADDED DAY"+str(d)+"-std("+str(s)+")")
            columns.append("Ocurr (day "+str(d)+"-"+str(s)+")")
    
    columns.append("Avg-Corr")

    for symbol in symbols:
        average = []
        print(symbol)
        try:
            row = [symbol]
            data = assets.loadTimeframes(symbol)
            df = calculation_open_momentum(data)
            for row_idx, day in enumerate(target_days, start=1):
                current_col = f"Added_Return_{day}"            
                df_clean = df[["Return", current_col]].dropna()
                for col_idx, sigma in enumerate(sigmas, start=1):
                    if len(df_clean) >= 2:
                        mean_k = df_clean[current_col].mean()
                        std_k = df_clean[current_col].std()
                        df_filtered = df_clean[(df_clean[current_col] - mean_k).abs() >= (sigma * std_k)]
                        r_value = 0.0
                        if len(df_filtered) > 1:
                            r_value = df_filtered["Return"].corr(df_filtered[current_col])
                            row.append(round(r_value, 2))
                            average.append(r_value)
                            row.append(len(df_filtered))
                        else:
                            r_value = "-"
                    else:
                        r_value = "-"
                    if r_value == "-":
                        row.append(np.nan)
                        row.append(np.nan)
            aux_df = pd.DataFrame(average)
            row.append(round(float(aux_df.mean().item()), 2))
            rows.append(row)
        except Exception as e:
            print(e)
    try:
        df_ordered = pd.DataFrame(rows, columns=columns)
        df_ordered = df_ordered.sort_values(by="Avg-Corr", ascending=False)
        return df_ordered
    except Exception as e:
        print(e)