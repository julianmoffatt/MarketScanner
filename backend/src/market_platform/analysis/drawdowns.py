from backend.src.market_platform.data.ingestion import *
import pandas as pd

def calculation_drawdowns_ema_10_20(N=5, min_days_above=5, vol_k=0.2, min_occurrences=100, neutral_threshold = 0.01):
    assets = Assets()
    symbols = assets.getAssets("all")
    symbols = list(dict.fromkeys(symbols))
    rows = []

    for symbol in symbols:
        print("EMA DRAWDOWN:", symbol)
        try:
            data_aux = assets.loadStatistics(assets.loadTimeframes(symbol))
            daily = data_aux[0].copy()
            vol, vol_p20, vol_p80 = Assets.calculate_volatility(daily["Close"])
            daily["vol"] = vol / 100
            vol_p20 = vol_p20 / 100
            vol_p80 = vol_p80 / 100
            daily = daily.iloc[20:].reset_index(drop=False)

            row = {"Symbol": assets.name_sustitution(symbol)}
            row["Vol Avg%"] = round(daily["vol"].mean() * 100, 3)

            variants = [("ema10", "EMA10C", False), ("ema10", "EMA10L", True)]
            for ema_col, label, use_low in variants:
                buckets = [[] for _ in range(N + 1)]  # D0 + D1..DN
                tol_i = np.clip(daily["vol"].iloc[0] * vol_k, vol_p20 * vol_k, vol_p80 * vol_k)
                above = daily["Close"].iloc[0] >= daily[ema_col].iloc[0] * (1 - tol_i)
                days_above = 1 if above else 0
                tols_used = []

                for i in range(1, len(daily) - N):
                    tol_i = np.clip(daily["vol"].iloc[i] * vol_k, vol_p20 * vol_k, vol_p80 * vol_k)
                    now_above = daily["Close"].iloc[i] >= daily[ema_col].iloc[i] * (1 - tol_i)
                    if days_above >= min_days_above and not now_above:
                        ref = daily[ema_col].iloc[i] * (1 - (tol_i*1.1))
                        tols_used.append(tol_i * 100)
                        price_d0 = daily["Low"].iloc[i] if use_low else daily["Close"].iloc[i]
                        buckets[0].append(((price_d0 - ref) / ref) * 100)
                        for d in range(N):
                            price_d = daily["Low"].iloc[i + 1 + d] if use_low else daily["Close"].iloc[i + 1 + d]
                            buckets[d + 1].append(((price_d - ref) / ref) * 100)
                    days_above = days_above + 1 if now_above else 0
                    above = now_above

                row[f"{label} Occurrences"] = f"{len(buckets[0])}n"
                row[f"{label} Avg Tol%"] = round(np.mean(tols_used), 3) if tols_used else 0
                row[f"{label} D0 Avg"] = round(np.mean(buckets[0]), 2) if buckets[0] else 0
                row[f"{label} D0 Med"] = round(np.median(buckets[0]), 2) if buckets[0] else 0
                for d in range(N):
                    row[f"{label} D{d+1} Avg"] = round(np.mean(buckets[d+1]), 2) if buckets[d+1] else 0
                    row[f"{label} D{d+1} Med"] = round(np.median(buckets[d+1]), 2) if buckets[d+1] else 0

            # EMA10T: low toca 1x tolerancia, referencia en ese nivel, D0 = close del día
            buckets_t = [[] for _ in range(N + 1)]
            tols_used_t = []
            tol_i = np.clip(daily["vol"].iloc[0] * vol_k, vol_p20 * vol_k, vol_p80 * vol_k)
            days_above_t = 1 if daily["Close"].iloc[0] >= daily["ema10"].iloc[0] * (1 - tol_i) else 0
            for i in range(1, len(daily) - N):
                tol_i = np.clip(daily["vol"].iloc[i] * vol_k, vol_p20 * vol_k, vol_p80 * vol_k)
                ema_thresh = daily["ema10"].iloc[i] * (1 - tol_i)
                ref_t = daily["ema10"].iloc[i] * (1 - tol_i)
                low_touches = daily["Low"].iloc[i] < ref_t
                now_above = daily["Close"].iloc[i] >= ema_thresh
                if days_above_t >= min_days_above and low_touches:
                    tols_used_t.append(tol_i * 100)
                    buckets_t[0].append(((daily["Close"].iloc[i] - ref_t) / ref_t) * 100)
                    for d in range(N):
                        buckets_t[d + 1].append(((daily["Close"].iloc[i + 1 + d] - ref_t) / ref_t) * 100)
                days_above_t = days_above_t + 1 if now_above else 0

            row["EMA10T Occurrences"] = f"{len(buckets_t[0])}n"
            row["EMA10T Avg Tol%"] = round(np.mean(tols_used_t), 3) if tols_used_t else 0
            row["EMA10T D0 Avg"] = round(np.mean(buckets_t[0]), 2) if buckets_t[0] else 0
            row["EMA10T D0 Med"] = round(np.median(buckets_t[0]), 2) if buckets_t[0] else 0
            for d in range(N):
                row[f"EMA10T D{d+1} Avg"] = round(np.mean(buckets_t[d+1]), 2) if buckets_t[d+1] else 0
                row[f"EMA10T D{d+1} Med"] = round(np.median(buckets_t[d+1]), 2) if buckets_t[d+1] else 0
            rows.append(row)
        except Exception as e:
            print(f"Error {symbol}: {e}")

    df = pd.DataFrame(rows)

    def parse_count(val):
        try:
            return int(str(val).replace("n", ""))
        except:
            return 0

    neutral_threshold = 0.1

    def build_summary_rows(group_df, prefix, N, neutral_threshold):
        r_g = {"Symbol": f"{prefix} G"}
        r_r = {"Symbol": f"{prefix} R"}
        for label in ["EMA10C", "EMA10L", "EMA10T"]:
            occ_col = f"{label} Occurrences"
            eligible = group_df
            counts = []
            for day_label in ["D0"] + [f"D{d+1}" for d in range(N)]:
                col_avg = f"{label} {day_label} Avg"
                col_med = f"{label} {day_label} Med"
                for r in [r_g, r_r]:
                    r.setdefault(col_avg, "")
                    r.setdefault(col_med, "")

                vals_avg = eligible[col_avg]
                nn_avg = vals_avg[abs(vals_avg) > neutral_threshold]
                g_a = (nn_avg > neutral_threshold).sum(); r_a = (nn_avg < -neutral_threshold).sum()
                d_a = g_a + r_a; counts.append(int(d_a))
                r_g[col_avg] = f"{round((g_a/d_a)*100,1)}%" if d_a > 0 else "0%"
                r_r[col_avg] = f"{round((r_a/d_a)*100,1)}%" if d_a > 0 else "0%"

                vals_med = eligible[col_med]
                nn_med = vals_med[abs(vals_med) > neutral_threshold]
                g_m = (nn_med > neutral_threshold).sum(); r_m = (nn_med < -neutral_threshold).sum()
                d_m = g_m + r_m
                r_g[col_med] = f"{round((g_m/d_m)*100,1)}%" if d_m > 0 else "0%"
                r_r[col_med] = f"{round((r_m/d_m)*100,1)}%" if d_m > 0 else "0%"

            for r in [r_g, r_r]:
                r[occ_col] = f"{len(eligible)}n"
                r[f"{label} Avg Tol%"] = ""
        return [r_g, r_r]

    # filtrar por min_occurrences primero, luego dividir por beta
    df_assets = df[df["Vol Avg%"].notna() & (df["Vol Avg%"] > 0)].copy()
    df_assets = df_assets[df_assets["EMA10C Occurrences"].apply(parse_count) >= min_occurrences]
    t25 = df_assets["Vol Avg%"].quantile(0.2)
    t75 = df_assets["Vol Avg%"].quantile(0.8)
    low_vol  = df_assets[df_assets["Vol Avg%"] <= t25]
    mid_vol  = df_assets[(df_assets["Vol Avg%"] > t25) & (df_assets["Vol Avg%"] <= t75)]
    high_vol = df_assets[df_assets["Vol Avg%"] > t75]

    summary_rows = (
        build_summary_rows(df_assets, "ALL", N, neutral_threshold) +
        build_summary_rows(high_vol,  "HIGH", N, neutral_threshold) +
        build_summary_rows(mid_vol,   "MID",  N, neutral_threshold) +
        build_summary_rows(low_vol,   "LOW",  N, neutral_threshold)
    )

    df_summary = pd.DataFrame(summary_rows)
    df = pd.concat([df_summary, df], ignore_index=True)

    database = Database()
    database.save_csv(df, "drawdowns_ema10y20")
    print(df)
    return df