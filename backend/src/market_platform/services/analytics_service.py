# services/analytics_service.py
from ..analysis import rsi, mean_reversion_extension_to_mean, mean_reversion_time_away, deviations_candle, deviation_ema_trend, strikes_candles, strikes_trend, quarter_patterns
from .. import pipeline

def get_mean_reversion_extension_to_mean_lt(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 1)
    return mean_reversion_extension_to_mean.compute_lowertimeframe(df)

def get_mean_reversion_extension_to_mean_ht(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return mean_reversion_extension_to_mean.compute_highertimeframe(df)

def get_mean_reversion_extension_to_mean_macro(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return mean_reversion_extension_to_mean.compute_macrotimeframe(df)

def get_mean_reversion_time_away_ht(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return mean_reversion_time_away.compute_highertimeframe(df)

def get_mean_reversion_time_away_macro(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return mean_reversion_time_away.compute_macro(df)

def get_deviations_candle(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return deviations_candle.compute(df)

def get_deviation_ema_trend(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return deviation_ema_trend.compute(df)

def get_strikes_candles(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return strikes_candles.compute(df)

def get_trend_duration(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return strikes_trend.compute(df)

def get_rsi(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return rsi.compute(df)

def get_quarter_patterns(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return quarter_patterns.compute(df)


"""
# tab-1: Daily chart
def get_daily_chart(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return df.to_dict(orient="records")

# tab-2: Weekly chart
def get_weekly_chart(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return df.to_dict(orient="records")

# tab-3: Monthly chart
def get_monthly_chart(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return df.to_dict(orient="records")

# tab-4: extensiones ema 10/20
def get_ema_extension_10_20(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return df.to_dict(orient="records")

# tab-5: extensions ema 50/200
def get_ema_extension_50_200(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return df.to_dict(orient="records")

# tab-9: Flips probability (Daily)
def get_flips_probability_daily(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return flips_calculation.compute(df)

# tab-209: Flips probability (Monthly)
def get_flips_probability_monthly(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return flips_calculation.compute(df)

# tab-210: Flips probability (Quarterly)
def get_flips_probability_quarterly(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return flips_calculation.compute(df)

# tab-18: Detalle Flips probability (Daily)
def get_flips_probability_daily_detail(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return flips_calculation.compute(df)

# tab-14: Last Flip
def get_last_flip(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return flips_calculation.compute(df)

# tab-6: Deviations
def get_deviations(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return deviations.compute(df)

# tab-102: Deviations (Trends)
def get_deviations_trends(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return deviations.compute(df)

# tab-7: Candle Strikes
def get_candle_strikes(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return strikes_candles.compute(df)

# tab-8: RSI distribution
def get_rsi_distribution(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return rsi.compute(df)

# tab-23: extension ema 1h/4h
def get_ema_extension_1h_4h(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return df.to_dict(orient="records")

# tab-24: Mean reversion (LowerTimeframe)
def get_mean_reversion_lower_timeframe(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return retest_bands.compute(df)

# tab-13: Mean reversion (HigherTimeframe)
def get_mean_reversion_higher_timeframe(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return retest_bands.compute(df)

# tab-17: OPEN GAPS
def get_open_gaps(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return gaps.compute(df)

# tab-20: Flips y LastFlip vs Returns%
def get_flips_last_flip_vs_returns(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return flips_calculation.compute(df)

# tab-21: Last flip vs PEAKs
def get_last_flip_vs_peaks(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return peaks.compute(df)

# tab-15: Peaks distribution
def get_peaks_distribution(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return peaks.compute(df)

# tab-16: Gaps distribution
def get_gaps_distribution(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return gaps.compute(df)

# tab-26: Volatility distribution
def get_volatility_distribution(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return statistics_calculations.compute(df)

# tab-27: Return distribution
def get_return_distribution(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return statistics_calculations.compute(df)

# tab-25: Cash.S.
def get_cash_session(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return cash_session_direction.compute(df)

# tab-100: Quater.Patterns
def get_quarter_patterns(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return quarter_patterns.compute(df)

# tab-12: Screnner Extension
def get_screener_extension(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return screener_ema_extensions.compute(df)

# tab-104: Candles patterns
def get_candle_patterns(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return candle_patterns.compute(df)

# tab-404: Backtesting
def get_backtesting(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return backtesting.compute(df)

# tab-405: EMA Trends
def get_ema_trends(ticker: str) -> dict:
    df = pipeline.get_processed_data(ticker)
    return trend_strikes.compute(df)
"""