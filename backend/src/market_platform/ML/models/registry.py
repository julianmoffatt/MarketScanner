_REGISTRY: dict[str, type] = {}

def register_model(name: str):
    """
    Decorador: registra la clase bajo `name`. Se usa una vez, encima de
    la definicion de cada modelo concreto:

        @register_model("linear_regression")
        class LinearRegressionModel(BaseModel):
            ...
    """
    def decorator(cls):
        if name in _REGISTRY and _REGISTRY[name] is not cls:
            raise ValueError(f"Ya existe un modelo registrado como '{name}': {_REGISTRY[name]}")
        _REGISTRY[name] = cls
        return cls
    return decorator


def get_model(name: str, **kwargs):
    """Factory: instancia el modelo pedido por nombre, con sus hiperparametros."""
    if name not in _REGISTRY:
        raise KeyError(f"Modelo '{name}' no registrado. Disponibles: {available_models()}")
    return _REGISTRY[name](**kwargs)


def available_models() -> list:
    return sorted(_REGISTRY.keys())