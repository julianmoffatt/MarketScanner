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
    model: object = None  # pipeline (preprocessor + clasificador) ya ajustado, para predecir sin reentrenar
    label_encoder: object = None  # LabelEncoder ajustado sobre todo y, para decodificar predicciones (0/1 -> Green/Red)
    calibration: Optional[list] = None  # reliability diagram: [{prob_pred, prob_true}, ...] por decil, sobre el conjunto out-of-fold (walk-forward)
    baseline_accuracy: Optional[float] = None  # accuracy de un DummyClassifier(most_frequent), para contextualizar el accuracy real
    train_metrics: Optional[dict] = None  # mismas 4 metricas que "metrics" pero sobre train del ultimo fold, para chequear overfitting
    confusion: Optional[dict] = None  # {"labels": ["Green","Red"], "matrix": [[..],[..]]} sobre el conjunto out-of-fold (walk-forward)
    roc: Optional[dict] = None  # {"auc": float, "points": [{fpr, tpr}, ...]} sobre el conjunto out-of-fold (walk-forward)

@dataclass
class PredictionResult:
    model_name: str
    predictions: list
    predicted_at: datetime = field(default_factory=datetime.now)