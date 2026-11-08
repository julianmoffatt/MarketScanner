"""
Rutas HTTP de los screeners: una tabla con una fila por valor de un universo (config.yaml).
Capa delgada: solo traduce HTTP <-> Python, no calcula nada aqui.
Cada screener nuevo es una ruta mas bajo /screeners/<nombre>/{universe}.
"""
from typing import Literal, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from ...services import screener_service


class MeanReversionScreener_Row(BaseModel):
    ticker: str
    daily_type: Optional[str] = None
    daily_strike: Optional[float] = None
    daily_strike_percentile: Optional[float] = None
    weekly_type: Optional[str] = None
    weekly_strike: Optional[float] = None
    weekly_strike_percentile: Optional[float] = None
    monthly_type: Optional[str] = None
    monthly_strike: Optional[float] = None
    monthly_strike_percentile: Optional[float] = None
    daily_time_away_ema10: Optional[float] = None
    daily_time_away_ema10_percentile: Optional[float] = None
    daily_time_away_ema20: Optional[float] = None
    daily_time_away_ema20_percentile: Optional[float] = None
    daily_time_away_ema50: Optional[float] = None
    daily_time_away_ema50_percentile: Optional[float] = None
    weekly_time_away_ema10: Optional[float] = None
    weekly_time_away_ema10_percentile: Optional[float] = None
    daily_extension_ema10_percentile: Optional[float] = None
    daily_extension_ema20_percentile: Optional[float] = None
    weekly_extension_ema10_percentile: Optional[float] = None
    weekly_extension_ema20_percentile: Optional[float] = None
    trend_ema10_side: Optional[float] = None
    trend_ema10_duration: Optional[float] = None
    trend_ema10_percentile: Optional[float] = None
    trend_ema20_side: Optional[float] = None
    trend_ema20_duration: Optional[float] = None
    trend_ema20_percentile: Optional[float] = None

class MeanReversionScreener_Response(BaseModel):
    universe: str
    rows: list[MeanReversionScreener_Row]


class FlipsScreener_Block(BaseModel):
    timeframe: str
    occurrences: int
    distribution: list[float]
    last_flip_p50: Optional[float] = None
    current_flips: Optional[int] = None
    current_bucket: Optional[int] = None

class FlipsScreener_Row(BaseModel):
    ticker: str
    blocks: list[FlipsScreener_Block]

class FlipsScreener_Response(BaseModel):
    universe: str
    lower: str
    buckets: dict[str, list[str]]
    rows: list[FlipsScreener_Row]
    missing: list[str]


router = APIRouter(prefix="/screeners", tags=["screeners"])

@router.get("/mean_reversion/{universe}", response_model=MeanReversionScreener_Response)
def get_mean_reversion_screener(universe: str):
    rows = screener_service.get_mean_reversion_screener(universe)
    return {"universe": universe, "rows": rows}


@router.get("/flips/{universe}", response_model=FlipsScreener_Response)
def get_flips_screener(universe: str, lower: Literal["daily", "monthly"] = Query("daily")):
    return screener_service.get_flips_screener(universe, lower)
