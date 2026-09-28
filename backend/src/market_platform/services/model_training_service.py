import threading
from functools import lru_cache
from .. import pipeline
from ..features.build_features_ML import build_features_ML
from ..ML.training_service import train_model

CLASSIFIER_MODELS = ["random_forest_classifier", "xgboost_classifier", "logistic_regression"]

# Candado por ticker: sin esto, dos peticiones casi simultaneas para el mismo
# ticker nuevo (ej. el doble-fetch de React StrictMode en desarrollo, o dos
# usuarios pidiendo lo mismo a la vez) entran juntas en un "cache miss" de
# lru_cache -- que no es thread-safe frente a eso -- y las dos entrenan por
# su cuenta en paralelo, duplicando el coste de CPU.
# Con el lock, la segunda espera a que la primera termine y cachee,
# y reutiliza ese resultado en vez de re-entrenar.

_locks_by_asset = {}
_locks_guard = threading.Lock()

def _get_asset_lock(asset):
    with _locks_guard:
        if asset not in _locks_by_asset:
            _locks_by_asset[asset] = threading.Lock()
        return _locks_by_asset[asset]

def _macro_weekly(symbol):
    # ^TNX/^IRX se cachean solos via el propio lru_cache de
    # pipeline.processedTimeframes -- es el mismo valor para cualquier
    # activo esa semana, no hace falta cachearlo de nuevo aqui.
    timeframes = pipeline.processedTimeframes(symbol, 0)
    return timeframes[1].reset_index(names="date")


@lru_cache(maxsize=32)
def _train_all_models_cached(asset):
    timeframes = pipeline.processedTimeframes(asset, 0)  # daily, weekly, etc
    weekly = timeframes[1].reset_index(names="date")
    tnx_weekly = _macro_weekly("^TNX")
    irx_weekly = _macro_weekly("^IRX")
    X, y, X_latest = build_features_ML(weekly, tnx_weekly, irx_weekly)
    as_of_date = weekly["date"].iloc[-1]
    results = [train_model(model_name, X, y) for model_name in CLASSIFIER_MODELS]
    return results, X_latest, as_of_date


def _train_all_models(asset):
    with _get_asset_lock(asset):
        return _train_all_models_cached(asset)


def run_training(asset="sp500", model_name="random_forest_classifier"):
    results, _, _ = _train_all_models(asset)
    return next(r for r in results if r.model_name == model_name)


def run_training_comparison(asset="sp500"):
    results, _, _ = _train_all_models(asset)
    return results


def run_prediction(asset="sp500"):
    """Predice el tipo de vela de la PROXIMA SEMANA usando la fila mas reciente"""
    results, X_latest, as_of_date = _train_all_models(asset)
    predictions = []
    for result in results:
        proba = result.model.predict_proba(X_latest)[0]
        classes = result.label_encoder.classes_
        probabilities = dict(zip(classes, proba.tolist()))
        predicted_type = classes[proba.argmax()]
        predictions.append({
            "model_name": result.model_name,
            "predicted_type": predicted_type,
            "probabilities": probabilities,
        })
    return as_of_date, predictions
