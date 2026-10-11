# services/analytics_service.py
from ..analysis import home_statistics, rsi, mean_reversion_extension_to_mean, mean_reversion_time_away, deviations_candle, deviation_ema_trend, strikes_candles, strikes_trend, quarter_patterns, returns
from .. import pipeline

def get_home_statistics(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return home_statistics.compute(df)

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

def get_z_score_return_month(ticker: str) -> dict:
    df = pipeline.processedTimeframes(ticker, 0)
    return returns.compute(df)
