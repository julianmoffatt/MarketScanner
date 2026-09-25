"""
Baseline lineal: sirve para contestar "¿hacia falta tanta complejidad
(arboles/boosting), o un modelo lineal simple daba lo mismo?" -- el mismo
Pipeline generico (preprocesado + GridSearchCV + TimeSeriesSplit + matriz
de confusion + ROC + calibracion) que ya usan RandomForest/XGBoost sirve
tal cual, sin tocar nada de training_service.py.
"""

from sklearn.linear_model import LogisticRegression
import numpy as np
from .registry import register_model


@register_model("logistic_regression")
class LogisticRegressionModel(LogisticRegression):

    task_type = "classification"

    def __init__(self, C: float = 1.0, max_iter: int = 1000,
                 random_state: int | None = 42, **kwargs):
        super().__init__(
            C=C,
            max_iter=max_iter,
            random_state=random_state,
            **kwargs,
        )

    def feature_importance(self):
        # No hay feature_importances_ en un modelo lineal -- el equivalente
        # es la magnitud (valor absoluto) de cada coeficiente: cuanto mayor,
        # mas peso tiene esa feature en la decision (una vez escaladas todas
        # a la misma unidad via StandardScaler, si no esta comparacion no
        # tendria sentido).
        return np.abs(self.coef_).flatten()
