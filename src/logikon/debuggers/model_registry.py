from __future__ import annotations

from typing import MutableMapping, Any


_model_registry: MutableMapping[str, Any] = {}


def register_model(model_id: str, model: Any):
    if model_id in _model_registry:
        raise ValueError(
            f"Duplicate model id. Model of type {type(_model_registry[model_id])} already registered under id {model_id}."
        )
    _model_registry[model_id] = model


def get_registry_model(model_id: str):
    return _model_registry.get(model_id)
