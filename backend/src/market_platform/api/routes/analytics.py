"""
Rutas HTTP para las estadisticas descriptivas de analysis/.
Capa delgada: solo traduce HTTP <-> Python, no calcula nada aqui.
"""
from fastapi import APIRouter, HTTPException
from ..schemas import *
from ...services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/{ticker}/mean_reversion_extension_to_mean_lt", response_model=MeanReversion_ExtensionToMean_Response)
def get_descriptive_stats_lt(ticker: str):
    panels = analytics_service.get_mean_reversion_extension_to_mean_lt(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/mean_reversion_extension_to_mean_ht", response_model=MeanReversion_ExtensionToMean_Response)
def get_descriptive_stats_ht(ticker: str):
    panels = analytics_service.get_mean_reversion_extension_to_mean_ht(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/mean_reversion_extension_to_mean_macro", response_model=MeanReversion_ExtensionToMean_Response)
def get_descriptive_stats_macro(ticker: str):
    panels = analytics_service.get_mean_reversion_extension_to_mean_macro(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/mean_reversion_time_away_ht", response_model=MeanReversion_TimeAway_Response)
def get_time_away_ht(ticker: str):
    panels = analytics_service.get_mean_reversion_time_away_ht(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/mean_reversion_time_away_macro", response_model=MeanReversion_TimeAway_Response)
def get_time_away_macro(ticker: str):
    panels = analytics_service.get_mean_reversion_time_away_macro(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/deviations_candle", response_model=DeviationCandle_Response)
def get_deviations_candle(ticker: str):
    panels = analytics_service.get_deviations_candle(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/deviation_ema_trend", response_model=DeviationEmaTrend_Response)
def get_deviation_ema_trend(ticker: str):
    panels = analytics_service.get_deviation_ema_trend(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/strikes_candles", response_model=StrikeStreaks_Response)
def get_strikes_candles(ticker: str):
    panels = analytics_service.get_strikes_candles(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/trend_duration", response_model=TrendDuration_Response)
def get_trend_duration(ticker: str):
    panels = analytics_service.get_trend_duration(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/rsi", response_model=RSI_Response)
def get_rsi(ticker: str):
    panels = analytics_service.get_rsi(ticker)
    return {"ticker": ticker, "panels": panels}


@router.get("/{ticker}/quarter_patterns", response_model=QuarterPattern_Response)
def get_quarter_patterns(ticker: str):
    panels = analytics_service.get_quarter_patterns(ticker)
    return {"ticker": ticker, "panels": panels}

"""
# tab-1: Daily chart
@router.get("/{ticker}/daily-chart", response_model=DailyChartResponse)
def get_daily_chart(ticker: str):
    data = analytics_service.get_daily_chart(ticker)
    return DailyChartResponse(ticker=ticker, **data)


# tab-2: Weekly chart
@router.get("/{ticker}/weekly-chart", response_model=WeeklyChartResponse)
def get_weekly_chart(ticker: str):
    data = analytics_service.get_weekly_chart(ticker)
    return WeeklyChartResponse(ticker=ticker, **data)


# tab-3: Monthly chart
@router.get("/{ticker}/monthly-chart", response_model=MonthlyChartResponse)
def get_monthly_chart(ticker: str):
    data = analytics_service.get_monthly_chart(ticker)
    return MonthlyChartResponse(ticker=ticker, **data)


# tab-4: extensiones ema 10/20
@router.get("/{ticker}/ema-extension-10-20", response_model=EmaExtension1020Response)
def get_ema_extension_10_20(ticker: str):
    data = analytics_service.get_ema_extension_10_20(ticker)
    return EmaExtension1020Response(ticker=ticker, **data)


# tab-5: extensions ema 50/200
@router.get("/{ticker}/ema-extension-50-200", response_model=EmaExtension50200Response)
def get_ema_extension_50_200(ticker: str):
    data = analytics_service.get_ema_extension_50_200(ticker)
    return EmaExtension50200Response(ticker=ticker, **data)


# tab-9: Flips probability (Daily)
@router.get("/{ticker}/flips-probability-daily", response_model=FlipsProbabilityDailyResponse)
def get_flips_probability_daily(ticker: str):
    data = analytics_service.get_flips_probability_daily(ticker)
    return FlipsProbabilityDailyResponse(ticker=ticker, **data)


# tab-209: Flips probability (Monthly)
@router.get("/{ticker}/flips-probability-monthly", response_model=FlipsProbabilityMonthlyResponse)
def get_flips_probability_monthly(ticker: str):
    data = analytics_service.get_flips_probability_monthly(ticker)
    return FlipsProbabilityMonthlyResponse(ticker=ticker, **data)


# tab-210: Flips probability (Quarterly)
@router.get("/{ticker}/flips-probability-quarterly", response_model=FlipsProbabilityQuarterlyResponse)
def get_flips_probability_quarterly(ticker: str):
    data = analytics_service.get_flips_probability_quarterly(ticker)
    return FlipsProbabilityQuarterlyResponse(ticker=ticker, **data)


# tab-18: Detalle Flips probability (Daily)
@router.get("/{ticker}/flips-probability-daily-detail", response_model=FlipsProbabilityDailyDetailResponse)
def get_flips_probability_daily_detail(ticker: str):
    data = analytics_service.get_flips_probability_daily_detail(ticker)
    return FlipsProbabilityDailyDetailResponse(ticker=ticker, **data)


# tab-14: Last Flip
@router.get("/{ticker}/last-flip", response_model=LastFlipResponse)
def get_last_flip(ticker: str):
    data = analytics_service.get_last_flip(ticker)
    return LastFlipResponse(ticker=ticker, **data)


# tab-6: Deviations
@router.get("/{ticker}/deviations", response_model=DeviationsResponse)
def get_deviations(ticker: str):
    data = analytics_service.get_deviations(ticker)
    return DeviationsResponse(ticker=ticker, **data)


# tab-102: Deviations (Trends)
@router.get("/{ticker}/deviations-trends", response_model=DeviationsTrendsResponse)
def get_deviations_trends(ticker: str):
    data = analytics_service.get_deviations_trends(ticker)
    return DeviationsTrendsResponse(ticker=ticker, **data)


# tab-7: Candle Strikes
@router.get("/{ticker}/candle-strikes", response_model=CandleStrikesResponse)
def get_candle_strikes(ticker: str):
    data = analytics_service.get_candle_strikes(ticker)
    return CandleStrikesResponse(ticker=ticker, **data)


# tab-8: RSI distribution
@router.get("/{ticker}/rsi-distribution", response_model=RsiDistributionResponse)
def get_rsi_distribution(ticker: str):
    data = analytics_service.get_rsi_distribution(ticker)
    return RsiDistributionResponse(ticker=ticker, **data)


# tab-23: extension ema 1h/4h
@router.get("/{ticker}/ema-extension-1h-4h", response_model=EmaExtension1h4hResponse)
def get_ema_extension_1h_4h(ticker: str):
    data = analytics_service.get_ema_extension_1h_4h(ticker)
    return EmaExtension1h4hResponse(ticker=ticker, **data)


# tab-24: Mean reversion (LowerTimeframe)
@router.get("/{ticker}/mean-reversion-lower-timeframe", response_model=MeanReversionLowerTimeframeResponse)
def get_mean_reversion_lower_timeframe(ticker: str):
    data = analytics_service.get_mean_reversion_lower_timeframe(ticker)
    return MeanReversionLowerTimeframeResponse(ticker=ticker, **data)


# tab-13: Mean reversion (HigherTimeframe)
@router.get("/{ticker}/mean-reversion-higher-timeframe", response_model=MeanReversionHigherTimeframeResponse)
def get_mean_reversion_higher_timeframe(ticker: str):
    data = analytics_service.get_mean_reversion_higher_timeframe(ticker)
    return MeanReversionHigherTimeframeResponse(ticker=ticker, **data)


# tab-17: OPEN GAPS
@router.get("/{ticker}/open-gaps", response_model=OpenGapsResponse)
def get_open_gaps(ticker: str):
    data = analytics_service.get_open_gaps(ticker)
    return OpenGapsResponse(ticker=ticker, **data)


# tab-20: Flips y LastFlip vs Returns%
@router.get("/{ticker}/flips-last-flip-vs-returns", response_model=FlipsLastFlipVsReturnsResponse)
def get_flips_last_flip_vs_returns(ticker: str):
    data = analytics_service.get_flips_last_flip_vs_returns(ticker)
    return FlipsLastFlipVsReturnsResponse(ticker=ticker, **data)


# tab-21: Last flip vs PEAKs
@router.get("/{ticker}/last-flip-vs-peaks", response_model=LastFlipVsPeaksResponse)
def get_last_flip_vs_peaks(ticker: str):
    data = analytics_service.get_last_flip_vs_peaks(ticker)
    return LastFlipVsPeaksResponse(ticker=ticker, **data)


# tab-15: Peaks distribution
@router.get("/{ticker}/peaks-distribution", response_model=PeaksDistributionResponse)
def get_peaks_distribution(ticker: str):
    data = analytics_service.get_peaks_distribution(ticker)
    return PeaksDistributionResponse(ticker=ticker, **data)


# tab-16: Gaps distribution
@router.get("/{ticker}/gaps-distribution", response_model=GapsDistributionResponse)
def get_gaps_distribution(ticker: str):
    data = analytics_service.get_gaps_distribution(ticker)
    return GapsDistributionResponse(ticker=ticker, **data)


# tab-26: Volatility distribution
@router.get("/{ticker}/volatility-distribution", response_model=VolatilityDistributionResponse)
def get_volatility_distribution(ticker: str):
    data = analytics_service.get_volatility_distribution(ticker)
    return VolatilityDistributionResponse(ticker=ticker, **data)


# tab-27: Return distribution
@router.get("/{ticker}/return-distribution", response_model=ReturnDistributionResponse)
def get_return_distribution(ticker: str):
    data = analytics_service.get_return_distribution(ticker)
    return ReturnDistributionResponse(ticker=ticker, **data)


# tab-25: Cash.S.
@router.get("/{ticker}/cash-session", response_model=CashSessionResponse)
def get_cash_session(ticker: str):
    data = analytics_service.get_cash_session(ticker)
    return CashSessionResponse(ticker=ticker, **data)


# tab-100: Quater.Patterns
@router.get("/{ticker}/quarter-patterns", response_model=QuarterPatternsResponse)
def get_quarter_patterns(ticker: str):
    data = analytics_service.get_quarter_patterns(ticker)
    return QuarterPatternsResponse(ticker=ticker, **data)


# tab-12: Screnner Extension
@router.get("/{ticker}/screener-extension", response_model=ScreenerExtensionResponse)
def get_screener_extension(ticker: str):
    data = analytics_service.get_screener_extension(ticker)
    return ScreenerExtensionResponse(ticker=ticker, **data)


# tab-104: Candles patterns
@router.get("/{ticker}/candle-patterns", response_model=CandlePatternsResponse)
def get_candle_patterns(ticker: str):
    data = analytics_service.get_candle_patterns(ticker)
    return CandlePatternsResponse(ticker=ticker, **data)


# tab-404: Backtesting
@router.get("/{ticker}/backtesting", response_model=BacktestingResponse)
def get_backtesting(ticker: str):
    data = analytics_service.get_backtesting(ticker)
    return BacktestingResponse(ticker=ticker, **data)


# tab-405: EMA Trends
@router.get("/{ticker}/ema-trends", response_model=EmaTrendsResponse)
def get_ema_trends(ticker: str):
    data = analytics_service.get_ema_trends(ticker)
    return EmaTrendsResponse(ticker=ticker, **data)
"""