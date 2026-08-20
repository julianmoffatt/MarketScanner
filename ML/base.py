from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd


class BaseModel(ABC):
    """
    Contrato que debe cumplir cualquier modelo del proyecto.
    Toda clase de modelo (sklearn, xgboost, torch, etc.) debe
    heredar de aquí e implementar fit() y predict().
    """

    name: str = "base_model"

    def __init__(self, **hyperparams: Any) -> None:
        self.hyperparams = hyperparams
        self.model_: Any = None          # aquí guarda cada subclase su objeto real
        self.is_fitted: bool = False

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseModel":
        ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        ...

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError(f"{self.name} no soporta predict_proba")

    def save(self, path: str | Path) -> None:
        if not self.is_fitted:
            raise RuntimeError("No se puede guardar un modelo sin entrenar")
        joblib.dump(self, Path(path))

    @classmethod
    def load(cls, path: str | Path) -> "BaseModel":
        return joblib.load(Path(path))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} fitted={self.is_fitted} params={self.hyperparams}>"
