_REGISTRY: dict[str, type] = {}

def register_model(name: str):
    def decorator(cls):
        if name in _REGISTRY and _REGISTRY[name] is not cls:
            raise ValueError(f"Ya existe un modelo registrado como '{name}': {_REGISTRY[name]}")
        _REGISTRY[name] = cls
        return cls
    return decorator

def get_strategy(name: str):
    """Factory: instancia la estrategia pedida por nombre."""
    if name not in _REGISTRY:
        raise ValueError(f"Estrategia '{name}' no registrada. Disponibles: {available_strategys()}")
    return _REGISTRY[name]()

def available_strategys() -> list:
    return sorted(_REGISTRY.keys())