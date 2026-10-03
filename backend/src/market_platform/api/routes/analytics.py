"""
Rutas HTTP para las estadisticas descriptivas de analysis/.
Capa delgada: solo traduce HTTP <-> Python, no calcula nada aqui.
"""
from fastapi import APIRouter, HTTPException
from ..schemas import *
from ...services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/{ticker}/home", response_model=Home_Response)
def get_home(ticker: str):
    stats = analytics_service.get_home_statistics(ticker)
    return {"ticker": ticker, **stats}


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
