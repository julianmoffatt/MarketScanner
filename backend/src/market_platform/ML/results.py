from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class TrainingResult:
    model_name: str
    params: dict
    metrics: dict
    feature_importance: Optional[dict] = None
    n_train: int = 0
    n_test: int = 0
    trained_at: datetime = field(default_factory=datetime.now)

@dataclass
class PredictionResult:
    model_name: str
    predictions: list
    predicted_at: datetime = field(default_factory=datetime.now)