# utils/config.py
import yaml
from pathlib import Path

def load_config(path: str = None) -> dict:
    if path is None:
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        path = backend_dir / "config" / "config.yaml"
    with open(Path(path)) as f:
        return yaml.safe_load(f)