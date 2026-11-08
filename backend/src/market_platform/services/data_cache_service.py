from pathlib import Path
from .. import pipeline
from ..data import storage
from . import fundamentals_service, model_training_service

# Carpetas de backend/data con datos descargables de nuevo desde Yahoo Finance.
# "external" no se toca: no se genera con yfinance.
DOWNLOADED_SECTIONS = ("raw", "processed")


def clear_market_data() -> dict:
    """Borra los CSV descargados (raw) y procesados (processed) y vacia las caches
    en memoria. No descarga nada: cuando una pantalla pida un ticker, el pipeline
    ve que faltan los archivos y los baja de Yahoo Finance de nuevo.

    Los archivos se borran antes de vaciar la memoria: al reves, una peticion
    entre medias podria volver a cargar en memoria datos que ya no estan en disco.
    Un archivo que no se pueda borrar (ej. abierto por otro proceso en Windows)
    no detiene el resto: se informa en 'failed'.
    """
    base = Path(storage.url_database())
    deleted = {section: 0 for section in DOWNLOADED_SECTIONS}
    failed = []

    for section in DOWNLOADED_SECTIONS:
        for path in sorted((base / section).glob("*.csv")):
            try:
                path.unlink()
                deleted[section] += 1
            except OSError as e:
                failed.append({"file": f"{section}/{path.name}", "error": str(e)})

    pipeline.clear_cache()
    model_training_service.clear_cache()
    fundamentals_service.clear_cache()
    return {"deleted_raw": deleted["raw"], "deleted_processed": deleted["processed"], "failed": failed}
