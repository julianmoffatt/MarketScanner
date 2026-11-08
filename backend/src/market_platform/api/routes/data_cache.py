"""
Ruta HTTP para borrar los datos de mercado descargados y las caches en memoria.
Capa delgada: la logica esta en services/data_cache_service.py.

Es una operacion destructiva y sin autenticacion, igual que el resto de la API:
pensada para uso local. Si la API se publicara, habria que protegerla.
"""
from fastapi import APIRouter
from ..schemas import DataCacheClear_Response
from ...services import data_cache_service

router = APIRouter(prefix="/data-cache", tags=["data-cache"])


@router.post("/clear", response_model=DataCacheClear_Response)
def clear_data_cache():
    return data_cache_service.clear_market_data()
