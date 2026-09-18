"""
XGBClassifier imita la interfaz de sklearn (fit/predict/get_params/set_params) --
encaja en el mismo patron que RandomForestClassifier, sin wrapper adicional.
"""

from xgboost import XGBClassifier
from .registry import register_model


@register_model("xgboost_classifier")
class XGBoostModel(XGBClassifier):

    task_type = "classification"

    def __init__(self, n_estimators: int = 100, max_depth: int = 6,
                 learning_rate: float = 0.3, random_state: int | None = None, **kwargs):
        super().__init__(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            **kwargs,
        )

    def feature_importance(self):
        return self.feature_importances_
