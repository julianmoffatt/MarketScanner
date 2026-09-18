from pathlib import Path
import joblib

def models_dir() -> Path:
    current_dir = Path(__file__).resolve()
    backend_dir = current_dir.parent.parent.parent.parent
    path = backend_dir / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_model(model, name: str) -> Path:
    path = models_dir() / (name + ".joblib")
    joblib.dump(model, path)
    print("Modelo guardado: ", path)
    return path


def load_model(name: str):
    try:
        path = models_dir() / (name + ".joblib")
        model = joblib.load(path)
        print("Modelo cargado: ", path)
        return model
    except Exception as e:
        return False
