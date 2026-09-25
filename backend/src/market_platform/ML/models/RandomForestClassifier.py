"""
RandomForestRegressor vive en sklearn, el wrapper generico ya sabe
como entrenarlo, predecir con el, y sacarle feature_importance()
(via feature_importances_, que RandomForest si expone).
"""

from sklearn.ensemble import RandomForestClassifier
from .registry import register_model

@register_model("random_forest_classifier")
class RandomForestModel(RandomForestClassifier):

    task_type = "classification"

    def __init__(self, n_estimators: int = 100, max_depth: int | None = None,
                 min_samples_split: int = 2, min_samples_leaf: int = 1,
                 random_state: int | None = 42, class_weight=None, **kwargs):
        # min_samples_split/leaf declarados explicitos (no dentro de **kwargs):
        # sklearn arma get_params() introspeccionando la firma de __init__ y
        # descarta el propio **kwargs, asi que cualquier parametro que solo
        # viviera ahi era invisible para GridSearchCV -- nunca se ajustaba.
        super().__init__(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            class_weight=class_weight,
            **kwargs,
        )

    def feature_importance(self):
        return self.feature_importances_