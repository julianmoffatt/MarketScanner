"""
Rutas HTTP de los screeners: una tabla con una fila por valor de un universo (config.yaml).
Capa delgada: solo traduce HTTP <-> Python, no calcula nada aqui.
Cada screener nuevo es una ruta mas bajo /screeners/<nombre>/{universe}.
"""
from fastapi import APIRouter
from ..schemas import MeanReversionScreener_Response
from ...services import screener_service

router = APIRouter(prefix="/screeners", tags=["screeners"])

@router.get("/mean_reversion/{universe}", response_model=MeanReversionScreener_Response)
def get_mean_reversion_screener(universe: str):
    rows = screener_service.get_mean_reversion_screener(universe)
    return {"universe": universe, "rows": rows}
