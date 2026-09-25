"""
Rutas HTTP para los resultados de entrenamiento de ML.
Capa delgada: solo traduce HTTP <-> Python, no entrena nada aqui.
"""
from fastapi import APIRouter
from ..schemas import ML_Training_Response
from ...services import model_training_service

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/{ticker}/training", response_model=ML_Training_Response)
def get_training_results(ticker: str):
    results = model_training_service.run_training_comparison(ticker)
    panels = []
    for result in results:
        top_features = sorted(
            (result.feature_importance or {}).items(), key=lambda kv: -kv[1]
        )[:15]
        panels.append({
            "model_name": result.model_name,
            "metrics": result.metrics,
            "train_metrics": result.train_metrics,
            "baseline_accuracy": result.baseline_accuracy,
            "confusion": result.confusion,
            "roc": result.roc,
            "top_features": [{"feature": k, "importance": v} for k, v in top_features],
            "calibration": result.calibration or [],
            "n_train": result.n_train,
            "n_test": result.n_test,
        })
    return {"ticker": ticker, "panels": panels}
