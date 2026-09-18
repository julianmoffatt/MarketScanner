from typing import Optional, Sequence
from sklearn.metrics import (
    mean_absolute_error, r2_score, root_mean_squared_error,
    accuracy_score, precision_score, recall_score, f1_score,
)
from .models.registry import get_model
from .results import TrainingResult, PredictionResult
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.base import is_classifier, is_regressor

def compute_regression_metrics(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(root_mean_squared_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }

def compute_classification_metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }

def train_model(
    model_name: str,
    X,
    y,
    model_params: Optional[dict] = None,
    feature_names: Optional[Sequence[str]] = None,
    test_size: float = 0.2,
) -> TrainingResult:
    """
    Caso de uso: entrena `model_name` (tal como esta registrado en ML.models.registry) sobre (X, y)
    """
    model_params = model_params or {}

    model = get_model(model_name, **model_params) 
    # 1. Split temporal final
    split = int(len(X) * test_size)
    X_train = X.iloc[:split]
    X_test = X.iloc[split:]
    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    # 2. TimeSeriesSplit SOLO sobre X_train
    tscv = TimeSeriesSplit(n_splits=5)

    # Grid generico: solo se prueban los hiperparametros que el modelo
    # realmente acepta (RandomForest y XGBoost no comparten todos).
    candidate_grid = {
        'n_estimators': [50, 100],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5],
    }
    param_grid = {k: v for k, v in candidate_grid.items() if k in model.get_params()}

    grid = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=tscv,
        scoring='accuracy' if is_classifier(model) else 'r2',
    )

    grid.fit(X_train, y_train)
    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)

    if is_classifier(model):
        metrics = compute_classification_metrics(y_test, y_pred)
    elif is_regressor(model):
        metrics = compute_regression_metrics(y_test, y_pred)
    else:
        raise ValueError(f"No se pudo determinar el tipo de tarea para {type(model).__name__}")

    try:
        importances = best_model.feature_importance()
        names = feature_names if feature_names is not None else [f"x{i}" for i in range(len(importances))]
        feature_importance = {name: float(v) for name, v in zip(names, importances)}
    except NotImplementedError:
        feature_importance = None

    return TrainingResult(
        model_name=model_name,
        params=best_model.get_params(),
        metrics=metrics,
        feature_importance=feature_importance,
        n_train=len(X_train),
        n_test=len(X_test),
    )


def predict(model_name: str, modelo, X) -> PredictionResult:
    preds = modelo.predict(X)
    return PredictionResult(model_name=model_name, predictions=list(map(float, preds)))