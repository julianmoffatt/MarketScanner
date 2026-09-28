# api/schemas.py
from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

RowT = TypeVar("RowT", bound=BaseModel)

# ---- Base compartida por todas las respuestas de analytics ----
class TickerBaseResponse(BaseModel):
    ticker: str

# ---- Piezas genéricas reutilizables (para cualquier pantalla futura) ----
class TableResponse(TickerBaseResponse, Generic[RowT]):
    """Para pantallas simples: una sola tabla de filas, sin multi-timeframe."""
    rows: list[RowT]

class TimeframePanel(BaseModel, Generic[RowT]):
    """Un panel identificado por timeframe, con sus propias filas."""
    timeframe: str
    rows: list[RowT]

class Timeframes_Percentiles_and_CurrentValue_Panel(TimeframePanel[RowT], Generic[RowT]):
    current_value: float
    p05: float
    p95: float
    percentile: float

class TimeframeEmaPanel(TimeframePanel[RowT], Generic[RowT]):
    """Un panel identificado por timeframe y por ema, con sus propias filas."""
    ema_period: int

class TimeframesEma_Percentiles_and_CurrentValue_Panel(TimeframeEmaPanel[RowT], Generic[RowT]):
    current_value: float
    p05: float
    p95: float
    percentile: float

class TimeframeTypePanel(TimeframePanel[RowT], Generic[RowT]):
    """Un panel identificado por timeframe y por tipo de vela (Green/Red), con sus propias filas."""
    type: str

class TimeframesType_Percentiles_and_CurrentValue_Panel(TimeframeTypePanel[RowT], Generic[RowT]):
    current_value: float
    p05: float
    p95: float
    percentile: float

class TimeframeEmaTypePanel(TimeframeEmaPanel[RowT], Generic[RowT]):
    """Un panel identificado por timeframe, ema y tipo de patrón (Absorption/Rejection)."""
    type: str

class TimeframesEmaType_Percentiles_and_CurrentValue_Panel(TimeframeEmaTypePanel[RowT], Generic[RowT]):
    current_value: float
    p05: float
    p95: float
    percentile: float

# ---- Pantalla 1: Extensión a la media ----

class MeanReversion_ExtensionToMean_Row(BaseModel):
    date: str
    extension_to_mean: float

class MeanReversion_ExtensionToMean_Response(TickerBaseResponse):
    panels: list[TimeframesEma_Percentiles_and_CurrentValue_Panel[MeanReversion_ExtensionToMean_Row]]


# ---- Pantalla 2: Tiempo alejado de la media ----

class MeanReversion_TimeAway_Row(BaseModel):
    date: str
    time_away: int

class MeanReversion_TimeAway_Panel(TimeframesEma_Percentiles_and_CurrentValue_Panel[MeanReversion_TimeAway_Row]):
    median: float
    p25: float
    max: float

class MeanReversion_TimeAway_Response(TickerBaseResponse):
    panels: list[MeanReversion_TimeAway_Panel]


# ---- Pantalla 3: Desviación de velas (MAE) ----

class DeviationCandle_Row(BaseModel):
    date: str
    deviation: float

class DeviationCandle_Response(TickerBaseResponse):
    panels: list[TimeframesType_Percentiles_and_CurrentValue_Panel[DeviationCandle_Row]]


# ---- Pantalla 4: Deviation EMA Trend (Absorption/Rejection) ----

class DeviationEmaTrend_Row(BaseModel):
    date: str
    deviation: float
    forward_return_1: Optional[float] = None
    forward_return_3: Optional[float] = None
    forward_return_5: Optional[float] = None

class DeviationEmaTrend_Response(TickerBaseResponse):
    panels: list[TimeframesEmaType_Percentiles_and_CurrentValue_Panel[DeviationEmaTrend_Row]]


# ---- Pantalla 5: Rachas de velas (Strikes) ----

class StrikeStreak_Row(BaseModel):
    length: int
    count: int
    pct: float

class StrikeStreaks_Panel(BaseModel):
    timeframe: str
    type: str
    current_length: int
    is_current: bool
    rows: list[StrikeStreak_Row]

class StrikeStreaks_Response(TickerBaseResponse):
    panels: list[StrikeStreaks_Panel]


# ---- Pantalla 6: Duracion de tendencia (dias por encima/debajo de la EMA) ----

class TrendDuration_Row(BaseModel):
    date: str
    num_days: int

class TrendDuration_Panel(BaseModel):
    timeframe: str
    type: str
    is_current: bool
    current_value: int
    p25: float
    median: float
    p75: float
    p95: float
    percentile: float
    rows: list[TrendDuration_Row]

class TrendDuration_Response(TickerBaseResponse):
    panels: list[TrendDuration_Panel]

# Pantalla RSI
class RSI_Row(BaseModel):
    date: str
    rsi_value: float

class RSI_Panel(Timeframes_Percentiles_and_CurrentValue_Panel[RSI_Row]):
    pass

class RSI_Response(TickerBaseResponse):
    panels: list[RSI_Panel]


# ---- Pantalla: Combinaciones de color mensuales por trimestre ----

class QuarterPattern_Row(BaseModel):
    pattern: str
    count: int
    pct: float
    is_possible: bool

class QuarterPattern_Panel(BaseModel):
    quarter: str
    is_current: bool
    current_prefix: str
    occurrences: int
    still_possible: int
    rows: list[QuarterPattern_Row]

class QuarterPattern_Response(TickerBaseResponse):
    panels: list[QuarterPattern_Panel]


# ---- Pantalla: Machine Learning - Training ----

class ML_Metrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float

class ML_FeatureImportance_Row(BaseModel):
    feature: str
    importance: float

class ML_Calibration_Point(BaseModel):
    prob_pred: float
    prob_true: float

class ML_Confusion_Matrix(BaseModel):
    labels: list[str]
    matrix: list[list[int]]

class ML_Roc_Point(BaseModel):
    fpr: float
    tpr: float

class ML_Roc(BaseModel):
    auc: float
    points: list[ML_Roc_Point]

class ML_Training_Panel(BaseModel):
    model_name: str
    metrics: ML_Metrics
    train_metrics: ML_Metrics
    baseline_accuracy: float
    confusion: ML_Confusion_Matrix
    roc: ML_Roc
    top_features: list[ML_FeatureImportance_Row]
    calibration: list[ML_Calibration_Point]
    n_train: int
    n_test: int

class ML_Training_Response(TickerBaseResponse):
    panels: list[ML_Training_Panel]


# ---- Pantalla: Machine Learning - Prediction ----

class ML_Prediction_Panel(BaseModel):
    model_name: str
    predicted_type: str
    probability_green: float
    probability_red: float

class ML_Prediction_Response(TickerBaseResponse):
    as_of_date: str
    panels: list[ML_Prediction_Panel]


