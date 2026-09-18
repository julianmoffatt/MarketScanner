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
                 random_state: int | None = None, class_weight=None, **kwargs):
        super().__init__(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            class_weight=class_weight,
            **kwargs,
        )

    def feature_importance(self):
        return self.feature_importances_