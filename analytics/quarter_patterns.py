from data.assets import *
import pandas as pd

def calculation_patterns():
    try:
        assets = Assets()
        all_patterns = ['GGG','GGR','GRG','GRR','RRR','RRG','RGR','RGG']
        green_patterns = ['GGG', 'GGR', 'GRG', 'GRR']
        red_patterns   = ['RRR', 'RRG', 'RGR', 'RGG']
        gg_patterns = ['GGG', 'GGR']
        gr_patterns = ['GRG', 'GRR']
        rr_patterns = ['RRR', 'RRG']
        rg_patterns = ['RGR', 'RGG']
        symbols = assets.getAssets("mysymbols")
        data = []
        for symbol in symbols:
            data_aux = assets.loadStatistics(assets.loadTimeframes(symbol))
            monthly = data_aux[2].copy()
            monthly['year']       = monthly.index.year
            monthly['quarter']    = monthly.index.quarter
            monthly['month_of_q'] = monthly.index.month - (monthly['quarter'] - 1) * 3
            results = []
            for (year, quarter), group in monthly.groupby(['year', 'quarter']):
                group = group.sort_values('month_of_q')
                if len(group) != 3:
                    continue
                pattern = ''.join(group['type'].map({'Green': 'G', 'Red': 'R'}).tolist())
                results.append({
                    'symbol':  symbol,
                    'year':    year,
                    'quarter': quarter,
                    'pattern': pattern,
                })
            df_patterns = pd.DataFrame(results)
            if not df_patterns.empty:
                pattern_counts = (df_patterns.groupby('pattern').size().reindex(all_patterns, fill_value=0))
                total = pattern_counts.sum()
                pattern_formatted = pattern_counts.apply(lambda x: f"{round(x/total*100)}% ({x})" if total > 0 else "0% (0)")
                row = {'symbol': symbol} | pattern_formatted.to_dict()
                data.append(row)
                total_green = pattern_counts[green_patterns].sum()
                total_red   = pattern_counts[red_patterns].sum()
                pattern_green = pattern_counts[green_patterns].apply(lambda x: f"{round(x/total_green*100)}% ({x})" if total_green > 0 else "0% (0)")
                pattern_red   = pattern_counts[red_patterns].apply(lambda x: f"{round(x/total_red*100)}% ({x})"   if total_red   > 0 else "0% (0)")
                row = {'symbol': symbol} | pattern_green.to_dict() | pattern_red.to_dict()
                data.append(row)
                total_gg = pattern_counts[gg_patterns].sum()
                total_gr = pattern_counts[gr_patterns].sum()
                total_rr = pattern_counts[rr_patterns].sum()
                total_rg = pattern_counts[rg_patterns].sum()                
                pattern_gg = pattern_counts[gg_patterns].apply(lambda x: f"{round(x/total_gg*100)}% ({x})" if total_gg > 0 else "0% (0)")
                pattern_gr = pattern_counts[gr_patterns].apply(lambda x: f"{round(x/total_gr*100)}% ({x})" if total_gr > 0 else "0% (0)")
                pattern_rr = pattern_counts[rr_patterns].apply(lambda x: f"{round(x/total_rr*100)}% ({x})" if total_rr > 0 else "0% (0)")
                pattern_rg = pattern_counts[rg_patterns].apply(lambda x: f"{round(x/total_rg*100)}% ({x})" if total_rg > 0 else "0% (0)")
                row = {'symbol': symbol} | pattern_gg.to_dict() | pattern_gr.to_dict() | pattern_rr.to_dict() | pattern_rg.to_dict()
                data.append(row)
        return pd.DataFrame(data)
    except Exception as e:
        print(e)