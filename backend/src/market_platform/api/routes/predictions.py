"""
Rutas HTTP para la prediccion en vivo (candela de manana) de ML.
Capa delgada: solo traduce HTTP <-> Python, no predice nada aqui.
"""
from fastapi import APIRouter
from ..schemas import ML_Prediction_Response
from ...services import model_training_service

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/{ticker}/prediction", response_model=ML_Prediction_Response)
def get_prediction(ticker: str):
    as_of_date, predictions = model_training_service.run_prediction(ticker)
    panels = [
        {
            "model_name": p["model_name"],
            "predicted_type": p["predicted_type"],
            "probability_green": p["probabilities"].get("Green", 0.0),
            "probability_red": p["probabilities"].get("Red", 0.0),
        }
        for p in predictions
    ]
    return {"ticker": ticker, "as_of_date": str(as_of_date), "panels": panels}
