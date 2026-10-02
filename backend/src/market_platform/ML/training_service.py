from typing import Optional
import numpy as np
from sklearn.metrics import (
    mean_absolute_error, r2_score, root_mean_squared_error,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, roc_auc_score,
)
from .models.registry import get_model
from .results import TrainingResult, PredictionResult
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.calibration import calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.base import is_classifier, is_regressor, clone

def compute_regression_metrics(y_true, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(root_mean_squared_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }

def compute_classification_metrics(y_true, y_pred, pos_label="Green") -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=pos_label, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=pos_label, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, pos_label=pos_label, zero_division=0)),
    }

def _build_pipeline(model, numeric_features, categorical_features):
    # Las features numericas se escalan con StandardScaler.
    # A los arboles (RandomForest/XGBoost) escalar no les cambia nada -- es una transformacion monotona,
    # pero a un modelo lineal (logistic regression) SI
    numeric_transformer = Pipeline(steps=[('scaler', StandardScaler())])
    categorical_transformer = Pipeline(steps=[('onehot', OneHotEncoder(handle_unknown='ignore', drop='if_binary'))])
    preprocessor = ColumnTransformer(transformers=[('num', numeric_transformer, numeric_features), ('cat', categorical_transformer, categorical_features)])
    return Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])


def _apply_class_balance(model, y_train):
    # Balance de clases: cada modelo lo resuelve con un mecanismo distinto
    if "class_weight" in model.get_params():
        model.set_params(class_weight="balanced")
    elif "scale_pos_weight" in model.get_params():
        neg = int((y_train == 0).sum())
        pos = int((y_train == 1).sum())
        model.set_params(scale_pos_weight=(neg / pos) if pos else 1.0)


def train_model(
    model_name: str,
    X,
    y,
    model_params: Optional[dict] = None,
) -> TrainingResult:
    """
    Caso de uso: entrena `model_name` (tal como esta registrado en ML.models.registry) sobre (X, y)

    Walk-forward (TimeSeriesSplit) en vez de un unico split final: antes se
    evaluaba solo sobre el ultimo 20% del historico (un unico regimen de
    mercado, que podia haber sido casualmente favorable o adverso). Ahora se
    recorren varios folds cronologicos -- cada uno entrena con todo el
    pasado disponible hasta ese punto (con al menos la mitad mas antigua del
    historico como ancla minima, ver mas abajo) y predice sobre el tramo
    siguiente, nunca al reves -- y las predicciones out-of-fold de TODOS los
    folds se concatenan en un unico conjunto sobre el que se calculan
    metricas, matriz de confusion, ROC y calibracion. Eso cubre ~la mitad
    mas reciente del historico como test acumulado (repartida en varios
    folds cronologicos), en vez del 20% final fijo de antes.

    El modelo que se devuelve para predecir en vivo (X_latest) se reentrena
    aparte sobre TODO el historico disponible una vez validado el walk-
    forward -- antes, al usar un unico split, el modelo en produccion nunca
    llegaba a ver el ultimo 20% de las velas.
    """
    model_params = model_params or {}
    template_model = get_model(model_name, **model_params)

    numeric_features = X.select_dtypes(include=['number']).columns.tolist()
    categorical_features = X.select_dtypes(include=["object", "category"]).columns.tolist()

    # XGBoost (a diferencia de RandomForest) no acepta etiquetas de texto,
    # solo enteros -- codificamos el target siempre igual para cualquier
    # clasificador, asi el comportamiento no depende de que modelo se use.
    # Se ajusta sobre TODO y de una vez, no por fold: es solo un mapeo
    # texto->entero de un conjunto de clases fijo y conocido (Green/Red),
    # no depende del orden ni del valor de ninguna fila concreta, asi que
    # ajustarlo sobre el dataset completo antes de partir en folds no
    # introduce ninguna fuga de informacion futura.
    label_encoder = None
    if is_classifier(template_model):
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
    else:
        y_encoded = y.to_numpy()

    # Se reserva un ancla minima de entrenamiento ANTES de evaluar el primer fold
    ANCHOR_PREFERRED_ROWS = 50 * 52
    MAX_ANCHOR_FRACTION = 0.7
    anchor = max(len(X) // 2, min(ANCHOR_PREFERRED_ROWS, int(len(X) * MAX_ANCHOR_FRACTION)))
    usable_for_folds = len(X) - anchor
    # Umbral de 200 filas (~4 años) por fold en vez de 50: menos folds pero
    # mas grandes, sin tocar el tamaño total de usable_for_folds -- cada
    # AUC individual (visto en el diagnostico fold-a-fold de SP500/NASDAQ)
    # era demasiado ruidoso con folds de ~80-120 filas.
    n_splits = max(2, min(5, usable_for_folds // 200))
    test_size = usable_for_folds // n_splits
    tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)

    # 1. Hiperparametros fijos, no buscados por ticker. Para generalizar parametros al probar el modelo a tra ves de los distintos assets
    #
    # Regularizados tras el cambio a walk-forward: con el split unico de
    # antes, min_samples_split/leaf=20 y XGB n_estimators=50 daban un gap
    # train/test razonable -- pero evaluando ahora sobre varios folds y
    # regimenes de mercado (mas exigente), esos mismos valores se traducian
    # en gaps de 20-35 puntos en varios tickers (XGB especialmente: hasta
    # +35.6 en NVDA), con un modelo memorizando el fold de turno sin que
    # eso se tradujera en mas edge real sobre el baseline. Ablation
    # controlado (SP500, NASDAQ, EURGBP, AUDUSD, AAPL, NVDA, walk-forward
    # completo) confirma que esta version mas conservadora baja el gap
    # medio de 14.0 a 10.6 puntos SIN perder edge medio sobre baseline (de
    # hecho mejora ligeramente, de -0.66 a -0.11 pts) -- menos overfitting,
    # no menos señal real.
    n_estimators = 100 if model_name == "random_forest_classifier" else 25
    fixed_params = {
        'n_estimators': n_estimators,
        'max_depth': 3,
        'min_samples_split': 35,
        'min_samples_leaf': 35,
        'learning_rate': 0.03,
        'subsample': 0.7,
        'colsample_bytree': 0.7,
        'C': 0.3,
    }

    # 2. Bucle walk-forward: un fit por fold, todas las predicciones
    # out-of-fold se van acumulando para evaluarlas juntas al final.
    y_true_oof, y_pred_oof, y_proba_oof = [], [], []
    baseline_pred_oof = []
    last_fold_pipeline, last_fold_X_train, last_fold_y_train = None, None, None

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y_encoded[train_idx], y_encoded[test_idx]

        model = clone(template_model)
        if is_classifier(model):
            _apply_class_balance(model, y_train)
        model.set_params(**{k: v for k, v in fixed_params.items() if k in model.get_params()})

        pipeline = _build_pipeline(model, numeric_features, categorical_features)
        pipeline.fit(X_train, y_train)

        y_pred_oof.append(pipeline.predict(X_test))
        y_true_oof.append(y_test)

        if is_classifier(model):
            y_proba_oof.append(pipeline.predict_proba(X_test))
            # Baseline trivial por fold, igual que el modelo real: un
            # DummyClassifier que siempre predice la clase mayoritaria de
            # ESE fold de train, evaluado sobre ESE fold de test -- asi la
            # comparacion final es justa (mismos tramos exactos para ambos).
            dummy = DummyClassifier(strategy="most_frequent")
            dummy.fit(X_train, y_train)
            baseline_pred_oof.append(dummy.predict(X_test))

        last_fold_pipeline, last_fold_X_train, last_fold_y_train = pipeline, X_train, y_train

    y_true_oof = np.concatenate(y_true_oof)
    y_pred_oof = np.concatenate(y_pred_oof)

    calibration = None
    baseline_accuracy = None
    train_metrics = None
    confusion = None
    roc = None
    if is_classifier(template_model):
        y_proba_oof = np.concatenate(y_proba_oof)
        baseline_pred_oof = np.concatenate(baseline_pred_oof)
        pos_label = label_encoder.transform(["Green"])[0]

        metrics = compute_classification_metrics(y_true_oof, y_pred_oof, pos_label=pos_label)

        # Train vs Test (overfitting gap): se toma el ULTIMO fold -- es el
        # que mas historico acumula en su train, el mas parecido al modelo
        # final que se reentrena sobre todo el dataset a continuacion.
        y_train_pred = last_fold_pipeline.predict(last_fold_X_train)
        train_metrics = compute_classification_metrics(last_fold_y_train, y_train_pred, pos_label=pos_label)

        # Baseline trivial: accuracy del DummyClassifier acumulado sobre
        # los mismos tramos out-of-fold que el modelo real, para que la
        # comparacion sea sobre exactamente los mismos datos.
        baseline_accuracy = float(accuracy_score(y_true_oof, baseline_pred_oof))

        # Matriz de confusion: filas/columnas en el orden [Green, Red] para
        # que sea legible directamente en el frontend sin decodificar nada.
        label_order = label_encoder.transform(["Green", "Red"])
        confusion = {
            "labels": ["Green", "Red"],
            "matrix": confusion_matrix(y_true_oof, y_pred_oof, labels=label_order).tolist(),
        }

        # Curva de calibracion (reliability diagram) sobre el conjunto
        # out-of-fold completo: agrupa las probabilidades predichas en
        # deciles (strategy="quantile", mismo numero de muestras por bin) y
        # compara, por bin, la probabilidad media predicha vs. la tasa real
        # de acierto -- si el modelo estuviera bien calibrado, ambas
        # coincidirian (la diagonal y=x).
        y_proba = y_proba_oof[:, pos_label]
        prob_true, prob_pred = calibration_curve(y_true_oof, y_proba, pos_label=pos_label, n_bins=10, strategy="quantile")
        calibration = [
            {"prob_pred": float(pp), "prob_true": float(pt)}
            for pp, pt in zip(prob_pred, prob_true)
        ]

        # ROC / AUC: se reconstruye y_true_oof como binario "es Green o no"
        # (1/0) para no depender de si Green quedo codificado como 0 o como
        # 1 -- asi roc_auc_score/roc_curve interpretan "1" como positivo
        # sin ambiguedad, sea cual sea el valor real que le dio el
        # LabelEncoder.
        y_is_green = (y_true_oof == pos_label).astype(int)
        fpr, tpr, _ = roc_curve(y_is_green, y_proba)
        roc = {
            "auc": float(roc_auc_score(y_is_green, y_proba)),
            "points": [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)],
        }
    elif is_regressor(template_model):
        metrics = compute_regression_metrics(y_true_oof, y_pred_oof)
    else:
        raise ValueError(f"No se pudo determinar el tipo de tarea para {type(template_model).__name__}")

    # 3. Modelo final para produccion (prediccion en vivo sobre X_latest):
    # se reentrena desde cero sobre TODO el historico, no sobre el ultimo
    # fold -- el walk-forward de arriba es solo para VALIDAR el enfoque, el
    # modelo que de verdad predice la semana que viene debe aprovechar
    # tambien las filas mas recientes, que en un split unico se quedaban
    # fuera del entrenamiento.
    final_model = clone(template_model)
    if is_classifier(final_model):
        _apply_class_balance(final_model, y_encoded)
    final_model.set_params(**{k: v for k, v in fixed_params.items() if k in final_model.get_params()})
    best_model = _build_pipeline(final_model, numeric_features, categorical_features)
    best_model.fit(X, y_encoded)

    try:
        importances = best_model.named_steps["classifier"].feature_importance()
        # Los nombres pre-encoding (feature_names) ya no sirven aqui: el
        # preprocessor expande day_of_week/type en varias columnas one-hot,
        # asi que la cuenta y el orden cambian. Hay que pedirselos al propio
        # ColumnTransformer ya ajustado, que es quien sabe la forma final.
        names = best_model.named_steps["preprocessor"].get_feature_names_out()
        feature_importance = {name: float(v) for name, v in zip(names, importances)}
    except NotImplementedError:
        feature_importance = None

    return TrainingResult(
        model_name=model_name,
        params=best_model.get_params(),
        metrics=metrics,
        feature_importance=feature_importance,
        n_train=len(X),
        n_test=len(y_true_oof),
        model=best_model,
        label_encoder=label_encoder,
        calibration=calibration,
        baseline_accuracy=baseline_accuracy,
        train_metrics=train_metrics,
        confusion=confusion,
        roc=roc,
    )


def predict(model_name: str, modelo, X) -> PredictionResult:
    preds = modelo.predict(X)
    return PredictionResult(model_name=model_name, predictions=list(map(float, preds)))
