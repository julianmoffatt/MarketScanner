"""
XGBRegressor no es de sklearn, pero sus autores lo diseñaron a proposito
para imitar la interfaz de sklearn (fit/predict/get_params/set_params) --
por eso encaja en el mismo patron que RandomForest, sin wrapper adicional.
"""

from xgboost import XGBRegressor
from .registry import register_model


@register_model("xgboost_regressor")
class XGBoostModel(XGBRegressor):

    task_type = "regression"

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
