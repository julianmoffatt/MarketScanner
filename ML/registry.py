from __future__ import annotations

from typing import Any, Callable

from base import BaseModel


class ModelRegistry:
    """
    Registro central de modelos. Cada modelo se "apunta" con un nombre
    usando el decorador @ModelRegistry.register("nombre"), y luego se
    puede instanciar por ese nombre sin necesidad de if/elif.
    """

    _models: dict[str, type[BaseModel]] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[BaseModel]], type[BaseModel]]:
        def decorator(model_cls: type[BaseModel]) -> type[BaseModel]:
            cls._models[name] = model_cls
            model_cls.name = name
            return model_cls
        return decorator

    @classmethod
    def create(cls, name: str, **hyperparams: Any) -> BaseModel:
        if name not in cls._models:
            raise KeyError(
                f"Modelo '{name}' no registrado. Disponibles: {list(cls._models)}"
            )
        return cls._models[name](**hyperparams)

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._models.keys())
