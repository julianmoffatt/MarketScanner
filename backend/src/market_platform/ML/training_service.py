from typing import Optional
import numpy as np
from sklearn.metrics import (
    mean_absolute_error, r2_score, root_mean_squared_error,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, roc_auc_score,
)
from .models.registry import get_model
from .results import TrainingResult, PredictionResult
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.calibration import calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.base import is_classifier, is_regressor

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

def train_model(
    model_name: str,
    X,
    y,
    model_params: Optional[dict] = None,
    test_size: float = 0.2,
) -> TrainingResult:
    """
    Caso de uso: entrena `model_name` (tal como esta registrado en ML.models.registry) sobre (X, y)
    """
    model_params = model_params or {}

    model = get_model(model_name, **model_params) 
    # 1. Split temporal final
    split = int(len(X) * (1 - test_size))
    X_train = X.iloc[:split]
    X_test = X.iloc[split:]
    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    # XGBoost (a diferencia de RandomForest) no acepta etiquetas de texto,
    # solo enteros -- codificamos el target siempre igual para cualquier
    # clasificador, asi el comportamiento no depende de que modelo se use.
    label_encoder = None
    if is_classifier(model):
        label_encoder = LabelEncoder()
        y_train = label_encoder.fit_transform(y_train)
        y_test = label_encoder.transform(y_test)

        # Balance de clases: cada modelo lo resuelve con un mecanismo
        # distinto, no hay un unico "class_weight" universal. RandomForest
        # tiene class_weight nativo de sklearn ("balanced" pesa cada clase
        # segun su frecuencia inversa). XGBoost no tiene class_weight -- usa
        # scale_pos_weight, un numero unico (no un string) que hay que
        # calcular a mano como neg/pos, porque depende del balance real de
        # ESTE y_train concreto, no es un valor fijo de antemano.
        if "class_weight" in model.get_params():
            model.set_params(class_weight="balanced")
        elif "scale_pos_weight" in model.get_params():
            neg = int((y_train == 0).sum())
            pos = int((y_train == 1).sum())
            model.set_params(scale_pos_weight=(neg / pos) if pos else 1.0)

    numeric_features = X_train.select_dtypes(include=['number']).columns.tolist()
    categorical_features = X_train.select_dtypes(include=["object", "category"]).columns.tolist()

   
    # One-hot encode the categoricals. Las numericas se escalan con
    # StandardScaler: a los arboles (RandomForest/XGBoost) escalar no les
    # cambia nada -- es una transformacion monotona, los splits quedan
    # identicos -- pero a un modelo lineal (logistic regression) SI le hace
    # falta, o las features con rango mas grande dominarian el ajuste solo
    # por su escala, no por su relevancia real.
    numeric_transformer = Pipeline(steps=[('scaler', StandardScaler())])
    categorical_transformer = Pipeline(steps=[('onehot', OneHotEncoder(handle_unknown='ignore', drop='if_binary'))])
    preprocessor = ColumnTransformer(transformers=[('num', numeric_transformer, numeric_features),('cat', categorical_transformer, categorical_features)])
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])

    # 2. TimeSeriesSplit SOLO sobre X_train
    tscv = TimeSeriesSplit(n_splits=5)

    # Grid generico: solo se prueban los hiperparametros que el modelo
    # realmente acepta (RandomForest y XGBoost no comparten todos), via el
    # filtro "k in model.get_params()" de la linea de abajo.
    #
    # max_depth/n_estimators antes solo ofrecian opciones sin apenas freno
    # (None, 10, 20 -- nada realmente "poco profundo"), y min_samples_split
    # nunca llegaba a aplicarse (bug ya arreglado en RandomForestClassifier.py).
    # Resultado medido: 100% accuracy en train, ~48-52% en test -- overfitting
    # de libro. Este grid añade opciones que SI regularizan de verdad:
    # - max_depth mas bajo (3, 5) ademas de 10, en vez de dejar crecer sin limite.
    # - min_samples_leaf (solo RandomForest): exige varias muestras por hoja,
    #   evita que el arbol memorice casos aislados.
    # - learning_rate/subsample (solo XGBoost): learning_rate mas bajo que el
    #   0.3 por defecto, y subsample<1 para que cada arbol de boosting vea
    #   solo una parte de los datos, en vez de sobreajustar al 100% de train.
    candidate_grid = {
        'n_estimators': [50, 100],
        'max_depth': [2, 3, 5],
        'min_samples_leaf': [5, 10, 20],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.7, 1.0],
        'C': [0.01, 0.1, 1, 10],  # solo logistic regression -- fuerza de regularizacion (inversa)
    }
    param_grid = {f"classifier__{k}": v for k, v in candidate_grid.items() if k in model.get_params()}

    grid = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=tscv,
        scoring='accuracy' if is_classifier(model) else 'r2',
    )

    grid.fit(X_train, y_train)
    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test)

    calibration = None
    baseline_accuracy = None
    train_metrics = None
    confusion = None
    roc = None
    if is_classifier(model):
        pos_label = label_encoder.transform(["Green"])[0]
        metrics = compute_classification_metrics(y_test, y_pred, pos_label=pos_label)

        # Train vs Test: mismo modelo ya ajustado, prediciendo sobre train --
        # si el accuracy de train es mucho mayor que el de test, es la señal
        # clasica de overfitting (el modelo memorizo en vez de generalizar).
        y_train_pred = best_model.predict(X_train)
        train_metrics = compute_classification_metrics(y_train, y_train_pred, pos_label=pos_label)

        # Baseline trivial: un DummyClassifier que siempre predice la clase
        # mayoritaria de train. Si el modelo real no le saca ventaja clara,
        # no hay edge real por mucho que el accuracy "suene" bien.
        dummy = DummyClassifier(strategy="most_frequent")
        dummy.fit(X_train, y_train)
        baseline_accuracy = float(accuracy_score(y_test, dummy.predict(X_test)))

        # Matriz de confusion: filas/columnas en el orden [Green, Red] para
        # que sea legible directamente en el frontend sin decodificar nada.
        label_order = label_encoder.transform(["Green", "Red"])
        confusion = {
            "labels": ["Green", "Red"],
            "matrix": confusion_matrix(y_test, y_pred, labels=label_order).tolist(),
        }

        # Curva de calibracion (reliability diagram) sobre el test set: agrupa
        # las probabilidades predichas en deciles (strategy="quantile", mismo
        # numero de muestras por bin) y compara, por bin, la probabilidad
        # media predicha vs. la tasa real de acierto -- si el modelo estuviera
        # bien calibrado, ambas coincidirian (la diagonal y=x).
        y_proba = best_model.predict_proba(X_test)[:, pos_label]
        prob_true, prob_pred = calibration_curve(y_test, y_proba, pos_label=pos_label, n_bins=10, strategy="quantile")
        calibration = [
            {"prob_pred": float(pp), "prob_true": float(pt)}
            for pp, pt in zip(prob_pred, prob_true)
        ]

        # ROC / AUC: se reconstruye y_test como binario "es Green o no" (1/0)
        # para no depender de si Green quedo codificado como 0 o como 1 --
        # asi roc_auc_score/roc_curve interpretan "1" como positivo sin
        # ambiguedad, sea cual sea el valor real que le dio el LabelEncoder.
        y_test_is_green = (y_test == pos_label).astype(int)
        fpr, tpr, _ = roc_curve(y_test_is_green, y_proba)
        roc = {
            "auc": float(roc_auc_score(y_test_is_green, y_proba)),
            "points": [{"fpr": float(f), "tpr": float(t)} for f, t in zip(fpr, tpr)],
        }
    elif is_regressor(model):
        metrics = compute_regression_metrics(y_test, y_pred)
    else:
        raise ValueError(f"No se pudo determinar el tipo de tarea para {type(model).__name__}")

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
        n_train=len(X_train),
        n_test=len(X_test),
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